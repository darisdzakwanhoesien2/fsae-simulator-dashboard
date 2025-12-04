# simulator/run_simulator_with_recommender.py
# Run a simulation using either a DriverProfile or recommended policy actions.
import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

import time, datetime, argparse
from tqdm import tqdm

from utils.config_loader import load_yaml
from utils.json_writer import write_realtime_json, write_session_log
from simulator.track_loader import generate_oval_track
from simulator.driver_profiles import simple_lap_profile
from simulator.driver_manager import load_drivers
from simulator.new_sensors.wheel_speed_sensor import WheelSpeedSensor
from simulator.new_sensors.brake_pressure_sensor import BrakePressureSensor
from simulator.new_sensors.coolant_temp_sensor import CoolantTempSensor
from simulator.new_sensors.imu_sensor import IMUSensor
from simulator.physics.simple.dynamics import update_speed
from simulator.physics.simple.thermal import update_coolant_temp
from simulator.physics.simple.steering_yaw import compute_yaw_rate
from simulator.physics.simple.gps_simulator import GPSMock

from recommender import load_all_sessions, build_segment_database, best_action_per_segment_by_best_lap, train_regressors_per_action, recommend_action_segment

parser = argparse.ArgumentParser()
parser.add_argument("--driver-id", type=str, default=None, help="Driver profile id to simulate")
parser.add_argument("--target-laps", type=int, default=5)
parser.add_argument("--use-policy", action="store_true", help="Use recommended policy instead of driver profile actions")
parser.add_argument("--train-models", action="store_true", help="Train regressors (requires scikit-learn)")
parser.add_argument("--limit-sessions", type=int, default=None, help="Limit number of sessions used to build DB")
args = parser.parse_args()

# load configs
sim_cfg = load_yaml(os.path.join(ROOT, "configs", "simulation.yaml"))
sensors_cfg = load_yaml(os.path.join(ROOT, "configs", "sensors.yaml"))
car_cfg = load_yaml(os.path.join(ROOT, "configs", "car_simple.yaml"))
dt = sim_cfg.get("dt", 0.1)

# sensors
wheel_sensor = WheelSpeedSensor(std=sensors_cfg["wheel_speed"]["std"], dropout_prob=sensors_cfg["wheel_speed"]["dropout_prob"])
brake_sensor = BrakePressureSensor(std=sensors_cfg["brake_pressure"]["std"], dropout_prob=sensors_cfg["brake_pressure"]["dropout_prob"])
coolant_sensor = CoolantTempSensor(std=sensors_cfg["coolant_temp"]["std"], dropout_prob=sensors_cfg["coolant_temp"]["dropout_prob"])
imu_sensor = IMUSensor(accel_std=sensors_cfg["imu"]["accel_std"], yaw_std=sensors_cfg["imu"]["yaw_std"], dropout_prob=sensors_cfg["imu"]["dropout_prob"])

# drivers
drivers = load_drivers()
driver = drivers.get(args.driver_id) if args.driver_id else None

# build recommender DB
sessions = load_all_sessions(limit=args.limit_sessions)
db = build_segment_database(sessions)
policy = best_action_per_segment_by_best_lap(db)
models = None
if args.train_models:
    if not SKLEARN_AVAILABLE:
        print("sklearn not available, skipping model training.")
    else:
        models = train_regressors_per_action(db)

# prepare track & gps
# track & gps
from simulator.track_loader import generate_custom_track

track = generate_custom_track(
    n_left=6,
    n_right=6
)

#track = generate_oval_track(n_points=400, a=120.0, b=60.0)
gps = GPSMock(track)

DATA_DIR = os.path.join(ROOT, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
session = []
session_name = f"race_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
session_path = os.path.join(LOG_DIR, session_name)

print(f"Starting sim. driver={args.driver_id} policy_mode={args.use_policy} laps={args.target_laps}")
pbar = tqdm(total=args.target_laps)

# initial state
v_ms = 0.0
coolant_temp = car_cfg.get("initial_coolant_temp", 60.0)
yaw_deg = 0.0
t = 0.0
last_finished_lap = 0

try:
    while True:
        # determine action
        if args.use_policy:
            # state vector (for policy) - we will use current true state and lap_progress estimate
            max_idx = len(track) - 1
            current_idx = gps.index
            lap_progress = current_idx / max_idx if max_idx > 0 else 0.0
            state_vec = [v_ms * 3.6, coolant_temp, yaw_deg, lap_progress]
            # get recommended action
            rec = recommend_action_segment(current_idx, state_vec, policy_segment_db=policy, models=models)
            throttle, brake_cmd, steering = rec[0], rec[1], rec[2]
        else:
            # default driver profile behavior
            throttle, brake_cmd, steering = simple_lap_profile(t=t, lap_time=25.0)
            # apply low-level driver perturbations if driver provided
            if driver:
                throttle, brake_cmd, steering = driver.perturb_action(throttle, brake_cmd, steering)

        # dynamics update
        v_ms = update_speed(v_ms, throttle, brake_cmd, dt=dt)
        true_speed_kmh = v_ms * 3.6
        coolant_temp = update_coolant_temp(coolant_temp, throttle, true_speed_kmh, dt=dt)
        yaw_deg = compute_yaw_rate(steering, true_speed_kmh)

        # gps advance
        distance_m = v_ms * dt
        (gps_x, gps_y), gps_idx, laps = gps.advance(distance_m)

        # update tqdm on lap finish
        if laps > last_finished_lap:
            pbar.update(1)
            last_finished_lap = laps
        if laps >= args.target_laps:
            break

        # sensors read
        ws = wheel_sensor.read(true_speed_kmh)
        bp = brake_sensor.read(brake_cmd * 100.0)
        ct = coolant_sensor.read(coolant_temp)
        imu = imu_sensor.read(true_ax=0.0, true_ay=0.0, true_yaw=yaw_deg)

        packet = {
            "timestamp": time.time(),
            "t": round(t, 3),
            "lap": laps,
            "track_index": gps_idx,
            "gps": {"x": round(gps_x, 3), "y": round(gps_y, 3)},
            "driver_id": args.driver_id,
            "policy_mode": bool(args.use_policy),
            "true": {
                "speed_kmh": round(true_speed_kmh, 2),
                "coolant_temp": round(coolant_temp, 2),
                "brake_cmd": round(brake_cmd, 2),
                "throttle": round(throttle, 2),
                "yaw_deg": round(yaw_deg, 3),
                "steering": round(steering, 3)
            },
            "sensors": {
                "wheel_speed": ws,
                "brake_pressure": bp,
                "coolant_temp": ct,
                "imu": imu
            },
            "recommended": {
                "throttle": rec[0] if args.use_policy else None,
                "brake": rec[1] if args.use_policy else None,
                "steering": rec[2] if args.use_policy else None
            }
        }

        write_realtime_json(os.path.join(DATA_DIR, "realtime.json"), packet)
        session.append(packet)
        write_session_log(session_path, session)

        t += dt
        time.sleep(dt)

except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    pbar.close()
    print("Saved to", session_path)
