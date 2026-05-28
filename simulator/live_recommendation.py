# simulator/live_recommendation.py

import numpy as np
from typing import Dict, Any, List

from simulator.recommender import (
    load_all_sessions,
    build_segment_database,
)

# ============================================================
# PART 1 — Build Segment Reference From Historical Data
# ============================================================
def build_segment_reference(
    limit_sessions: int | None = None,
    min_samples_per_segment: int = 5,
) -> Dict[int, Dict[str, Any]]:
    """
    Build a reference "target behaviour" from all past sessions.

    Output (per segment idx):
      {
        "target_speed": float,
        "target_throttle": float,
        "target_brake_cmd": float,
        "samples": int
      }
    """
    sessions = load_all_sessions(limit=limit_sessions)
    db = build_segment_database(sessions)

    segment_ref: Dict[int, Dict[str, Any]] = {}

    for idx, records in db.items():
        if len(records) < min_samples_per_segment:
            continue  # not enough data → skip

        speeds = np.array([r[0][0] for r in records])      # speed_kmh
        throttles = np.array([r[1][0] for r in records])   # throttle
        brakes = np.array([r[1][1] for r in records])      # brake_cmd

        target_speed = float(np.percentile(speeds, 75))     # "fast but safe"
        target_throttle = float(throttles.mean())
        target_brake_cmd = float(brakes.mean())

        segment_ref[idx] = {
            "target_speed": target_speed,
            "target_throttle": target_throttle,
            "target_brake_cmd": target_brake_cmd,
            "samples": len(records),
        }

    return segment_ref


# ============================================================
# PART 2 — Live Recommendation Engine
# ============================================================
def recommend_for_packet(
    packet: Dict[str, Any],
    segment_ref: Dict[int, Dict[str, Any]],
    speed_margin: float = 8.0,
    throttle_margin: float = 0.2,
    brake_margin: float = 0.2,
) -> Dict[str, Any]:
    """
    Produce live coaching feedback for a telemetry packet.
    Used by Streamlit's real-time viewer.

    Returns a dict:
      {
        "messages": [...],
        "has_reference": bool,
        "target_speed": float | None,
        "target_throttle": float | None,
        "target_brake_cmd": float | None,
        "delta_speed": float | None,
        "segment_samples": int | None,
      }
    """

    messages: List[str] = []

    # "true" is the canonical source of simulator state in each packet.
    true = packet.get("true", {})
    idx = packet.get("track_index", None)

    if idx is None:
        return {
            "messages": ["No track_index in packet — cannot map to segment."],
            "has_reference": False,
            "target_speed": None,
            "target_throttle": None,
            "target_brake_cmd": None,
            "delta_speed": None,
            "segment_samples": None,
        }

    if idx not in segment_ref:
        return {
            "messages": [
                "Not enough historical data for this segment yet. "
                "Drive more laps to build a reference."
            ],
            "has_reference": False,
            "target_speed": None,
            "target_throttle": None,
            "target_brake_cmd": None,
            "delta_speed": None,
            "segment_samples": None,
        }

    ref = segment_ref[idx]

    curr_speed = float(true.get("speed_kmh", 0.0))
    curr_throttle = float(true.get("throttle", 0.0))
    curr_brake_cmd = float(true.get("brake_cmd", 0.0))

    target_speed = ref["target_speed"]
    target_throttle = ref["target_throttle"]
    target_brake_cmd = ref["target_brake_cmd"]

    delta_speed = curr_speed - target_speed

    # --------------------------------------------------------
    # SPEED RECOMMENDATION
    # --------------------------------------------------------
    if delta_speed < -speed_margin:
        messages.append(
            f"🟡 Speed is ~{-delta_speed:.1f} km/h lower than reference. "
            f"You may be able to carry more speed."
        )
    elif delta_speed > speed_margin:
        messages.append(
            f"🔻 Speed is ~{delta_speed:.1f} km/h higher than reference. "
            f"Consider braking earlier for stability."
        )
    else:
        messages.append("✅ Speed is close to reference.")

    # --------------------------------------------------------
    # THROTTLE RECOMMENDATION
    # --------------------------------------------------------
    if curr_throttle > target_throttle + throttle_margin:
        messages.append("🔸 Throttle higher than typical — risk of understeer.")
    elif curr_throttle < target_throttle - throttle_margin:
        messages.append("🔹 Throttle lower — consider accelerating earlier.")
    else:
        messages.append("✅ Throttle application looks good.")

    # --------------------------------------------------------
    # BRAKE RECOMMENDATION
    # --------------------------------------------------------
    if curr_brake_cmd > target_brake_cmd + brake_margin:
        messages.append("🛑 Stronger braking than reference — might be over-slowing.")
    elif curr_brake_cmd < target_brake_cmd - brake_margin and curr_brake_cmd > 0.05:
        messages.append("🟡 Lighter braking — verify you reach correct corner entry speed.")
    else:
        messages.append("✅ Braking matches reference.")

    return {
        "messages": messages,
        "has_reference": True,
        "target_speed": target_speed,
        "target_throttle": target_throttle,
        "target_brake_cmd": target_brake_cmd,
        "delta_speed": delta_speed,
        "segment_samples": ref["samples"],
    }


# # simulator/live_recommendation.py

# import os
# import numpy as np
# from typing import Dict, Any, Tuple, List

# from simulator.recommender import (
#     load_all_sessions,
#     build_segment_database,
# )


# def build_segment_reference(
#     limit_sessions: int | None = None,
#     min_samples_per_segment: int = 5,
# ) -> Dict[int, Dict[str, Any]]:
#     """
#     Build a reference "target behaviour" per track_index (segment).

