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
REC_DIR = os.path.join(DATA_DIR, "recommendations")   # 🚀 NEW
REALTIME_FILE = os.path.join(DATA_DIR, "realtime.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "sim_progress.json")
STOP_FILE = os.path.join(DATA_DIR, "stop_signal.txt")

os.makedirs(REC_DIR, exist_ok=True)   # ensure folder exists

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
        "t": [], "speed": [], "brake": [], "coolant": [], "yaw": []
    }

# 🚀 NEW — storage for exported recommendation packets
if "recommendation_log" not in st.session_state:
    st.session_state.recommendation_log = []


# ------------------------------------------------------
# Track Selection
# ------------------------------------------------------
tracks = sorted([f for f in os.listdir(TRACK_DIR) if f.endswith(".csv")])
track_name = st.selectbox("Select Track:", tracks)
track_path = os.path.join(TRACK_DIR, track_name)
track_pts = load_track_csv(track_path)
track_x = [p[0] for p in track_pts]
track_y = [p[1] for p in track_pts]

# ------------------------------------------------------
# Simulation Settings
# ------------------------------------------------------
st.subheader("⚙️ Simulation Settings")

driver = st.selectbox(
    "Driver Profile:",
    ["driver_normal", "driver_aggressive", "driver_smooth"],
)

target_laps = st.number_input("Target Laps", 1, 50, 3)
use_policy = st.checkbox("Use Recommender Policy", False)
train_models = st.checkbox("Train Models Before Running", False)

sim_script = os.path.join(ROOT, "simulator", "run_simulator_with_recommender.py")
cmd = [
    "python", sim_script,
    "--track", track_name,
    "--driver-id", driver,
    "--target-laps", str(target_laps),
    "--progress-file", PROGRESS_FILE,
    "--data-dir", DATA_DIR,
    "--track-dir", TRACK_DIR,
    "--log-dir", LOG_DIR,
]
if use_policy: cmd.append("--use-policy")
if train_models: cmd.append("--train-models")

# ------------------------------------------------------
# Start / Stop
# ------------------------------------------------------
st.markdown("---")
colA, colB = st.columns(2)

if colA.button("🚀 Start Simulation"):
    # clear old progress files
    if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)
    if os.path.exists(STOP_FILE): os.remove(STOP_FILE)

    # reset reference + logs
    st.session_state.segment_ref = build_segment_reference()
    st.session_state.recommendation_log = []           # 🚀 NEW — reset logs
    st.session_state.telemetry_history = {
        "t": [], "speed": [], "brake": [], "coolant": [], "yaw": []
    }

    import subprocess
    subprocess.Popen(cmd)
    st.session_state.sim_running = True
    st.success("Simulation started!")

if colB.button("🛑 Stop Simulation"):
    with open(STOP_FILE, "w") as f: f.write("1")
    st.session_state.sim_running = False
    st.warning("Stop signal sent!")


# ------------------------------------------------------
# UI Placeholders
# ------------------------------------------------------
metrics_placeholder = st.empty()
coaching_placeholder = st.empty()
track_col, graph_col = st.columns([2, 1])
track_placeholder = track_col.empty()
graphs_placeholder = graph_col.empty()

progress_placeholder = st.empty()
progress_bar = st.progress(0.0)

telemetry_history = st.session_state.telemetry_history
segment_ref = st.session_state.segment_ref


# ------------------------------------------------------
# Drawing Helpers
# ------------------------------------------------------
def draw_numeric(packet):
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    t = packet["true"]; s = packet["sensors"]
    c1.metric("Speed", f"{t['speed_kmh']:.1f}")
    c2.metric("Throttle", f"{t['throttle']:.2f}")
    c3.metric("Brake", f"{s['brake_pressure']:.1f}")
    c4.metric("Coolant", f"{t['coolant_temp']:.1f}")
    c5.metric("Yaw", f"{t['yaw_deg']:.3f}")
    c6.metric("Lap", int(packet.get("lap", 0)))


def draw_track(packet):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(track_x, track_y, color="lightgray")
    ax.scatter([packet["gps"]["x"]], [packet["gps"]["y"]], color="red", s=80)
    ax.set_aspect("equal"); ax.grid(True)
    return fig


def draw_graphs():
    t = telemetry_history["t"]
    if not t:
        fig, ax = plt.subplots(); ax.text(.5,.5,"No data",ha="center"); return fig
    fig, axes = plt.subplots(4,1,figsize=(6,8),sharex=True)
    axes[0].plot(t, telemetry_history["speed"]); axes[0].set_ylabel("Speed")
    axes[1].plot(t, telemetry_history["brake"], color="green"); axes[1].set_ylabel("Brake")
    axes[2].plot(t, telemetry_history["coolant"], color="red"); axes[2].set_ylabel("Coolant")
    axes[3].plot(t, telemetry_history["yaw"], color="purple"); axes[3].set_ylabel("Yaw")
    for ax in axes: ax.grid(True)
    return fig


def draw_coaching(packet):
    result = recommend_for_packet(packet, segment_ref)
    with coaching_placeholder.container():
        st.markdown("### 🧠 Live Recommendations")
        for msg in result["messages"]:
            st.write(f"- {msg}")

    # 🚀 NEW — Store exported record
    exported_item = {
        "timestamp": packet.get("timestamp"),
        "time": packet.get("t", None),
        "lap": packet.get("lap"),
        "track_index": packet.get("track_index"),
        "speed": packet["true"]["speed_kmh"],
        "throttle": packet["true"]["throttle"],
        "brake": packet["sensors"]["brake_pressure"],
        "delta_speed": result.get("delta_speed"),
        "target_speed": result.get("target_speed"),
        "messages": result["messages"],
    }
    st.session_state.recommendation_log.append(exported_item)


# ------------------------------------------------------
# Save recommendation log
# ------------------------------------------------------
def save_recommendations_to_file():
    ts = int(time.time())
    filename = f"recommendations_{ts}.json"
    full_path = os.path.join(REC_DIR, filename)

    with open(full_path, "w") as f:
        json.dump(st.session_state.recommendation_log, f, indent=2)

    st.success(f"📁 Recommendation log saved: {filename}")
    return filename


# ------------------------------------------------------
# PROGRESS + LIVE LOOP
# ------------------------------------------------------
if st.session_state.sim_running:
    while st.session_state.sim_running:
        # detect stop
        if os.path.exists(STOP_FILE):
            st.session_state.sim_running = False
            save_recommendations_to_file()          # 🚀 NEW
            break

        # progress bar
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE) as f:
                prog = json.load(f)
            lap = prog.get("lap", 0)
            target = prog.get("target", target_laps)
            progress_bar.progress(min(lap / max(target, 1), 1.0))
            progress_placeholder.write(f"Lap {lap}/{target}")

        # realtime packet
        if os.path.exists(REALTIME_FILE):
            with open(REALTIME_FILE) as f:
                packet = json.load(f)

            # numeric + track + graphs
            metrics_placeholder.empty()
            with metrics_placeholder.container():
                draw_numeric(packet)

            track_placeholder.pyplot(draw_track(packet))
            graphs_placeholder.pyplot(draw_graphs())

            # coaching
            draw_coaching(packet)

        time.sleep(0.1)

else:
    st.info("Simulation not running.")
