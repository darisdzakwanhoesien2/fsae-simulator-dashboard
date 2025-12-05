# streamlit_app/pages/7_Custom_Track_Designer.py

import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from simulator.track_loader import (
    generate_custom_track,
    generate_realistic_track,
    generate_fia_style_track,
    compute_track_length,
    estimate_turns,
    compute_difficulty,
)

st.set_page_config(layout="wide")
st.title("🗺️ Custom Track Designer")

st.subheader("Track Generator Type")

track_mode = st.selectbox(
    "Choose generator:",
    ["Legacy Custom", "Realistic Circuit", "FIA / Advanced"],
)

st.markdown("---")
st.subheader("Base Parameters")

col1, col2, col3 = st.columns(3)
n_left = col1.number_input("Number of LEFT turns (for Legacy/Realistic)", 0, 20, 6)
n_right = col2.number_input("Number of RIGHT turns (for Legacy/Realistic)", 0, 20, 6)
seg_length = col3.number_input("Base Straight / Segment Length (m)", 5.0, 200.0, 20.0)

radius_min = st.slider("Min Turn Radius (m)", 5, 100, 20)
radius_max = st.slider("Max Turn Radius (m)", 10, 200, 60)

points_per_turn = st.slider(
    "Points per Turn (Legacy Custom only)", 10, 200, 40
)

st.markdown("---")

# -----------------------------------------------------------
# ADVANCED (FIA) PARAMETERS
# -----------------------------------------------------------
if track_mode == "FIA / Advanced":
    st.subheader("FIA / Advanced Settings")

    colA, colB, colC, colD = st.columns(4)
    n_corners = colA.number_input("Normal Corners", 0, 20, 6)
    n_s_curves = colB.number_input("S-Curves", 0, 10, 2)
    n_chicanes = colC.number_input("Chicanes", 0, 10, 1)
    n_hairpins = colD.number_input("Hairpins", 0, 10, 1)

    colE, colF = st.columns(2)
    fia_min_st = colE.number_input("FIA Min Straight (m)", 10.0, 300.0, seg_length)
    fia_max_st = colF.number_input("FIA Max Straight (m)", 20.0, 500.0, seg_length * 3)


# -----------------------------------------------------------
# Helper: Generate timestamped filename
# -----------------------------------------------------------
def generate_track_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"track_{timestamp}.csv"
    folder = os.path.join(ROOT, "data", "tracks")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)


# -----------------------------------------------------------
# Generate Button
# -----------------------------------------------------------
if st.button("🚀 Generate Track"):
    if track_mode == "Legacy Custom":
        track = generate_custom_track(
            n_left=n_left,
            n_right=n_right,
            seg_length=seg_length,
            radius_range=(radius_min, radius_max),
            points_per_turn=points_per_turn,
        )

    elif track_mode == "Realistic Circuit":
        track = generate_realistic_track(
            n_left=n_left,
            n_right=n_right,
            min_straight=seg_length,
            max_straight=seg_length * 2.0,
            min_radius=radius_min,
            max_radius=radius_max,
        )

    else:  # FIA / Advanced
        track = generate_fia_style_track(
            n_corners=n_corners,
            n_s_curves=n_s_curves,
            n_chicanes=n_chicanes,
            n_hairpins=n_hairpins,
            min_straight=fia_min_st,
            max_straight=fia_max_st,
            min_radius=radius_min,
            max_radius=radius_max,
        )

    # -------------------------------------------------------
    # Plot
    # -------------------------------------------------------
    st.subheader("Track Preview")

    xs = [p[0] for p in track]
    ys = [p[1] for p in track]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(xs, ys, "-b", linewidth=1.5)
    ax.scatter(xs[0], ys[0], color="green", label="Start")
    ax.scatter(xs[-1], ys[-1], color="red", label="Finish")
    ax.set_aspect("equal", "box")
    ax.grid(True, linewidth=0.3)
    ax.legend()
    st.pyplot(fig)

    # -------------------------------------------------------
    # Stats / Difficulty
    # -------------------------------------------------------
    length = compute_track_length(track)
    turns = estimate_turns(track)
    curvature_score = turns / max(length, 1.0)
    difficulty = compute_difficulty(length, turns, curvature_score)

    st.subheader("📊 Track Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Length (m)", f"{length:.1f}")
    c2.metric("Turns (approx.)", turns)
    c3.metric("Curvature Score", f"{curvature_score:.3f}")
    c4.metric("Difficulty", difficulty)

    # -------------------------------------------------------
    # Save track
    # -------------------------------------------------------
    save_path = generate_track_filename()
    df = pd.DataFrame({"x": xs, "y": ys})
    df.to_csv(save_path, index=False)

    st.success(f"✅ Track saved: `{os.path.relpath(save_path, ROOT)}`")
