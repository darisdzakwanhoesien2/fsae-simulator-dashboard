# simulator/recommender.py
import os
import json
import numpy as np
from collections import defaultdict
from statistics import mean

# optional ML
try:
    from sklearn.ensemble import RandomForestRegressor
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "logs")

def load_all_sessions(limit=None):
    """Load all JSON sessions from logs directory (optionally limit)."""
    files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])
    sessions = []
    for i, fn in enumerate(files):
        if limit and i >= limit:
            break
        path = os.path.join(LOG_DIR, fn)
        with open(path, "r") as f:
            try:
                sessions.append(json.load(f))
            except Exception:
                continue
    return sessions

def build_segment_database(sessions):
    """
    Build per-segment database from sessions that contain Stage-1 physics format.
    Sessions missing required fields ("true", "track_index", "gps") are skipped.

    Returns:
        db: dict[track_index] = list of (feature_vec, action_vec, lap_time)
    """
    db = defaultdict(list)

    for sess_i, session in enumerate(sessions):

        # Skip empty sessions
        if not session:
            print(f"⚠️ Skipping empty session #{sess_i}")
            continue

        # Check Stage-1 structure
        if not all(
            ("true" in r and
             "track_index" in r and
             "gps" in r and
             "lap" in r)
            for r in session
        ):
            print(f"⚠️ Skipping older session #{sess_i}: missing Stage-1 fields")
            continue

        # Determine max track index
        max_idx = max(r["track_index"] for r in session) or 1

        # Estimate lap time
        try:
            lap_time = session[-1]["t"] - session[0]["t"]
        except:
            lap_time = None

        # Build DB records
        for r in session:
            idx = r["track_index"]
            lap_progress = idx / max_idx

            # feature vector
            f = [
                r["true"].get("speed_kmh", 0),
                r["true"].get("coolant_temp", 0),
                r["true"].get("yaw_deg", 0),
                lap_progress
            ]

            # action vector
            a = [
                r["true"].get("throttle", 0),
                r["true"].get("brake_cmd", 0),
                r["true"].get("steering", 0)
            ]

            db[idx].append((f, a, lap_time))

    print(f"📘 Database built with {sum(len(v) for v in db.values())} samples "
          f"from {len(sessions)} sessions")
    return db


# def build_segment_database(sessions):
#     """
#     Build a per-track-index database: for each index collect feature-action records.
#     Feature vector design (simple):
#       - speed_kmh (true)
#       - coolant_temp (true)
#       - yaw (true)
#       - lap_progress (track_index / max_index)
#     Action:
#       - throttle (true)
#       - brake (true)
#       - steering (if present in true or sensors; Stage1 driver_profile returns steering in-run)
#     Returns:
#       db: dict[track_index] = list of (feature_vec, action_vec, lap_time_reference)
#     """
#     db = defaultdict(list)
#     for session in sessions:
#         # estimate lap time per session by extracting times between lap increments
#         # we'll compute session lap_time as last timestamp - first for simplicity
#         try:
#             lap_time = session[-1]["t"] - session[0]["t"]
#         except Exception:
#             lap_time = None

#         # find max track_index to compute lap_progress
#         if not session:
#             continue
#         max_idx = max([r.get("track_index", 0) for r in session]) or 1
#         for r in session:
#             idx = r.get("track_index", 0)
#             lap_progress = idx / max_idx
#             f = [
#                 r["true"]["speed_kmh"],
#                 r["true"]["coolant_temp"],
#                 r["true"]["yaw_deg"],
#                 lap_progress
#             ]
#             # prefer true actions if present; else fall back to sensors mapping (brake cmd)
#             a = [
#                 r["true"].get("throttle", 0.0),
#                 r["true"].get("brake_cmd", 0.0),
#                 # steering not stored in Stage1 "true" by default; if you add it, use it
#                 r["true"].get("steering", 0.0)
#             ]
#             db[idx].append((f, a, lap_time))
#     return db

def best_action_per_segment_by_best_lap(db):
    """
    Simple policy: choose, for each segment, action tuple from the record that came from the fastest lap (smallest lap_time).
    If lap_time not available, choose mean action.
    """
    policy = {}
    for idx, records in db.items():
        # records: list of (f, a, lap_time)
        # filter records with lap_time
        with_time = [rec for rec in records if rec[2] is not None]
        if with_time:
            best = min(with_time, key=lambda r: r[2])
            policy[idx] = best[1]  # action vector
        else:
            # fallback mean
            ths = [r[1][0] for r in records]
            brs = [r[1][1] for r in records]
            sts = [r[1][2] for r in records]
            policy[idx] = [mean(ths), mean(brs), mean(sts)]
    return policy

def train_regressors_per_action(db, max_samples_per_segment=1000):
    """
    Train small regressors (one per action) using all segment records.
    Returns: models dict with keys "throttle", "brake", "steer" each mapping track_index -> model
    Requires scikit-learn (RandomForestRegressor).
    """
    if not SKLEARN_AVAILABLE:
        raise RuntimeError("scikit-learn not available. Install scikit-learn to use regression policy.")

    models = {}
    models['throttle'] = {}
    models['brake'] = {}
    models['steer'] = {}

    for idx, records in db.items():
        # sample up to max_samples
        recs = records if len(records) <= max_samples_per_segment else records[:max_samples_per_segment]
        X = np.array([r[0] for r in recs])
        Y_th = np.array([r[1][0] for r in recs])
        Y_br = np.array([r[1][1] for r in recs])
        Y_st = np.array([r[1][2] for r in recs])
        # train small RFs
        m_th = RandomForestRegressor(n_estimators=40, max_depth=6, random_state=42)
        m_br = RandomForestRegressor(n_estimators=40, max_depth=6, random_state=42)
        m_st = RandomForestRegressor(n_estimators=40, max_depth=6, random_state=42)
        try:
            m_th.fit(X, Y_th)
            m_br.fit(X, Y_br)
            m_st.fit(X, Y_st)
            models['throttle'][idx] = m_th
            models['brake'][idx] = m_br
            models['steer'][idx] = m_st
        except Exception:
            # fallback: skip if training fails
            continue
    return models

def recommend_action_segment(segment_idx, state_vector, policy_segment_db=None, models=None):
    """
    Recommend [throttle, brake, steer] for single segment.
    - if models provided and has model for index -> use models
    - else if policy_segment_db provided -> return stored action
    - else fallback zeros
    state_vector is feature vector with same ordering used during training
    """
    if models:
        try:
            th = models['throttle'][segment_idx].predict([state_vector])[0]
            br = models['brake'][segment_idx].predict([state_vector])[0]
            st = models['steer'][segment_idx].predict([state_vector])[0]
            return [float(max(0.0, min(1.0, th))), float(max(0.0, min(1.0, br))), float(max(-1.0, min(1.0, st)))]
        except Exception:
            pass
    if policy_segment_db and segment_idx in policy_segment_db:
        return policy_segment_db[segment_idx]
    # fallback conservative
    return [0.5, 0.0, 0.0]
