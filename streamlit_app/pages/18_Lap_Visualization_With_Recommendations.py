import streamlit as st
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Lap Visualization + Recommendation Analysis")

LOG_DIR = os.path.join("data", "logs")

# ------------------------------------------------------
# Load sessions
# ------------------------------------------------------
if not os.path.exists(LOG_DIR):
    st.error("❌ Logs folder not found.")
    st.stop()

files = [f for f in os.listdir(LOG_DIR) if f.startswith("session_") and f.endswith(".json")]

if not files:
    st.warning("⚠ No session logs found.")
    st.stop()

selected_file = st.selectbox("Select a session:", files)
session_path = os.path.join(LOG_DIR, selected_file)

# Matching recommendation file
recommendation_file = selected_file.replace("session_", "recommendations_")
recommendation_path = os.path.join(LOG_DIR, recommendation_file)

# ------------------------------------------------------
# Load session JSON
# ------------------------------------------------------
try:
    with open(session_path, "r") as f:
        raw = json.load(f)
except Exception as e:
    st.error(f"Failed to read log file: {e}")
    st.stop()

if len(raw) == 0:
    st.warning("Empty log.")
    st.stop()

# ------------------------------------------------------
# Flatten telemetry rows
# ------------------------------------------------------
flattened = []
t0 = raw[0]["timestamp"]

for row in raw:
    sensors = row["sensors"]
    imu = sensors.get("imu")

    flattened.append({
        "timestamp": row["timestamp"],
        "time": row["timestamp"] - t0,
        "lap": row.get("lap"),
        "track_index": row.get("track_index"),

        "gps_x": row["gps"]["x"],
        "gps_y": row["gps"]["y"],

        "true_speed": row["true"]["speed_kmh"],
        "true_coolant": row["true"]["coolant_temp"],
        "true_brake_cmd": row["true"]["brake_cmd"],
        "true_throttle": row["true"]["throttle"],
        "true_yaw": row["true"]["yaw_deg"],

        "wheel_speed": sensors["wheel_speed"],
        "brake_pressure": sensors["brake_pressure"],
        "coolant_temp": sensors["coolant_temp"],

        "imu_yaw": imu.get("yaw") if imu else None,
    })

df = pd.DataFrame(flattened)

# ------------------------------------------------------
# Load recommendations (if available)
# ------------------------------------------------------
if os.path.exists(recommendation_path):
    with open(recommendation_path, "r") as f:
        rec_raw = json.load(f)
    rec_df = pd.DataFrame(rec_raw)
else:
    rec_df = None

# ------------------------------------------------------
# Compute lap progress
# ------------------------------------------------------
max_index = df["track_index"].max()
df["lap_progress"] = df["track_index"] / max_index

st.subheader("📄 Telemetry Data Preview")
st.dataframe(df.head(), use_container_width=True)

if rec_df is not None:
    st.subheader("🧠 Recommendation Log Preview")
    st.dataframe(rec_df.head(), use_container_width=True)
else:
    st.info("No recommendation log available for this session.")

# ------------------------------------------------------
# Lap-based visualization
# ------------------------------------------------------
laps = sorted(df["lap"].unique())
selected_lap = st.selectbox("Select lap:", laps)

lap_df = df[df["lap"] == selected_lap]

if rec_df is not None:
    lap_rec = rec_df[rec_df["lap"] == selected_lap]
else:
    lap_rec = pd.DataFrame()

# ------------------------------------------------------
# Timeline visualizations
# ------------------------------------------------------
st.markdown("## 📉 Lap Telemetry with Recommendation Markers")

fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)

# -------- Speed --------
axes[0].plot(lap_df["lap_progress"], lap_df["true_speed"], label="Speed")
axes[0].set_ylabel("Speed (km/h)")
axes[0].grid(True)

# Add recommendation markers
for _, r in lap_rec.iterrows():
    x = r["track_index"] / max_index
    axes[0].axvline(x, color="red", linestyle="--", alpha=0.6)

# -------- Throttle --------
axes[1].plot(lap_df["lap_progress"], lap_df["true_throttle"], color="orange")
axes[1].set_ylabel("Throttle")
axes[1].grid(True)

for _, r in lap_rec.iterrows():
    x = r["track_index"] / max_index
    axes[1].axvline(x, color="red", linestyle="--", alpha=0.6)

# -------- Brake --------
axes[2].plot(lap_df["lap_progress"], lap_df["brake_pressure"], color="green")
axes[2].set_ylabel("Brake")
axes[2].grid(True)

for _, r in lap_rec.iterrows():
    x = r["track_index"] / max_index
    axes[2].axvline(x, color="red", linestyle="--", alpha=0.6)

# -------- Yaw --------
axes[3].plot(lap_df["lap_progress"], lap_df["imu_yaw"], color="black")
axes[3].set_ylabel("Yaw (deg)")
axes[3].set_xlabel("Lap Progress (0–1)")
axes[3].grid(True)

for _, r in lap_rec.iterrows():
    x = r["track_index"] / max_index
    axes[3].axvline(x, color="red", linestyle="--", alpha=0.6)

st.pyplot(fig)

# ------------------------------------------------------
# Track map with delta-speed color
# ------------------------------------------------------
if rec_df is not None:
    st.markdown("## 🗺️ Track Map — Delta Speed Heatmap")

    # compute delta speed per point
    heat = np.zeros(len(df))
    for _, r in rec_df.iterrows():
        idx = int(r["track_index"])
        if idx < len(heat):
            heat[idx] = r["delta_speed"]

    colors = plt.cm.coolwarm((heat - heat.min()) / (heat.max() - heat.min() + 1e-9))

    fig2, ax2 = plt.subplots(figsize=(6, 6))
    ax2.scatter(df["gps_x"], df["gps_y"], c=colors, s=12)
    ax2.set_title("Delta-Speed Heatmap")
    ax2.set_aspect("equal")
    ax2.grid(True)

    st.pyplot(fig2)

# ------------------------------------------------------
# Recommendation timeline
# ------------------------------------------------------
if rec_df is not None:
    st.markdown("## 🧠 Recommendation Timeline")

    for _, r in rec_df.iterrows():
        st.markdown(f"### ⏱ Time {r['time']:.2f}s — Segment {r['track_index']}")
        for m in r["messages"]:
            st.write(f"- {m}")
        st.markdown("---")
else:
    st.info("No recommendations recorded for this session.")
