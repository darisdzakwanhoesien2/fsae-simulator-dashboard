import sys, os, time, json
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

from simulator.track_loader import load_track_csv

st.set_page_config(layout="wide")
st.title("🎥 Session Replay (Video-style)")

# -------------------------------------------------------
# Load sessions
# -------------------------------------------------------
LOG_DIR = os.path.join(ROOT, "data", "logs")
sessions = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])

if not sessions:
    st.error("No session logs found.")
    st.stop()

session_file = st.selectbox("Choose recorded session", sessions)
session_path = os.path.join(LOG_DIR, session_file)

with open(session_path, "r") as f:
    data = json.load(f)

# Coordinates for all timestamps
xs = [r["gps"]["x"] for r in data]
ys = [r["gps"]["y"] for r in data]
timestamps = [r["t"] for r in data]

max_time = max(timestamps)

# -------------------------------------------------------
# UI Controls
# -------------------------------------------------------
st.subheader("Controls")

col1, col2, col3 = st.columns([2,1,1])

# Slider without key conflict
t = col1.slider("Timeline", 0.0, max_time, 0.0, step=0.1)

play = col2.button("▶ Play")
pause = col3.button("⏸ Pause")

if "is_playing" not in st.session_state:
    st.session_state.is_playing = False

if play:
    st.session_state.is_playing = True
if pause:
    st.session_state.is_playing = False


# -------------------------------------------------------
# Matplotlib Placeholder (single instance)
# -------------------------------------------------------
frame_placeholder = st.empty()

def draw_frame(t_value):
    """Draws the track + car position at time t."""
    # Find nearest frame
    idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - t_value))

    fig, ax = plt.subplots(figsize=(6,6))
    ax.plot(xs, ys, "-", color="lightgray", linewidth=2)

    # car position
    ax.scatter(xs[idx], ys[idx], color="red", s=100, label="Car")

    ax.set_aspect("equal")
    ax.grid(True)
    ax.legend()
    ax.set_title(f"Time = {timestamps[idx]:.2f} s")

    frame_placeholder.pyplot(fig)
    plt.close(fig)

# Initial drawing
draw_frame(t)


# -------------------------------------------------------
# Animation Loop
# -------------------------------------------------------
if st.session_state.is_playing:
    current_t = t
    while current_t <= max_time and st.session_state.is_playing:
        draw_frame(current_t)
        current_t += 0.1      # playback speed
        time.sleep(0.05)       # smoother animation

        # Update UI slider live
        col1.slider("Timeline", 0.0, max_time, current_t,
                    step=0.1, key=f"slider_{current_t}")

    st.session_state.is_playing = False


# # streamlit_app/pages/9_Session_Replay.py

# import sys, os, json, time
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt

# import streamlit as st

# ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# sys.path.append(ROOT)

# LOG_DIR = os.path.join(ROOT, "data", "logs")

# st.set_page_config(layout="wide")
# st.title("🎞️ Session Replay — Time-Based Telemetry Visualization")

# # ---------------------------------------------------------
# # Load available sessions
# # ---------------------------------------------------------
# files = sorted([f for f in os.listdir(LOG_DIR) if f.startswith("race_session")])
# if not files:
#     st.warning("No race sessions found.")
#     st.stop()

# session_name = st.selectbox("Select session:", files)
# session_path = os.path.join(LOG_DIR, session_name)

# with open(session_path, "r") as f:
#     data = json.load(f)

# # Convert to DataFrame for convenience
# df = pd.DataFrame(data)

# # Extract useful arrays
# times = df["t"].values
# xs = [p["x"] for p in df["gps"]]
# ys = [p["y"] for p in df["gps"]]
# speed = df["true"].apply(lambda r: r["speed_kmh"]).values
# throttle = df["true"].apply(lambda r: r["throttle"]).values
# brake = df["true"].apply(lambda r: r["brake_cmd"]).values
# yaw = df["true"].apply(lambda r: r["yaw_deg"]).values

# max_time = float(times[-1])

# st.subheader("⏱️ Playback Controls")

# # Player controls
# col1, col2, col3 = st.columns([3, 1, 1])
# current_time = col1.slider("Time (s)", 0.0, max_time, 0.0, step=0.1)
# play_button = col2.button("▶ Play")
# stop_button = col3.button("⏹ Stop")

# if "replay_running" not in st.session_state:
#     st.session_state.replay_running = False

# # If stop is pressed
# if stop_button:
#     st.session_state.replay_running = False

# # When Play button clicked
# if play_button:
#     st.session_state.replay_running = True

# # Helper: find nearest frame based on current_time
# def get_frame_idx(t):
#     return int(np.argmin(np.abs(times - t)))

# # ---------------------------------------------------------
# # Live Plot Area
# # ---------------------------------------------------------
# plot_placeholder = st.empty()
# info_placeholder = st.empty()

# def draw_frame(idx):
#     fig, ax = plt.subplots(figsize=(6, 6))

#     # Draw entire driven path
#     # ax.plot(xs, ys, "-lightgray")
#     ax.plot(xs, ys, "-", color="lightgray")

#     # Car current position
#     ax.scatter(xs[idx], ys[idx], s=100, color="red")

#     ax.set_aspect("equal")
#     ax.grid(True)
#     ax.set_title(f"Car Position (t = {times[idx]:.2f}s)")
#     st.pyplot(fig)

#     # Telemetry info
#     info_placeholder.markdown(
#         f"""
#         ### 📡 Telemetry @ {times[idx]:.2f}s  
#         **Speed:** {speed[idx]:.2f} km/h  
#         **Throttle:** {throttle[idx]:.3f}  
#         **Brake:** {brake[idx]:.3f}  
#         **Yaw:** {yaw[idx]:.3f}°  
#         """
#     )

# # ---------------------------------------------------------
# # Manual Slider → Draw Frame
# # ---------------------------------------------------------
# idx = get_frame_idx(current_time)
# draw_frame(idx)

# # ---------------------------------------------------------
# # PLAYBACK LOOP
# # ---------------------------------------------------------
# if st.session_state.replay_running:
#     # Replay loop
#     for t in np.arange(current_time, max_time, 0.1):
#         if not st.session_state.replay_running:
#             break

#         idx = get_frame_idx(t)
#         draw_frame(idx)

#         # Update slider visually
#         col1.slider("Time (s)", 0.0, max_time, t, step=0.1, key="slider_key")

#         time.sleep(0.1)

#     st.session_state.replay_running = False
#     st.success("Replay finished!")
