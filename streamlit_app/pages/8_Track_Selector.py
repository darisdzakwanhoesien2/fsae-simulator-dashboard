import sys, os, time, json, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from simulator.track_loader import (
    load_track_csv,
    compute_track_length,
    estimate_turns,
    compute_difficulty
)

TRACK_DIR = os.path.join(ROOT, "data", "tracks")
PROGRESS_FILE = os.path.join(ROOT, "data", "sim_progress.json")
STOP_FILE = os.path.join(ROOT, "data", "stop_signal.txt")

st.set_page_config(layout="wide")
st.title("🎯 Track Selector + Simulator Control")

# ------------------------------------------------------
# Load Available Tracks
# ------------------------------------------------------
tracks = sorted([f for f in os.listdir(TRACK_DIR) if f.endswith(".csv")])
if not tracks:
    st.error("⚠ No tracks found in data/tracks/")
    st.stop()

track_name = st.selectbox("Select Track:", tracks)
track_path = os.path.join(TRACK_DIR, track_name)

# Load track
points = load_track_csv(track_path)
xs = [p[0] for p in points]
ys = [p[1] for p in points]

# ------------------------------------------------------
# Track Stats
# ------------------------------------------------------
length = compute_track_length(points)
turns = estimate_turns(points)
curvature = turns / max(length, 1)
difficulty = compute_difficulty(length, turns, curvature)

st.subheader("📊 Track Stats")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Length (m)", f"{length:.1f}")
col2.metric("Turns", turns)
col3.metric("Curvature Score", f"{curvature:.3f}")
col4.metric("Difficulty", difficulty)

# ------------------------------------------------------
# Track Preview
# ------------------------------------------------------
st.subheader("🗺️ Track Preview")

fig, ax = plt.subplots(figsize=(6,6))
ax.plot(xs, ys, "-b", linewidth=1.5)
ax.scatter(xs[0], ys[0], color="green", label="Start")
ax.scatter(xs[-1], ys[-1], color="red", label="Finish")
ax.set_aspect("equal")
ax.grid(True)
ax.legend()
st.pyplot(fig)

# ------------------------------------------------------
# Simulation Settings
# ------------------------------------------------------
st.subheader("🏎 Simulation Settings")

driver = st.selectbox("Driver Profile:", ["driver_normal", "driver_aggressive", "driver_smooth"])
target_laps = st.number_input("Target Laps", min_value=1, max_value=50, value=5)

use_policy = st.checkbox("Use Recommender Policy", value=False)
train_models = st.checkbox("Train Models Before Running", value=False)

cmd = [
    "python",
    os.path.join(ROOT, "simulator", "run_simulator_with_recommender.py"),
    "--track", track_name,
    "--driver-id", driver,
    "--target-laps", str(target_laps),
    "--progress-file", PROGRESS_FILE,
]

if use_policy:
    cmd.append("--use-policy")
if train_models:
    cmd.append("--train-models")

# ------------------------------------------------------
# Start Simulation
# ------------------------------------------------------
if st.button("🚀 Start Simulation"):
    # Remove old progress or stop signals
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)

    st.session_state["sim_running"] = True
    subprocess.Popen(cmd)
    st.success("Simulator launched in background!")

# ------------------------------------------------------
# Stop Simulation
# ------------------------------------------------------
if st.button("🛑 STOP Simulation"):
    with open(STOP_FILE, "w") as f:
        f.write("1")
    st.session_state["sim_running"] = False
    st.warning("Stop signal sent. Simulator will stop soon.")

# ------------------------------------------------------
# Progress Bar
# ------------------------------------------------------
if st.session_state.get("sim_running", False):
    st.subheader("📡 Simulation Progress")

    progress_placeholder = st.empty()
    bar = st.progress(0)

    while True:
        if os.path.exists(STOP_FILE):
            st.warning("Simulation stopped by user.")
            break

        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r") as f:
                    prog = json.load(f)

                lap = prog.get("lap", 0)
                target = prog.get("target", target_laps)
                pct = min(lap / target, 1.0)

                bar.progress(pct)
                progress_placeholder.write(f"Lap {lap} / {target}")

                if lap >= target:
                    st.success("Simulation complete!")
                    st.session_state["sim_running"] = False
                    break

            except Exception:
                pass

        time.sleep(0.25)



# # streamlit_app/pages/8_Track_Selector.py

# import sys, os
# ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# sys.path.append(ROOT)

# import streamlit as st
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import subprocess

# from simulator.track_loader import (
#     load_track_csv,
#     compute_track_length,
#     estimate_turns,
#     compute_difficulty
# )

# TRACK_DIR = os.path.join(ROOT, "data", "tracks")

# st.set_page_config(layout="wide")
# st.title("🎯 Track Selector & Difficulty Analyzer")

# # --------------------------------------------------------------
# # Load available tracks
# # --------------------------------------------------------------
# tracks = sorted([f for f in os.listdir(TRACK_DIR) if f.endswith(".csv")])

# if len(tracks) == 0:
#     st.warning("No tracks found in data/tracks/. Create one first!")
#     st.stop()

# selected_track = st.selectbox("Choose a track:", tracks)

# # --------------------------------------------------------------
# # Load & analyze track
# # --------------------------------------------------------------
# track_path = os.path.join(TRACK_DIR, selected_track)

# points = load_track_csv(track_path)
# xs = [p[0] for p in points]
# ys = [p[1] for p in points]

# length = compute_track_length(points)
# turns = estimate_turns(points)
# curvature_score = turns / length        # simple heuristic
# difficulty = compute_difficulty(length, turns, curvature_score)

# # --------------------------------------------------------------
# # Display statistics
# # --------------------------------------------------------------
# st.subheader("📊 Track Statistics")

# col1, col2, col3, col4 = st.columns(4)
# col1.metric("Track Length (m)", f"{length:.1f}")
# col2.metric("Estimated Turns", turns)
# col3.metric("Curvature Score", f"{curvature_score:.4f}")
# col4.metric("Difficulty (0-100)", difficulty)

# # --------------------------------------------------------------
# # Plot track
# # --------------------------------------------------------------
# st.subheader("🗺️ Track Preview")

# fig, ax = plt.subplots(figsize=(6,6))
# ax.plot(xs, ys, "-b", linewidth=1.5)
# ax.scatter(xs[0], ys[0], color="green", label="Start")
# ax.scatter(xs[-1], ys[-1], color="red", label="End")
# ax.set_aspect("equal")
# ax.grid(True)
# ax.legend()

# st.pyplot(fig)

# # --------------------------------------------------------------
# # Run simulator button
# # --------------------------------------------------------------
# st.subheader("🏎️ Run Simulator with This Track")

# if st.button("Run Simulation"):
#     sim_script = os.path.join(ROOT, "simulator", "run_simulator_stage_1.py")
#     command = ["python", sim_script, "--track", selected_track]

#     st.info(f"Running: {' '.join(command)}")

#     try:
#         subprocess.Popen(command)
#         st.success("Simulator started in background.")
#     except Exception as e:
#         st.error(f"Failed to launch simulator:\n{e}")
