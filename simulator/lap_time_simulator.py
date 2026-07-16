"""
Optimal lap time simulator.

Computes theoretical best lap time from track geometry and vehicle limits,
without running a full physics simulation.

Approach:
  1. Analyze track geometry → corner radii, straight lengths, curvature profile
  2. Compute maximum corner speed (friction circle + downforce)
  3. Compute optimal braking points (trail-braking model)
  4. Compute acceleration zones (full throttle)
  5. Assemble predicted lap time

This provides a "gold standard" lap time for comparison with actual simulation runs.

Usage:
    from simulator.lap_time_simulator import LapTimeSimulator
    from simulator.track_loader import generate_oval_track

    track = generate_oval_track()
    lts = LapTimeSimulator(track, car_params={"mass": 210, "max_engine_force": 6000, ...})
    result = lts.simulate_optimal_lap()
    print(result["lap_time"])          # predicted optimal lap time (seconds)
    print(result["speed_profile"])     # optimal speed at each track point
"""

import numpy as np
import math

from simulator.physics.simple.vehicle_model import CAR
from simulator.physics.simple.aero import AeroModel


class TrackGeometry:
    """Analyze track waypoints to extract geometry features."""

    def __init__(self, points: list):
        self.points = np.array(points)
        self.n = len(points)

    def compute_curvatures(self) -> np.ndarray:
        """Compute curvature at each track point (1/radius, signed)."""
        curvatures = np.zeros(self.n)
        for i in range(self.n):
            prev = self.points[(i - 1) % self.n]
            curr = self.points[i]
            next_p = self.points[(i + 1) % self.n]

            v1 = curr - prev
            v2 = next_p - curr
            v1_len = np.linalg.norm(v1)
            v2_len = np.linalg.norm(v2)
            if v1_len < 1e-6 or v2_len < 1e-6:
                continue

            cross_z = v1[0] * v2[1] - v1[1] * v2[0]
            dot = np.dot(v1, v2)
            angle = np.arctan2(abs(cross_z), dot)
            curvature = 2.0 * np.sin(angle / 2.0) / max(v1_len, v2_len)

            sign = 1.0 if cross_z > 0 else -1.0
            curvatures[i] = curvature * sign

        return curvatures

    def compute_corner_radii(self, curvature_threshold: float = 0.005) -> list:
        """Extract corner segments with radius and arc length."""
        curvatures = self.compute_curvatures()
        corners = []
        in_corner = False
        start = 0
        peak_curv = 0.0
        peak_idx = 0

        for i in range(self.n):
            abs_curv = abs(curvatures[i])
            if abs_curv > curvature_threshold and not in_corner:
                start = i
                peak_curv = abs_curv
                peak_idx = i
                in_corner = True
            elif abs_curv > curvature_threshold and in_corner:
                if abs_curv > peak_curv:
                    peak_curv = abs_curv
                    peak_idx = i
            elif abs_curv <= curvature_threshold and in_corner:
                if i - start > 3:
                    arc_length = self._arc_length(start, i)
                    radius = 1.0 / peak_curv if peak_curv > 0 else float("inf")
                    corners.append({
                        "start_idx": start,
                        "end_idx": i,
                        "peak_idx": peak_idx,
                        "radius": radius,
                        "arc_length": arc_length,
                        "direction": "L" if curvatures[peak_idx] > 0 else "R",
                    })
                in_corner = False

        return corners

    def compute_straights(self, curvature_threshold: float = 0.005) -> list:
        """Extract straight segments."""
        curvatures = self.compute_curvatures()
        straights = []
        in_straight = False
        start = 0

        for i in range(self.n):
            abs_curv = abs(curvatures[i])
            if abs_curv <= curvature_threshold and not in_straight:
                start = i
                in_straight = True
            elif abs_curv > curvature_threshold and in_straight:
                if i - start > 3:
                    length = self._arc_length(start, i)
                    straights.append({"start_idx": start, "end_idx": i, "length": length})
                in_straight = False

        return straights

    def _arc_length(self, start: int, end: int) -> float:
        """Arc length between two track indices."""
        if start >= end:
            end += self.n
        length = 0.0
        for i in range(start, end):
            i1 = i % self.n
            i2 = (i + 1) % self.n
            length += np.linalg.norm(self.points[i2] - self.points[i1])
        return length

    def track_length(self) -> float:
        """Total track length."""
        return self._arc_length(0, self.n)


