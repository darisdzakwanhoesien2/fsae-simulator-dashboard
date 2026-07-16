"""
Advanced driver behavior models with adaptation, fatigue, and style parameters.

Extends the simple DriverProfile with:
  - Braking consistency (variance in braking point)
  - Corner aggressiveness (late braking / early throttle)
  - Racing line preference (inside, middle, outside)
  - Reaction time (delay in control changes)
  - Fatigue (performance degradation over stint)
  - Learning rate (improvement over consecutive laps)
"""

import numpy as np
from typing import Callable


class AdaptiveDriver:
    def __init__(
        self,
        driver_id: str = "adaptive_driver",
        name: str = "Adaptive Driver",
        # Base skill
        throttle_bias: float = 1.0,
        aggressiveness: float = 0.2,
        steering_noise: float = 0.02,
        # Advanced parameters
        braking_consistency: float = 0.9,
        corner_aggressiveness: float = 0.5,
        racing_line_preference: str = "middle",
        reaction_time: float = 0.15,
        # Adaptation
        fatigue_rate: float = 0.02,
        learning_rate: float = 0.01,
        # Initial state
        initial_fatigue: float = 0.0,
        initial_confidence: float = 0.5,
    ):
        self.driver_id = driver_id
        self.name = name

        # Base parameters (compatible with DriverProfile)
        self.throttle_bias = throttle_bias
        self.aggressiveness = aggressiveness
        self.steering_noise = steering_noise

        # Advanced parameters
        self.braking_consistency = np.clip(braking_consistency, 0.0, 1.0)
        self.corner_aggressiveness = np.clip(corner_aggressiveness, 0.0, 1.0)
        self.racing_line_preference = racing_line_preference
        self.reaction_time = max(0.0, reaction_time)

        # Adaptation parameters
        self.fatigue_rate = fatigue_rate
        self.learning_rate = learning_rate

        # State
        self.fatigue = np.clip(initial_fatigue, 0.0, 1.0)
        self.confidence = np.clip(initial_confidence, 0.0, 1.0)
        self.lap_count = 0
        self.consecutive_laps = 0
        self.braking_points = []  # history of braking points for consistency calc

        # Internal state for reaction time delay
        self._prev_throttle = 0.0
        self._prev_brake = 0.0
        self._prev_steering = 0.0
        self._reaction_buffer = 0.0

    def get_effective_params(self) -> dict:
        """Return effective driving parameters modulated by fatigue and confidence."""
        eff_aggressiveness = self.aggressiveness * (1.0 - self.fatigue * 0.3)
        eff_consistency = self.braking_consistency * (1.0 - self.fatigue * 0.2)
        eff_reaction = self.reaction_time * (1.0 + self.fatigue * 0.5)

        # Learning: confidence increases with laps, reducing noise
        eff_steering_noise = self.steering_noise * (1.0 - self.confidence * 0.3)
        eff_throttle_bias = self.throttle_bias * (1.0 - self.fatigue * 0.1)

        return {
            "aggressiveness": eff_aggressiveness,
            "braking_consistency": eff_consistency,
            "reaction_time": eff_reaction,
            "steering_noise": eff_steering_noise,
            "throttle_bias": eff_throttle_bias,
        }

    def get_action(
        self,
        t: float,
        lap_time: float = 25.0,
        track_curvature: float = 0.0,
        speed_kmh: float = 0.0,
    ) -> tuple:
        """
        Generate throttle/brake/steering with advanced driver behavior.

        Parameters
        ----------
        t : float
            Time within lap.
        lap_time : float
            Expected lap time for the profile.
        track_curvature : float
            Normalized curvature (-1..1, positive = right turn).
        speed_kmh : float
            Current speed.

        Returns
        -------
        tuple[float, float, float] — (throttle, brake, steering)
        """
        lap_progress = t / lap_time if lap_time > 0 else 0.0
        eff = self.get_effective_params()

        # Base profile: simple_lap_profile logic with modulation
        throttle, brake, steering = self._base_profile(
            lap_progress, track_curvature, speed_kmh, eff
        )

        # Apply fatigue and confidence modulation
        throttle *= (1.0 - self.fatigue * 0.15)
        throttle = np.clip(throttle, 0.0, 1.0)

        # Corner aggressiveness: later braking, earlier throttle
        if brake > 0 and track_curvature != 0:
            brake *= (1.0 - eff["corner_aggressiveness"] * 0.3)

        # Braking consistency: add jitter inversely proportional to consistency
        if brake > 0:
            brake_jitter = np.random.normal(0, (1.0 - eff["braking_consistency"]) * 0.1)
            brake = np.clip(brake + brake_jitter, 0.0, 1.0)

        # Steering with noise
        steering_noise = np.random.normal(0, eff["steering_noise"])
        steering = np.clip(steering + steering_noise, -1.0, 1.0)

        # Racing line preference affects steering bias
        if self.racing_line_preference == "inside":
            steering *= 1.1
        elif self.racing_line_preference == "outside":
            steering *= 0.9

        # Reaction time delay
        throttle, brake, steering = self._apply_reaction_delay(
            throttle, brake, steering, eff["reaction_time"], dt=0.1
        )

        self._prev_throttle = throttle
        self._prev_brake = brake
        self._prev_steering = steering

        return (float(throttle), float(brake), float(steering))

    def _base_profile(
        self, lap_progress: float, curvature: float, speed_kmh: float, eff: dict
    ) -> tuple:
        """Base throttle/brake/steering profile with 4 braking zones."""
        throttle = eff["throttle_bias"] * 0.85
        brake = 0.0
        steering = curvature * 0.5

        # 4 braking zones
        braking_zones = [(0.12, 0.18), (0.32, 0.38), (0.57, 0.63), (0.82, 0.88)]
        for start, end in braking_zones:
            if start <= lap_progress <= end:
                brake = 0.6 + eff["aggressiveness"] * 0.3
                throttle *= 0.3
                break

        # On straights, add random perturbations
        if brake == 0:
            throttle += np.random.uniform(-0.05, 0.05)
            steering = np.random.uniform(-0.02, 0.02)

        return (
            np.clip(throttle, 0.0, 1.0),
            np.clip(brake, 0.0, 1.0),
            np.clip(steering, -1.0, 1.0),
        )

    def _apply_reaction_delay(
        self, throttle: float, brake: float, steering: float, reaction_time: float, dt: float
    ) -> tuple:
        """Simulate driver reaction time by blending toward target."""
        if reaction_time <= 0 or dt <= 0:
            return throttle, brake, steering
        alpha = min(1.0, dt / reaction_time)
        throttle = self._prev_throttle + (throttle - self._prev_throttle) * alpha
        brake = self._prev_brake + (brake - self._prev_brake) * alpha
        steering = self._prev_steering + (steering - self._prev_steering) * alpha
        return throttle, brake, steering

    def on_lap_complete(self, lap_time: float, target_time: float):
        """Called when a lap is completed. Updates adaptation state."""
        self.lap_count += 1
        self.consecutive_laps += 1

        # Fatigue increases with laps
        self.fatigue = np.clip(self.fatigue + self.fatigue_rate, 0.0, 1.0)

        # Confidence increases with experience
        if lap_time <= target_time * 1.05:
            self.confidence = np.clip(self.confidence + self.learning_rate, 0.0, 1.0)
        else:
            self.confidence = np.clip(self.confidence - self.learning_rate * 0.5, 0.0, 1.0)

    def reset_stint(self):
        """Reset fatigue and confidence for a new stint."""
        self.fatigue = 0.0
        self.consecutive_laps = 0

    def get_state(self) -> dict:
        eff = self.get_effective_params()
        return {
            "driver_id": self.driver_id,
            "name": self.name,
            "fatigue": round(self.fatigue, 3),
            "confidence": round(self.confidence, 3),
            "lap_count": self.lap_count,
            "consecutive_laps": self.consecutive_laps,
            "effective_aggressiveness": round(eff["aggressiveness"], 3),
            "effective_braking_consistency": round(eff["braking_consistency"], 3),
            "effective_reaction_time": round(eff["reaction_time"], 3),
        }


