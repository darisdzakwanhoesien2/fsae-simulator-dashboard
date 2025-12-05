# -------------------------------------------------------------
# run_simulator_with_recommender.py  (FINAL VERSION)
# -------------------------------------------------------------

import sys, os, time, json, argparse, datetime
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

# Utils
from utils.json_writer import write_session_log, write_realtime_json
from utils.config_loader import load_yaml

# Driver + Recommender
from simulator.driver_profiles import simple_lap_profile
from simulator.recommender import (
    load_driver_policy,
    build_segment_database,
    train_models,
    choose_action_from_policy
)

# Track
from simulator.track_loader import (
    load_track_csv,
    generate_oval_track  # fallback
)

# Sensors
from simulator.new_sensors.wheel_speed_sensor import WheelSpeedSensor
from simulator.new_sensors.brake_pressure_sensor import BrakePressureSensor
from simulator.new_sensors.coolant_temp_sensor import CoolantTempSensor
from simulator.new_sensors.imu_sensor import IMUSensor

# Physics
from simulator.physics.simple.dynamics import update_speed
from simulator.physics.simple.thermal import update_coolant_temp
from simulator.physics.simple.steering_yaw import compute_yaw_rate
from simulator.physics.simple.gps_simulator import GPSMock


# -------------------------------------------------------------
# CLI ARGUMENTS
# -------------------------------------------------------------
parser = argparse.ArgumentParser()

parser.add_argument("--driver-id", type=str, default="driver_normal")
parser.add_argument("--target-laps", type=int, default=5)
parser.add_argument("--use-policy", action="store_true")
parser.add_argument("--train-models", action="store_true")
parser.add_argument("--limit-sessions", type=int, default=None)

# ⭐ NEW ARGUMENTS ADDED
parser.add_argument("--track", type=str, default=None,
                    help="Track file inside data/tracks/. Example: track_20251205_111545.csv")

parser.add_argument("--progress-file", type=str, default="data/sim_progress.json",
                    help="File for progress updates so Streamlit can read it")

args = parser.parse_args()


# -------------------------------------------------------------
# Paths
# -------------------------------------------------------------
DATA_DIR = os.path.join(ROOT, "data")
TRACK_DIR = os.path.join(DATA_DIR, "tracks")
LOG_DIR = os.path.join(DATA_DIR, "logs")
STOP_FILE = os.path.join(DATA_DIR, "stop_signal.txt")
os.makedirs(LOG_DIR, exist_ok=True)

PROGRESS_FILE = os.path.join(ROOT, args.progress_file)


# -------------------------------------------------------------
# Load configs
# -------------------------------------------------------------
sim_cfg = load_yaml(os.path.join(ROOT, "configs", "simulation.yaml"))
car_cfg = load_yaml(os.path.join(ROOT, "configs", "car_simple.yaml"))
sensor_cfg = load_yaml(os.path.join(ROOT, "configs", "sensors.yaml"))

dt = sim_cfg.get("dt", 0.1)


# -------------------------------------------------------------
# Track loading
# -------------------------------------------------------------
if args.track:
    track_path = os.path.join(TRACK_DIR, args.track)
    if os.path.exists(track_path):
        print(f"📌 Loading track: {track_path}")
        track = load_track_csv(track_path)
    else:
        print(f"⚠ Track not found: {track_path}, using oval")
        track = generate_oval_track()
else:
    print("📌 No custom track selected — using oval track")
    track = generate_oval_track()

gps = GPSMock(track)


# -------------------------------------------------------------
# Prepare sensors
# -------------------------------------------------------------
wheel_sensor = WheelSpeedSensor(sensor_cfg["wheel_speed"]["std"],
                                sensor_cfg["wheel_speed"]["dropout_prob"])

brake_sensor = BrakePressureSensor(sensor_cfg["brake_pressure"]["std"],
                                   sensor_cfg["brake_pressure"]["dropout_prob"])

