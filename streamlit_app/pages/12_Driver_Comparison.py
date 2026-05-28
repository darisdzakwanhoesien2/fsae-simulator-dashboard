import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from simulator.driver_aggregate import (
    load_all_sessions,
    aggregate_driver_profile
)

LOG_DIR = os.path.join(ROOT, "data", "logs")

st.set_page_config(layout="wide")
st.title("⚔️ Driver Comparison — Style & Performance")

mapping = load_all_sessions(LOG_DIR)
drivers = sorted(mapping.keys())

if len(drivers) < 2:
    st.error("Need at least two drivers to compare.")
    st.stop()

col1, col2 = st.columns(2)
d1 = col1.selectbox("Driver A:", drivers)
d2 = col2.selectbox("Driver B:", drivers)

profileA = aggregate_driver_profile(mapping[d1])
profileB = aggregate_driver_profile(mapping[d2])

st.markdown("---")
st.subheader("📈 Score Comparison")

# Show metrics side-by-side
mA = np.array([
    profileA["avg_aggression"],
    profileA["avg_smoothness"],
    profileA["avg_consistency"],
    profileA["avg_cornering"],
])

mB = np.array([
    profileB["avg_aggression"],
    profileB["avg_smoothness"],
    profileB["avg_consistency"],
    profileB["avg_cornering"],
])

labels = ["Aggression", "Smoothness", "Consistency", "Cornering"]

fig, ax = plt.subplots(figsize=(7,4))
x = np.arange(len(labels))
width = 0.35

ax.bar(x - width/2, mA, width, label=d1)
ax.bar(x + width/2, mB, width, label=d2)

ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylim(0, 1)
ax.legend()
ax.grid(True)

st.pyplot(fig)

# Lap time comparison
st.subheader("⏱ Lap Time Comparison")

ltA = profileA["avg_lap_time"]
ltB = profileB["avg_lap_time"]

st.write(f"Avg Lap Time — **{d1}**: {ltA:.2f} s")
st.write(f"Avg Lap Time — **{d2}**: {ltB:.2f} s")

fig2, ax2 = plt.subplots(figsize=(5,3))
ax2.bar([d1, d2], [ltA, ltB], color=["blue","orange"])
ax2.set_ylabel("Lap Time (s)")
ax2.grid(axis="y")

st.pyplot(fig2)