# ---------------------------------------------------------------------------
#  FACTORY / BUILT-IN DRIVERS
# ---------------------------------------------------------------------------

BUILTIN_ADAPTIVE_DRIVERS = {
    "adaptive_fast": AdaptiveDriver(
        driver_id="adaptive_fast", name="Fast Adaptive",
        throttle_bias=1.05, aggressiveness=0.15,
        braking_consistency=0.95, corner_aggressiveness=0.7,
        learning_rate=0.02, fatigue_rate=0.01,
    ),
    "adaptive_smooth": AdaptiveDriver(
        driver_id="adaptive_smooth", name="Smooth Adaptive",
        throttle_bias=0.90, aggressiveness=0.05,
        braking_consistency=0.98, corner_aggressiveness=0.3,
        steering_noise=0.01, fatigue_rate=0.005,
    ),
    "adaptive_aggressive": AdaptiveDriver(
        driver_id="adaptive_aggressive", name="Aggressive Adaptive",
        throttle_bias=1.10, aggressiveness=0.30,
        braking_consistency=0.70, corner_aggressiveness=0.9,
        steering_noise=0.04, fatigue_rate=0.03,
        braking_consistency=0.6,
    ),
    "adaptive_novice": AdaptiveDriver(
        driver_id="adaptive_novice", name="Novice Adaptive",
        throttle_bias=0.80, aggressiveness=0.15,
        braking_consistency=0.50, corner_aggressiveness=0.3,
        steering_noise=0.06, fatigue_rate=0.04,
        learning_rate=0.03, reaction_time=0.3,
    ),
    "adaptive_expert": AdaptiveDriver(
        driver_id="adaptive_expert", name="Expert Adaptive",
        throttle_bias=1.0, aggressiveness=0.15,
        braking_consistency=0.98, corner_aggressiveness=0.6,
        steering_noise=0.005, fatigue_rate=0.005,
        learning_rate=0.005, reaction_time=0.08,
    ),
}


def load_adaptive_drivers() -> dict[str, AdaptiveDriver]:
    """Return dict of all built-in adaptive drivers."""
    return dict(BUILTIN_ADAPTIVE_DRIVERS)


def create_adaptive_driver_from_profile(profile_driver, driver_id: str = None) -> AdaptiveDriver:
    """Convert a simple DriverProfile to an AdaptiveDriver."""
    if profile_driver is None:
        return AdaptiveDriver(driver_id=driver_id or "converted")

    return AdaptiveDriver(
        driver_id=driver_id or profile_driver.driver_id,
        name=getattr(profile_driver, "name", profile_driver.driver_id),
        throttle_bias=getattr(profile_driver, "throttle_bias", 1.0),
        aggressiveness=getattr(profile_driver, "aggressiveness", 0.2),
        steering_noise=getattr(profile_driver, "steering_noise", 0.02),
    )
