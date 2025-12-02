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
# 2. Load & flatten JSON into dataframe
# -----------------------------------
file_path = os.path.join(LOG_DIR, selected_file)

try:
    with open(file_path, "r") as f:
        raw = json.load(f)
except Exception as e:
    st.error(f"Failed to read log file: {e}")
    st.stop()

# If log empty
if len(raw) == 0:
    st.warning("Selected log file is empty.")
    st.stop()

# Flatten nested IMU fields
flattened = []
for row in raw:
    flattened.append({
        "timestamp": row["timestamp"],
        "time": row["timestamp"] - raw[0]["timestamp"],
        "coolant_temp": row["coolant_temp"],
        "wheel_speed": row["wheel_speed"],
        "brake_pressure": row["brake_pressure"],
        "imu_ax": row["imu"]["ax"],
        "imu_ay": row["imu"]["ay"],
        "imu_yaw": row["imu"]["yaw"]
    })

df = pd.DataFrame(flattened)

# -----------------------------------
# 3. Data Preview
# -----------------------------------
st.subheader("📄 Raw Data Preview")
st.dataframe(df.head(), use_container_width=True)

# -----------------------------------
# 4. Summary Statistics
# -----------------------------------
st.subheader("📈 Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("Max Coolant Temp (°C)", f"{df['coolant_temp'].max():.2f}")
col2.metric("Max Wheel Speed (km/h)", f"{df['wheel_speed'].max():.2f}")
col3.metric("Max Brake Pressure (bar)", f"{df['brake_pressure'].max():.2f}")

# -----------------------------------
# 5. Matplotlib Charts
# -----------------------------------

# ----------- Coolant Temp Chart -----------
st.subheader("🌡️ Coolant Temperature Over Time")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["time"], df["coolant_temp"], color="red")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Coolant Temp (°C)")
ax.grid(True)
st.pyplot(fig)

# ----------- Wheel Speed Chart -----------
st.subheader("🏎️ Wheel Speed Over Time")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["time"], df["wheel_speed"], color="blue")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Wheel Speed (km/h)")
ax.grid(True)
st.pyplot(fig)

# ----------- Brake Pressure Chart -----------
st.subheader("🛑 Brake Pressure Over Time")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["time"], df["brake_pressure"], color="green")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Brake Pressure (bar)")
ax.grid(True)
st.pyplot(fig)

# ----------- IMU Chart -----------
st.subheader("📟 IMU Ax, Ay, Yaw Over Time")

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
# 6. Correlation Heatmap (Matplotlib)
# -----------------------------------
st.subheader("🔗 Telemetry Correlation Matrix")

corr = df[
    ["coolant_temp", "wheel_speed", "brake_pressure",
     "imu_ax", "imu_ay", "imu_yaw"]
].corr()

fig, ax = plt.subplots(figsize=(6, 5))
cax = ax.matshow(corr, cmap="coolwarm")
fig.colorbar(cax)

# show variable names on axes
ax.set_xticks(range(len(corr.columns)))
ax.set_yticks(range(len(corr.columns)))
ax.set_xticklabels(corr.columns, rotation=45, ha="left")
ax.set_yticklabels(corr.columns)

# annotate values
for (i, j), val in np.ndenumerate(corr.values):
    ax.text(j, i, f"{val:.2f}", va='center', ha='center', color="black")

st.pyplot(fig)


# import streamlit as st
# import os
# import json
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go

# st.set_page_config(layout="wide")
# st.title("📊 FSAE Telemetry — Data Visualization")

# # -----------------------------------
# # 1. Load session files
# # -----------------------------------
# LOG_DIR = os.path.join("data", "logs")

# if not os.path.exists(LOG_DIR):
#     st.error("❌ Logs folder not found. Make sure /data/logs exists.")
#     st.stop()

# files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

# if not files:
#     st.warning("⚠️ No logs found yet. Run the simulator first.")
#     st.stop()

# selected_file = st.selectbox("Select a session:", files)

# # -----------------------------------
# # 2. Load & flatten JSON into dataframe
# # -----------------------------------
# file_path = os.path.join(LOG_DIR, selected_file)

# try:
#     with open(file_path, "r") as f:
#         raw = json.load(f)
# except Exception as e:
#     st.error(f"Failed to read log file: {e}")
#     st.stop()

# # If log is empty
# if len(raw) == 0:
#     st.warning("Selected log file is empty.")
#     st.stop()

