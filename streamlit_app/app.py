import streamlit as st

st.set_page_config(
    page_title="FSAE Telemetry Dashboard",
    layout="wide"
)

st.title("🏎️ FSAE Telemetry System")

st.write("""
Welcome to the **Future Systems FSAE Telemetry Dashboard**.

Use the pages on the left:
- **📡 Realtime Telemetry** – live data streamed from the simulator  
- (Later) Track Map  
- (Later) Replay Tool  
""")
