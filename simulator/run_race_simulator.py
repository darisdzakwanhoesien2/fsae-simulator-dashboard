import json, os, datetime
from tqdm import tqdm

from sensors.coolant_temp import CoolantTempSimulator
from sensors.wheel_speed import WheelSpeedSimulator
from sensors.brake_pressure import BrakePressureSimulator
from sensors.imu import IMUSimulator

# --------------------------
# CONFIGURATION
# --------------------------
NUM_LAPS = 10
SAMPLES_PER_LAP = 500   # total samples per lap
PRINT_EVERY = 100       # how often to update tqdm text

# --------------------------
# INIT
# --------------------------
coolant = CoolantTempSimulator()
wheels = WheelSpeedSimulator()
brakes = BrakePressureSimulator()
imu = IMUSimulator()

log_path = "data/logs"
os.makedirs(log_path, exist_ok=True)

session_name = f"race_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
session_file = os.path.join(log_path, session_name)

session_log = []

print("\n🏁 Starting Race Simulation: 10 Laps")
print("This is NOT real-time. Generating fast simulation...\n")

# --------------------------
# SIMULATION LOOP
# --------------------------
total_samples = NUM_LAPS * SAMPLES_PER_LAP

with tqdm(total=total_samples, unit="samples", dynamic_ncols=True) as pbar:
    for lap in range(1, NUM_LAPS + 1):
        for i in range(SAMPLES_PER_LAP):

            data = {
                "lap": lap,
                "lap_progress": i / SAMPLES_PER_LAP,
                "coolant_temp": coolant.step(),
                "wheel_speed": wheels.step(),
                "brake_pressure": brakes.step(),
                "imu": imu.step(),
            }

            session_log.append(data)

            if len(session_log) % PRINT_EVERY == 0:
                pbar.set_description(
                    f"Lap {lap}/{NUM_LAPS} | Coolant {data['coolant_temp']}°C | Speed {data['wheel_speed']} km/h"
                )

            pbar.update(1)

# Save results
with open(session_file, "w") as f:
    json.dump(session_log, f, indent=2)

print(f"\n🏁 Race simulation complete! Saved to:\n📁 {session_file}\n")