# # Flatten rows
# flattened = []
# for row in raw:
#     flattened.append({
#         "timestamp": row["timestamp"],
#         "time": row["timestamp"] - raw[0]["timestamp"],  # normalize starting at 0
#         "coolant_temp": row["coolant_temp"],
#         "wheel_speed": row["wheel_speed"],
#         "brake_pressure": row["brake_pressure"],
#         "imu_ax": row["imu"]["ax"],
#         "imu_ay": row["imu"]["ay"],
#         "imu_yaw": row["imu"]["yaw"]
#     })

# df = pd.DataFrame(flattened)

# # -----------------------------------
# # 3. Data preview
# # -----------------------------------
# st.subheader("📄 Raw Data Preview")
# st.dataframe(df.head(), use_container_width=True)

# # -----------------------------------
# # 4. Summary statistics
# # -----------------------------------
# st.subheader("📈 Summary Statistics")

# c1, c2, c3 = st.columns(3)
# c1.metric("Max Coolant Temp (°C)", f"{df['coolant_temp'].max():.2f}")
# c2.metric("Max Wheel Speed (km/h)", f"{df['wheel_speed'].max():.2f}")
# c3.metric("Max Brake Pressure (bar)", f"{df['brake_pressure'].max():.2f}")

# # -----------------------------------
# # 5. Charts
# # -----------------------------------
# st.subheader("📉 Time-Series Visualization")

# # ------- Coolant Temperature -------
# fig1 = px.line(
#     df,
#     x="time",
#     y="coolant_temp",
#     title="Coolant Temperature Over Time",
#     labels={"time": "Time (s)", "coolant_temp": "Coolant Temp (°C)"}
# )
# st.plotly_chart(fig1, use_container_width=True)

# # ------- Wheel Speed -------
# fig2 = px.line(
#     df,
#     x="time",
#     y="wheel_speed",
#     title="Wheel Speed Over Time",
#     labels={"time": "Time (s)", "wheel_speed": "Wheel Speed (km/h)"}
# )
# st.plotly_chart(fig2, use_container_width=True)

# # ------- Brake Pressure -------
# fig3 = px.line(
#     df,
#     x="time",
#     y="brake_pressure",
#     title="Brake Pressure Over Time",
#     labels={"time": "Time (s)", "brake_pressure": "Brake Pressure (bar)"}
# )
# st.plotly_chart(fig3, use_container_width=True)

# # ------- IMU -------
# st.subheader("📟 IMU (Acceleration + Yaw)")

# fig4 = go.Figure()
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ax"], mode="lines", name="ax"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ay"], mode="lines", name="ay"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_yaw"], mode="lines", name="yaw"))
# fig4.update_layout(
#     title="IMU Data Over Time",
#     xaxis_title="Time (s)",
#     yaxis_title="Value",
#     height=350
# )
# st.plotly_chart(fig4, use_container_width=True)

# # -----------------------------------
# # 6. Correlation Heatmap
# # -----------------------------------
# st.subheader("🔗 Telemetry Variable Correlations")

# corr_df = df[
#     ["coolant_temp", "wheel_speed", "brake_pressure", "imu_ax", "imu_ay", "imu_yaw"]
# ].corr()

# fig_corr = px.imshow(
#     corr_df,
#     text_auto=True,
#     title="Correlation Heatmap",
#     color_continuous_scale="RdBu"
# )
# st.plotly_chart(fig_corr, use_container_width=True)


# import streamlit as st
# import os
# import json
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go

# # ------------------------------------------------------------
# # Page Setup
# # ------------------------------------------------------------
# st.set_page_config(layout="wide")
# st.title("📊 FSAE Telemetry — Data Visualization")

# # ------------------------------------------------------------
# # Correct log folder path
# # ------------------------------------------------------------
# LOG_DIR = os.path.join("data", "logs")

# files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

# if not files:
#     st.error("No log files found in ../data/logs")
#     st.stop()

# selected_file = st.selectbox("Select a session file:", files)

# # ------------------------------------------------------------
# # Load JSON log
# # ------------------------------------------------------------
# with open(os.path.join(LOG_DIR, selected_file), "r") as f:
#     raw = json.load(f)

