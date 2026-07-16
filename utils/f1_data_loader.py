"""
FastF1 integration — fetch real F1 session data and convert to project's session log format.

Dependencies: fastf1 (pip install fastf1)

Usage:
    from utils.f1_data_loader import fetch_session, session_to_log_format, compare_laps

    # Download a session
    session = fetch_session(2023, "Monza", "R")

    # Get lap telemetry as DataFrame
    laps_telemetry = get_all_laps_telemetry(session)

    # Convert to project session log format
    session_log = session_to_log_format(session, laps_telemetry, driver_id="f1_driver")

    # Compare simulated vs real lap
    errors = compare_laps(simulated_log, real_telemetry_df, lap_number=1)
"""

import os
import sys
import math
import json
import time
import datetime
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

FASTF1_AVAILABLE = False
try:
    import fastf1
    from fastf1 import plotting
    FASTF1_AVAILABLE = True
except ImportError:
    fastf1 = None


# ---------------------------------------------------------------------------
#  SESSION FETCHING
# ---------------------------------------------------------------------------

def fetch_session(year: int, gp: str, session_type: str = "R", cache_path: str = None):
    """
    Fetch an F1 session via FastF1.

    Parameters
    ----------
    year : int
        Season year (2018 onward for telemetry).
    gp : str
        Grand Prix name, e.g. "Monza", "Monaco", "Silverstone".
    session_type : str
        "R" = Race, "Q" = Qualifying, "FP1", "FP2", "FP3", "S" = Sprint.
    cache_path : str, optional
        Path to FastF1 cache directory. Defaults to data/f1_cache.

    Returns
    -------
    fastf1.core.Session or None if unavailable.
    """
    if not FASTF1_AVAILABLE:
        print("fastf1 not installed. Run: pip install fastf1")
        return None

    enable_cache(cache_path)
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        print(f"Loaded {year} {gp} {session_type} — {len(session.laps)} laps")
        return session
    except Exception as e:
        print(f"Failed to load session: {e}")
        return None


def enable_cache(cache_path: str = None):
    if cache_path is None:
        cache_path = os.path.join(ROOT, "data", "f1_cache")
    os.makedirs(cache_path, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path)


def list_available_events(year: int):
    """List all Grands Prix available for a given year."""
    if not FASTF1_AVAILABLE:
        return []
    schedule = fastf1.get_event_schedule(year)
    return schedule["EventName"].tolist()


# ---------------------------------------------------------------------------
#  TELEMETRY EXTRACTION
# ---------------------------------------------------------------------------

def get_lap_telemetry(session, lap_number: int, driver: str = None):
    """
    Extract telemetry for a specific lap.

    Parameters
    ----------
    session : fastf1.core.Session
    lap_number : int
        Lap number (1-indexed).
    driver : str, optional
        Driver code (e.g. "VER", "HAM"). If None, uses fastest driver.

    Returns
    -------
    pd.DataFrame with columns: speed, throttle, brake, rpm, gear, drs, x, y, distance, time
    """
    if not FASTF1_AVAILABLE:
        return None

    if driver is None:
        driver = session.results["DriverCode"].iloc[0]

    laps = session.laps.pick_driver(driver)
    try:
        lap = laps.iloc[lap_number - 1]
    except IndexError:
        print(f"Lap {lap_number} not found for driver {driver}")
        return None

    telemetry = lap.get_telemetry()
    return telemetry


def get_all_laps_telemetry(session, driver: str = None):
    """
    Extract telemetry for all laps of a given driver.

    Returns
    -------
    dict[int, pd.DataFrame] — lap_number -> telemetry
    """
    if not FASTF1_AVAILABLE:
        return None

    if driver is None:
        driver = session.results["DriverCode"].iloc[0]

    laps = session.laps.pick_driver(driver)
    result = {}
    for i, lap in laps.iterlaps():
        telemetry = lap.get_telemetry()
        result[lap["LapNumber"]] = telemetry

    return result


def get_driver_lap_times(session, driver: str = None):
    """Return list of (lap_number, lap_time_seconds) for a driver."""
    if driver is None:
        driver = session.results["DriverCode"].iloc[0]
    laps = session.laps.pick_driver(driver)
    result = []
    for _, lap in laps.iterlaps():
        if pd.notna(lap["LapTime"]):
            result.append((lap["LapNumber"], lap["LapTime"].total_seconds()))
    return result


# ---------------------------------------------------------------------------
#  CONVERT TO PROJECT SESSION LOG FORMAT
# ---------------------------------------------------------------------------

