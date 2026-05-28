import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
from simulator.driver_aggregate import load_all_sessions, aggregate_driver_profile
import matplotlib.pyplot as plt
import numpy as np

LOG_DIR = os.path.join(ROOT, "data", "logs")

st.set_page_config(layout="wide")
st.title("🧑‍✈️ Driver Profile — Detailed View")

mapping = load_all_sessions(LOG_DIR)

if not mapping:
    st.error("No drivers found.")
    st.stop()

drivers = sorted(mapping.keys())
driver_id = st.selectbox("Select Driver:", drivers)

prof = aggregate_driver_profile(mapping[driver_id])

# Summary section
st.subheader(f"Driver: **{driver_id}**")
st.metric("Sessions", prof["sessions"])
st.metric("Dominant Style", prof["style_label"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Aggression", f"{prof['avg_aggression']:.2f}")
col2.metric("Smoothness", f"{prof['avg_smoothness']:.2f}")
col3.metric("Consistency", f"{prof['avg_consistency']:.2f}")
col4.metric("Cornering Skill", f"{prof['avg_cornering']:.2f}")

# Radar chart
labels = ["Agg.", "Smooth.", "Consist.", "Corner"]
values = [
    prof["avg_aggression"],
    prof["avg_smoothness"],
    prof["avg_consistency"],
    prof["avg_cornering"],
]

fig, ax = plt.subplots(figsize=(5,5))
ax.bar(labels, values)
ax.set_ylim(0, 1)
ax.set_title("Driver Style Profile")
ax.grid(True)
st.pyplot(fig)

if prof["avg_lap_time"]:
    st.metric("Average Lap Time", f"{prof['avg_lap_time']:.2f} sec")

st.markdown("---")
st.info("This driver profile combines all sessions for holistic performance evaluation.")