class LapTimeSimulator:
    """
    Predict optimal lap time from track geometry and vehicle parameters.

    Uses a quasi-steady-state approach:
      - Corners: speed limited by friction circle + downforce
      - Straights: full throttle acceleration with drag
      - Braking zones: optimal deceleration from straight speed to corner entry speed
    """

    def __init__(
        self,
        track_points: list,
        car_params: dict = None,
        mu: float = 1.2,
        aero: AeroModel = None,
    ):
        self.track = TrackGeometry(track_points)
        self.params = car_params if car_params else dict(CAR)
        self.mu = mu
        self.aero = aero or AeroModel()

        self._track_length = self.track.track_length()
        self._curvatures = self.track.compute_curvatures()
        self._corners = self.track.compute_corner_radii()
        self._straights = self.track.compute_straights()

    def max_corner_speed(self, radius: float) -> float:
        """
        Maximum speed (m/s) through a corner of given radius.

        Uses friction circle: max_lateral_accel = mu * g (+ downforce effect)
        v_max = sqrt(mu * g * r) — with downforce enhancement.
        """
        if radius <= 0:
            return float("inf")

        # Base friction-limited speed
        v_base = math.sqrt(self.mu * 9.81 * radius)

        # Iterative correction for downforce (since downforce depends on v)
        v = v_base
        for _ in range(5):
            grip_mult = self.aero.effective_grip_multiplier(v, self.params["mass"])
            v = math.sqrt(self.mu * grip_mult * 9.81 * radius)

        return v

    def max_straight_speed(self, distance_m: float, initial_speed_ms: float = 0.0) -> tuple:
        """
        Maximum speed achieved after accelerating along a straight.

        Parameters
        ----------
        distance_m : float
            Length of straight (m).
        initial_speed_ms : float
            Speed at start of straight (m/s).

        Returns
        -------
        tuple[float, float, float] — (final_speed_ms, time_s, avg_speed_ms)
        """
        v = initial_speed_ms
        t = 0.0
        dt = 0.01
        d = 0.0

        while d < distance_m:
            engine_force = self.params["max_engine_force"]
            drag = 0.5 * self.params["air_density"] * self.params["drag_coeff"] * self.params["frontal_area"] * (v ** 2)
            aero_downforce = self.aero.compute_downforce(v)
            roll = self.params["rolling_resistance"] * self.params["mass"] * 9.81

            net_F = engine_force - drag - roll
            a = net_F / self.params["mass"]

            v_new = v + a * dt
            if v_new <= 0:
                break
            v = v_new

            d += v * dt
            t += dt

        return v, t, d / t if t > 0 else v

    def braking_distance(self, v_initial_ms: float, v_final_ms: float) -> float:
        """
        Distance required to brake from v_initial to v_final.

        Uses constant max brake force + drag + aero resistance.
        """
        v = v_initial_ms
        d = 0.0
        dt = 0.01

        while v > v_final_ms:
            brake_force = self.params["max_brake_force"]
            drag = 0.5 * self.params["air_density"] * self.params["drag_coeff"] * self.params["frontal_area"] * (v ** 2)
            roll = self.params["rolling_resistance"] * self.params["mass"] * 9.81

            net_F = -brake_force - drag - roll
            a = net_F / self.params["mass"]
            v_new = v + a * dt
            v = max(v_new, v_final_ms)
            d += v * dt

        return d

    def simulate_optimal_lap(self) -> dict:
        """
        Compute optimal lap time and speed profile.

        Returns
        -------
        dict with:
          - lap_time: total predicted lap time (s)
          - speed_profile: list of (track_index, speed_ms, speed_kmh)
          - corner_stats: per-corner entry/apex/exit speeds
          - segment_breakdown: time spent in corners vs straights
          - track_length_m: total track length
          - average_speed_kmh: mean speed
        """
        n = len(self.track.points)
        speed_profile_ms = np.zeros(n)
        segment_times = []
        total_time = 0.0

        # Phase 1: Compute corner apex speeds
        corner_speeds = {}
        for corner in self._corners:
            v_max = self.max_corner_speed(corner["radius"])
            v_max_kmh = v_max * 3.6
            corner_speeds[corner["peak_idx"]] = v_max
            speed_profile_ms[corner["start_idx"]:corner["end_idx"] + 1] = v_max

        # Phase 2: Fill straights with acceleration/deceleration
        i = 0
        current_speed = 0.0
        while i < n:
            # Check if we're approaching a corner
            next_corner = None
            for corner in self._corners:
                if corner["start_idx"] > i:
                    next_corner = corner
                    break

            if next_corner is None:
                # No more corners — final straight
                straight_len = self.track._arc_length(i, n)
                if straight_len > 1.0:
                    final_speed, seg_time, avg_speed = self.max_straight_speed(straight_len, current_speed)
                    for j in range(i, n):
                        frac = (j - i) / max(n - i, 1)
                        speed_profile_ms[j] = current_speed + (final_speed - current_speed) * frac
                    total_time += seg_time
                break

            # Straight before corner
            straight_len = self.track._arc_length(i, next_corner["start_idx"])
            corner_entry_speed = corner_speeds.get(next_corner["peak_idx"], 0)

            if straight_len > 0.5:
                # Try to accelerate, then brake to corner entry speed
                accel_distance = straight_len * 0.6
                brake_distance = self.braking_distance(
                    min(self.max_straight_speed(accel_distance, current_speed)[0], 80.0),
                    corner_entry_speed,
                )

                # If brake_distance > available, just coast
                if brake_distance > straight_len * 0.4:
                    brake_distance = straight_len * 0.3

                accel_len = straight_len - brake_distance

                if accel_len > 0.5:
                    accel_speed, accel_time, _ = self.max_straight_speed(accel_len, current_speed)
                    speed_before_brake = min(accel_speed, 80.0)

                    # Fill acceleration phase
                    for j in range(i, min(i + int(accel_len / 1.0), next_corner["start_idx"])):
                        frac = (j - i) / max(int(accel_len / 1.0), 1)
                        speed_profile_ms[j] = current_speed + (speed_before_brake - current_speed) * min(frac, 1.0)

                    total_time += accel_time

                    # Braking phase
                    brake_time = (speed_before_brake - corner_entry_speed) / (self.params["max_brake_force"] / self.params["mass"])
                    total_time += max(0.0, brake_time)

            # Corner transit time
            corner_arc = next_corner["arc_length"]
            if corner_entry_speed > 0.5:
                corner_time = corner_arc / corner_entry_speed
                total_time += corner_time

            # Fill corner speed profile
            for j in range(next_corner["start_idx"], next_corner["end_idx"] + 1):
                speed_profile_ms[j] = corner_entry_speed

            i = next_corner["end_idx"] + 1
            current_speed = corner_entry_speed

        speed_profile_kmh = speed_profile_ms * 3.6
        avg_speed_ms = np.mean(speed_profile_ms)
        avg_speed_kmh = avg_speed_ms * 3.6

        # Corner stats
        corner_stats = []
        for c in self._corners:
            v_apex = corner_speeds.get(c["peak_idx"], 0)
            corner_stats.append({
                "radius_m": round(c["radius"], 1),
                "arc_length_m": round(c["arc_length"], 1),
                "apex_speed_kmh": round(v_apex * 3.6, 1),
                "direction": c["direction"],
            })

        return {
            "lap_time_s": round(total_time, 3),
            "track_length_m": round(self._track_length, 1),
            "average_speed_kmh": round(avg_speed_kmh, 1),
            "speed_profile_kmh": [round(s, 1) for s in speed_profile_kmh],
            "n_corners": len(self._corners),
            "corner_stats": corner_stats,
            "n_straights": len(self._straights),
            "params": {
                "mass": self.params["mass"],
                "engine_force": self.params["max_engine_force"],
                "brake_force": self.params["max_brake_force"],
                "mu": self.mu,
                "drag_coeff": self.params["drag_coeff"],
                "downforce_coeff": self.aero.downforce_coeff,
            },
        }

    def compare_to_actual(self, actual_lap_time: float, actual_speed_profile: list = None) -> dict:
        """Compare optimal prediction to an actual simulation run."""
        optimal = self.simulate_optimal_lap()

        time_delta = actual_lap_time - optimal["lap_time_s"]
        time_pct = (actual_lap_time / optimal["lap_time_s"] - 1.0) * 100 if optimal["lap_time_s"] > 0 else 0.0

        result = {
            "optimal_lap_time": optimal["lap_time_s"],
            "actual_lap_time": actual_lap_time,
            "delta_s": round(time_delta, 3),
            "delta_pct": round(time_pct, 2),
            "n_corners": optimal["n_corners"],
            "track_length_m": optimal["track_length_m"],
            "optimal_avg_speed_kmh": optimal["average_speed_kmh"],
        }

        if actual_speed_profile and len(actual_speed_profile) > 0:
            actual_speed = np.array(actual_speed_profile)
            optimal_speed = np.array(optimal["speed_profile_kmh"])

            n = min(len(actual_speed), len(optimal_speed))
            if n > 0:
                result["speed_rmse"] = round(float(np.sqrt(np.mean((actual_speed[:n] - optimal_speed[:n]) ** 2))), 2)
                result["speed_mae"] = round(float(np.mean(np.abs(actual_speed[:n] - optimal_speed[:n]))), 2)

        return result

    def print_report(self):
        """Print detailed lap time analysis report."""
        optimal = self.simulate_optimal_lap()

        print(f"\n{'='*60}")
        print(f"  OPTIMAL LAP TIME ANALYSIS")
        print(f"{'='*60}")
        print(f"  Track length:       {optimal['track_length_m']:.1f} m")
        print(f"  Number of corners:  {optimal['n_corners']}")
        print(f"  Number of straights:{optimal['n_straights']}")
        print(f"  Optimal lap time:   {optimal['lap_time_s']:.3f} s")
        print(f"  Average speed:      {optimal['average_speed_kmh']:.1f} km/h")
        print(f"\n  Vehicle parameters:")
        for k, v in optimal["params"].items():
            print(f"    {k}: {v}")
        print(f"\n  Corner breakdown:")
        for i, c in enumerate(optimal["corner_stats"]):
            print(f"    T{i+1}: R={c['radius_m']}m  "
                  f"len={c['arc_length_m']}m  "
                  f"apex={c['apex_speed_kmh']}km/h  "
                  f"dir={c['direction']}")
        print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