# # ------------------------------------------------------------
# # Flatten JSON → DataFrame
# # ------------------------------------------------------------
# df = pd.DataFrame([
#     {
#         "timestamp": row["timestamp"],
#         "coolant_temp": row["coolant_temp"],
#         "wheel_speed": row["wheel_speed"],
#         "brake_pressure": row["brake_pressure"],
#         "imu_ax": row["imu"]["ax"],
#         "imu_ay": row["imu"]["ay"],
#         "imu_yaw": row["imu"]["yaw"],
#     }
#     for row in raw
# ])

# # ------------------------------------------------------------
# # Force ALL telemetry columns to numeric
# # ------------------------------------------------------------
# numeric_cols = [
#     "timestamp", "coolant_temp", "wheel_speed", "brake_pressure",
#     "imu_ax", "imu_ay", "imu_yaw"
# ]

# for col in numeric_cols:
#     df[col] = pd.to_numeric(df[col], errors="coerce")

# # ------------------------------------------------------------
# # Create time axis (relative seconds)
# # ------------------------------------------------------------
# df["time"] = df["timestamp"] - df["timestamp"].iloc[0]
# df["time"] = df["time"].round(3)

# # ------------------------------------------------------------
# # Display preview
# # ------------------------------------------------------------
# st.subheader("📄 Raw Data Preview")
# st.dataframe(df.head())

# # ------------------------------------------------------------
# # Summary statistics
# # ------------------------------------------------------------
# st.subheader("📊 Session Summary Statistics")

# col1, col2, col3 = st.columns(3)
# col1.metric("Max Coolant Temp (°C)", f"{df['coolant_temp'].max():.2f}")
# col2.metric("Max Wheel Speed (km/h)", f"{df['wheel_speed'].max():.2f}")
# col3.metric("Max Brake Pressure (bar)", f"{df['brake_pressure'].max():.2f}")

# # ------------------------------------------------------------
# # Time-Series Charts — MANUAL AXIS FIX (important)
# # ------------------------------------------------------------
# st.subheader("📈 Time-Series Charts")

# # Coolant Temperature
# fig1 = px.line(df, x="time", y="coolant_temp", title="Coolant Temperature Over Time")
# fig1.update_yaxes(range=[
#     df["coolant_temp"].min() - 5,
#     df["coolant_temp"].max() + 5
# ])
# st.plotly_chart(fig1, use_container_width=True)

# # Wheel Speed
# fig2 = px.line(df, x="time", y="wheel_speed", title="Wheel Speed Over Time")
# fig2.update_yaxes(range=[
#     df["wheel_speed"].min() - 5,
#     df["wheel_speed"].max() + 5
# ])
# st.plotly_chart(fig2, use_container_width=True)

# # Brake Pressure
# fig3 = px.line(df, x="time", y="brake_pressure", title="Brake Pressure Over Time")
# fig3.update_yaxes(range=[
#     df["brake_pressure"].min() - 5,
#     df["brake_pressure"].max() + 5
# ])
# st.plotly_chart(fig3, use_container_width=True)

# # ------------------------------------------------------------
# # IMU Visualization (ax, ay, yaw)
# # ------------------------------------------------------------
# st.subheader("📟 IMU — Accelerations & Yaw")

# fig4 = go.Figure()
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ax"], mode="lines", name="ax"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ay"], mode="lines", name="ay"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_yaw"], mode="lines", name="yaw"))

# fig4.update_layout(title="IMU Signals Over Time")

# # IMU axis auto-range
# fig4.update_yaxes(range=[
#     min(df["imu_ax"].min(), df["imu_ay"].min(), df["imu_yaw"].min()) - 1,
#     max(df["imu_ax"].max(), df["imu_ay"].max(), df["imu_yaw"].max()) + 1
# ])

# st.plotly_chart(fig4, use_container_width=True)

# # ------------------------------------------------------------
# # Correlation Matrix
# # ------------------------------------------------------------
# st.subheader("🔗 Correlation Matrix")

# corr = df[["coolant_temp", "wheel_speed", "brake_pressure",
#            "imu_ax", "imu_ay", "imu_yaw"]].corr()

# fig5 = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
#                  title="Correlation Between Telemetry Channels")
# st.plotly_chart(fig5, use_container_width=True)


# import streamlit as st
# import os
# import json
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go

# st.set_page_config(layout="wide")
# st.title("📊 FSAE Telemetry — Data Visualization (with Debugging)")

# # correct path
# LOG_DIR = os.path.join("data", "logs")

