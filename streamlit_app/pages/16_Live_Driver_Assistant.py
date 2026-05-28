import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from simulator.live_recommendation import (
    build_segment_reference,
    recommend_for_packet,
)

DATA_DIR = os.path.join(ROOT, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
REALTIME_FILE = os.path.join(DATA_DIR, "realtime.json")

st.set_page_config(layout="wide")
st.title("🧠 Live Driving Assistant (Segment-Based Recommendations)")


# -------------------------------------------------
# Cached reference table from history
# -------------------------------------------------
@st.cache_data
def get_segment_reference(limit_sessions: int | None = None, min_samples: int = 5):
    return build_segment_reference(
        limit_sessions=limit_sessions,
        min_samples_per_segment=min_samples,
    )


with st.sidebar:
    st.header("Reference Settings")
    limit_sessions = st.number_input(
        "Max training sessions (0 = all)",
        min_value=0,
        max_value=500,
        value=0,
        step=1,
    )
    min_samples = st.number_input(
        "Min samples per segment",
        min_value=3,
        max_value=100,
        value=5,
        step=1,
    )

    if limit_sessions == 0:
        limit_arg = None
    else:
        limit_arg = int(limit_sessions)

    st.write("Building reference from logs in `data/logs`…")

seg_ref = get_segment_reference(limit_arg, int(min_samples))

st.sidebar.write(f"Segments with reference: **{len(seg_ref)}**")


# -------------------------------------------------
# Load current realtime packet
# -------------------------------------------------
if not os.path.exists(REALTIME_FILE):
    st.error(f"Realtime telemetry file not found: `{REALTIME_FILE}`")
    st.stop()

try:
    with open(REALTIME_FILE, "r") as f:
        packet = json.load(f)
except Exception as e:
    st.error(f"Failed to read realtime.json: {e}")
    st.stop()

true = packet.get("true", {})
sensors = packet.get("sensors", {})
imu = sensors.get("imu", {}) or {}

speed = float(true.get("speed_kmh", 0.0))
throttle = float(true.get("throttle", 0.0))
brake_cmd = float(true.get("brake_cmd", 0.0))
brake_pressure = float(sensors.get("brake_pressure", 0.0))
coolant = float(true.get("coolant_temp", sensors.get("coolant_temp", 0.0)))
yaw = float(true.get("yaw_deg", imu.get("yaw", 0.0)))
lap = int(packet.get("lap", 0))
track_index = int(packet.get("track_index", -1))
t = float(packet.get("t", 0.0))

# -------------------------------------------------
# Compute recommendation
# -------------------------------------------------
rec = recommend_for_packet(packet, seg_ref)


# -------------------------------------------------
# Top numeric metrics
# -------------------------------------------------
st.subheader("📌 Current Telemetry Snapshot")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Speed (km/h)", f"{speed:.1f}")
c2.metric("Throttle", f"{throttle:.2f}")
c3.metric("Brake Cmd", f"{brake_cmd:.2f}")
c4.metric("Brake Pressure", f"{brake_pressure:.1f}")
c5.metric("Coolant (°C)", f"{coolant:.1f}")
c6.metric("Yaw (deg)", f"{yaw:.2f}")

st.markdown(
    f"- **Lap:** {lap} &nbsp;&nbsp; "
    f"**Segment (track_index):** {track_index} &nbsp;&nbsp; "
    f"**Time t:** {t:.2f} s"
)

st.markdown("---")


# -------------------------------------------------
# Current vs Reference Bar Plots
# -------------------------------------------------
st.subheader("📊 Current vs Reference (This Segment)")

if not rec["has_reference"]:
    st.info("\n".join(rec["messages"]))
else:
    left, right = st.columns([2, 1])

    # --- Left: bar charts ---
    with left:
        fig, axes = plt.subplots(3, 1, figsize=(5, 7))

        # 1. Speed
        axes[0].bar(
            ["Current", "Reference"],
            [speed, rec["target_speed"]],
        )
        axes[0].set_ylabel("Speed (km/h)")
        axes[0].set_title("Speed")
        axes[0].grid(axis="y", linestyle="--", alpha=0.4)

        # 2. Throttle
        axes[1].bar(
            ["Current", "Reference"],
            [throttle, rec["target_throttle"]],
        )
        axes[1].set_ylabel("Throttle (0–1)")
        axes[1].set_title("Throttle")
        axes[1].set_ylim(0, 1.0)
        axes[1].grid(axis="y", linestyle="--", alpha=0.4)

        # 3. Brake cmd
        axes[2].bar(
            ["Current", "Reference"],
            [brake_cmd, rec["target_brake_cmd"]],
        )
        axes[2].set_ylabel("Brake Cmd (0–1)")
        axes[2].set_title("Brake Command")
        axes[2].set_ylim(0, 1.0)
        axes[2].grid(axis="y", linestyle="--", alpha=0.4)

        plt.tight_layout()
        st.pyplot(fig)

    # --- Right: coaching messages ---
    with right:
        st.markdown("### 🧑‍🏫 Coach Feedback")

        st.write(f"Reference built from **{rec['segment_samples']}** samples in this segment.")

        for msg in rec["messages"]:
            st.markdown(f"- {msg}")


st.markdown("---")
st.info(
    "This assistant uses historical sessions to build a per-segment reference for "
    "speed, throttle, and brake. As you log more good laps, the recommendations "
    "will become more meaningful."
)
