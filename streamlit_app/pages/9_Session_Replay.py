# import sys, os, time, json
# import streamlit as st
# import matplotlib.pyplot as plt
# import pandas as pd

# ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# sys.path.append(ROOT)

# from simulator.track_loader import load_track_csv

# st.set_page_config(layout="wide")
# st.title("🎥 Session Replay (Video-style)")

# # -------------------------------------------------------
# # Load sessions
# # -------------------------------------------------------
# LOG_DIR = os.path.join(ROOT, "data", "logs")
# sessions = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])

# if not sessions:
#     st.error("No session logs found.")
#     st.stop()

# session_file = st.selectbox("Choose recorded session", sessions)
# session_path = os.path.join(LOG_DIR, session_file)

# with open(session_path, "r") as f:
#     data = json.load(f)

# # Coordinates for all timestamps
# xs = [r["gps"]["x"] for r in data]
# ys = [r["gps"]["y"] for r in data]
# timestamps = [r["t"] for r in data]

# max_time = max(timestamps)

# # -------------------------------------------------------
# # UI Controls
# # -------------------------------------------------------
# st.subheader("Controls")

# col1, col2, col3 = st.columns([2,1,1])

# # Slider without key conflict
# t = col1.slider("Timeline", 0.0, max_time, 0.0, step=0.1)

# play = col2.button("▶ Play")
# pause = col3.button("⏸ Pause")

# if "is_playing" not in st.session_state:
#     st.session_state.is_playing = False

# if play:
#     st.session_state.is_playing = True
# if pause:
#     st.session_state.is_playing = False


# # -------------------------------------------------------
# # Matplotlib Placeholder (single instance)
# # -------------------------------------------------------
# frame_placeholder = st.empty()

# def draw_frame(t_value):
#     """Draws the track + car position at time t."""
#     # Find nearest frame
#     idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - t_value))

#     fig, ax = plt.subplots(figsize=(6,6))
#     ax.plot(xs, ys, "-", color="lightgray", linewidth=2)

#     # car position
#     ax.scatter(xs[idx], ys[idx], color="red", s=100, label="Car")

#     ax.set_aspect("equal")
#     ax.grid(True)
#     ax.legend()
#     ax.set_title(f"Time = {timestamps[idx]:.2f} s")

#     frame_placeholder.pyplot(fig)
#     plt.close(fig)

# # Initial drawing
# draw_frame(t)


# # -------------------------------------------------------
# # Animation Loop
# # -------------------------------------------------------
# if st.session_state.is_playing:
#     current_t = t
#     while current_t <= max_time and st.session_state.is_playing:
#         draw_frame(current_t)
#         current_t += 0.1      # playback speed
#         time.sleep(0.05)       # smoother animation

#         # Update UI slider live
#         col1.slider("Timeline", 0.0, max_time, current_t,
#                     step=0.1, key=f"slider_{current_t}")

#     st.session_state.is_playing = False

# import sys, os, time, json
# import streamlit as st
# import matplotlib.pyplot as plt

# ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# sys.path.append(ROOT)

# st.set_page_config(layout="wide")
# st.title("🎥 Session Replay (Video Player Style)")

# # -------------------------------------------------------
# # Load session
# # -------------------------------------------------------
# LOG_DIR = os.path.join(ROOT, "data", "logs")
# sessions = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])

# session_file = st.selectbox("Choose recorded session", sessions)
# session_path = os.path.join(LOG_DIR, session_file)

# with open(session_path, "r") as f:
#     data = json.load(f)

# xs = [r["gps"]["x"] for r in data]
# ys = [r["gps"]["y"] for r in data]
# timestamps = [r["t"] for r in data]
# max_time = max(timestamps)

# # Initialize play state
# if "is_playing" not in st.session_state:
#     st.session_state.is_playing = False

# if "current_t" not in st.session_state:
#     st.session_state.current_t = 0.0

# # -------------------------------------------------------
# # Controls
# # -------------------------------------------------------
# col1, col2, col3 = st.columns([2,1,1])

# # ONE slider ONLY
# new_t = col1.slider("Timeline", 0.0, max_time,
#                     st.session_state.current_t,
#                     step=0.1, key="timeline_slider")

