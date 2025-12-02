import streamlit as st
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 FSAE Telemetry — Data Visualization (Stage 1)")

# -----------------------------------
# 1. Load session files
# -----------------------------------
LOG_DIR = os.path.join("data", "logs")

if not os.path.exists(LOG_DIR):
    st.error("❌ Logs folder not found. Make sure /data/logs exists.")
    st.stop()

files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

if not files:
    st.warning("⚠️ No logs found yet. Run the simulator first.")
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
# 3. Flatten telemetry into DataFrame
# -----------------------------------
flattened = []
t0 = raw[0]["timestamp"]

for row in raw:
    sensors = row["sensors"]
    imu = sensors["imu"]

    flattened.append({
        "timestamp": row["timestamp"],
        "time": row["timestamp"] - t0,

        # GPS
        "gps_x": row["gps"]["x"],
        "gps_y": row["gps"]["y"],
        "lap": row["lap"],

        # TRUE vehicle physics
        "true_speed": row["true"]["speed_kmh"],
        "true_coolant_temp": row["true"]["coolant_temp"],
        "true_brake_cmd": row["true"]["brake_cmd"],
        "true_throttle": row["true"]["throttle"],
        "true_yaw": row["true"]["yaw_deg"],

        # SENSOR values
        "wheel_speed": sensors["wheel_speed"],
        "brake_pressure": sensors["brake_pressure"],
        "coolant_temp": sensors["coolant_temp"],

        "imu_ax": imu["ax"] if imu else None,
        "imu_ay": imu["ay"] if imu else None,
        "imu_yaw": imu["yaw"] if imu else None,
    })

df = pd.DataFrame(flattened)

# -----------------------------------
# 4. Data Preview
# -----------------------------------
st.subheader("📄 Data Preview")
st.dataframe(df.head(), use_container_width=True)

# -----------------------------------
# 5. Summary Statistics
# -----------------------------------
st.subheader("📈 Summary Statistics")

col1, col2, col3 = st.columns(3)
col1.metric("Max Coolant Temp (°C)", f"{df['coolant_temp'].max():.2f}")
col2.metric("Max Speed (km/h)", f"{df['true_speed'].max():.2f}")
col3.metric("Max Brake Pressure", f"{df['brake_pressure'].max():.2f}")

# -----------------------------------
# 6. Matplotlib Charts
# -----------------------------------
st.markdown("---")
st.subheader("🌡️ Coolant Temperature (Sensor)")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["time"], df["coolant_temp"], color="red")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Coolant Temp (°C)")
ax.grid(True)
st.pyplot(fig)

# TRUE coolant temp
st.subheader("🌡️ Coolant Temperature (True Physics Value)")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["time"], df["true_coolant_temp"], color="darkred")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Coolant Temp (°C)")
ax.grid(True)
st.pyplot(fig)

# -----------------------------------
st.markdown("---")
st.subheader("🏎️ Speed Over Time")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["time"], df["wheel_speed"], label="Wheel Speed (sensor)", color="blue")
ax.plot(df["time"], df["true_speed"], label="True Speed (km/h)", color="cyan")
ax.legend()
ax.set_xlabel("Time (s)")
ax.set_ylabel("Speed (km/h)")
ax.grid(True)
st.pyplot(fig)

# -----------------------------------
st.markdown("---")
st.subheader("🛑 Brake Pressure")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["time"], df["brake_pressure"], color="green")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Brake Pressure (bar)")
ax.grid(True)
st.pyplot(fig)

# -----------------------------------
st.markdown("---")
st.subheader("📟 IMU Values (ax, ay, yaw)")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df["time"], df["imu_ax"], label="ax", color="purple")
ax.plot(df["time"], df["imu_ay"], label="ay", color="orange")
ax.plot(df["time"], df["imu_yaw"], label="yaw", color="black")
ax.set_xlabel("Time (s)")
ax.set_ylabel("IMU Values")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# -----------------------------------
# 7. GPS Track Map
# -----------------------------------
st.markdown("---")
st.subheader("🗺️ GPS Track Visualization")

fig, ax = plt.subplots(figsize=(5, 5))
ax.plot(df["gps_x"], df["gps_y"], color="black", linewidth=1)
ax.scatter(df["gps_x"].iloc[0], df["gps_y"].iloc[0], color="green", label="Start")
ax.scatter(df["gps_x"].iloc[-1], df["gps_y"].iloc[-1], color="red", label="End")
ax.set_aspect("equal")
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.grid(True)
ax.legend()
st.pyplot(fig)

# -----------------------------------
# 8. Correlation Heatmap
# -----------------------------------
st.markdown("---")
st.subheader("🔗 Telemetry Correlation")

corr_cols = [
    "true_speed",
    "coolant_temp",
    "brake_pressure",
    "imu_ax",
    "imu_ay",
    "imu_yaw",
]

corr = df[corr_cols].corr()

fig, ax = plt.subplots(figsize=(6, 5))
cax = ax.matshow(corr, cmap="coolwarm")
fig.colorbar(cax)

ax.set_xticks(range(len(corr.columns)))
ax.set_yticks(range(len(corr.columns)))
ax.set_xticklabels(corr.columns, rotation=45, ha="left")
ax.set_yticklabels(corr.columns)

# annotate
for (i, j), val in np.ndenumerate(corr.values):
    ax.text(j, i, f"{val:.2f}", va="center", ha="center", color="black")

st.pyplot(fig)
