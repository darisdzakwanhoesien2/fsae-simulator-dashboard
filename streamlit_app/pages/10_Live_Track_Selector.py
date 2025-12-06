# streamlit_app/pages/8_Track_Selector.py

import sys, os, json, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from simulator.track_loader import load_track_csv

TRACK_DIR = os.path.join(ROOT, "data", "tracks")
DATA_DIR = os.path.join(ROOT, "data")
REALTIME_FILE = os.path.join(DATA_DIR, "realtime.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "sim_progress.json")
STOP_FILE = os.path.join(DATA_DIR, "stop_signal.txt")

st.set_page_config(layout="wide")
st.title("🏎 Live Simulation + Telemetry Viewer")


# ------------------------------------------------------
# Select Track
# ------------------------------------------------------
tracks = sorted([f for f in os.listdir(TRACK_DIR) if f.endswith(".csv")])
track_name = st.selectbox("Select Track:", tracks)
track_path = os.path.join(TRACK_DIR, track_name)

track_pts = load_track_csv(track_path)
track_x = [p[0] for p in track_pts]
track_y = [p[1] for p in track_pts]


# ------------------------------------------------------
# Driver + Simulation Settings
# ------------------------------------------------------
st.subheader("Simulation Settings")

driver = st.selectbox("Driver Profile", [
    "driver_normal", "driver_aggressive", "driver_smooth"
])

target_laps = st.number_input("Target Laps", 1, 50, 3)
use_policy = st.checkbox("Use Recommender Policy", False)
train_models = st.checkbox("Train Models Before Running", False)

sim_cmd = [
    "python",
    os.path.join(ROOT, "simulator", "run_simulator_with_recommender.py"),
    "--track", track_name,
    "--driver-id", driver,
    "--target-laps", str(target_laps),
    "--progress-file", PROGRESS_FILE,
    "--data-dir", DATA_DIR,
    "--track-dir", TRACK_DIR,
    "--log-dir", os.path.join(DATA_DIR, "logs"),
]

if use_policy:
    sim_cmd.append("--use-policy")
if train_models:
    sim_cmd.append("--train-models")


# ------------------------------------------------------
# Start / Stop buttons
# ------------------------------------------------------
colA, colB = st.columns(2)

if "sim_running" not in st.session_state:
    st.session_state.sim_running = False

if colA.button("🚀 Start Simulation"):
    if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)
    if os.path.exists(STOP_FILE): os.remove(STOP_FILE)

    import subprocess
    subprocess.Popen(sim_cmd)

    st.session_state.sim_running = True
    st.success("Simulation Started!")


if colB.button("🛑 Stop Simulation"):
    with open(STOP_FILE, "w") as f:
        f.write("1")
    st.session_state.sim_running = False
    st.warning("Stop signal sent!")


st.markdown("---")
st.subheader("📡 Live Telemetry")


# ------------------------------------------------------
# UI placeholders
# ------------------------------------------------------
metrics_placeholder = st.empty()
track_col, graph_col = st.columns([2, 1])
track_placeholder = track_col.empty()
graph_placeholder = graph_col.empty()


# ------------------------------------------------------
# Live telemetry loop
# ------------------------------------------------------
def draw_numeric(packet):
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Speed", f"{packet['true']['speed_kmh']:.1f} km/h")
    c2.metric("Throttle", f"{packet['true']['throttle']:.2f}")
    c3.metric("Brake", f"{packet['sensors']['brake_pressure']:.1f} bar")
    c4.metric("Coolant", f"{packet['true']['coolant_temp']:.1f} °C")
    c5.metric("Yaw", f"{packet['true']['yaw_deg']:.3f}")
    c6.metric("Lap", int(packet.get("lap", 0)))


def draw_track(packet):
    x = packet["gps"]["x"]
    y = packet["gps"]["y"]

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot(track_x, track_y, color="lightgray")
    ax.scatter([x], [y], color="red", s=80)
    ax.set_aspect("equal")
    ax.grid(True)
    ax.set_title("Live Car Position")
    return fig


telemetry_history = {
    "t": [],
    "speed": [],
    "brake": [],
    "coolant": [],
    "yaw": [],
}


def draw_graphs():
    t = telemetry_history["t"]

    fig, axes = plt.subplots(4, 1, figsize=(6, 8), sharex=True)

    axes[0].plot(t, telemetry_history["speed"])
    axes[0].set_ylabel("Speed")

    axes[1].plot(t, telemetry_history["brake"], color="green")
    axes[1].set_ylabel("Brake")

    axes[2].plot(t, telemetry_history["coolant"], color="red")
    axes[2].set_ylabel("Coolant")

    axes[3].plot(t, telemetry_history["yaw"], color="purple")
    axes[3].set_ylabel("Yaw")
    axes[3].set_xlabel("Time (s)")

    for ax in axes:
        ax.grid(True)

    return fig


# ------------------------------------------------------
# LIVE LOOP
# ------------------------------------------------------
if st.session_state.sim_running:
    while st.session_state.sim_running:
        if os.path.exists(REALTIME_FILE):
            with open(REALTIME_FILE, "r") as f:
                packet = json.load(f)

            t = packet["timestamp"]

            telemetry_history["t"].append(t)
            telemetry_history["speed"].append(packet["true"]["speed_kmh"])
            telemetry_history["brake"].append(packet["sensors"]["brake_pressure"])
            telemetry_history["coolant"].append(packet["true"]["coolant_temp"])
            telemetry_history["yaw"].append(packet["true"]["yaw_deg"])

            # show UI
            metrics_placeholder.empty()
            with metrics_placeholder.container():
                draw_numeric(packet)

            track_placeholder.pyplot(draw_track(packet))
            graph_placeholder.pyplot(draw_graphs())

        time.sleep(0.1)

else:
    st.info("Simulation not running.")