# if new_t != st.session_state.current_t:
#     # User moved slider manually → pause animation
#     st.session_state.is_playing = False
#     st.session_state.current_t = new_t

# if col2.button("▶ Play"):
#     st.session_state.is_playing = True

# if col3.button("⏸ Pause"):
#     st.session_state.is_playing = False

# # -------------------------------------------------------
# # Drawing function
# # -------------------------------------------------------
# placeholder = st.empty()

# def draw_frame(t_value):
#     idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - t_value))

#     fig, ax = plt.subplots(figsize=(6,6))
#     ax.plot(xs, ys, "-", color="lightgray")
#     ax.scatter(xs[idx], ys[idx], color="red", s=100)

#     ax.set_title(f"t = {timestamps[idx]:.2f} s")
#     ax.set_aspect("equal")
#     ax.grid(True)

#     placeholder.pyplot(fig)
#     plt.close(fig)

# # Draw initial
# draw_frame(st.session_state.current_t)

# # -------------------------------------------------------
# # Animation Loop (NO new sliders created)
# # -------------------------------------------------------
# if st.session_state.is_playing:
#     while st.session_state.current_t < max_time and st.session_state.is_playing:

#         st.session_state.current_t += 0.1

#         # Update slider value *without creating new widget*
#         st.session_state["timeline_slider"] = st.session_state.current_t

#         draw_frame(st.session_state.current_t)

#         time.sleep(0.05)

#     st.session_state.is_playing = False

# import sys, os, time, json
# import streamlit as st
# import matplotlib.pyplot as plt

# ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# sys.path.append(ROOT)

# st.set_page_config(layout="wide")
# st.title("🎥 Session Replay (Video Playback)")

# # -------------------------------------------------------
# # Load session
# # -------------------------------------------------------
# LOG_DIR = os.path.join(ROOT, "data", "logs")
# sessions = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])

# session_file = st.selectbox("Choose recorded session", sessions)
# session_path = os.path.join(LOG_DIR, session_file)

# with open(session_path, "r") as f:
#     data = json.load(f)

# xs = [r["gps"]["x"] for r in data]
# ys = [r["gps"]["y"] for r in data]
# timestamps = [r["t"] for r in data]
# max_time = max(timestamps)

# # -------------------------------------------------------
# # Init Streamlit State
# # -------------------------------------------------------
# if "current_t" not in st.session_state:
#     st.session_state.current_t = 0.0

# if "is_playing" not in st.session_state:
#     st.session_state.is_playing = False


# # -------------------------------------------------------
# # Slider Callback
# # -------------------------------------------------------
# def slider_changed():
#     """User manually changed slider -> pause playback."""
#     st.session_state.is_playing = False
#     st.session_state.current_t = st.session_state.timeline_value


# # -------------------------------------------------------
# # Control Bar
# # -------------------------------------------------------
# col1, col2, col3 = st.columns([2, 1, 1])

# # ONE SLIDER — NOT UPDATED BY CODE
# st.slider(
#     "Timeline",
#     min_value=0.0,
#     max_value=max_time,
#     value=st.session_state.current_t,
#     step=0.1,
#     key="timeline_value",
#     on_change=slider_changed,
# )

# if col2.button("▶ Play"):
#     st.session_state.is_playing = True

# if col3.button("⏸ Pause"):
#     st.session_state.is_playing = False

# # -------------------------------------------------------
# # Drawing Function
# # -------------------------------------------------------
# placeholder = st.empty()

# def draw_frame(t_value):
#     idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - t_value))

#     fig, ax = plt.subplots(figsize=(6, 6))
#     ax.plot(xs, ys, "-", color="lightgray")
#     ax.scatter(xs[idx], ys[idx], color="red", s=100)

#     ax.set_title(f"t = {timestamps[idx]:.2f} s")
#     ax.set_aspect("equal")
#     ax.grid(True)

#     placeholder.pyplot(fig)
#     plt.close(fig)


# draw_frame(st.session_state.current_t)

# # -------------------------------------------------------
# # Playback Loop (Does NOT modify slider widget)
# # -------------------------------------------------------
# if st.session_state.is_playing:
#     while st.session_state.current_t < max_time and st.session_state.is_playing:

