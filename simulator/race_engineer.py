"""
Race engineer analysis module.

Processes session telemetry through the race engineer's mental model:

  Raw telemetry
  → Derived metrics (accel, yaw, slip)
  → Track position (corner/straight segmentation)
  → Per-corner analysis (entry, apex, exit speeds)
  → Lap summaries
  → Multi-lap comparison
  → Root cause: "Why was this lap slower?"
  → Prediction

Usage:
    from simulator.race_engineer import RaceEngineer

    engineer = RaceEngineer()
    engineer.load_packets(packets)
    engineer.analyze()

    summary = engineer.get_lap_summary(lap_number)
    delta = engineer.compare_laps(5, 6)  # why was lap 6 slower?
    print(delta["root_cause"])
"""

import numpy as np
import math

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class RaceEngineer:
    """
    Post-processes telemetry packets through the race engineering pipeline.
    """

    def __init__(self):
        self.packets = []
        self.lap_data = {}        # lap_number → list of packets
        self.lap_summaries = {}   # lap_number → dict of metrics
        self.corners = []         # list of corner segments
        self.sector_boundaries = []
        self._analyzed = False

    # ------------------------------------------------------------------
    #  DATA LOADING
    # ------------------------------------------------------------------

    def load_packets(self, packets: list):
        """Load raw telemetry packets."""
        self.packets = packets
        self._group_by_lap()
        self._analyzed = False

    def load_from_file(self, path: str):
        """Load packets from a session log JSON file."""
        import json
        with open(path) as f:
            packets = json.load(f)
        self.load_packets(packets)

    def _group_by_lap(self):
        """Group packets by lap number."""
        self.lap_data = {}
        for p in self.packets:
            ln = p.get("lap", 1)
            self.lap_data.setdefault(ln, []).append(p)

    # ------------------------------------------------------------------
    #  STAGE 2 — DERIVED METRICS
    # ------------------------------------------------------------------

    def compute_derived(self, packets: list) -> list:
        """Enrich each packet with acceleration, power, slip angle."""
        n = len(packets)
        if n < 2:
            return packets

        enriched = []
        for i, p in enumerate(packets):
            ep = dict(p)
            true = ep.setdefault("true", {})
            prev = packets[i - 1] if i > 0 else p
            next_p = packets[i + 1] if i < n - 1 else p

            dt = max(ep.get("t", 0) - prev.get("t", 0), 0.01)
            speed_ms = true.get("speed_kmh", 0) / 3.6
            prev_speed_ms = prev.get("true", {}).get("speed_kmh", 0) / 3.6

            # Longitudinal acceleration
            long_accel = (speed_ms - prev_speed_ms) / dt

            # Engine power estimate (kW)
            throttle = true.get("throttle", 0)
            mass = ep.get("vehicle_state", {}).get("mass_kg", 210)
            power_kw = (long_accel * mass * speed_ms) / 1000 if speed_ms > 0.1 else 0

            # Yaw rate (deg/s)
            yaw = true.get("yaw_deg", 0)
            prev_yaw = prev.get("true", {}).get("yaw_deg", 0)
            yaw_rate = (yaw - prev_yaw) / dt

            # Slip angle proxy (difference between heading and path direction)
            gx = ep.get("gps", {}).get("x", 0)
            gy = ep.get("gps", {}).get("y", 0)
            px = prev.get("gps", {}).get("x", 0)
            py = prev.get("gps", {}).get("y", 0)
            path_angle = math.degrees(math.atan2(gy - py, gx - px)) if (gx != px or gy != py) else yaw
            slip_angle = yaw - path_angle

            # Brake pressure gradient
            brake = true.get("brake_cmd", 0)
            prev_brake = prev.get("true", {}).get("brake_cmd", 0)
            brake_gradient = (brake - prev_brake) / dt

            # Throttle application rate
            prev_throttle = prev.get("true", {}).get("throttle", 0)
            throttle_rate = (throttle - prev_throttle) / dt

            # Steering rate
            steering = true.get("steering", 0)
            prev_steering = prev.get("true", {}).get("steering", 0)
            steering_rate = (steering - prev_steering) / dt

            ep["derived"] = {
                "long_accel_ms2": round(long_accel, 3),
                "yaw_rate_dps": round(yaw_rate, 3),
                "slip_angle_deg": round(slip_angle, 3),
                "power_kw": round(power_kw, 1),
                "brake_gradient": round(brake_gradient, 3),
                "throttle_rate": round(throttle_rate, 3),
                "steering_rate": round(steering_rate, 3),
            }
            enriched.append(ep)

        return enriched

    # ------------------------------------------------------------------
    #  STAGE 3 — TRACK POSITION (CORNER DETECTION)
    # ------------------------------------------------------------------

    def detect_corners(self, yaw_deg: np.ndarray, threshold: float = 3.0, min_gap: int = 8) -> list:
        """
        Detect corner segments from yaw trace.

        Returns list of dicts: {start_idx, end_idx, peak_idx, peak_yaw, direction}
        """
        corners = []
        abs_yaw = np.abs(yaw_deg)
        in_corner = False
        start = 0
        peak = 0
        peak_val = 0

        for i in range(len(abs_yaw)):
            if abs_yaw[i] > threshold and not in_corner:
                start = i
                peak = i
                peak_val = abs_yaw[i]
                in_corner = True
            elif abs_yaw[i] > threshold and in_corner:
                if abs_yaw[i] > peak_val:
                    peak_val = abs_yaw[i]
                    peak = i
            elif abs_yaw[i] <= threshold and in_corner:
                if i - start >= min_gap:
                    entry_idx = start
                    apex_idx = peak
                    exit_idx = i

                    # Find braking point (look back from entry for brake application)
                    brake_point = entry_idx
                    corners.append({
                        "start_idx": entry_idx,
                        "apex_idx": apex_idx,
                        "end_idx": exit_idx,
                        "peak_yaw": round(peak_val, 1),
                        "direction": "L" if yaw_deg[apex_idx] > 0 else "R",
                        "brake_idx": brake_point,
                    })
                in_corner = False

        self.corners = corners
        return corners

    def compute_sector_boundaries(self, track_length: int, n_sectors: int = 3):
        """Divide track into equal-length sectors."""
        sector_size = track_length // n_sectors
        self.sector_boundaries = [sector_size * i for i in range(n_sectors + 1)]

    # ------------------------------------------------------------------
    #  STAGE 4 — PER-CORNER METRICS
    # ------------------------------------------------------------------

    def compute_corner_metrics(self, packets: list, corner: dict) -> dict:
        """Compute entry/apex/exit speeds and braking metrics for one corner."""
        start = max(0, corner["start_idx"] - 5)
        apex = corner["apex_idx"]
        end = min(len(packets) - 1, corner["end_idx"] + 5)

        entry_speed = packets[start].get("true", {}).get("speed_kmh", 0)
        apex_speed = packets[apex].get("true", {}).get("speed_kmh", 0)
        exit_speed = packets[end].get("true", {}).get("speed_kmh", 0)

        # Find braking point — where brake first exceeds 0.1 before entry
        brake_idx = start
        for i in range(start, apex):
            if packets[i].get("true", {}).get("brake_cmd", 0) > 0.1:
                brake_idx = i
                break
        brake_speed = packets[brake_idx].get("true", {}).get("speed_kmh", 0)
        brake_distance = brake_speed / 3.6 * (apex - brake_idx) * 0.1

        # Minimum speed in corner
        min_speed = min(
            packets[i].get("true", {}).get("speed_kmh", float("inf"))
            for i in range(start, end + 1)
        )

        return {
            "entry_speed_kmh": round(entry_speed, 1),
            "apex_speed_kmh": round(apex_speed, 1),
            "exit_speed_kmh": round(exit_speed, 1),
            "min_speed_kmh": round(min_speed, 1),
            "brake_speed_kmh": round(brake_speed, 1),
            "brake_distance_m": round(brake_distance, 1),
            "brake_idx": brake_idx,
            "apex_idx": apex,
            "delta_entry_apex": round(entry_speed - apex_speed, 1),
            "delta_apex_exit": round(exit_speed - apex_speed, 1),
        }

    # ------------------------------------------------------------------
    #  STAGE 5-6 — TIRE & FUEL STATE
    # ------------------------------------------------------------------

    def extract_tire_fuel_state(self, packets: list) -> dict:
        """Extract tire and fuel state at start/end of a set of packets."""
        first = packets[0] if packets else {}
        last = packets[-1] if packets else {}

        tire_start = first.get("tire_state", {}) or {}
        tire_end = last.get("tire_state", {}) or {}
        fuel_start = first.get("fuel_state", {}) or {}
        fuel_end = last.get("fuel_state", {}) or {}

        return {
            "tire_wear_start_pct": tire_start.get("wear_pct", 0),
            "tire_wear_end_pct": tire_end.get("wear_pct", 0),
            "tire_surface_temp_start": tire_start.get("surface_temp_c", 0),
            "tire_surface_temp_end": tire_end.get("surface_temp_c", 0),
            "tire_grip_start": tire_start.get("grip", 1.0),
            "tire_grip_end": tire_end.get("grip", 1.0),
            "fuel_start_kg": fuel_start.get("fuel_kg", 0),
            "fuel_end_kg": fuel_end.get("fuel_kg", 0),
            "fuel_used_kg": fuel_start.get("fuel_kg", 0) - fuel_end.get("fuel_kg", 0),
        }

    # ------------------------------------------------------------------
    #  STAGE 8 — LAP SUMMARY
    # ------------------------------------------------------------------

    def compute_lap_summary(self, lap_number: int) -> dict:
        """Compress one lap into a summary dict."""
        packets = self.lap_data.get(lap_number, [])
        if not packets:
            return {"lap": lap_number, "error": "no data"}

        # Enrich with derived metrics
        enriched = self.compute_derived(packets)
        n = len(enriched)

        # Detect corners from yaw
        yaw_trace = np.array([p.get("true", {}).get("yaw_deg", 0) for p in enriched])
        corners = self.detect_corners(yaw_trace)

        # Basic stats
        speeds = np.array([p.get("true", {}).get("speed_kmh", 0) for p in enriched])
        throttles = np.array([p.get("true", {}).get("throttle", 0) for p in enriched])
        brakes = np.array([p.get("true", {}).get("brake_cmd", 0) for p in enriched])

        # Lap time (from last packet timestamp - first packet timestamp)
        t_start = enriched[0].get("t", 0)
        t_end = enriched[-1].get("t", 0)
        lap_time = t_end - t_start

        # Sector times — divide track_index into 3 sectors
        track_indices = np.array([p.get("track_index", 0) for p in enriched])
        if len(track_indices) > 0:
            max_idx = max(track_indices)
            sector_times = {}
            for s in range(3):
                s_start = max_idx * s / 3
                s_end = max_idx * (s + 1) / 3
                sector_packets = [p for p in enriched if s_start <= p.get("track_index", 0) <= s_end]
                if sector_packets:
                    sector_times[f"sector_{s+1}"] = round(
                        sector_packets[-1].get("t", 0) - sector_packets[0].get("t", 0), 3
                    )

        # Derived acceleration stats
        long_accels = np.array([p.get("derived", {}).get("long_accel_ms2", 0) for p in enriched])

        # Tire and fuel
        tire_fuel = self.extract_tire_fuel_state(enriched)

        # Corner metrics
        corner_metrics = []
        for c in corners:
            cm = self.compute_corner_metrics(enriched, c)
            corner_metrics.append(cm)

        # Driver score (0-100 composite)
        # Based on: braking consistency, throttle smoothness, corner speed maintenance
        brake_jerk = np.std(np.diff(brakes)) if len(brakes) > 1 else 0
        throttle_smoothness = 1.0 - min(np.std(np.diff(throttles)) / 0.5, 1.0) if len(throttles) > 1 else 0.5
        corner_speed_score = np.mean([c["apex_speed_kmh"] for c in corner_metrics]) / 200 if corner_metrics else 0.5
        consistency = 1.0 - min(brake_jerk / 0.3, 1.0)

        driver_score = int((throttle_smoothness * 30 + consistency * 30 + corner_speed_score * 40))

        summary = {
            "lap": lap_number,
            "lap_time": round(lap_time, 3),
            "avg_speed_kmh": round(float(np.mean(speeds)), 1),
            "top_speed_kmh": round(float(np.max(speeds)), 1),
            "avg_throttle_pct": round(float(np.mean(throttles)) * 100, 1),
            "avg_brake_pct": round(float(np.mean(brakes)) * 100, 1),
            "max_brake": round(float(np.max(brakes)) * 100, 1),
            "max_long_accel_ms2": round(float(np.max(long_accels)), 2),
            "min_long_accel_ms2": round(float(np.min(long_accels)), 2),
            "n_corners": len(corner_metrics),
            "driver_score": min(driver_score, 100),
            "tire_wear_start_pct": tire_fuel["tire_wear_start_pct"],
            "tire_wear_end_pct": tire_fuel["tire_wear_end_pct"],
            "tire_grip_start": tire_fuel["tire_grip_start"],
            "tire_grip_end": tire_fuel["tire_grip_end"],
            "tire_surface_temp_start": tire_fuel["tire_surface_temp_start"],
            "tire_surface_temp_end": tire_fuel["tire_surface_temp_end"],
            "fuel_start_kg": tire_fuel["fuel_start_kg"],
            "fuel_end_kg": tire_fuel["fuel_end_kg"],
            "fuel_used_kg": tire_fuel["fuel_used_kg"],
            "corner_metrics": corner_metrics,
        }
        summary.update(sector_times)
        return summary

    # ------------------------------------------------------------------
    #  STAGE 9 — MULTI-LAP ANALYSIS
    # ------------------------------------------------------------------

    def analyze(self):
        """Run full analysis on all laps."""
        self.lap_summaries = {}
        for ln in sorted(self.lap_data.keys()):
            summary = self.compute_lap_summary(ln)
            self.lap_summaries[ln] = summary
        self._analyzed = True

    def get_multi_lap_table(self) -> list:
        """Return list of lap summaries (Stage 9 table format)."""
        if not self._analyzed:
            self.analyze()
        return [self.lap_summaries[ln] for ln in sorted(self.lap_summaries)]

    def get_lap_summary(self, lap_number: int) -> dict:
        if not self._analyzed:
            self.analyze()
        return self.lap_summaries.get(lap_number, {})

    # ------------------------------------------------------------------
    #  STAGE 10 — ROOT CAUSE ANALYSIS
    # ------------------------------------------------------------------

    def compare_laps(self, lap_a: int, lap_b: int) -> dict:
        """
        Answer: "Why was lap B slower/faster than lap A?"

        Returns dict with:
          - delta_total: time difference (s)
          - sector_deltas: {sector_1: delta, sector_2: delta, sector_3: delta}
          - corner_deltas: [{corner, entry_delta, apex_delta, exit_delta}]
          - tire_delta: change in tire state between laps
          - fuel_delta: change in fuel state between laps
          - root_cause: human-readable explanation string
          - primary_factor: which factor contributed most
        """
        sa = self.get_lap_summary(lap_a)
        sb = self.get_lap_summary(lap_b)

        if not sa or not sb:
            return {"error": "One or both laps not found"}

        delta_total = round(sb.get("lap_time", 0) - sa.get("lap_time", 0), 3)

        # Sector deltas
        sector_deltas = {}
        for s in range(1, 4):
            key = f"sector_{s}"
            va = sa.get(key, 0)
            vb = sb.get(key, 0)
            if va and vb:
                sector_deltas[key] = round(vb - va, 3)

        # Identify which sector lost/gained the most
        primary_sector = None
        max_sector_delta = 0
        for s, d in sector_deltas.items():
            if abs(d) > abs(max_sector_delta):
                max_sector_delta = d
                primary_sector = s

        # Corner deltas
        corners_a = sa.get("corner_metrics", [])
        corners_b = sb.get("corner_metrics", [])
        corner_deltas = []
        for i in range(min(len(corners_a), len(corners_b))):
            ca = corners_a[i]
            cb = corners_b[i]
            cd = {
                "corner": i + 1,
                "entry_delta": round(cb.get("entry_speed_kmh", 0) - ca.get("entry_speed_kmh", 0), 1),
                "apex_delta": round(cb.get("apex_speed_kmh", 0) - ca.get("apex_speed_kmh", 0), 1),
                "exit_delta": round(cb.get("exit_speed_kmh", 0) - ca.get("exit_speed_kmh", 0), 1),
                "brake_distance_delta": round(cb.get("brake_distance_m", 0) - ca.get("brake_distance_m", 0), 1),
            }
            corner_deltas.append(cd)

        # Find biggest corner delta
        primary_corner = None
        max_corner_loss = 0
        for cd in corner_deltas:
            total_loss = abs(cd["entry_delta"]) + abs(cd["apex_delta"]) + abs(cd["exit_delta"])
            if total_loss > max_corner_loss:
                max_corner_loss = total_loss
                primary_corner = cd["corner"]

        # Tire/fuel changes
        tire_delta = {
            "wear_change": round(sb.get("tire_wear_end_pct", 0) - sa.get("tire_wear_end_pct", 0), 1),
            "grip_change": round(sb.get("tire_grip_end", 1.0) - sa.get("tire_grip_end", 1.0), 3),
            "temp_change": round(sb.get("tire_surface_temp_end", 0) - sa.get("tire_surface_temp_end", 0), 1),
        }
        fuel_delta = {
            "start_diff": round(sb.get("fuel_start_kg", 0) - sa.get("fuel_start_kg", 0), 1),
            "used_diff": round(sb.get("fuel_used_kg", 0) - sa.get("fuel_used_kg", 0), 1),
        }

        # Determine primary factor
        factors = {}
        if sector_deltas:
            factors["sector"] = max_sector_delta
        if tire_delta["grip_change"] < -0.01:
            factors["tire_degradation"] = tire_delta["grip_change"]
        if fuel_delta["start_diff"] > 5:
            factors["fuel_load"] = -fuel_delta["start_diff"] * 0.01

        primary_factor = max(factors, key=lambda k: abs(factors[k])) if factors else "unknown"

        # Build root cause text
        direction = "faster" if delta_total < 0 else "slower"
        abs_delta = abs(delta_total)
        lines = [
            f"Lap {lap_b} was {abs_delta:.3f}s {direction} than Lap {lap_a}."
        ]
        if primary_sector and sector_deltas.get(primary_sector, 0) != 0:
            sd = sector_deltas[primary_sector]
            lines.append(f"Main loss in {primary_sector} ({sd:+.3f}s).")
        if primary_corner:
            cd = corner_deltas[primary_corner - 1]
            lines.append(f"Turn {primary_corner}: entry {cd['entry_delta']:+.1f}km/h, "
                        f"apex {cd['apex_delta']:+.1f}km/h, exit {cd['exit_delta']:+.1f}km/h.")
        if tire_delta["grip_change"] < -0.01:
            lines.append(f"Tire grip dropped {abs(tire_delta['grip_change'])*100:.1f}% "
                        f"(wear +{tire_delta['wear_change']:.1f}%, "
                        f"temp {tire_delta['temp_change']:+.0f}°C).")
        if fuel_delta["start_diff"] != 0:
            lines.append(f"Fuel: {abs(fuel_delta['start_diff']):.1f}kg {'less' if fuel_delta['start_diff'] < 0 else 'more'} at start.")

        if not lines:
            lines.append("Negligible difference between laps.")

        return {
            "lap_a": lap_a,
            "lap_b": lap_b,
            "delta_total": delta_total,
            "direction": direction,
            "sector_deltas": sector_deltas,
            "corner_deltas": corner_deltas,
            "tire_delta": tire_delta,
            "fuel_delta": fuel_delta,
            "primary_factor": primary_factor,
            "root_cause": "\n".join(lines),
        }

    # ------------------------------------------------------------------
    #  STAGE 11 — PREDICTION
    # ------------------------------------------------------------------

    def predict_next_lap(self, current_lap: int) -> dict:
        """
        Predict next lap time based on trends.

        Uses linear extrapolation of lap times, adjusted for tire wear and fuel.
        """
        summaries = self.get_multi_lap_table()
        if len(summaries) < 3:
            return {"error": "Need at least 3 laps for prediction"}

        laps = [s["lap"] for s in summaries]
        times = [s["lap_time"] for s in summaries]

        if len(times) < 2:
            return {"error": "not enough data"}

        # Linear trend of last 3 laps
        recent = min(3, len(times))
        x = np.arange(recent)
        y = np.array(times[-recent:])
        if np.std(x) > 0 and np.std(y) > 0:
            slope, _ = np.polyfit(x, y, 1)
        else:
            slope = 0

        # Tire wear penalty (grip drops → time increases)
        last_summary = summaries[-1]
        tire_grip = last_summary.get("tire_grip_end", 1.0)
        grip_penalty = max(0, (1.0 - tire_grip) * 2.0)  # seconds

        # Fuel benefit (less fuel → faster)
        fuel_kg = last_summary.get("fuel_end_kg", 0)
        fuel_benefit = fuel_kg * 0.005  # ~0.005s per kg

        predicted_time = times[-1] + slope - fuel_benefit + grip_penalty

        # Confidence interval (wider with more variability)
        std_time = np.std(times[-min(5, len(times)):])
        ci_upper = predicted_time + std_time * 1.5
        ci_lower = predicted_time - std_time * 1.5

        return {
            "predicted_lap_time": round(predicted_time, 3),
            "ci_lower": round(ci_lower, 3),
            "ci_upper": round(ci_upper, 3),
            "trend_slope": round(slope, 4),
            "grip_penalty_s": round(grip_penalty, 3),
            "fuel_benefit_s": round(fuel_benefit, 3),
            "fuel_remaining_kg": round(fuel_kg, 1),
            "tire_wear_pct": last_summary.get("tire_wear_end_pct", 0),
            "remaining_laps_estimate": self._estimate_remaining_laps(),
        }

    def _estimate_remaining_laps(self) -> int:
        """Estimate laps remaining based on tire wear trend."""
        summaries = self.get_multi_lap_table()
        if len(summaries) < 2:
            return 0
        wear_rates = []
        for s in summaries:
            wear_rates.append(s.get("tire_wear_end_pct", 0))
        if len(wear_rates) > 1:
            avg_wear_per_lap = (wear_rates[-1] - wear_rates[0]) / len(wear_rates)
        else:
            avg_wear_per_lap = 2.0
        if avg_wear_per_lap <= 0:
            return 99
        remaining = int((100 - wear_rates[-1]) / avg_wear_per_lap)
        return max(0, remaining)

    # ------------------------------------------------------------------
    #  EXPORT
    # ------------------------------------------------------------------

    def to_dataframe(self) -> "pd.DataFrame":
        """Return multi-lap summary as a DataFrame."""
        if not PANDAS_AVAILABLE:
            return None
        rows = self.get_multi_lap_table()
        df_rows = []
        for r in rows:
            row = {k: v for k, v in r.items() if k != "corner_metrics"}
            df_rows.append(row)
        return pd.DataFrame(df_rows).set_index("lap") if df_rows else pd.DataFrame()


