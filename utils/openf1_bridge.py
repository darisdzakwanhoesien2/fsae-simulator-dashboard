"""
OpenF1 API bridge — fetch real-time and historical F1 telemetry via REST API.

API docs: https://openf1.org/docs/

No authentication required. Data from 2023 onward.
Rate limit: ~250 requests/hour (generous).

Usage:
    from utils.openf1_bridge import (
        get_session_info, get_car_data, get_laps,
        get_weather, telemetry_to_project_format,
        OpenF1Stream
    )

    # Fetch session info
    sessions = get_session_info(year=2024, gp_name="Monza")

    # Stream live car data
    stream = OpenF1Stream(session_key=latest_session["session_key"])
    for packet in stream.poll():
        print(packet)
"""

import os
import sys
import json
import time
import math
import datetime
import requests
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

OPENF1_BASE = "https://api.openf1.org/v1"


# ---------------------------------------------------------------------------
#  SESSION INFO
# ---------------------------------------------------------------------------

def get_session_info(year: int = None, gp_name: str = None, session_name: str = None):
    """
    Fetch session information.

    Parameters
    ----------
    year : int, optional
        Season year (e.g. 2024).
    gp_name : str, optional
        Grand Prix name (e.g. "Monza", "Monaco").
    session_name : str, optional
        e.g. "Race", "Qualifying", "Practice 1".

    Returns
    -------
    list[dict] — matching sessions.
    """
    params = {}
    if year:
        params["year"] = year
    if gp_name:
        params["circuit_short_name"] = gp_name
    if session_name:
        params["session_name"] = session_name

    resp = requests.get(f"{OPENF1_BASE}/sessions", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_latest_session(year: int = None, gp_name: str = None):
    """Get the most recent session matching criteria."""
    sessions = get_session_info(year=year, gp_name=gp_name)
    if not sessions:
        return None
    return max(sessions, key=lambda s: s.get("date_start", ""))


# ---------------------------------------------------------------------------
#  CAR DATA (TELEMETRY)
# ---------------------------------------------------------------------------

def get_car_data(
    session_key: int,
    driver_number: int = None,
    limit: int = None,
):
    """
    Fetch car telemetry data (~3.7 Hz).

    Parameters
    ----------
    session_key : int
        Unique session identifier from get_session_info().
    driver_number : int, optional
        Driver number (e.g. 1 for Verstappen, 44 for Hamilton).
    limit : int, optional
        Max results.

    Returns
    -------
    list[dict] — each entry has: brake, drs, gear, rpm, speed, throttle, date, driver_number, session_key
    """
    params = {"session_key": session_key}
    if driver_number is not None:
        params["driver_number"] = driver_number
    if limit is not None:
        params["limit"] = limit

    resp = requests.get(f"{OPENF1_BASE}/car_data", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
#  LAP DATA
# ---------------------------------------------------------------------------

def get_laps(
    session_key: int,
    driver_number: int = None,
    lap_number: int = None,
):
    """
    Fetch lap timing data.

    Returns
    -------
    list[dict] — each entry has: lap_number, lap_duration, sector_1, sector_2, sector_3,
                  duration_sector_1, duration_sector_2, duration_sector_3, driver_number, etc.
    """
    params = {"session_key": session_key}
    if driver_number is not None:
        params["driver_number"] = driver_number
    if lap_number is not None:
        params["lap_number"] = lap_number

    resp = requests.get(f"{OPENF1_BASE}/laps", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
#  POSITION DATA
# ---------------------------------------------------------------------------

def get_position(session_key: int, driver_number: int = None):
    """
    Fetch GPS position data.

    Returns
    -------
    list[dict] — each entry has: x, y, z, driver_number, date
    """
    params = {"session_key": session_key}
    if driver_number is not None:
        params["driver_number"] = driver_number

    resp = requests.get(f"{OPENF1_BASE}/position", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
#  WEATHER DATA
# ---------------------------------------------------------------------------

def get_weather(session_key: int):
    """
    Fetch weather data for a session.

    Returns
    -------
    list[dict] — each entry has: air_temperature, track_temperature, humidity,
                  pressure, wind_speed, wind_direction, rainfall, date
    """
    params = {"session_key": session_key}
    resp = requests.get(f"{OPENF1_BASE}/weather", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
#  DRIVERS
# ---------------------------------------------------------------------------

def get_drivers(session_key: int = None, driver_number: int = None):
    """Fetch driver information."""
    params = {}
    if session_key is not None:
        params["session_key"] = session_key
    if driver_number is not None:
        params["driver_number"] = driver_number

    resp = requests.get(f"{OPENF1_BASE}/drivers", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
#  CONVERT TO PROJECT FORMAT
# ---------------------------------------------------------------------------

def telemetry_to_project_format(
    car_data: list,
    position_data: list,
    laps_data: list,
    driver_id: str = "f1_driver",
    session_key: int = None,
):
    """
    Convert OpenF1 car_data, position_data, and laps_data into the project's
    session log format.

    Parameters
    ----------
    car_data : list[dict]
        From get_car_data().
    position_data : list[dict]
        From get_position().
    laps_data : list[dict]
        From get_laps().
    driver_id : str
    session_key : int, optional

    Returns
    -------
    list[dict] — project session log format.
    """
    # Index position by date for matching
    pos_by_date = {}
    for p in position_data:
        pos_by_date[p["date"]] = (p["x"], p["y"])

    # Index laps by number for quick lookup
    lap_info = {}
    for l in laps_data:
        lap_info[l["lap_number"]] = l

    packets = []
    current_lap = 1
    start_time = time.time()

    for i, entry in enumerate(car_data):
        date_str = entry.get("date", "")
        x, y = pos_by_date.get(date_str, (0.0, 0.0))

        # Determine lap from duration tracking
        brake = entry.get("brake", 0)
        throttle = entry.get("throttle", 0) / 100.0
        speed_kmh = entry.get("speed", 0)
        rpm = entry.get("rpm", 0)
        gear = entry.get("gear", 0)
        drs = entry.get("drs", 0)

        # Estimate yaw from position
        yaw_deg = _estimate_yaw_from_pos(position_data, date_str)

        # Approximate coolant temp
        coolant_temp = _estimate_coolant(speed_kmh, throttle)

        # Time relative to first entry
        t_rel = i * 0.27  # ~3.7 Hz

        # Estimate lap from lap duration data
        if laps_data:
            for ln, li in lap_info.items():
                if li.get("date_start", "") <= date_str <= li.get("date_end", ""):
                    current_lap = ln
                    break

        packet = {
            "timestamp": start_time + t_rel,
            "t": t_rel,
            "lap": current_lap,
            "track_index": i % 500,
            "driver_id": driver_id,
            "gps": {"x": float(x), "y": float(y)},
            "true": {
                "speed_kmh": float(speed_kmh),
                "coolant_temp": float(coolant_temp),
                "brake_cmd": float(brake),
                "throttle": float(throttle),
                "yaw_deg": float(yaw_deg),
            },
            "sensors": {
                "wheel_speed": float(speed_kmh),
                "brake_pressure": float(brake * 100.0),
                "coolant_temp": float(coolant_temp),
                "imu": {
                    "ax": 0.0,
                    "ay": 0.0,
                    "yaw": float(yaw_deg),
                },
            },
            "openf1": {
                "rpm": rpm,
                "gear": gear,
                "drs": drs,
                "session_key": session_key,
            },
        }
        packets.append(packet)

    return packets


def save_openf1_session(session_key: int, driver_number: int = None, log_dir: str = None):
    """Fetch OpenF1 data and save as a project session log."""
    if log_dir is None:
        log_dir = os.path.join(ROOT, "data", "logs")
    os.makedirs(log_dir, exist_ok=True)

    car_data = get_car_data(session_key, driver_number)
    position_data = get_position(session_key, driver_number)
    laps_data = get_laps(session_key, driver_number)

    if not car_data:
        print("No car data found.")
        return None

    driver_id = f"driver_{driver_number}" if driver_number else "f1_driver"
    packets = telemetry_to_project_format(car_data, position_data, laps_data, driver_id=driver_id, session_key=session_key)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"openf1_{driver_id}_{timestamp}.json"
    fpath = os.path.join(log_dir, fname)

    from utils.json_writer import write_session_log
    write_session_log(fpath, packets)
    print(f"Saved {len(packets)} packets to {fpath}")
    return fpath


# ---------------------------------------------------------------------------
#  LIVE STREAMING
# ---------------------------------------------------------------------------

class OpenF1Stream:
    """
    Poll OpenF1 API for live car data during a session.
    Mimics the project's realtime.json update pattern.
    """

    def __init__(self, session_key: int, driver_number: int = None, poll_interval: float = 0.5):
        self.session_key = session_key
        self.driver_number = driver_number
        self.poll_interval = poll_interval
        self._last_date = ""
        self._buffer = []

    def poll(self, return_buffer: bool = False):
        """
        Fetch new car data since last poll.

        Returns
        -------
        list[dict] — new telemetry packets in project format.
        """
        params = {"session_key": self.session_key}
        if self.driver_number is not None:
            params["driver_number"] = self.driver_number

        try:
            resp = requests.get(f"{OPENF1_BASE}/car_data", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[OpenF1Stream] Error: {e}")
            return []

        # Filter to new entries
        new_data = []
        for entry in data:
            if entry["date"] > self._last_date:
                new_data.append(entry)

        if new_data:
            self._last_date = new_data[-1]["date"]

        # Convert to project format
        packets = []
        for entry in new_data:
            packet = {
                "timestamp": time.time(),
                "t": time.time(),
                "lap": 0,
                "track_index": 0,
                "driver_id": f"f1_{self.driver_number}" if self.driver_number else "f1_driver",
                "gps": {"x": 0.0, "y": 0.0},
                "true": {
                    "speed_kmh": float(entry.get("speed", 0)),
                    "coolant_temp": 80.0,
                    "brake_cmd": float(entry.get("brake", 0)),
                    "throttle": float(entry.get("throttle", 0)) / 100.0,
                    "yaw_deg": 0.0,
                },
                "sensors": {
                    "wheel_speed": float(entry.get("speed", 0)),
                    "brake_pressure": float(entry.get("brake", 0)) * 100.0,
                    "coolant_temp": 80.0,
                    "imu": {"ax": 0.0, "ay": 0.0, "yaw": 0.0},
                },
                "openf1": {
                    "rpm": entry.get("rpm", 0),
                    "gear": entry.get("gear", 0),
                    "drs": entry.get("drs", 0),
                },
            }
            packets.append(packet)

        if return_buffer:
            self._buffer.extend(packets)

        return packets

    def poll_continuous(self, max_iterations: int = None, callback=None):
        """
        Continuously poll and yield packets.

        Parameters
        ----------
        max_iterations : int, optional
        callback : callable, optional
            Called with each batch of packets.
        """
        iterations = 0
        while max_iterations is None or iterations < max_iterations:
            packets = self.poll()
            if packets:
                if callback:
                    callback(packets)
                yield packets
            iterations += 1
            time.sleep(self.poll_interval)

    def write_to_realtime(self, realtime_path: str = None):
        """Poll and write to realtime.json continuously."""
        if realtime_path is None:
            realtime_path = os.path.join(ROOT, "data", "realtime.json")

        from utils.json_writer import write_realtime_json

        for packets in self.poll_continuous():
            if packets:
                write_realtime_json(realtime_path, packets[-1])


# ---------------------------------------------------------------------------
#  INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _estimate_yaw_from_pos(position_data, target_date: str):
    """Estimate yaw from position data near target_date."""
    for i, p in enumerate(position_data):
        if p["date"] == target_date and i > 0:
            prev = position_data[i - 1]
            dx = p["x"] - prev["x"]
            dy = p["y"] - prev["y"]
            return math.degrees(math.atan2(dy, dx))
    return 0.0


def _estimate_coolant(speed_kmh: float, throttle: float, initial_temp: float = 80.0):
    """Simplified coolant estimate (OpenF1 doesn't provide it)."""
    heat = throttle * 2.0
    cooling = speed_kmh / 300.0 * 0.5
    return max(70.0, min(120.0, initial_temp + heat - cooling))


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="OpenF1 API bridge")
    sub = parser.add_subparsers(dest="command")

    # sessions
    p_sessions = sub.add_parser("sessions", help="List sessions")
    p_sessions.add_argument("--year", type=int, default=2024)
    p_sessions.add_argument("--gp", type=str)

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch and save session data")
    p_fetch.add_argument("--session-key", type=int, required=True)
    p_fetch.add_argument("--driver", type=int)

    # live
    p_live = sub.add_parser("live", help="Stream live car data to realtime.json")
    p_live.add_argument("--session-key", type=int, required=True)
    p_live.add_argument("--driver", type=int)

    args = parser.parse_args()

    if args.command == "sessions":
        sessions = get_session_info(year=args.year, gp_name=args.gp)
        for s in sessions[:10]:
            print(f"  [{s['session_key']}] {s['circuit_short_name']} - {s['session_name']} ({s['date_start'][:10]})")

    elif args.command == "fetch":
        fpath = save_openf1_session(args.session_key, args.driver)
        if fpath:
            print(f"Data saved to {fpath}")

    elif args.command == "live":
        stream = OpenF1Stream(session_key=args.session_key, driver_number=args.driver)
        print(f"Streaming session {args.session_key}... Press Ctrl+C to stop")
        try:
            stream.write_to_realtime()
        except KeyboardInterrupt:
            print("\nStopped.")

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