coolant_sensor = CoolantTempSensor(sensor_cfg["coolant_temp"]["std"],
                                   sensor_cfg["coolant_temp"]["dropout_prob"])

imu_sensor = IMUSensor(
    accel_std=sensor_cfg["imu"]["accel_std"],
    yaw_std=sensor_cfg["imu"]["yaw_std"],
    dropout_prob=sensor_cfg["imu"]["dropout_prob"]
)


# -------------------------------------------------------------
# State initialization
# -------------------------------------------------------------
v_ms = 0.0
coolant = car_cfg["initial_coolant_temp"]
yaw_deg = 0.0


# -------------------------------------------------------------
# Prepare logging
# -------------------------------------------------------------
session = []
session_name = f"race_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
session_path = os.path.join(LOG_DIR, session_name)


# -------------------------------------------------------------
# Helper: write progress
# -------------------------------------------------------------
def write_progress(lap, target):
    data = {"lap": lap, "target": target}
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)


# -------------------------------------------------------------
# TRAIN MODELS (optional)
# -------------------------------------------------------------
if args.train_models:
    print("📘 Building session database…")
    db = build_segment_database(limit=args.limit_sessions)
    print(f"📘 Training models using {len(db)} samples…")
    train_models(db)


# -------------------------------------------------------------
# Load recommender policy (optional)
# -------------------------------------------------------------
policy = None
if args.use_policy:
    policy = load_driver_policy(args.driver_id)
    print(f"🤖 Using learned driver policy: {args.driver_id}")


# -------------------------------------------------------------
# MAIN SIMULATION LOOP
# -------------------------------------------------------------
print(f"🏁 Starting simulation for {args.target_laps} laps…")
pbar = tqdm(total=args.target_laps, dynamic_ncols=True)

t = 0.0
last_lap = 0

try:
    while True:

        # STOP SIGNAL SUPPORT
        if os.path.exists(STOP_FILE):
            print("🛑 Stop signal detected — exiting simulation.")
            break

        # -----------------------------
        #  Driver control logic
        # -----------------------------
        if policy:
            throttle, brake_cmd, steering = choose_action_from_policy(policy)
        else:
            throttle, brake_cmd, steering = simple_lap_profile(t)

        # -----------------------------
        #  Physics
        # -----------------------------
        v_ms = update_speed(v_ms, throttle, brake_cmd, dt)
        speed_kmh = v_ms * 3.6

        coolant = update_coolant_temp(coolant, throttle, speed_kmh, dt)
        yaw_deg = compute_yaw_rate(steering, speed_kmh)

        # GPS movement
        dist = v_ms * dt
        (x, y), idx, laps = gps.advance(dist)

        # Progress update
        if laps > last_lap:
            pbar.update(1)
            last_lap = laps

        write_progress(laps, args.target_laps)

        if laps >= args.target_laps:
            print("🏁 Target laps reached!")
            break

        # -----------------------------
        # Sensors
        # -----------------------------
        ws = wheel_sensor.read(speed_kmh)
        bp = brake_sensor.read(brake_cmd * 100)
        ct = coolant_sensor.read(coolant)
        imu = imu_sensor.read(true_ax=0.0, true_ay=0.0, true_yaw=yaw_deg)

        packet = {
            "timestamp": time.time(),
            "t": t,
            "lap": laps,
            "track_index": idx,
            "gps": {"x": x, "y": y},
            "true": {
                "speed_kmh": speed_kmh,
                "coolant_temp": coolant,
                "brake_cmd": brake_cmd,
                "throttle": throttle,
                "yaw_deg": yaw_deg,
            },
            "sensors": {
                "wheel_speed": ws,
                "brake_pressure": bp,
                "coolant_temp": ct,
                "imu": imu,
            },
        }

        write_realtime_json(os.path.join(DATA_DIR, "realtime.json"), packet)
        session.append(packet)
        write_session_log(session_path, session)

        # Step time
        t += dt
        time.sleep(dt)

