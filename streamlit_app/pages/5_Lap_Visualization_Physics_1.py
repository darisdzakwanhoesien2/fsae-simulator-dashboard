import streamlit as st
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 FSAE Telemetry — Lap Visualization (Physics Stage 1)")

# -----------------------------------
# 1. Load session files
# -----------------------------------
LOG_DIR = os.path.join("data", "logs")

if not os.path.exists(LOG_DIR):
    st.error("❌ Logs folder not found. Ensure /data/logs exists.")
    st.stop()

files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

if not files:
    st.warning("⚠️ No logs found. Run the simulator first.")
    st.stop()

selected_file = st.selectbox("Select a session:", files)

# -----------------------------------
# 2. Load JSON
# -----------------------------------
file_path = os.path.join(LOG_DIR, selected_file)

try:
    with open(file_path, "r") as f:
        raw = json.load(f)
except Exception as e:
    st.error(f"Failed to read log file: {e}")
    st.stop()

if len(raw) == 0:
    st.warning("Selected log file is empty.")
    st.stop()

# -----------------------------------
# 3. Flatten rows safely
# -----------------------------------
flattened = []
t0 = raw[0]["timestamp"]

for row in raw:
    sensors = row["sensors"]
    imu = sensors.get("imu")  # <-- may be None

    flattened.append({
        # --- Time ---
        "timestamp": row["timestamp"],
        "time": row["timestamp"] - t0,

        # --- Lap fields ---
        "lap": row.get("lap"),
        "track_index": row.get("track_index"),

        # --- GPS ---
        "gps_x": row["gps"]["x"],
        "gps_y": row["gps"]["y"],

        # --- TRUE physics values ---
        "true_speed": row["true"]["speed_kmh"],
        "true_coolant": row["true"]["coolant_temp"],
        "true_brake_cmd": row["true"]["brake_cmd"],
        "true_throttle": row["true"]["throttle"],
        "true_yaw": row["true"]["yaw_deg"],

        # --- SENSOR values ---
        "wheel_speed": sensors["wheel_speed"],
        "brake_pressure": sensors["brake_pressure"],
        "coolant_temp": sensors["coolant_temp"],

        # --- IMU (safe fallback during dropout) ---
        "imu_ax": imu["ax"] if imu else None,
        "imu_ay": imu["ay"] if imu else None,
        "imu_yaw": imu["yaw"] if imu else None,
    })

df = pd.DataFrame(flattened)

# -----------------------------------
# 4. Compute lap progress (0–1)
# -----------------------------------
if "track_index" not in df.columns:
    st.error("❌ 'track_index' missing — check simulator output structure.")
    st.stop()

max_index = df["track_index"].max()
df["lap_progress"] = df["track_index"] / max_index

# -----------------------------------
# 5. Data Preview
# -----------------------------------
st.subheader("📄 Data Preview")
st.dataframe(df.head(), use_container_width=True)

# -----------------------------------
# 6. Lap-Based Visualization
# -----------------------------------
st.subheader("🏁 Lap-Based Telemetry Visualization")

laps = sorted(df["lap"].unique())

if len(laps) == 0:
    st.info("This session does not contain lap data.")
    st.stop()

# UI controls
col_lap1, col_lap2 = st.columns(2)
selected_lap = col_lap1.selectbox("Select lap:", laps)
compare_laps = col_lap2.multiselect("Compare laps:", laps, default=[laps[0]])

lap_df = df[df["lap"] == selected_lap]

# -----------------------------------
# 6A — Multi-Channel Lap Overview
# -----------------------------------
st.markdown(f"### 📌 Lap {selected_lap} — Multi-Channel Overview")

fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)

# Speed (true vs sensor)
axes[0].plot(lap_df["lap_progress"], lap_df["true_speed"], label="True Speed")
axes[0].plot(lap_df["lap_progress"], lap_df["wheel_speed"], label="Wheel Speed (sensor)", alpha=0.7)
axes[0].set_ylabel("Speed (km/h)")
axes[0].grid(True)
axes[0].legend()

# Coolant temperature
axes[1].plot(lap_df["lap_progress"], lap_df["coolant_temp"], color="red")
axes[1].set_ylabel("Coolant (°C)")
axes[1].grid(True)

# Brake pressure
axes[2].plot(lap_df["lap_progress"], lap_df["brake_pressure"], color="green")
axes[2].set_ylabel("Brake (bar)")
axes[2].grid(True)

# Yaw angle
axes[3].plot(lap_df["lap_progress"], lap_df["imu_yaw"], color="black")
axes[3].set_ylabel("Yaw (deg)")
axes[3].set_xlabel("Lap Progress (0–1)")
axes[3].grid(True)

st.pyplot(fig)

# -----------------------------------
# 6B — Multi-Lap Overlay (Speed)
# -----------------------------------
st.markdown("### 🔍 Multi-Lap Speed Overlay")

fig, ax = plt.subplots(figsize=(11, 4))
for lap in compare_laps:
    d = df[df["lap"] == lap]
    ax.plot(d["lap_progress"], d["true_speed"], label=f"Lap {lap}")

ax.set_ylabel("Speed (km/h)")
ax.set_xlabel("Lap Progress (0–1)")
ax.grid(True)
ax.legend()

st.pyplot(fig)

# -----------------------------------
# 6C — Small Multiples (Speed per Lap)
# -----------------------------------
st.markdown("### 📊 Speed Sparklines (Lap-by-Lap)")

cols = st.columns(3)

for i, lap in enumerate(laps):
    d = df[df["lap"] == lap]

    fig, ax = plt.subplots(figsize=(3.2, 1.8))
    ax.plot(d["lap_progress"], d["true_speed"], color="blue")
    ax.set_title(f"Lap {lap}")
    ax.set_ylim(0, df["true_speed"].max() + 10)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(True)

    cols[i % 3].pyplot(fig)

# -----------------------------------
# 6D — GPS Track by Lap
# -----------------------------------
st.markdown("### 🗺️ GPS Track Colored by Lap")

fig, ax = plt.subplots(figsize=(6, 6))

colors = plt.cm.tab10(np.linspace(0, 1, len(laps)))

for color, lap in zip(colors, laps):
    d = df[df["lap"] == lap]
    ax.plot(d["gps_x"], d["gps_y"], color=color, linewidth=1.5, label=f"Lap {lap}")

# Mark start and finish
ax.scatter(df["gps_x"].iloc[0], df["gps_y"].iloc[0], color="green", s=70, label="Start", zorder=5)
ax.scatter(df["gps_x"].iloc[-1], df["gps_y"].iloc[-1], color="red", s=70, label="End", zorder=5)

ax.set_aspect("equal")
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.grid(True)
ax.legend()

st.pyplot(fig)