#         st.session_state.current_t += 0.1

#         # REDRAW
#         draw_frame(st.session_state.current_t)

#         # Stop if Streamlit reruns (button interaction)
#         time.sleep(0.05)
#         st.experimental_rerun()

import os
import sys
import json
import time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT)

import streamlit as st
import matplotlib.pyplot as plt
from simulator.track_loader import load_track_csv

# -------------------------------
# Streamlit Page Setup
# -------------------------------
st.set_page_config(layout="wide")
st.title("🎬 Session Replay Viewer")

LOG_DIR = os.path.join(ROOT, "data", "logs")
TRACK_DIR = os.path.join(ROOT, "data", "tracks")

# -------------------------------
# Load Log Files
# -------------------------------
files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])
if not files:
    st.error("❌ No session logs found.")
    st.stop()

file_name = st.selectbox("Select Session Log:", files)
file_path = os.path.join(LOG_DIR, file_name)

# -------------------------------
# Load Session JSON
# -------------------------------
try:
    with open(file_path, "r") as f:
        raw = json.load(f)
except:
    st.error("❌ Failed to load JSON.")
    st.stop()

cleaned = []
missing = 0

for r in raw:
    if "gps" in r and isinstance(r["gps"], dict) and "x" in r["gps"]:
        cleaned.append(r)
    else:
        missing += 1

if missing > 0:
    st.warning(f"⚠ Removed {missing} rows with missing GPS data.")

if len(cleaned) == 0:
    st.error("❌ Session has no valid GPS data.")
    st.stop()

data = cleaned

# -------------------------------
# Extract Replay Data
# -------------------------------
xs = np.array([r["gps"]["x"] for r in data])
ys = np.array([r["gps"]["y"] for r in data])
ts = np.array([r["t"] for r in data])
laps = np.array([r.get("lap", 0) for r in data])

min_t, max_t = ts.min(), ts.max()

# -------------------------------
# Choose Track (Optional)
# -------------------------------
tracks = sorted([f for f in os.listdir(TRACK_DIR) if f.endswith(".csv")])
track = None

if tracks:
    default_track = st.selectbox("Select Track (optional):", ["(none)"] + tracks)
    if default_track != "(none)":
        track_path = os.path.join(TRACK_DIR, default_track)
        track_pts = load_track_csv(track_path)
        track_x = [p[0] for p in track_pts]
        track_y = [p[1] for p in track_pts]
else:
    track_x, track_y = [], []

# -------------------------------
# Animation + Controls
# -------------------------------
colA, colB = st.columns([4, 1])

# Timeline slider
if "timeline_t" not in st.session_state:
    st.session_state.timeline_t = min_t

with colB:
    st.write("### Playback Controls")

    # play speed
    speed = st.slider("Speed", 0.1, 5.0, 1.0, 0.1)

    # play / pause buttons
    if st.button("▶ Play"):
        st.session_state.playing = True

    if st.button("⏸ Pause"):
        st.session_state.playing = False

    if st.button("⏹ Restart"):
        st.session_state.timeline_t = min_t
        st.session_state.playing = False

# timeline slider inside main area, unique key
with colA:
    t = st.slider(
        "Time",
        float(min_t),
        float(max_t),
        float(st.session_state.timeline_t),
        step=0.1,
        key="slider_timeline_main"
    )
    st.session_state.timeline_t = t


# -------------------------------
# Helper: Draw a Frame
# -------------------------------
def draw_frame(time_t):
    # interpolate position at time_t
    i = np.searchsorted(ts, time_t)

    if i <= 0:
        x, y = xs[0], ys[0]
    elif i >= len(ts):
        x, y = xs[-1], ys[-1]
    else:
        # linear interpolation
        t0, t1 = ts[i-1], ts[i]
        ratio = (time_t - t0) / (t1 - t0 + 1e-9)
        x = xs[i-1] + ratio * (xs[i] - xs[i-1])
        y = ys[i-1] + ratio * (ys[i] - ys[i-1])

    lap = int(laps[i if i < len(laps) else -1])

    fig, ax = plt.subplots(figsize=(8, 8))

    # Draw track
    if len(track_x) > 0:
        ax.plot(track_x, track_y, color="lightgray", linewidth=2)

    # Draw full driven line
    ax.plot(xs, ys, color="blue", alpha=0.3)

    # Draw car
    ax.scatter([x], [y], color="red", s=80, label=f"Car (Lap {lap})")

    ax.set_aspect("equal")
    ax.grid(True)
    ax.legend()
    ax.set_title(f"Time: {time_t:.2f}s")

    return fig


