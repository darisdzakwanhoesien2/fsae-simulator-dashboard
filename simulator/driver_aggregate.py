# simulator/driver_aggregate.py

import os
import json
from typing import Dict, Any, List
from simulator.driver_features import load_session, compute_driver_metrics


def extract_driver_id(session: List[Dict[str, Any]]) -> str:
    """Pull driver_id from first valid packet."""
    for r in session:
        if "driver_id" in r:
            return r["driver_id"]
    return "unknown_driver"


def load_all_sessions(log_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Loads all logs and groups them by driver_id.
    Returns:
        { driver_id: [session_path1, session_path2, ...] }
    """
    files = sorted([f for f in os.listdir(log_dir) if f.endswith(".json")])
    mapping = {}

    for fn in files:
        try:
            session = load_session(os.path.join(log_dir, fn))
        except:
            continue

        driver = extract_driver_id(session)

        if driver not in mapping:
            mapping[driver] = []

        mapping[driver].append(os.path.join(log_dir, fn))

    return mapping


def aggregate_driver_profile(session_paths: List[str]) -> Dict[str, Any]:
    """
    Computes aggregated metrics across all sessions for one driver.
    """
    all_scores = []
    all_lap_times = []
    all_styles = []
    all_aggr = []
    all_smooth = []
    all_cons = []
    all_corner = []

    for path in session_paths:
        session = load_session(path)
        m = compute_driver_metrics(session)

        s = m["scores"]
        all_aggr.append(s["aggression"])
        all_smooth.append(s["smoothness"])
        all_cons.append(s["consistency"])
        all_corner.append(s["cornering_skill"])

        if m["derived"]["lap_time_mean"] > 0:
            all_lap_times.append(m["derived"]["lap_time_mean"])

        all_styles.append(m["style_label"])

    # Majority style label
    from collections import Counter
    style = Counter(all_styles).most_common(1)[0][0]

    return {
        "sessions": len(session_paths),
        "avg_aggression": float(sum(all_aggr) / len(all_aggr)),
        "avg_smoothness": float(sum(all_smooth) / len(all_smooth)),
        "avg_consistency": float(sum(all_cons) / len(all_cons)),
        "avg_cornering": float(sum(all_corner) / len(all_corner)),
        "avg_lap_time": float(sum(all_lap_times) / len(all_lap_times))
            if all_lap_times else None,
        "style_label": style,
    }
