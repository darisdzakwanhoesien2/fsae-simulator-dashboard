# simulator/run_simulator_stage_1.py

# --- FIX IMPORT PATHS ---
import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)
# ------------------------

import time
import datetime
from tqdm import tqdm

# config utils
from utils.config_loader import load_yaml
from utils.json_writer import write_realtime_json, write_session_log

# track & driver
from simulator.track_loader import generate_oval_track
from simulator.driver_profiles import simple_lap_profile

# physics
from simulator.physics.simple.dynamics import update_speed
from simulator.physics.simple.thermal import update_coolant_temp
from simulator.physics.simple.steering_yaw import compute_yaw_rate
from simulator.physics.simple.gps_simulator import GPSMock

# sensors
from simulator.new_sensors.wheel_speed_sensor import WheelSpeedSensor
from simulator.new_sensors.brake_pressure_sensor import BrakePressureSensor
from simulator.new_sensors.coolant_temp_sensor import CoolantTempSensor
from simulator.new_sensors.imu_sensor import IMUSensor

# --------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------
TARGET_LAPS = 10  # 🔥 change to any number (10 laps recommended)
LAP_TIME_ESTIMATE = 25  # seconds per lap (just for progress estimate)
# --------------------------------------------------------------------

DATA_DIR = os.path.join(ROOT, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# load configs
sim_cfg = load_yaml(os.path.join(ROOT, "configs", "simulation.yaml"))
car_cfg = load_yaml(os.path.join(ROOT, "configs", "car_simple.yaml"))
sensors_cfg = load_yaml(os.path.join(ROOT, "configs", "sensors.yaml"))

dt = sim_cfg.get("dt", 0.1)

# sensors creation
wheel_sensor = WheelSpeedSensor(std=sensors_cfg["wheel_speed"]["std"],
                                dropout_prob=sensors_cfg["wheel_speed"]["dropout_prob"])
brake_sensor = BrakePressureSensor(std=sensors_cfg["brake_pressure"]["std"],
                                   dropout_prob=sensors_cfg["brake_pressure"]["dropout_prob"])
coolant_sensor = CoolantTempSensor(std=sensors_cfg["coolant_temp"]["std"],
                                   dropout_prob=sensors_cfg["coolant_temp"]["dropout_prob"])
imu_sensor = IMUSensor(accel_std=sensors_cfg["imu"]["accel_std"],
                       yaw_std=sensors_cfg["imu"]["yaw_std"],
                       dropout_prob=sensors_cfg["imu"]["dropout_prob"])

# initial state
v_ms = 0.0
coolant_temp = car_cfg.get("initial_coolant_temp", 60.0)
yaw_deg = 0.0

# track & gps
from simulator.track_loader import generate_custom_track

track = generate_custom_track(
    n_left=6,
    n_right=6
)

#track = generate_oval_track(n_points=400, a=120.0, b=60.0)
gps = GPSMock(track)

# log
session = []
session_name = f"race_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
session_path = os.path.join(LOG_DIR, session_name)

# --------------------------------------------------------------------
# Progress Bar (laps)
# --------------------------------------------------------------------
print(f"🏁 Starting Stage-1 Physics Simulation for {TARGET_LAPS} laps…")
pbar = tqdm(total=TARGET_LAPS, unit="lap", dynamic_ncols=True)

# --------------------------------------------------------------------
# MAIN LOOP
# --------------------------------------------------------------------
t = 0.0
last_finished_lap = 0

try:
    while True:
        throttle, brake_cmd, steering = simple_lap_profile(t=t, lap_time=25.0)

        # update longitudinal dynamics
        v_ms = update_speed(v_ms, throttle, brake_cmd, dt=dt)
        true_speed_kmh = v_ms * 3.6

        # thermal
        coolant_temp = update_coolant_temp(coolant_temp, throttle, true_speed_kmh, dt=dt)

        # yaw
        yaw_deg = compute_yaw_rate(steering, true_speed_kmh)

        # gps advancement
        distance_m = v_ms * dt
        (gps_x, gps_y), gps_idx, laps = gps.advance(distance_m)

        # update tqdm when a new lap is completed
        if laps > last_finished_lap:
            pbar.update(1)
            last_finished_lap = laps

        # Stop when TARGET_LAPS reached
        if laps >= TARGET_LAPS:
            break

        # sensors
        ws = wheel_sensor.read(true_speed_kmh)
        bp = brake_sensor.read(brake_cmd * 100)
        ct = coolant_sensor.read(coolant_temp)
        imu = imu_sensor.read(true_ax=0.0, true_ay=0.0, true_yaw=yaw_deg)

        # packet
        packet = {
            "timestamp": time.time(),
            "t": round(t, 3),
            "lap": laps,
            "track_index": gps_idx,
            "gps": {"x": round(gps_x, 3), "y": round(gps_y, 3)},
            "true": {
                "speed_kmh": round(true_speed_kmh, 2),
                "coolant_temp": round(coolant_temp, 2),
                "brake_cmd": round(brake_cmd, 2),
                "throttle": round(throttle, 2),
                "yaw_deg": round(yaw_deg, 3),
            },
            "sensors": {
                "wheel_speed": ws,
                "brake_pressure": bp,
                "coolant_temp": ct,
                "imu": imu,
            },
        }

        # write realtime + append log
        write_realtime_json(os.path.join(DATA_DIR, "realtime.json"), packet)
        session.append(packet)
        write_session_log(session_path, session)

        # time stepping
        t += dt
        time.sleep(dt)

except KeyboardInterrupt:
    print("\n🛑 Simulation manually stopped by user.")

finally:
    pbar.close()
    print(f"💾 Session saved to {session_path}")
    print("🏁 Simulation finished.")
