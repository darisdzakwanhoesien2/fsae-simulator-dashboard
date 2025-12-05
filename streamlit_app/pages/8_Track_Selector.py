# streamlit_app/pages/8_Track_Selector.py

import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import subprocess

from simulator.track_loader import (
    load_track_csv,
    compute_track_length,
    estimate_turns,
    compute_difficulty
)

TRACK_DIR = os.path.join(ROOT, "data", "tracks")

st.set_page_config(layout="wide")
st.title("🎯 Track Selector & Difficulty Analyzer")

# --------------------------------------------------------------
# Load available tracks
# --------------------------------------------------------------
tracks = sorted([f for f in os.listdir(TRACK_DIR) if f.endswith(".csv")])

if len(tracks) == 0:
    st.warning("No tracks found in data/tracks/. Create one first!")
    st.stop()

selected_track = st.selectbox("Choose a track:", tracks)

# --------------------------------------------------------------
# Load & analyze track
# --------------------------------------------------------------
track_path = os.path.join(TRACK_DIR, selected_track)

points = load_track_csv(track_path)
xs = [p[0] for p in points]
ys = [p[1] for p in points]

length = compute_track_length(points)
turns = estimate_turns(points)
curvature_score = turns / length        # simple heuristic
difficulty = compute_difficulty(length, turns, curvature_score)

# --------------------------------------------------------------
# Display statistics
# --------------------------------------------------------------
st.subheader("📊 Track Statistics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Track Length (m)", f"{length:.1f}")
col2.metric("Estimated Turns", turns)
col3.metric("Curvature Score", f"{curvature_score:.4f}")
col4.metric("Difficulty (0-100)", difficulty)

# --------------------------------------------------------------
# Plot track
# --------------------------------------------------------------
st.subheader("🗺️ Track Preview")

fig, ax = plt.subplots(figsize=(6,6))
ax.plot(xs, ys, "-b", linewidth=1.5)
ax.scatter(xs[0], ys[0], color="green", label="Start")
ax.scatter(xs[-1], ys[-1], color="red", label="End")
ax.set_aspect("equal")
ax.grid(True)
ax.legend()

st.pyplot(fig)

# --------------------------------------------------------------
# Run simulator button
# --------------------------------------------------------------
st.subheader("🏎️ Run Simulator with This Track")

if st.button("Run Simulation"):
    sim_script = os.path.join(ROOT, "simulator", "run_simulator_stage_1.py")
    command = ["python", sim_script, "--track", selected_track]

    st.info(f"Running: {' '.join(command)}")

    try:
        subprocess.Popen(command)
        st.success("Simulator started in background.")
    except Exception as e:
        st.error(f"Failed to launch simulator:\n{e}")
