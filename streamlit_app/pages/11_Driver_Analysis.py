# streamlit_app/pages/10_Driver_Analysis.py

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import json
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from simulator.driver_features import (
    load_session,
    compute_driver_metrics,
)

LOG_DIR = os.path.join(ROOT, "data", "logs")

st.set_page_config(layout="wide")
st.title("🧠 Driver Performance & Style Analysis (Part 1)")


# ----------------------------------------------------
# 1. Select Session
# ----------------------------------------------------
if not os.path.exists(LOG_DIR):
    st.error(f"Log directory not found: {LOG_DIR}")
    st.stop()

files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])

if not files:
    st.warning("No log files found in data/logs/. Run a simulation first.")
    st.stop()

selected_file = st.selectbox("Select a session log:", files)
session_path = os.path.join(LOG_DIR, selected_file)


# ----------------------------------------------------
# 2. Load Session & Compute Metrics
# ----------------------------------------------------
try:
    session = load_session(session_path)
except Exception as e:
    st.error(f"Failed to load session: {e}")
    st.stop()

if len(session) == 0:
    st.warning("Selected session is empty.")
    st.stop()

metrics = compute_driver_metrics(session)


# ----------------------------------------------------
# 3. Show Basic Info
# ----------------------------------------------------
st.subheader("📄 Session Info")
col_a, col_b = st.columns(2)
col_a.write(f"**File:** `{selected_file}`")
col_b.write(f"**Packets:** {len(session)}")

basic = metrics["basic"]
derived = metrics["derived"]
scores = metrics["scores"]
style_label = metrics["style_label"]

st.markdown("---")

# ----------------------------------------------------
# 4. Basic Telemetry Statistics
# ----------------------------------------------------
st.subheader("📊 Basic Telemetry Statistics")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Speed (km/h)**")
    st.write(basic["speed"])
with c2:
    st.markdown("**Throttle**")
    st.write(basic["throttle"])
with c3:
    st.markdown("**Brake Pressure (bar)**")
    st.write(basic["brake_pressure"])

c4, c5 = st.columns(2)
with c4:
    st.markdown("**Coolant Temperature (°C)**")
    st.write(basic["coolant"])
with c5:
    st.markdown("**Yaw (deg)**")
    st.write(basic["yaw"])

st.markdown(
    f"- **Laps detected (max lap index):** {basic['laps_completed']}\n"
    f"- **Corners detected:** {metrics['num_corners_detected']}"
)

st.markdown("---")

# ----------------------------------------------------
# 5. Derived Metrics
# ----------------------------------------------------
st.subheader("🧩 Derived Behaviour Metrics")

d1, d2, d3 = st.columns(3)
d1.metric("Throttle Spike Rate", f"{derived['throttle_spike_rate']:.3f}")
d2.metric("Brake Spike Rate", f"{derived['brake_spike_rate']:.3f}")
d3.metric("Steering Spike Rate", f"{derived['steering_spike_rate']:.3f}")

d4, d5, d6 = st.columns(3)
d4.metric("Corner Speed Mean", f"{derived['corner_speed_mean']:.1f} km/h")
d5.metric("Corner Stability", f"{derived['corner_stability']:.3f}")
d6.metric("Lap Time Mean", f"{derived['lap_time_mean']:.2f} s")

c7, c8 = st.columns(2)
c7.metric("Lap Time Std", f"{derived['lap_time_std']:.3f} s")
c8.write(" ")


st.markdown("---")

# ----------------------------------------------------
# 6. Style Scores & Classification
# ----------------------------------------------------
st.subheader("🎭 Driver Style Scores")

s1, s2, s3, s4 = st.columns(4)
s1.metric("Aggression", f"{scores['aggression']:.2f}")
s2.metric("Smoothness", f"{scores['smoothness']:.2f}")
s3.metric("Consistency", f"{scores['consistency']:.2f}")
s4.metric("Cornering Skill", f"{scores['cornering_skill']:.2f}")

st.markdown(f"### 🏷 Detected Style: **`{style_label}`**")

st.markdown("""
- **Aggression** ↑ → more throttle & brake spikes + higher avg speed  
- **Smoothness** ↑ → fewer steering spikes (if steering logged)  
- **Consistency** ↑ → more stable lap times  
- **Cornering Skill** ↑ → high corner speed + stable yaw in corners
""")

# ----------------------------------------------------
# 7. Radar / Bar Plot for Style Scores
# ----------------------------------------------------
st.subheader("📈 Style Profile Plot")

labels = ["Aggression", "Smoothness", "Consistency", "Cornering"]
values = [
    scores["aggression"],
    scores["smoothness"],
    scores["consistency"],
    scores["cornering_skill"],
]

fig, ax = plt.subplots(figsize=(5, 4))
ax.bar(labels, values)
ax.set_ylim(0, 1.05)
ax.set_ylabel("Score (0–1)")
ax.grid(axis="y", linestyle="--", alpha=0.3)
st.pyplot(fig)
