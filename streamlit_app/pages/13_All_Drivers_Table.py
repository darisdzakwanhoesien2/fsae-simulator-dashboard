import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st

from simulator.driver_aggregate import load_all_sessions, aggregate_driver_profile

LOG_DIR = os.path.join(ROOT, "data", "logs")

st.set_page_config(layout="wide")
st.title("📋 All Driver Performance Summary")

mapping = load_all_sessions(LOG_DIR)

if not mapping:
    st.warning("No sessions found. Run simulations first.")
    st.stop()

rows = []

for driver, sessions in mapping.items():
    prof = aggregate_driver_profile(sessions)

    rows.append({
        "Driver": driver,
        "Sessions": prof["sessions"],
        "Style": prof["style_label"],
        "Aggression": prof["avg_aggression"],
        "Smoothness": prof["avg_smoothness"],
        "Consistency": prof["avg_consistency"],
        "Cornering": prof["avg_cornering"],
        "Avg Lap Time (s)": prof["avg_lap_time"],
    })

df = pd.DataFrame(rows)

# Show interactive table
st.dataframe(df, use_container_width=True)

st.info("Tip: You can sort columns to find fastest, smoothest, or most aggressive drivers.")