# files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

# if not files:
#     st.error("No logs found in ../data/logs")
#     st.stop()

# selected_file = st.selectbox("Select a session file:", files)

# # load JSON
# with open(os.path.join(LOG_DIR, selected_file), "r") as f:
#     raw = json.load(f)

# # flatten json
# df = pd.DataFrame([
#     {
#         "timestamp": row["timestamp"],
#         "coolant_temp": row["coolant_temp"],
#         "wheel_speed": row["wheel_speed"],
#         "brake_pressure": row["brake_pressure"],
#         "imu_ax": row["imu"]["ax"],
#         "imu_ay": row["imu"]["ay"],
#         "imu_yaw": row["imu"]["yaw"],
#     }
#     for row in raw
# ])

# # ---------------------------------------------------------
# # DEBUG SECTION: SHOW RAW VALUES AND TYPES
# # ---------------------------------------------------------
# st.subheader("🛠 Debug: Raw Input Before Conversion")
# st.write(df.head())

# st.subheader("🛠 Debug: dtypes BEFORE conversion")
# st.write(df.dtypes)

# # ---------------------------------------------------------
# # FORCE numeric conversion
# # ---------------------------------------------------------

# numeric_cols = [
#     "timestamp",
#     "coolant_temp",
#     "wheel_speed",
#     "brake_pressure",
#     "imu_ax",
#     "imu_ay",
#     "imu_yaw",
# ]

# # convert each column individually
# for col in numeric_cols:
#     df[col] = pd.to_numeric(df[col], errors="coerce")

# st.subheader("🛠 Debug: dtypes AFTER conversion")
# st.write(df.dtypes)

# # ---------------------------------------------------------
# # Debug: check for NaN values
# # ---------------------------------------------------------
# st.subheader("🛠 Debug: NaN count per column")
# st.write(df.isna().sum())

# # if time column would fail, catch it
# if df["timestamp"].isna().all():
#     st.error("❌ ERROR: All timestamps are NaN — graphs won't work.")
#     st.stop()

# # create time axis
# df["time"] = df["timestamp"] - df["timestamp"].iloc[0]

# st.subheader("🛠 Debug: First 10 rows AFTER conversion")
# st.write(df.head(10))

# st.subheader("🛠 Debug: Min/Max Values")
# stats = {
#     col: {"min": df[col].min(), "max": df[col].max()}
#     for col in numeric_cols + ["time"]
# }
# st.write(stats)

# # ---------------------------------------------------------
# # If we detect broken values, stop before graphing
# # ---------------------------------------------------------
# if df["coolant_temp"].max() < 1:
#     st.error("❌ Coolant values are too small (all near zero). Conversion failed.")
#     st.stop()

# if df["wheel_speed"].max() < 1:
#     st.error("❌ Wheel speed values are too small. Conversion failed.")
#     st.stop()

# # ---------------------------------------------------------
# # FROM THIS POINT: plotting is safe
# # ---------------------------------------------------------
# st.subheader("📈 Time-Series Charts")

# fig1 = px.line(df, x="time", y="coolant_temp", title="Coolant Temperature")
# st.plotly_chart(fig1, use_container_width=True)

# fig2 = px.line(df, x="time", y="wheel_speed", title="Wheel Speed")
# st.plotly_chart(fig2, use_container_width=True)

# fig3 = px.line(df, x="time", y="brake_pressure", title="Brake Pressure")
# st.plotly_chart(fig3, use_container_width=True)

# st.subheader("📟 IMU — Accelerations & Yaw")
# fig4 = go.Figure()
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ax"], mode="lines", name="ax"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ay"], mode="lines", name="ay"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_yaw"], mode="lines", name="yaw"))
# st.plotly_chart(fig4, use_container_width=True)

# # correlation
# st.subheader("🔗 Correlation Matrix")
# corr = df[["coolant_temp","wheel_speed","brake_pressure","imu_ax","imu_ay","imu_yaw"]].corr()
# fig5 = px.imshow(corr, text_auto=True)
# st.plotly_chart(fig5, use_container_width=True)


# import streamlit as st
# import os
# import json
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go

# # -------------------------------
# # Page setup
# # -------------------------------
# st.set_page_config(layout="wide")
# st.title("📊 FSAE Telemetry — Data Visualization")

# # Correct path based on your folder structure
# LOG_DIR = os.path.join("data", "logs")