def telemetry_to_packets(
    telemetry_df,
    driver_id: str = "f1_driver",
    lap_number: int = 1,
    lap_progress_map: list = None,
    start_time: float = None,
    track_points: list = None,
):
    """
    Convert a FastF1 telemetry DataFrame into a list of dicts matching the
    project's session log format.

    Parameters
    ----------
    telemetry_df : pd.DataFrame
        Must contain columns: speed, throttle, brake, rpm, gear, drs, x, y, distance, time.
    driver_id : str
    lap_number : int
    lap_progress_map : list, optional
        Pre-computed track_index for each row. Auto-computed if None.
    start_time : float, optional
        Unix timestamp for first packet.
    track_points : list, optional
        List of (x, y) track points for track_index lookup.

    Returns
    -------
    list[dict] — compatible with the project's session log format.
    """
    if start_time is None:
        start_time = time.time()

    df = telemetry_df.copy()

    # Convert kmh to m/s
    speeds = df["speed"].values
    throttles = df["throttle"].values / 100.0
    brakes = df["brake"].values / 100.0

    # Compute yaw rate from x, y positions
    xs = df["x"].values
    ys = df["y"].values
    yaws = _compute_yaw_from_path(xs, ys)

    # Simulate coolant temp (not available in F1 telemetry)
    coolant_temps = _estimate_coolant_temp(speeds, throttles)

    # Build base track from telemetry positions
    if track_points is None:
        track_points = list(zip(xs, ys))

    # Normalize distance to [0, 1] for lap_progress
    total_distance = df["distance"].max() - df["distance"].min()
    if total_distance > 0:
        distances = (df["distance"].values - df["distance"].min()) / total_distance
    else:
        distances = np.linspace(0, 1, len(df))

    packets = []
    times = df["time"].values
    t0 = times[0] if len(times) > 0 else 0.0

    for i in range(len(df)):
        t_rel = (times[i] - t0).total_seconds() if hasattr(times[i], "total_seconds") else float(times[i] - t0)

        lap_progress = distances[i]
        track_idx = int(lap_progress * (len(track_points) - 1))

        packet = {
            "timestamp": start_time + t_rel,
            "t": t_rel,
            "lap": lap_number,
            "track_index": track_idx,
            "driver_id": driver_id,
            "gps": {"x": float(xs[i]), "y": float(ys[i])},
            "true": {
                "speed_kmh": float(speeds[i]),
                "coolant_temp": float(coolant_temps[i]),
                "brake_cmd": float(brakes[i]),
                "throttle": float(throttles[i]),
                "yaw_deg": float(yaws[i]),
            },
            "sensors": {
                "wheel_speed": float(speeds[i]),
                "brake_pressure": float(brakes[i] * 100.0),
                "coolant_temp": float(coolant_temps[i]),
                "imu": {
                    "ax": 0.0,
                    "ay": 0.0,
                    "yaw": float(yaws[i]),
                },
            },
            "f1_telemetry": {
                "rpm": int(df["rpm"].values[i]) if "rpm" in df.columns else 0,
                "gear": int(df["gear"].values[i]) if "gear" in df.columns else 0,
                "drs": int(df["drs"].values[i]) if "drs" in df.columns else 0,
            },
        }
        packets.append(packet)

    return packets


def session_to_log_format(session, laps_telemetry: dict, driver_id: str = None):
    """
    Convert an entire FastF1 session into a list of packets (multi-lap)
    matching the project's session log format.

    Parameters
    ----------
    session : fastf1.core.Session
    laps_telemetry : dict[int, pd.DataFrame]
        Output from get_all_laps_telemetry().
    driver_id : str, optional

    Returns
    -------
    list[dict] — all packets from all laps, sequential.
    """
    if driver_id is None:
        driver_id = session.results["DriverCode"].iloc[0]

    all_packets = []
    start_time = time.time()

    for lap_number, telemetry_df in laps_telemetry.items():
        packets = telemetry_to_packets(
            telemetry_df, driver_id=driver_id, lap_number=lap_number,
            start_time=start_time,
        )
        all_packets.extend(packets)
        start_time += telemetry_df["time"].iloc[-1].total_seconds()

    return all_packets


