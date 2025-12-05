# streamlit_app/pages/1_Realtime_Telemetry.py

import sys, os, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import pandas as pd

DATA_DIR = os.path.join(ROOT, "data")
REALTIME_FILE = os.path.join(DATA_DIR, "realtime.json")

st.set_page_config(layout="wide")
st.title("📡 Realtime Telemetry Viewer")

st.markdown(
    "This page reads `data/realtime.json` written by the simulator "
    "and shows the latest packet plus a tiny rolling history."
)

# Rolling history in session state
if "rt_history" not in st.session_state:
    st.session_state["rt_history"] = []

placeholder_header = st.empty()
placeholder_metrics = st.empty()
placeholder_table = st.empty()

refresh_interval = st.slider("Refresh interval (seconds)", 0.1, 2.0, 0.3)

if st.button("Start live view"):
    # Simple live loop – this page will block until stopped,
    # which is okay for a dedicated realtime viewer tab.
    try:
        while True:
            if not os.path.exists(REALTIME_FILE):
                placeholder_header.error("❌ No realtime.json yet. Start simulator first.")
                time.sleep(refresh_interval)
                continue

            try:
                with open(REALTIME_FILE, "r") as f:
                    pkt = json.load(f)
            except Exception as e:
                placeholder_header.error(f"Failed to read realtime.json: {e}")
                time.sleep(refresh_interval)
                continue

            st.session_state["rt_history"].append(pkt)
            # limit history to last 200 samples
            st.session_state["rt_history"] = st.session_state["rt_history"][-200:]

            placeholder_header.markdown(
                f"### Latest packet — t = {pkt.get('t', 0):.2f}s, lap = {pkt.get('lap', 0)}"
            )

            col1, col2, col3 = placeholder_metrics.columns(3) if hasattr(placeholder_metrics, "columns") else st.columns(3)
            col1.metric("Speed (km/h)", f"{pkt['true']['speed_kmh']:.1f}")
            col2.metric("Coolant (°C)", f"{pkt['true']['coolant_temp']:.1f}")
            col3.metric("Brake Cmd", f"{pkt['true']['brake_cmd']:.2f}")

            # show last N as dataframe
            df = pd.json_normalize(st.session_state["rt_history"])
            placeholder_table.dataframe(df.tail(20), use_container_width=True)

            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        st.info("Live view stopped.")
