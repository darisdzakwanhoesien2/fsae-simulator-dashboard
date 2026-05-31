"""
Legacy Stage-0 simulator (pre physics-pipeline refactor).

Kept for reference, but not used by the current dashboard flow.
Prefer:
- `simulator/run_simulator_stage_1.py` (Stage-1 physics + sensors)
- `simulator/run_simulator_stage_1_laps.py` (fixed-lap run)

This legacy script previously wrote to `../data/realtime.json`, which depends on
the current working directory. If you run it, it now writes to the repo-root
`data/realtime.json` and `data/logs/` consistently.
"""

import datetime
import json
import os
import time

from tqdm import tqdm

from simulator.sensors.brake_pressure import BrakePressureSimulator
from simulator.sensors.coolant_temp import CoolantTempSimulator
from simulator.sensors.imu import IMUSimulator
from simulator.sensors.wheel_speed import WheelSpeedSimulator


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(__file__))


def main():
    root = _repo_root()
    data_dir = os.path.join(root, "data")
    log_dir = os.path.join(data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    coolant = CoolantTempSimulator()
    wheels = WheelSpeedSimulator()
    brakes = BrakePressureSimulator()
    imu = IMUSimulator()

    session_name = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    session_file = os.path.join(log_dir, session_name)

    realtime_path = os.path.join(data_dir, "realtime.json")
    session_log = []

    print("\n▶️ Starting legacy telemetry simulator (10 Hz)...")
    print("Press CTRL+C to stop.\n")

    try:
        with tqdm(total=0, unit="samples", dynamic_ncols=True) as pbar:
            while True:
                data = {
                    "timestamp": time.time(),
                    "coolant_temp": coolant.step(),
                    "wheel_speed": wheels.step(),
                    "brake_pressure": brakes.step(),
                    "imu": imu.step(),
                }

                # Real-time output used by Streamlit pages.
                with open(realtime_path, "w") as f:
                    json.dump(data, f)

                # Simple replay log (rewritten each tick).
                session_log.append(data)
                with open(session_file, "w") as f:
                    json.dump(session_log, f, indent=2)

                pbar.update(1)
                pbar.set_description(
                    f"Coolant: {data['coolant_temp']}°C | Speed: {data['wheel_speed']} km/h"
                )

                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n🛑 Simulator stopped by user (CTRL+C).")
        print(f"📁 Session saved to: {session_file}\n")


if __name__ == "__main__":
    main()