def cli():
    import argparse
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from utils.config_loader import load_yaml
    from simulator.track_loader import generate_oval_track, generate_fia_style_track, generate_realistic_track, load_track_csv, generate_custom_track

    parser = argparse.ArgumentParser(description="Optimal lap time simulator")
    parser.add_argument("--track", type=str, default=None, help="Track CSV file path")
    parser.add_argument("--track-type", type=str, default="oval", choices=["oval", "custom", "realistic", "fia"])
    parser.add_argument("--car-config", type=str, default=None, help="Car YAML config path")
    parser.add_argument("--mu", type=float, default=1.2, help="Tire-road friction coefficient")
    parser.add_argument("--downforce", type=float, default=1.2, help="Downforce coefficient")
    parser.add_argument("--actual-lap-time", type=float, default=None, help="Actual lap time for comparison")

    args = parser.parse_args()

    ROOT = os.path.dirname(os.path.dirname(__file__))

    # Load track
    if args.track:
        track = load_track_csv(args.track)
        print(f"Loaded track from {args.track} ({len(track)} points)")
    else:
        if args.track_type == "oval":
            track = generate_oval_track()
        elif args.track_type == "custom":
            track = generate_custom_track(n_left=6, n_right=6)
        elif args.track_type == "realistic":
            track = generate_realistic_track()
        else:
            track = generate_fia_style_track()
        print(f"Generated {args.track_type} track ({len(track)} points)")

    # Load car params
    if args.car_config:
        car_params = load_yaml(args.car_config)
    else:
        car_params = load_yaml(os.path.join(ROOT, "configs", "car_simple.yaml"))

    # Run lap time simulation
    aero = AeroModel(downforce_coeff=args.downforce)
    lts = LapTimeSimulator(track, car_params=car_params, mu=args.mu, aero=aero)
    lts.print_report()

    if args.actual_lap_time:
        comparison = lts.compare_to_actual(args.actual_lap_time)
        print(f"\n  Comparison with actual lap time:")
        print(f"    Actual:     {comparison['actual_lap_time']:.3f} s")
        print(f"    Optimal:    {comparison['optimal_lap_time']:.3f} s")
        print(f"    Delta:      {comparison['delta_s']:+.3f} s ({comparison['delta_pct']:+.2f}%)")
        print()


if __name__ == "__main__":
    cli()
