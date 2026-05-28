import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import matplotlib.pyplot as plt

from simulator.driver_aggregate import (
    load_all_sessions,
    aggregate_driver_profile
)


LOG_DIR = os.path.join(ROOT, "data", "logs")

st.set_page_config(layout="wide")
st.title("🧑‍✈️ Driver Profiles — Aggregated Across Sessions")

mapping = load_all_sessions(LOG_DIR)

if not mapping:
    st.error("No sessions detected.")
    st.stop()

drivers = sorted(mapping.keys())
driver_id = st.selectbox("Select Driver:", drivers)

sessions = mapping[driver_id]
profile = aggregate_driver_profile(sessions)

st.subheader(f"Driver: **{driver_id}**")
st.write(f"Sessions: {profile['sessions']}")
st.write(f"Dominant Style: `{profile['style_label']}`")

# Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Avg Aggression", f"{profile['avg_aggression']:.2f}")
c2.metric("Avg Smoothness", f"{profile['avg_smoothness']:.2f}")
c3.metric("Avg Consistency", f"{profile['avg_consistency']:.2f}")
c4.metric("Avg Cornering", f"{profile['avg_cornering']:.2f}")

# Radar chart
labels = ["Aggression", "Smoothness", "Consistency", "Cornering"]
values = [
    profile["avg_aggression"],
    profile["avg_smoothness"],
    profile["avg_consistency"],
    profile["avg_cornering"],
]

fig, ax = plt.subplots(figsize=(5, 4))
ax.bar(labels, values)
ax.set_ylim(0, 1)
ax.set_ylabel("Score")
ax.grid(True)

st.pyplot(fig)
