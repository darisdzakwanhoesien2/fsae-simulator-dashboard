import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

from simulator.track_loader import generate_custom_track

st.set_page_config(layout="wide")
st.title("🗺️ Custom Track Designer")

st.subheader("Configure Your Track")

col1, col2, col3 = st.columns(3)

n_left = col1.number_input("Number of LEFT turns", value=6, min_value=0, max_value=20)
n_right = col2.number_input("Number of RIGHT turns", value=6, min_value=0, max_value=20)
seg_length = col3.number_input("Segment Length per Turn (m)", value=20.0)

radius_min = st.slider("Min Turn Radius (m)", 10, 80, 30)
radius_max = st.slider("Max Turn Radius (m)", 10, 150, 60)

points_per_turn = st.slider("Points per Turn", 10, 120, 40)

if st.button("Generate Track"):
    track = generate_custom_track(
        n_left=n_left,
        n_right=n_right,
        seg_length=seg_length,
        radius_range=(radius_min, radius_max),
        points_per_turn=points_per_turn
    )

    st.subheader("Track Preview")

    xs = [p[0] for p in track]
    ys = [p[1] for p in track]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(xs, ys, "-b")
    ax.scatter(xs[0], ys[0], color="green", label="Start")
    ax.scatter(xs[-1], ys[-1], color="red", label="Finish")
    ax.set_aspect("equal")
    ax.grid(True)
    ax.legend()
    
    st.pyplot(fig)

    # Save track to CSV
    import pandas as pd
    df = pd.DataFrame({"x": xs, "y": ys})
    df.to_csv("data/tracks/custom_track.csv", index=False)

    st.success("Track saved to data/tracks/custom_track.csv")