# # -------------------------------
# # Load available log files
# # -------------------------------
# files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

# if not files:
#     st.warning("⚠️ No logs found in /data/logs.\nRun the simulator to generate telemetry data.")
#     st.stop()

# selected_file = st.selectbox("Select a session file:", files)

# # -------------------------------
# # Load JSON data from selected file
# # -------------------------------
# with open(os.path.join(LOG_DIR, selected_file), "r") as f:
#     raw = json.load(f)

# # -------------------------------
# # Convert JSON list → pandas DataFrame
# # -------------------------------
# df = pd.DataFrame([
#     {
#         "timestamp": row["timestamp"],
#         "coolant_temp": row["coolant_temp"],
#         "wheel_speed": row["wheel_speed"],
#         "brake_pressure": row["brake_pressure"],
#         "imu_ax": row["imu"]["ax"],
#         "imu_ay": row["imu"]["ay"],
#         "imu_yaw": row["imu"]["yaw"],
#     }
#     for row in raw
# ])

# # -------------------------------
# # Convert ALL telemetry values to numeric
# # (This fixes empty charts)
# # -------------------------------
# numeric_cols = [
#     "timestamp",
#     "coolant_temp",
#     "wheel_speed",
#     "brake_pressure",
#     "imu_ax",
#     "imu_ay",
#     "imu_yaw",
# ]

# for col in numeric_cols:
#     df[col] = df[col].astype(str).str.replace(",", "")
#     df[col] = pd.to_numeric(df[col], errors="coerce")


# # -------------------------------
# # Create time axis (seconds since session start)
# # -------------------------------
# df["time"] = df["timestamp"] - df["timestamp"].iloc[0]

# # -------------------------------
# # Show preview of raw data
# # -------------------------------
# st.subheader("📄 Raw Data Preview")
# st.dataframe(df.head())

# # -------------------------------
# # Summary statistics cards
# # -------------------------------
# st.subheader("📊 Session Summary Statistics")

# col1, col2, col3 = st.columns(3)
# col1.metric("Max Coolant Temp (°C)", f"{df['coolant_temp'].max():.2f}")
# col2.metric("Max Wheel Speed (km/h)", f"{df['wheel_speed'].max():.2f}")
# col3.metric("Max Brake Pressure (bar)", f"{df['brake_pressure'].max():.2f}")

# # -------------------------------
# # Time-Series Charts (Plotly)
# # -------------------------------
# st.subheader("📈 Time-Series Charts")

# # Coolant Temperature Plot
# fig1 = px.line(
#     df, x="time", y="coolant_temp",
#     title="Coolant Temperature Over Time",
#     labels={"time": "Time (s)", "coolant_temp": "Coolant Temp (°C)"}
# )
# fig1.update_layout(height=300)
# st.plotly_chart(fig1, use_container_width=True)

# # Wheel Speed Plot
# fig2 = px.line(
#     df, x="time", y="wheel_speed",
#     title="Wheel Speed Over Time",
#     labels={"time": "Time (s)", "wheel_speed": "Wheel Speed (km/h)"}
# )
# fig2.update_layout(height=300)
# st.plotly_chart(fig2, use_container_width=True)

# # Brake Pressure Plot
# fig3 = px.line(
#     df, x="time", y="brake_pressure",
#     title="Brake Pressure Over Time",
#     labels={"time": "Time (s)", "brake_pressure": "Brake Pressure (bar)"}
# )
# fig3.update_layout(height=300)
# st.plotly_chart(fig3, use_container_width=True)

# # -------------------------------
# # IMU visualization: ax, ay, yaw
# # -------------------------------
# st.subheader("📟 IMU — Accelerations & Yaw")

# fig4 = go.Figure()
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ax"], mode="lines", name="ax"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ay"], mode="lines", name="ay"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_yaw"], mode="lines", name="yaw"))

# fig4.update_layout(
#     title="IMU Accelerations and Yaw",
#     xaxis_title="Time (s)",
#     height=300
# )

# st.plotly_chart(fig4, use_container_width=True)

# # -------------------------------
# # Correlation Heatmap
# # -------------------------------
# st.subheader("🔗 Correlation Between Telemetry Variables")

# corr = df[
#     ["coolant_temp", "wheel_speed", "brake_pressure", "imu_ax", "imu_ay", "imu_yaw"]
# ].corr()

