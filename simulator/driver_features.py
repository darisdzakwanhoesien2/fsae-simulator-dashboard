# simulator/driver_features.py

import os
import json
import math
from typing import Dict, Any, List, Tuple, Optional
import statistics as stats

import numpy as np


def load_session(path: str) -> List[Dict[str, Any]]:
    """Load a single JSON session file (list of packets)."""
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Session {path} is not a list of packets.")
    return data


def extract_time_series(session: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    """
    Extract core 1D time-series from a session into numpy arrays.
    Assumes Stage-1 physics packet structure.
    """

    ts = []
    laps = []
    speed = []
    throttle = []
    brake_cmd = []
    brake_pressure = []
    coolant_true = []
    coolant_sensor = []
    yaw_deg_true = []
    yaw_sensor = []
    steering = []

    for r in session:
        t = r.get("t", None)
        if t is None:
            # fallback to timestamp
            t = r.get("timestamp", 0.0)
        ts.append(float(t))

        laps.append(int(r.get("lap", 0)))

        true = r.get("true", {})
        sensors = r.get("sensors", {})

        speed.append(float(true.get("speed_kmh", 0.0)))
        throttle.append(float(true.get("throttle", 0.0)))
        brake_cmd.append(float(true.get("brake_cmd", 0.0)))
        coolant_true.append(float(true.get("coolant_temp", 0.0)))
        yaw_deg_true.append(float(true.get("yaw_deg", 0.0)))

        # optional steering (may not be present in your current packets)
        steering.append(float(true.get("steering", 0.0)))

        brake_pressure.append(float(sensors.get("brake_pressure", 0.0)))
        coolant_sensor.append(float(sensors.get("coolant_temp", coolant_true[-1])))

        imu = sensors.get("imu", None)
        if imu is not None:
            yaw_sensor.append(float(imu.get("yaw", yaw_deg_true[-1])))
        else:
            yaw_sensor.append(yaw_deg_true[-1])

    return {
        "t": np.array(ts),
        "lap": np.array(laps, dtype=int),
        "speed": np.array(speed),
        "throttle": np.array(throttle),
        "brake_cmd": np.array(brake_cmd),
        "brake_pressure": np.array(brake_pressure),
        "coolant_true": np.array(coolant_true),
        "coolant_sensor": np.array(coolant_sensor),
        "yaw_true": np.array(yaw_deg_true),
        "yaw_sensor": np.array(yaw_sensor),
        "steering": np.array(steering),
    }


def _safe_stats(arr: np.ndarray) -> Dict[str, float]:
    """Return mean/std/max for a 1D array, safely."""
    if arr.size == 0:
        return {"mean": 0.0, "std": 0.0, "max": 0.0}
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "max": float(arr.max()),
    }


def _spike_rate(arr: np.ndarray, threshold: float) -> float:
    """
    Fraction of time-steps where |Δx| > threshold.
    Measures aggressiveness / jerkiness of a control input.
    """
    if arr.size < 2:
        return 0.0
    diffs = np.abs(np.diff(arr))
    spikes = (diffs > threshold).sum()
    return float(spikes) / float(len(diffs))


def _detect_corners(yaw_deg: np.ndarray, t: np.ndarray,
                    yaw_thresh: float = 3.0,
                    min_duration: float = 0.2) -> List[Tuple[int, int]]:
    """
    Very simple corner detection: contiguous regions where |yaw| > yaw_thresh.
    Returns list of (start_idx, end_idx).
    """
    if yaw_deg.size == 0:
        return []

    in_corner = False
    start_idx = 0
    corners: List[Tuple[int, int]] = []

    for i in range(len(yaw_deg)):
        if abs(yaw_deg[i]) > yaw_thresh:
            if not in_corner:
                in_corner = True
                start_idx = i
        else:
            if in_corner:
                # close corner
                end_idx = i
                # check duration
                if t[end_idx - 1] - t[start_idx] >= min_duration:
                    corners.append((start_idx, end_idx))
                in_corner = False

    # If still in corner at end
    if in_corner:
        end_idx = len(yaw_deg) - 1
        if t[end_idx] - t[start_idx] >= min_duration:
            corners.append((start_idx, end_idx))

    return corners


def _lap_times(t: np.ndarray, laps: np.ndarray) -> List[float]:
    """
    Compute per-lap duration from time & lap arrays.
    Assumes lap increases when crossing start/finish.
    """
    lap_ids = np.unique(laps)
    lap_ids = lap_ids[lap_ids >= 0]

    lap_times: List[float] = []

    for lap in lap_ids:
        mask = laps == lap
        if not mask.any():
            continue
        t_lap = t[mask]
        if t_lap.size < 2:
            continue
        lap_times.append(float(t_lap[-1] - t_lap[0]))

    return lap_times