except KeyboardInterrupt:
    print("🛑 Interrupted by user")

finally:
    pbar.close()
    print(f"💾 Session saved to {session_path}")


# # simulator/run_simulator_with_recommender.py
# # Run a simulation using either a DriverProfile or recommended policy actions.
# import sys, os
# ROOT = os.path.dirname(os.path.dirname(__file__))
# sys.path.append(ROOT)

# import time, datetime, argparse
# from tqdm import tqdm

# from utils.config_loader import load_yaml
# from utils.json_writer import write_realtime_json, write_session_log
# from simulator.track_loader import generate_oval_track
# from simulator.driver_profiles import simple_lap_profile
# from simulator.driver_manager import load_drivers
# from simulator.new_sensors.wheel_speed_sensor import WheelSpeedSensor
# from simulator.new_sensors.brake_pressure_sensor import BrakePressureSensor
# from simulator.new_sensors.coolant_temp_sensor import CoolantTempSensor
# from simulator.new_sensors.imu_sensor import IMUSensor
# from simulator.physics.simple.dynamics import update_speed
# from simulator.physics.simple.thermal import update_coolant_temp
# from simulator.physics.simple.steering_yaw import compute_yaw_rate
# from simulator.physics.simple.gps_simulator import GPSMock

# from recommender import load_all_sessions, build_segment_database, best_action_per_segment_by_best_lap, train_regressors_per_action, recommend_action_segment

# parser = argparse.ArgumentParser()
# parser.add_argument("--driver-id", type=str, default=None, help="Driver profile id to simulate")
# parser.add_argument("--target-laps", type=int, default=5)
# parser.add_argument("--use-policy", action="store_true", help="Use recommended policy instead of driver profile actions")
# parser.add_argument("--train-models", action="store_true", help="Train regressors (requires scikit-learn)")
# parser.add_argument("--limit-sessions", type=int, default=None, help="Limit number of sessions used to build DB")
# args = parser.parse_args()

# # load configs
# sim_cfg = load_yaml(os.path.join(ROOT, "configs", "simulation.yaml"))
# sensors_cfg = load_yaml(os.path.join(ROOT, "configs", "sensors.yaml"))
# car_cfg = load_yaml(os.path.join(ROOT, "configs", "car_simple.yaml"))
# dt = sim_cfg.get("dt", 0.1)

# # sensors
# wheel_sensor = WheelSpeedSensor(std=sensors_cfg["wheel_speed"]["std"], dropout_prob=sensors_cfg["wheel_speed"]["dropout_prob"])
# brake_sensor = BrakePressureSensor(std=sensors_cfg["brake_pressure"]["std"], dropout_prob=sensors_cfg["brake_pressure"]["dropout_prob"])
# coolant_sensor = CoolantTempSensor(std=sensors_cfg["coolant_temp"]["std"], dropout_prob=sensors_cfg["coolant_temp"]["dropout_prob"])
# imu_sensor = IMUSensor(accel_std=sensors_cfg["imu"]["accel_std"], yaw_std=sensors_cfg["imu"]["yaw_std"], dropout_prob=sensors_cfg["imu"]["dropout_prob"])

# # drivers
# drivers = load_drivers()
# driver = drivers.get(args.driver_id) if args.driver_id else None

# # build recommender DB
# sessions = load_all_sessions(limit=args.limit_sessions)
# db = build_segment_database(sessions)
# policy = best_action_per_segment_by_best_lap(db)
# models = None
# if args.train_models:
#     if not SKLEARN_AVAILABLE:
#         print("sklearn not available, skipping model training.")
#     else:
#         models = train_regressors_per_action(db)

# # prepare track & gps
# # track & gps
# from simulator.track_loader import generate_custom_track

# track = generate_custom_track(
#     n_left=6,
#     n_right=6
# )

# #track = generate_oval_track(n_points=400, a=120.0, b=60.0)
# gps = GPSMock(track)

