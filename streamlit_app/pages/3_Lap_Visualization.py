import streamlit as st
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 FSAE Telemetry — Data Visualization (Matplotlib)")

# -----------------------------------
# 1. Load session files
# -----------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOG_DIR = os.path.join(ROOT, "data", "logs")

if not os.path.exists(LOG_DIR):
    st.error("❌ Logs folder not found. Make sure /data/logs exists.")
    st.stop()

files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

if not files:
    st.warning("⚠️ No logs found yet. Run the simulator first.")
    st.stop()

selected_file = st.selectbox("Select a session:", files)

# -----------------------------------
# 2. Load & flatten JSON into dataframe
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

# Flatten nested IMU fields + new lap data if present
flattened = []
for row in raw:
    # Support both legacy Stage-0 logs and Stage-1 nested logs.
    sensors = row.get("sensors") or {}
    imu = sensors.get("imu")
    if imu is None:
        imu = row.get("imu") or {}

    timestamp = row.get("timestamp")
    t0 = raw[0].get("timestamp")
    rel_time = (timestamp - t0) if (timestamp is not None and t0 is not None) else None

    flattened.append(
        {
            "timestamp": timestamp,
            "time": rel_time,
            "coolant_temp": sensors.get("coolant_temp", row.get("coolant_temp")),
            "wheel_speed": sensors.get("wheel_speed", row.get("wheel_speed")),
            "brake_pressure": sensors.get("brake_pressure", row.get("brake_pressure")),
            "imu_ax": imu.get("ax") if isinstance(imu, dict) else None,
            "imu_ay": imu.get("ay") if isinstance(imu, dict) else None,
            "imu_yaw": imu.get("yaw") if isinstance(imu, dict) else None,
            "lap": row.get("lap"),
            "lap_progress": row.get("lap_progress"),
        }
    )

df = pd.DataFrame(flattened)

# -----------------------------------
# 3. Data Preview
# -----------------------------------
st.subheader("📄 Raw Data Preview")
st.dataframe(df.head(), use_container_width=True)

# -----------------------------------
# 7. Lap-Based Visualization
# -----------------------------------
st.subheader("🏁 Lap-Based Telemetry Visualization")

# Check if there is lap data
if df["lap"].notna().sum() > 0:

    laps = sorted(df["lap"].dropna().unique())

    col_lap1, col_lap2 = st.columns(2)
    selected_lap = col_lap1.selectbox("Select a lap to view:", laps)
    compare_laps = col_lap2.multiselect("Compare laps:", laps, default=[laps[0]])

    df_sel = df[df["lap"] == selected_lap]

    # -----------------------------------
    # 7A. Single Lap Overview
    # -----------------------------------
    st.markdown(f"### 📌 Lap {selected_lap} — Telemetry Overview")

    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)

    axes[0].plot(df_sel["lap_progress"], df_sel["wheel_speed"])
    axes[0].set_ylabel("Speed (km/h)")
    axes[0].grid(True)

    axes[1].plot(df_sel["lap_progress"], df_sel["coolant_temp"], color="red")
    axes[1].set_ylabel("Coolant (°C)")
    axes[1].grid(True)

    axes[2].plot(df_sel["lap_progress"], df_sel["brake_pressure"], color="green")
    axes[2].set_ylabel("Brake (bar)")
    axes[2].grid(True)

    axes[3].plot(df_sel["lap_progress"], df_sel["imu_yaw"], color="black")
    axes[3].set_ylabel("Yaw")
    axes[3].set_xlabel("Lap Progress (0–1)")
    axes[3].grid(True)

    st.pyplot(fig)

    # -----------------------------------
    # 7B. Lap Comparison Overlay
    # -----------------------------------
    st.markdown("### 🔍 Compare Multiple Laps (Overlay)")

    fig, ax = plt.subplots(figsize=(10, 4))

    for lap in compare_laps:
        d = df[df["lap"] == lap]
        ax.plot(d["lap_progress"], d["wheel_speed"], label=f"Lap {lap}")

    ax.set_ylabel("Speed (km/h)")
    ax.set_xlabel("Lap Progress (0–1)")
    ax.grid(True)
    ax.legend()

    st.pyplot(fig)

    # -----------------------------------
    # 7C. Small Multiples for All Laps
    # -----------------------------------
    st.markdown("### 📊 Lap-by-Lap — Wheel Speed Small Multiples")

    cols = st.columns(3)

    for idx, lap in enumerate(laps):
        d = df[df["lap"] == lap]

        fig, ax = plt.subplots(figsize=(3.5, 2))
        ax.plot(d["lap_progress"], d["wheel_speed"])
        ax.set_title(f"Lap {lap}")
        ax.set_ylim(0, df["wheel_speed"].max() + 10)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(True)

        cols[idx % 3].pyplot(fig)

else:
    st.info("This session does not contain lap data.")
