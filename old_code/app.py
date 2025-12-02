import streamlit as st
import json
import time
import pandas as pd

st.set_page_config(
    page_title="FSAE Telemetry Dashboard",
    layout="wide"
)

st.title("🏎️ FSAE Realtime Telemetry Dashboard")

# Live updating
placeholder = st.empty()

while True:
    with open("data/realtime.json", "r") as f:
        data = json.load(f)

    with placeholder.container():
        col1, col2, col3 = st.columns(3)

        col1.metric("Coolant Temp (°C)", data["coolant_temp"])
        col2.metric("Wheel Speed (km/h)", data["wheel_speed"])
        col3.metric("Brake Pressure (bar)", data["brake_pressure"])

        st.line_chart(pd.DataFrame({
            "coolant_temp": [data["coolant_temp"]],
            "wheel_speed": [data["wheel_speed"]],
            "brake_pressure": [data["brake_pressure"]]
        }))

    time.sleep(0.15)