# DATA_DIR = os.path.join(ROOT, "data")
# LOG_DIR = os.path.join(DATA_DIR, "logs")
# os.makedirs(LOG_DIR, exist_ok=True)
# session = []
# session_name = f"race_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
# session_path = os.path.join(LOG_DIR, session_name)

# print(f"Starting sim. driver={args.driver_id} policy_mode={args.use_policy} laps={args.target_laps}")
# pbar = tqdm(total=args.target_laps)

# # initial state
# v_ms = 0.0
# coolant_temp = car_cfg.get("initial_coolant_temp", 60.0)
# yaw_deg = 0.0
# t = 0.0
# last_finished_lap = 0

# try:
#     while True:
#         # determine action
#         if args.use_policy:
#             # state vector (for policy) - we will use current true state and lap_progress estimate
#             max_idx = len(track) - 1
#             current_idx = gps.index
#             lap_progress = current_idx / max_idx if max_idx > 0 else 0.0
#             state_vec = [v_ms * 3.6, coolant_temp, yaw_deg, lap_progress]
#             # get recommended action
#             rec = recommend_action_segment(current_idx, state_vec, policy_segment_db=policy, models=models)
#             throttle, brake_cmd, steering = rec[0], rec[1], rec[2]
#         else:
#             # default driver profile behavior
#             throttle, brake_cmd, steering = simple_lap_profile(t=t, lap_time=25.0)
#             # apply low-level driver perturbations if driver provided
#             if driver:
#                 throttle, brake_cmd, steering = driver.perturb_action(throttle, brake_cmd, steering)

#         # dynamics update
#         v_ms = update_speed(v_ms, throttle, brake_cmd, dt=dt)
#         true_speed_kmh = v_ms * 3.6
#         coolant_temp = update_coolant_temp(coolant_temp, throttle, true_speed_kmh, dt=dt)
#         yaw_deg = compute_yaw_rate(steering, true_speed_kmh)

#         # gps advance
#         distance_m = v_ms * dt
#         (gps_x, gps_y), gps_idx, laps = gps.advance(distance_m)

#         # update tqdm on lap finish
#         if laps > last_finished_lap:
#             pbar.update(1)
#             last_finished_lap = laps
#         if laps >= args.target_laps:
#             break

#         # sensors read
#         ws = wheel_sensor.read(true_speed_kmh)
#         bp = brake_sensor.read(brake_cmd * 100.0)
#         ct = coolant_sensor.read(coolant_temp)
#         imu = imu_sensor.read(true_ax=0.0, true_ay=0.0, true_yaw=yaw_deg)

#         packet = {
#             "timestamp": time.time(),
#             "t": round(t, 3),
#             "lap": laps,
#             "track_index": gps_idx,
#             "gps": {"x": round(gps_x, 3), "y": round(gps_y, 3)},
#             "driver_id": args.driver_id,
#             "policy_mode": bool(args.use_policy),
#             "true": {
#                 "speed_kmh": round(true_speed_kmh, 2),
#                 "coolant_temp": round(coolant_temp, 2),
#                 "brake_cmd": round(brake_cmd, 2),
#                 "throttle": round(throttle, 2),
#                 "yaw_deg": round(yaw_deg, 3),
#                 "steering": round(steering, 3)
#             },
#             "sensors": {
#                 "wheel_speed": ws,
#                 "brake_pressure": bp,
#                 "coolant_temp": ct,
#                 "imu": imu
#             },
#             "recommended": {
#                 "throttle": rec[0] if args.use_policy else None,
#                 "brake": rec[1] if args.use_policy else None,
#                 "steering": rec[2] if args.use_policy else None
#             }
#         }

#         write_realtime_json(os.path.join(DATA_DIR, "realtime.json"), packet)
#         session.append(packet)
#         write_session_log(session_path, session)

#         t += dt
#         time.sleep(dt)

# except KeyboardInterrupt:
#     print("Stopped by user.")
# finally:
#     pbar.close()
#     print("Saved to", session_path)