def compute_driver_metrics(session: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute performance & style features for one session.
    Returns a dict with basic stats + higher level behavior scores.
    """
    ts = extract_time_series(session)

    t = ts["t"]
    laps = ts["lap"]
    speed = ts["speed"]
    throttle = ts["throttle"]
    brake_cmd = ts["brake_cmd"]
    brake_pressure = ts["brake_pressure"]
    coolant = ts["coolant_true"]
    yaw = ts["yaw_true"]
    steering = ts["steering"]

    # ---------- Basic stats ----------
    speed_stats = _safe_stats(speed)
    throttle_stats = _safe_stats(throttle)
    brake_stats = _safe_stats(brake_pressure)
    coolant_stats = _safe_stats(coolant)
    yaw_stats = _safe_stats(yaw)

    # ---------- Aggression / Smoothness ----------
    throttle_spike_rate = _spike_rate(throttle, threshold=0.15)
    brake_spike_rate = _spike_rate(brake_pressure, threshold=2.0)
    steering_spike_rate = _spike_rate(steering, threshold=0.15) if np.any(steering) else 0.0

    # ---------- Corner behaviour ----------
    corners = _detect_corners(yaw, t, yaw_thresh=3.0, min_duration=0.2)
    corner_speeds = []
    corner_yaw_std = []

    for (i0, i1) in corners:
        s_seg = speed[i0:i1]
        yaw_seg = yaw[i0:i1]
        if s_seg.size > 0:
            corner_speeds.append(float(s_seg.mean()))
        if yaw_seg.size > 0:
            corner_yaw_std.append(float(yaw_seg.std()))

    if corner_speeds:
        corner_speed_mean = float(np.mean(corner_speeds))
    else:
        corner_speed_mean = 0.0

    if corner_yaw_std:
        corner_stability = 1.0 / (1.0 + float(np.mean(corner_yaw_std)))  # lower yaw std ⇒ higher stability
    else:
        corner_stability = 0.0

    # ---------- Lap performance ----------
    lap_times = _lap_times(t, laps)
    if lap_times:
        lap_time_mean = float(np.mean(lap_times))
        lap_time_std = float(np.std(lap_times))
    else:
        lap_time_mean = 0.0
        lap_time_std = 0.0

    # ---------- Composite style scores (0–1-ish) ----------
    # normalize by some rough scales
    aggression_score = float(
        0.4 * min(throttle_spike_rate * 5.0, 1.0) +
        0.4 * min(brake_spike_rate * 2.0, 1.0) +
        0.2 * min(speed_stats["mean"] / 120.0, 1.0)
    )

    smoothness_score = float(
        1.0 - min(steering_spike_rate * 5.0, 1.0)
    )

    consistency_score = float(
        1.0 / (1.0 + lap_time_std) if lap_time_std > 0 else 0.0
    )

    cornering_skill_score = float(
        0.5 * min(corner_speed_mean / max(speed_stats["max"], 1.0), 1.0) +
        0.5 * corner_stability
    )

    # ---------- Overall style classification (simple heuristic) ----------
    style_label = "unknown"
    if aggression_score > 0.7 and smoothness_score < 0.4:
        style_label = "aggressive"
    elif aggression_score < 0.4 and smoothness_score > 0.6:
        style_label = "smooth"
    elif cornering_skill_score > 0.6 and consistency_score > 0.5:
        style_label = "fast_consistent"
    elif aggression_score < 0.3 and speed_stats["mean"] < 40:
        style_label = "conservative"
    else:
        style_label = "balanced"

    return {
        "basic": {
            "speed": speed_stats,
            "throttle": throttle_stats,
            "brake_pressure": brake_stats,
            "coolant": coolant_stats,
            "yaw": yaw_stats,
            "laps_completed": int(laps.max()) if laps.size > 0 else 0,
        },
        "derived": {
            "throttle_spike_rate": throttle_spike_rate,
            "brake_spike_rate": brake_spike_rate,
            "steering_spike_rate": steering_spike_rate,
            "corner_speed_mean": corner_speed_mean,
            "corner_stability": corner_stability,
            "lap_time_mean": lap_time_mean,
            "lap_time_std": lap_time_std,
        },
        "scores": {
            "aggression": aggression_score,
            "smoothness": smoothness_score,
            "consistency": consistency_score,
            "cornering_skill": cornering_skill_score,
        },
        "style_label": style_label,
        "num_corners_detected": len(corners),
        "num_laps_detected": len(_lap_times(t, laps)),
    }