# ------------------------------------------------------------------
#  CLI
# ------------------------------------------------------------------

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Race engineer analysis")
    parser.add_argument("--log-file", type=str, required=True, help="Session log JSON")
    parser.add_argument("--compare", type=int, nargs=2, metavar=("LAP_A", "LAP_B"),
                        help="Compare two laps")
    parser.add_argument("--predict", type=int, metavar="CURRENT_LAP",
                        help="Predict next lap time")

    args = parser.parse_args()

    engineer = RaceEngineer()
    engineer.load_from_file(args.log_file)
    engineer.analyze()

    table = engineer.get_multi_lap_table()
    print(f"\n{'Lap':<5} {'Time':<10} {'Avg Speed':<12} {'Top Speed':<12} {'Fuel':<10} {'Tire Wear':<12} {'Score':<8}")
    print("-" * 75)
    for s in table:
        print(f"{s['lap']:<5} {s['lap_time']:<10.3f} {s['avg_speed_kmh']:<12.1f} "
              f"{s['top_speed_kmh']:<12.1f} {s['fuel_end_kg']:<10.1f} "
              f"{s['tire_wear_end_pct']:<12.1f} {s['driver_score']:<8}")

    if args.compare:
        result = engineer.compare_laps(args.compare[0], args.compare[1])
        print(f"\n{'='*60}")
        print(f"  ROOT CAUSE ANALYSIS")
        print(f"{'='*60}")
        print(f"  {result['root_cause']}")
        if "sector_deltas" in result:
            print(f"\n  Sector breakdown:")
            for s, d in result["sector_deltas"].items():
                print(f"    {s}: {d:+.3f}s")
        print(f"{'='*60}\n")

    if args.predict:
        pred = engineer.predict_next_lap(args.predict)
        if "error" not in pred:
            print(f"\n{'='*60}")
            print(f"  PREDICTION")
            print(f"{'='*60}")
            print(f"  Next lap:   {pred['predicted_lap_time']:.3f}s")
            print(f"  Confidence: [{pred['ci_lower']:.3f} - {pred['ci_upper']:.3f}]s")
            print(f"  Fuel left:  {pred['fuel_remaining_kg']:.1f}kg")
            print(f"  Tire wear:  {pred['tire_wear_pct']:.1f}%")
            print(f"{'='*60}\n")


if __name__ == "__main__":
    cli()