# -------------------------------
# Auto-play animation loop
# -------------------------------
placeholder = st.empty()

if st.session_state.get("playing", False):
    frame_dt = 0.1 * speed

    while st.session_state.playing:
        fig = draw_frame(st.session_state.timeline_t)
        placeholder.pyplot(fig)

        st.session_state.timeline_t += frame_dt

        if st.session_state.timeline_t >= max_t:
            st.session_state.timeline_t = max_t
            st.session_state.playing = False
            break

        time.sleep(0.03)

else:
    # static display when paused
    fig = draw_frame(st.session_state.timeline_t)
    placeholder.pyplot(fig)


# import sys, os, time, json
# import streamlit as st
# import matplotlib.pyplot as plt

# ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# sys.path.append(ROOT)

# st.set_page_config(layout="wide")
# st.title("🎥 Session Replay (Smooth Animation)")

# # -------------------------------------------------------
# # Load session
# # -------------------------------------------------------
# LOG_DIR = os.path.join(ROOT, "data", "logs")
# sessions = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json")])

# session_file = st.selectbox("Choose recorded session", sessions)
# session_path = os.path.join(LOG_DIR, session_file)

# with open(session_path, "r") as f:
#     data = json.load(f)

# xs = [r["gps"]["x"] for r in data]
# ys = [r["gps"]["y"] for r in data]
# timestamps = [r["t"] for r in data]
# max_time = max(timestamps)

# # -------------------------------------------------------
# # Init Streamlit State
# # -------------------------------------------------------
# if "current_t" not in st.session_state:
#     st.session_state.current_t = 0.0

# if "is_playing" not in st.session_state:
#     st.session_state.is_playing = False


# # -------------------------------------------------------
# # Slider callback
# # -------------------------------------------------------
# def slider_changed():
#     st.session_state.is_playing = False
#     st.session_state.current_t = st.session_state.timeline_value


# # -------------------------------------------------------
# # Controls
# # -------------------------------------------------------
# col1, col2, col3 = st.columns([3, 1, 1])

# col1.slider(
#     "Timeline",
#     min_value=0.0,
#     max_value=max_time,
#     value=st.session_state.current_t,
#     step=0.1,
#     key="timeline_value",
#     on_change=slider_changed,
# )

# if col2.button("▶ Play"):
#     st.session_state.is_playing = True

# if col3.button("⏸ Pause"):
#     st.session_state.is_playing = False


# # -------------------------------------------------------
# # Rendering
# # -------------------------------------------------------
# frame_zone = st.empty()   # Only this part updates!


# def draw_frame(t_value):
#     """Draw ONE frame at time t."""
#     idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - t_value))

#     fig, ax = plt.subplots(figsize=(6, 6))
#     ax.plot(xs, ys, "-", color="lightgray")
#     ax.scatter(xs[idx], ys[idx], color="red", s=100)
#     ax.set_title(f"t = {timestamps[idx]:.2f} s")
#     ax.set_aspect("equal")
#     ax.grid(True)

#     frame_zone.pyplot(fig)
#     plt.close(fig)


# # Initial frame draw
# draw_frame(st.session_state.current_t)

# # -------------------------------------------------------
# # Animation loop (NO rerun!)
# # -------------------------------------------------------
# if st.session_state.is_playing:
#     for _ in range(30000):  # safety cap
#         if not st.session_state.is_playing:
#             break

#         st.session_state.current_t += 0.1
#         if st.session_state.current_t > max_time:
#             st.session_state.current_t = max_time
#             st.session_state.is_playing = False
#             break

#         # draw only image part
#         draw_frame(st.session_state.current_t)

#         time.sleep(0.05)


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