# fig5 = px.imshow(
#     corr,
#     text_auto=True,
#     title="Correlation Matrix",
#     color_continuous_scale="RdBu_r",
# )
# fig5.update_layout(height=500)
# st.plotly_chart(fig5, use_container_width=True)

# import streamlit as st
# import os
# import json
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go

# # -------------------------------
# # Page setup
# # -------------------------------
# st.set_page_config(layout="wide")
# st.title("📊 FSAE Telemetry — Data Visualization")

# # -------------------------------
# # Correct path to logs
# # (Streamlit runs inside streamlit_app/, so we go one directory up)
# # -------------------------------
# LOG_DIR = os.path.join("data", "logs")

# # -------------------------------
# # Load available log files
# # -------------------------------
# files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

# if not files:
#     st.warning("⚠️ No logs found in /data/logs.\nRun the simulator to generate telemetry data.")
#     st.stop()

# selected_file = st.selectbox("Select a session file:", files)

# # -------------------------------
# # Load JSON data
# # -------------------------------
# with open(os.path.join(LOG_DIR, selected_file), "r") as f:
#     raw = json.load(f)

# # -------------------------------
# # Convert JSON → DataFrame
# # -------------------------------
# df = pd.DataFrame([
#     {
#         "timestamp": row["timestamp"],
#         "coolant_temp": row["coolant_temp"],
#         "wheel_speed": row["wheel_speed"],
#         "brake_pressure": row["brake_pressure"],
#         "imu_ax": row["imu"]["ax"],
#         "imu_ay": row["imu"]["ay"],
#         "imu_yaw": row["imu"]["yaw"],
#     }
#     for row in raw
# ])

# # -------------------------------
# # FORCE ALL telemetry columns to numeric
# # (Critical fix for blank charts)
# # -------------------------------
# numeric_cols = [
#     "timestamp",
#     "coolant_temp",
#     "wheel_speed",
#     "brake_pressure",
#     "imu_ax",
#     "imu_ay",
#     "imu_yaw",
# ]

# for col in numeric_cols:
#     df[col] = pd.to_numeric(df[col], errors="coerce")

# # -------------------------------
# # Create time axis (seconds from start)
# # -------------------------------
# df["time"] = df["timestamp"] - df["timestamp"].iloc[0]
# df["time"] = df["time"].round(3)

# # -------------------------------
# # Debug (uncomment if needed)
# # st.write("Column Types:", df.dtypes)
# # st.write("Head:", df.head())
# # -------------------------------

# # -------------------------------
# # Data preview
# # -------------------------------
# st.subheader("📄 Raw Data Preview")
# st.dataframe(df.head())

# # -------------------------------
# # Statistics
# # -------------------------------
# st.subheader("📊 Session Summary Statistics")

# col1, col2, col3 = st.columns(3)
# col1.metric("Max Coolant Temp (°C)", f"{df['coolant_temp'].max():.2f}")
# col2.metric("Max Wheel Speed (km/h)", f"{df['wheel_speed'].max():.2f}")
# col3.metric("Max Brake Pressure (bar)", f"{df['brake_pressure'].max():.2f}")

# # -------------------------------
# # Time Series Charts
# # -------------------------------
# st.subheader("📈 Time-Series Charts")

# # Coolant Temperature Plot
# fig1 = px.line(
#     df, x="time", y="coolant_temp",
#     title="Coolant Temperature Over Time",
#     labels={"time": "Time (s)", "coolant_temp": "Coolant Temp (°C)"}
# )
# st.plotly_chart(fig1, use_container_width=True)

# # Wheel Speed Plot
# fig2 = px.line(
#     df, x="time", y="wheel_speed",
#     title="Wheel Speed Over Time",
#     labels={"time": "Time (s)", "wheel_speed": "Wheel Speed (km/h)"}
# )
# st.plotly_chart(fig2, use_container_width=True)

# # Brake Pressure Plot
# fig3 = px.line(
#     df, x="time", y="brake_pressure",
#     title="Brake Pressure Over Time",
#     labels={"time": "Time (s)", "brake_pressure": "Brake Pressure (bar)"}
# )
# st.plotly_chart(fig3, use_container_width=True)

# # -------------------------------
# # IMU Charts
# # -------------------------------
# st.subheader("📟 IMU — Accelerations & Yaw")

