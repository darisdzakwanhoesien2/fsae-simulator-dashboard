import sys
import os
import json
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

from simulator.track_loader import (
    load_track_csv,
    compute_track_length,
    estimate_turns,
    compute_difficulty,
)
from simulator.live_recommendation import (
    build_segment_reference,
    recommend_for_packet,
)

# ------------------------------------------------------
# Paths
# ------------------------------------------------------
TRACK_DIR = os.path.join(ROOT, "data", "tracks")
DATA_DIR = os.path.join(ROOT, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
REALTIME_FILE = os.path.join(DATA_DIR, "realtime.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "sim_progress.json")
STOP_FILE = os.path.join(DATA_DIR, "stop_signal.txt")

st.set_page_config(layout="wide")
st.title("🏎 Live Simulation + Telemetry + Coaching")

# ------------------------------------------------------
# Session State Init
# ------------------------------------------------------
if "sim_running" not in st.session_state:
    st.session_state.sim_running = False

if "segment_ref" not in st.session_state:
    st.session_state.segment_ref = None

if "telemetry_history" not in st.session_state:
    st.session_state.telemetry_history = {
        "t": [],
        "speed": [],
        "brake": [],
        "coolant": [],
        "yaw": [],
    }


# ------------------------------------------------------
# Track Selection
# ------------------------------------------------------
tracks = sorted([f for f in os.listdir(TRACK_DIR) if f.endswith(".csv")])
if not tracks:
    st.error("❌ No tracks found in data/tracks/")
    st.stop()

track_name = st.selectbox("Select Track:", tracks)
track_path = os.path.join(TRACK_DIR, track_name)

track_pts = load_track_csv(track_path)
track_x = [p[0] for p in track_pts]
track_y = [p[1] for p in track_pts]

# Track stats
length = compute_track_length(track_pts)
turns = estimate_turns(track_pts)
curvature = turns / max(length, 1.0)
difficulty = compute_difficulty(length, turns, curvature)

st.subheader("📊 Track Stats")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Length (m)", f"{length:.1f}")
c2.metric("Turns", turns)
c3.metric("Curvature", f"{curvature:.3f}")
c4.metric("Difficulty", difficulty)

st.subheader("🗺️ Track Layout")
fig_track, ax_track = plt.subplots(figsize=(5, 5))
ax_track.plot(track_x, track_y, "-b", linewidth=1.5)
ax_track.scatter(track_x[0], track_y[0], color="green", label="Start")
ax_track.scatter(track_x[-1], track_y[-1], color="red", label="Finish")
ax_track.set_aspect("equal")
ax_track.grid(True)
ax_track.legend()
st.pyplot(fig_track)

# ------------------------------------------------------
# Simulation Settings
# ------------------------------------------------------
st.subheader("⚙️ Simulation Settings")

driver = st.selectbox(
    "Driver Profile:",
    ["driver_normal", "driver_aggressive", "driver_smooth"],
)

target_laps = st.number_input("Target Laps", min_value=1, max_value=50, value=3)

use_policy = st.checkbox("Use Recommender Policy", value=False)
train_models = st.checkbox("Train Models Before Running", value=False)

sim_script = os.path.join(ROOT, "simulator", "run_simulator_with_recommender.py")
cmd = [
    "python",
    sim_script,
    "--track", track_name,
    "--driver-id", driver,
    "--target-laps", str(target_laps),
    "--progress-file", PROGRESS_FILE,
    "--data-dir", DATA_DIR,
    "--track-dir", TRACK_DIR,
    "--log-dir", LOG_DIR,
]
if use_policy:
    cmd.append("--use-policy")
if train_models:
    cmd.append("--train-models")

# ------------------------------------------------------
# Start / Stop Controls
# ------------------------------------------------------
st.markdown("---")
col_start, col_stop = st.columns(2)

if col_start.button("🚀 Start Simulation"):
    # clean old files
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)

    # build / refresh segment reference
    with st.spinner("Building historical reference for live coaching..."):
        st.session_state.segment_ref = build_segment_reference()

    # clear telemetry history
    st.session_state.telemetry_history = {
        "t": [],
        "speed": [],
        "brake": [],
        "coolant": [],
        "yaw": [],
    }

    import subprocess
    subprocess.Popen(cmd)
    st.session_state.sim_running = True
    st.success("Simulation started with live recommendations!")

if col_stop.button("🛑 Stop Simulation"):
    with open(STOP_FILE, "w") as f:
        f.write("1")
    st.session_state.sim_running = False
    st.warning("Stop signal sent. Simulator will stop soon.")

st.markdown("---")

# ------------------------------------------------------
# Layout: Telemetry + Coaching
# ------------------------------------------------------
top_left, top_right = st.columns([2, 2])
bottom_left, bottom_right = st.columns([2, 1])

metrics_placeholder = top_left.empty()
coaching_placeholder = top_right.empty()
track_placeholder = bottom_left.empty()
graphs_placeholder = bottom_right.empty()

progress_placeholder = st.empty()
progress_bar = st.progress(0.0)

telemetry_history = st.session_state.telemetry_history
segment_ref = st.session_state.segment_ref


# ------------------------------------------------------
# Drawing helpers
# ------------------------------------------------------
def draw_numeric(packet):
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    true = packet.get("true", {})
    sensors = packet.get("sensors", {})

    c1.metric("Speed", f"{true.get('speed_kmh', 0.0):.1f} km/h")
    c2.metric("Throttle", f"{true.get('throttle', 0.0):.2f}")
    c3.metric("Brake", f"{sensors.get('brake_pressure', 0.0):.1f} bar")
    c4.metric("Coolant", f"{true.get('coolant_temp', 0.0):.1f} °C")
    c5.metric("Yaw", f"{true.get('yaw_deg', 0.0):.3f}")
    c6.metric("Lap", int(packet.get("lap", 0)))


def draw_track(packet):
    x = packet["gps"]["x"]
    y = packet["gps"]["y"]

    fig, ax = plt.subplots(figsize=(6, 6))
    # track
    ax.plot(track_x, track_y, color="lightgray", linewidth=1.5)
    # driven line (optional: previous path)
    if telemetry_history["t"]:
        xs_hist = [p[0] for p in telemetry_history.get("pos", [])] if "pos" in telemetry_history else None
    # car position
    ax.scatter([x], [y], color="red", s=80)
    ax.set_aspect("equal")
    ax.grid(True)
    ax.set_title("Live Car Position")
    return fig


def draw_graphs():
    t = telemetry_history["t"]
    if not t:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.text(0.5, 0.5, "No telemetry yet", ha="center", va="center")
        ax.axis("off")
        return fig

    fig, axes = plt.subplots(4, 1, figsize=(6, 8), sharex=True)

    axes[0].plot(t, telemetry_history["speed"])
    axes[0].set_ylabel("Speed")

    axes[1].plot(t, telemetry_history["brake"], color="green")
    axes[1].set_ylabel("Brake")

    axes[2].plot(t, telemetry_history["coolant"], color="red")
    axes[2].set_ylabel("Coolant")

    axes[3].plot(t, telemetry_history["yaw"], color="purple")
    axes[3].set_ylabel("Yaw")
    axes[3].set_xlabel("Timestamp")

    for ax in axes:
        ax.grid(True)

    return fig


def draw_coaching(packet):
    if segment_ref is None:
        with coaching_placeholder.container():
            st.info("No reference data yet for coaching.")
        return

    result = recommend_for_packet(packet, segment_ref)

    with coaching_placeholder.container():
        st.markdown("### 🧠 Live Recommendations")
        for msg in result["messages"]:
            st.write(f"- {msg}")

        if result["has_reference"]:
            st.markdown("#### 📌 Reference Targets")
            st.write(f"- Target speed: {result['target_speed']:.1f} km/h")
            st.write(f"- Target throttle: {result['target_throttle']:.2f}")
            st.write(f"- Target brake cmd: {result['target_brake_cmd']:.2f}")
            st.write(f"- Segment samples: {result['segment_samples']}")
        else:
            st.write("Not enough data for this segment yet.")


def update_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                prog = json.load(f)
            lap = prog.get("lap", 0)
            target = prog.get("target", target_laps)
            pct = min(lap / max(target, 1), 1.0)
            progress_bar.progress(pct)
            progress_placeholder.write(f"📡 Lap {lap} / {target}")
            if lap >= target:
                st.session_state.sim_running = False
                st.success("✅ Simulation complete!")
        except Exception:
            pass


# ------------------------------------------------------
# LIVE LOOP
# ------------------------------------------------------
if st.session_state.sim_running:
    while st.session_state.sim_running:
        # Stop signal?
        if os.path.exists(STOP_FILE):
            st.warning("Stop signal detected. Ending live loop.")
            st.session_state.sim_running = False
            break

        # Progress bar from sim_progress.json
        update_progress()

        # Read realtime packet
        if os.path.exists(REALTIME_FILE):
            try:
                with open(REALTIME_FILE, "r") as f:
                    packet = json.load(f)
            except Exception:
                time.sleep(0.1)
                continue

            # Update history
            t = packet.get("timestamp", time.time())
            telemetry_history["t"].append(t)
            telemetry_history["speed"].append(packet["true"]["speed_kmh"])
            telemetry_history["brake"].append(packet["sensors"]["brake_pressure"])
            telemetry_history["coolant"].append(packet["true"]["coolant_temp"])
            telemetry_history["yaw"].append(packet["true"]["yaw_deg"])

            # Numeric metrics
            metrics_placeholder.empty()
            with metrics_placeholder.container():
                draw_numeric(packet)

            # Track + graphs
            track_placeholder.pyplot(draw_track(packet))
            graphs_placeholder.pyplot(draw_graphs())

            # Coaching
            draw_coaching(packet)

        time.sleep(0.1)

else:
    st.info("Simulation not running. Start it to see live telemetry and coaching.")
