import datetime
import json
import os
import sys
import time
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from simulator.sensors.coolant_temp import CoolantTempSimulator
from simulator.sensors.wheel_speed import WheelSpeedSimulator
from simulator.sensors.brake_pressure import BrakePressureSimulator
from simulator.sensors.imu import IMUSimulator

coolant = CoolantTempSimulator()
wheels = WheelSpeedSimulator()
brakes = BrakePressureSimulator()
imu = IMUSimulator()

# Create log directory
log_path = os.path.join(ROOT, "data", "logs")
os.makedirs(log_path, exist_ok=True)

session_name = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
session_file = os.path.join(log_path, session_name)

session_log = []

print("\n▶️ Starting FSAE Telemetry Simulator (10 Hz)...")
print("Press CTRL+C to stop.\n")

try:
    # Use tqdm progress bar that updates indefinitely
    with tqdm(total=0, unit="samples", unit_scale=False, dynamic_ncols=True) as pbar:
        while True:
            data = {
                "timestamp": time.time(),
                "coolant_temp": coolant.step(),
                "wheel_speed": wheels.step(),
                "brake_pressure": brakes.step(),
                "imu": imu.step()
            }

            # Write real-time data
            realtime_path = os.path.join(ROOT, "data", "realtime.json")
            with open(realtime_path, "w") as f:
                json.dump(data, f)

            # Save for replay
            session_log.append(data)
            with open(session_file, "w") as f:
                json.dump(session_log, f, indent=2)

            # Update tqdm bar
            pbar.update(1)
            pbar.set_description(f"Coolant: {data['coolant_temp']}°C | Speed: {data['wheel_speed']} km/h")

            time.sleep(0.1)  # 10 Hz

except KeyboardInterrupt:
    print("\n\n🛑 Simulator stopped by user (CTRL+C).")
    print(f"📁 Session saved to: {session_file}\n")