# fig4 = go.Figure()
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ax"], mode="lines", name="ax"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ay"], mode="lines", name="ay"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_yaw"], mode="lines", name="yaw"))

# fig4.update_layout(
#     title="IMU Accelerations and Yaw",
#     xaxis_title="Time (s)",
#     height=350
# )

# st.plotly_chart(fig4, use_container_width=True)

# # -------------------------------
# # Correlation Heatmap
# # -------------------------------
# st.subheader("🔗 Correlation Between Telemetry Variables")

# corr = df[
#     ["coolant_temp", "wheel_speed", "brake_pressure", "imu_ax", "imu_ay", "imu_yaw"]
# ].corr()

# fig5 = px.imshow(
#     corr,
#     text_auto=True,
#     title="Correlation Matrix",
#     color_continuous_scale="RdBu_r",
# )
# fig5.update_layout(height=500)

# st.plotly_chart(fig5, use_container_width=True)



# import streamlit as st
# import os
# import json
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go

# st.set_page_config(layout="wide")
# st.title("📊 FSAE Telemetry — Data Visualization")

# LOG_DIR = os.path.join("data", "logs")

# # Load available logs
# files = [f for f in os.listdir(LOG_DIR) if f.endswith(".json")]

# if not files:
#     st.warning("No logs found in /data/logs. Run simulator first.")
#     st.stop()

# selected_file = st.selectbox("Select a session file:", files)

# # Load JSON data
# with open(os.path.join(LOG_DIR, selected_file), "r") as f:
#     raw = json.load(f)

# # Flatten nested IMU into pandas DataFrame
# df = pd.DataFrame([
#     {
#         "timestamp": row["timestamp"],
#         "coolant_temp": row["coolant_temp"],
#         "wheel_speed": row["wheel_speed"],
#         "brake_pressure": row["brake_pressure"],
#         "imu_ax": row["imu"]["ax"],
#         "imu_ay": row["imu"]["ay"],
#         "imu_yaw": row["imu"]["yaw"],
#     }
#     for row in raw
# ])

# # Convert timestamp to human-readable
# df["timestamp"] = df["timestamp"].astype(float)
# df["time"] = df["timestamp"] - df["timestamp"].iloc[0]

# st.subheader("📄 Raw Data Preview")
# st.dataframe(df.head())

# # Compute stats
# st.subheader("📈 Session Summary Statistics")

# col1, col2, col3 = st.columns(3)
# col1.metric("Max Coolant Temp (°C)", round(df["coolant_temp"].max(), 2))
# col2.metric("Max Wheel Speed (km/h)", round(df["wheel_speed"].max(), 2))
# col3.metric("Max Brake Pressure (bar)", round(df["brake_pressure"].max(), 2))

# # ------------- LINE CHARTS -------------
# st.subheader("📉 Time-Series Charts")

# # Coolant
# fig1 = px.line(df, x="time", y="coolant_temp", title="Coolant Temperature Over Time")
# fig1.update_layout(height=300)
# st.plotly_chart(fig1, use_container_width=True)

# # Speed
# fig2 = px.line(df, x="time", y="wheel_speed", title="Wheel Speed Over Time")
# fig2.update_layout(height=300)
# st.plotly_chart(fig2, use_container_width=True)

# # Brake Pressure
# fig3 = px.line(df, x="time", y="brake_pressure", title="Brake Pressure Over Time")
# fig3.update_layout(height=300)
# st.plotly_chart(fig3, use_container_width=True)

# # IMU
# st.subheader("📟 IMU — Acceleration & Yaw")
# fig4 = go.Figure()
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ax"], mode="lines", name="ax"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_ay"], mode="lines", name="ay"))
# fig4.add_trace(go.Scatter(x=df["time"], y=df["imu_yaw"], mode="lines", name="yaw"))
# fig4.update_layout(title="IMU Accelerations + Yaw", height=300)
# st.plotly_chart(fig4, use_container_width=True)

# # Correlation Heatmap
# st.subheader("🔗 Correlation Between Telemetry Variables")

# corr = df[
#     ["coolant_temp", "wheel_speed", "brake_pressure", "imu_ax", "imu_ay", "imu_yaw"]
# ].corr()

# fig5 = px.imshow(corr, text_auto=True, title="Correlation Matrix")
# fig5.update_layout(height=500)
# st.plotly_chart(fig5, use_container_width=True)
