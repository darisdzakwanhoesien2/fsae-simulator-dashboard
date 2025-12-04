# simulator/driver_manager.py

import json
import os
import random

# UPDATED PATH → driver_simulation.json
DRIVER_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "driver_simulation.json"
)

class DriverProfile:
    """
    Encapsulates driver behavior parameters.
    """
    def __init__(self, driver_id, name="anon",
                 throttle_bias=1.0,
                 aggressiveness=0.2,
                 steering_noise=0.02):
        self.driver_id = driver_id
        self.name = name
        self.throttle_bias = throttle_bias
        self.aggressiveness = aggressiveness
        self.steering_noise = steering_noise

    def perturb_action(self, throttle, brake, steering):
        """Apply driver-specific perturbation to an action tuple."""
        # throttle
        t = max(0.0, min(1.0, throttle * self.throttle_bias))

        # brake — aggressiveness adds bias
        b = max(0.0, min(1.0, brake * (1.0 + self.aggressiveness * (random.random() - 0.5))))

        # steering noise
        s = steering + random.uniform(-self.steering_noise, self.steering_noise)
        s = max(-1.0, min(1.0, s))

        return t, b, s


def load_drivers():
    """
    Load driver definitions from driver_simulation.json.
    If the file does not exist, create default profiles.
    """
    drivers = {}

    if os.path.exists(DRIVER_DB_PATH):
        try:
            with open(DRIVER_DB_PATH, "r") as f:
                raw = json.load(f)

            for d in raw.get("drivers", []):
                dp = DriverProfile(
                    driver_id=d.get("driver_id"),
                    name=d.get("name", "driver"),
                    throttle_bias=d.get("throttle_bias", 1.0),
                    aggressiveness=d.get("aggressiveness", 0.2),
                    steering_noise=d.get("steering_noise", 0.02)
                )
                drivers[dp.driver_id] = dp

        except Exception as e:
            print(f"⚠️ Failed to load driver profiles: {e}")

    # fallback: basic drivers
    if not drivers:
        drivers["driver_fast"] = DriverProfile(
            "driver_fast", "Fast Driver",
            throttle_bias=1.05, aggressiveness=0.05, steering_noise=0.01
        )
        drivers["driver_smooth"] = DriverProfile(
            "driver_smooth", "Smooth Driver",
            throttle_bias=0.9, aggressiveness=0.1, steering_noise=0.02
        )
        drivers["driver_aggressive"] = DriverProfile(
            "driver_aggressive", "Aggressive Driver",
            throttle_bias=1.1, aggressiveness=0.25, steering_noise=0.03
        )

    return drivers