def save_session_as_project_log(session, laps_telemetry: dict, driver_id: str = None, log_dir: str = None):
    """Save FastF1 session data as a project session log JSON file."""
    if log_dir is None:
        log_dir = os.path.join(ROOT, "data", "logs")
    os.makedirs(log_dir, exist_ok=True)

    packets = session_to_log_format(session, laps_telemetry, driver_id)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    driver = driver_id or session.results["DriverCode"].iloc[0]
    filename = f"f1_{driver}_{timestamp}.json"
    filepath = os.path.join(log_dir, filename)

    from utils.json_writer import write_session_log
    write_session_log(filepath, packets)
    print(f"Saved {len(packets)} packets to {filepath}")
    return filepath


# ---------------------------------------------------------------------------
#  COMPARISON / VALIDATION
# ---------------------------------------------------------------------------

def compare_laps(simulated_log: list, real_telemetry: "pd.DataFrame", lap_number: int = 1):
    """
    Compare a simulated lap against real F1 telemetry.

    Parameters
    ----------
    simulated_log : list[dict]
        Project session log packets.
    real_telemetry : pd.DataFrame
        FastF1 telemetry DataFrame.

    Returns
    -------
    dict with MAE, RMSE, and per-sector errors.
    """
    if not FASTF1_AVAILABLE:
        return {"error": "fastf1 not installed"}

    import pandas as pd

    # Extract simulated speed trace
    sim_speeds = np.array([p["true"]["speed_kmh"] for p in simulated_log if p["lap"] == lap_number])
    real_speeds = real_telemetry["speed"].values

    # Interpolate to same length
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return {"error": "no data for comparison"}

    sim_speeds = sim_speeds[:n]
    real_speeds = real_speeds[:n]

    # Global metrics
    mae = np.mean(np.abs(sim_speeds - real_speeds))
    rmse = np.sqrt(np.mean((sim_speeds - real_speeds) ** 2))
    max_error = np.max(np.abs(sim_speeds - real_speeds))

    # Sector errors (split into 3 sectors)
    sector_size = n // 3
    sector_mae = []
    for s in range(3):
        start = s * sector_size
        end = start + sector_size if s < 2 else n
        sector_mae.append(np.mean(np.abs(sim_speeds[start:end] - real_speeds[start:end])))

    return {
        "mae_speed_kmh": float(mae),
        "rmse_speed_kmh": float(rmse),
        "max_error_speed_kmh": float(max_error),
        "sector_mae_kmh": [float(s) for s in sector_mae],
        "n_samples": n,
    }


# ---------------------------------------------------------------------------
#  INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _compute_yaw_from_path(xs, ys):
    """Compute yaw angle (degrees) from path (x, y) positions."""
    yaws = [0.0]
    for i in range(1, len(xs)):
        dx = xs[i] - xs[i - 1]
        dy = ys[i] - ys[i - 1]
        yaw = math.degrees(math.atan2(dy, dx))
        yaws.append(yaw)
    return yaws


def _estimate_coolant_temp(speeds, throttles, initial_temp=80.0):
    """Simple coolant temp model for F1 telemetry (since real data not available)."""
    temps = [initial_temp]
    for i in range(1, len(speeds)):
        heat = throttles[i] / 100.0 * 2.0
        cooling = speeds[i] / 300.0 * 0.5
        temp = temps[-1] + heat - cooling
        temp = max(70.0, min(120.0, temp))
        temps.append(temp)
    return temps


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

def cli():
    """Command-line entry point for fetching F1 data."""
    import argparse
    parser = argparse.ArgumentParser(description="Fetch F1 session data via FastF1")
    parser.add_argument("--year", type=int, required=True, help="Season year")
    parser.add_argument("--gp", type=str, required=True, help="Grand Prix name (e.g. Monza)")
    parser.add_argument("--session", type=str, default="R", help="Session type: R, Q, FP1, FP2, FP3, S")
    parser.add_argument("--driver", type=str, default=None, help="Driver code (e.g. VER)")
    parser.add_argument("--save", action="store_true", help="Save as project session log")
    parser.add_argument("--list-events", type=int, nargs="?", const=2024, help="List available events for a year")

    args = parser.parse_args()

    if args.list_events:
        events = list_available_events(args.list_events)
        print(f"Available events in {args.list_events}:")
        for e in events:
            print(f"  - {e}")
        return

    session = fetch_session(args.year, args.gp, args.session)
    if session is None:
        return

    laps_telemetry = get_all_laps_telemetry(session, driver=args.driver)
    if not laps_telemetry:
        print("No telemetry data found.")
        return

    print(f"Loaded {len(laps_telemetry)} laps of telemetry")

    if args.save:
        filepath = save_session_as_project_log(session, laps_telemetry, driver_id=args.driver)
        print(f"Saved to {filepath}")


if __name__ == "__main__":
    cli()