#     Uses your existing build_segment_database(), which returns:
#         db[idx] = list of (feature_vec, action_vec, lap_time)
#     where
#         feature_vec = [speed_kmh, coolant_temp, yaw_deg, lap_progress]
#         action_vec  = [throttle, brake_cmd, steering]

#     We convert that into:
#         segment_ref[idx] = {
#             "target_speed": ...,
#             "target_throttle": ...,
#             "target_brake_cmd": ...,
#             "samples": n,
#         }
#     """

#     sessions = load_all_sessions(limit=limit_sessions)
#     db = build_segment_database(sessions)

#     segment_ref: Dict[int, Dict[str, Any]] = {}

#     for idx, records in db.items():
#         if len(records) < min_samples_per_segment:
#             # skip segments with too little data
#             continue

#         speeds = np.array([r[0][0] for r in records])  # first feature = speed_kmh
#         throttles = np.array([r[1][0] for r in records])  # first action = throttle
#         brakes = np.array([r[1][1] for r in records])  # second action = brake_cmd

#         # "Reference" speed = 75th percentile (fast but not insane)
#         target_speed = float(np.percentile(speeds, 75))
#         # typical throttle / brake in that segment
#         target_throttle = float(throttles.mean())
#         target_brake = float(brakes.mean())

#         segment_ref[idx] = {
#             "target_speed": target_speed,
#             "target_throttle": target_throttle,
#             "target_brake_cmd": target_brake,
#             "samples": len(records),
#         }

#     return segment_ref


# def recommend_for_packet(
#     packet: Dict[str, Any],
#     segment_ref: Dict[int, Dict[str, Any]],
#     speed_margin: float = 8.0,
#     throttle_margin: float = 0.2,
#     brake_margin: float = 0.2,
# ) -> Dict[str, Any]:
#     """
#     Produce live coaching hints for a single telemetry packet, given a
#     precomputed segment reference table.

#     Returns:
#         {
#           "messages": [list of strings],
#           "has_reference": bool,
#           "target_speed": float | None,
#           "target_throttle": float | None,
#           "target_brake_cmd": float | None,
#           "delta_speed": float | None,
#           "segment_samples": int | None,
#         }
#     """
#     messages: List[str] = []

#     true = packet.get("true", {})
#     idx = packet.get("track_index", None)

#     if idx is None:
#         messages.append("No track_index in packet – cannot map to segment.")
#         return {
#             "messages": messages,
#             "has_reference": False,
#             "target_speed": None,
#             "target_throttle": None,
#             "target_brake_cmd": None,
#             "delta_speed": None,
#             "segment_samples": None,
#         }

#     if idx not in segment_ref:
#         messages.append(
#             "Not enough historical data for this segment yet. "
#             "Drive more laps to build a reference."
#         )
#         return {
#             "messages": messages,
#             "has_reference": False,
#             "target_speed": None,
#             "target_throttle": None,
#             "target_brake_cmd": None,
#             "delta_speed": None,
#             "segment_samples": None,
#         }

#     ref = segment_ref[idx]

#     curr_speed = float(true.get("speed_kmh", 0.0))
#     curr_throttle = float(true.get("throttle", 0.0))
#     curr_brake_cmd = float(true.get("brake_cmd", 0.0))

#     target_speed = ref["target_speed"]
#     target_throttle = ref["target_throttle"]
#     target_brake_cmd = ref["target_brake_cmd"]

#     delta_speed = curr_speed - target_speed

#     # --------- Speed guidance ----------
#     if delta_speed < -speed_margin:
#         messages.append(
#             f"Speed here is ~{-delta_speed:.1f} km/h slower than reference. "
#             "You can probably carry more speed or get on throttle earlier if the car feels stable."
#         )
#     elif delta_speed > speed_margin:
#         messages.append(
#             f"Speed here is ~{delta_speed:.1f} km/h faster than reference. "
#             "Make sure your braking point is early enough and you can still make the corner consistently."
#         )
#     else:
#         messages.append("Your speed in this segment is close to the reference – good job 👍.")

#     # --------- Throttle guidance ----------
#     if curr_throttle > target_throttle + throttle_margin:
#         messages.append(
#             "Throttle is higher than typical here. Consider rolling on more gently "
#             "to avoid traction issues or mid-corner understeer."
#         )
#     elif curr_throttle < target_throttle - throttle_margin:
#         messages.append(
#             "Throttle is lower than typical reference here. If the car feels stable, "
#             "you might be able to accelerate harder out of this section."
#         )

#     # --------- Brake guidance ----------
#     if curr_brake_cmd > target_brake_cmd + brake_margin:
#         messages.append(
#             "Braking harder than reference in this segment. You might be over-slowing "
#             "or braking later than needed."
#         )
#     elif curr_brake_cmd < target_brake_cmd - brake_margin and curr_brake_cmd > 0.05:
#         messages.append(
#             "Braking lighter than reference in what seems to be a braking zone. "
#             "Check that you're still reaching an appropriate entry speed for the corner."
#         )

#     # If no detailed advice beyond 'good job', add a generic positive note
#     if len(messages) == 1 and "good job" in messages[0]:
#         messages.append("Keep repeating this behaviour to build consistency.")

#     return {
#         "messages": messages,
#         "has_reference": True,
#         "target_speed": target_speed,
#         "target_throttle": target_throttle,
#         "target_brake_cmd": target_brake_cmd,
#         "delta_speed": delta_speed,
#         "segment_samples": ref["samples"],
#     }
