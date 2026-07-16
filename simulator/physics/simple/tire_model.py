"""
Tire degradation and thermal model.

Tracks per-corner tire state (4 corners simplified to single model):
  - Compound (soft, medium, hard, intermediate, wet)
  - Wear (0..1)
  - Surface temperature
  - Core temperature
  - Graining / blistering flags

Grip degrades with wear. Graining occurs on large surface-core temp deltas.
Blistering occurs at very high surface temperatures.
"""

import numpy as np

COMPOUNDS = {
    "soft":       {"base_grip": 1.10, "wear_rate": 0.012, "opt_temp": 85, "temp_window": 15},
    "medium":     {"base_grip": 1.00, "wear_rate": 0.008, "opt_temp": 90, "temp_window": 20},
    "hard":       {"base_grip": 0.90, "wear_rate": 0.005, "opt_temp": 95, "temp_window": 25},
    "intermediate": {"base_grip": 0.85, "wear_rate": 0.006, "opt_temp": 70, "temp_window": 20},
    "wet":        {"base_grip": 0.70, "wear_rate": 0.004, "opt_temp": 60, "temp_window": 15},
}


class TireModel:
    def __init__(
        self,
        compound: str = "medium",
        initial_wear: float = 0.0,
        initial_surface_temp: float = 40.0,
        initial_core_temp: float = 40.0,
        ambient_temp: float = 25.0,
        grip_drop_per_wear: float = 0.6,
    ):
        if compound not in COMPOUNDS:
            raise ValueError(f"Unknown compound: {compound}. Choose from {list(COMPOUNDS.keys())}")

        self.compound = compound
        self.compound_data = COMPOUNDS[compound]
        self.wear = np.clip(initial_wear, 0.0, 1.0)
        self.surface_temp = initial_surface_temp
        self.core_temp = initial_core_temp
        self.ambient_temp = ambient_temp
        self.grip_drop_per_wear = grip_drop_per_wear
        self.graining = False
        self.blistering = False
        self.total_distance_km = 0.0

    @property
    def grip_coefficient(self) -> float:
        """Current grip multiplier (1.0 = nominal)."""
        base = self.compound_data["base_grip"]
        wear_factor = 1.0 - self.grip_drop_per_wear * self.wear
        temp_factor = self._temperature_grip_factor()
        return base * wear_factor * temp_factor

    def _temperature_grip_factor(self) -> float:
        """Grip falls off when outside optimal temperature window."""
        opt = self.compound_data["opt_temp"]
        window = self.compound_data["temp_window"]
        diff = abs(self.surface_temp - opt)
        if diff <= window:
            return 1.0
        falloff = (diff - window) / 40.0
        return max(0.6, 1.0 - falloff)

    def step(
        self,
        speed_kmh: float,
        throttle: float,
        brake: float,
        lateral_accel: float,
        dt: float = 0.1,
    ):
        """
        Advance tire model by one timestep.

        Updates:
          - Wear from distance + slip (throttle/brake/lateral)
          - Surface temperature from friction + cooling
          - Core temperature from surface conduction
          - Graining / blistering flags
        """
        distance_km = speed_kmh * dt / 3600.0
        self.total_distance_km += distance_km

        # --- Wear accumulation ---
        slip_factor = (abs(throttle) + abs(brake) + abs(lateral_accel) / 10.0)
        wear_increment = self.compound_data["wear_rate"] * distance_km * (1.0 + slip_factor)
        self.wear = np.clip(self.wear + wear_increment, 0.0, 1.0)

        # --- Surface temperature ---
        friction_heat = slip_factor * speed_kmh * 0.01
        ambient_cooling = (self.ambient_temp - self.surface_temp) * 0.02
        conduction_to_core = (self.core_temp - self.surface_temp) * 0.05
        self.surface_temp += (friction_heat + ambient_cooling + conduction_to_core) * dt * 10
        self.surface_temp = np.clip(self.surface_temp, self.ambient_temp - 5, 140.0)

        # --- Core temperature ---
        conduction_from_surface = (self.surface_temp - self.core_temp) * 0.02
        self.core_temp += conduction_from_surface * dt * 10
        self.core_temp = np.clip(self.core_temp, self.ambient_temp - 5, 120.0)

        # --- Graining (large temp delta between surface and core) ---
        temp_delta = abs(self.surface_temp - self.core_temp)
        self.graining = temp_delta > 30.0

        # --- Blistering (very high surface temp) ---
        self.blistering = self.surface_temp > 120.0

    def reset(self, compound: str = None, initial_wear: float = 0.0):
        """Reset tire state (e.g., for a new set of tires)."""
        if compound:
            self.compound = compound
            self.compound_data = COMPOUNDS[compound]
        self.wear = np.clip(initial_wear, 0.0, 1.0)
        self.surface_temp = 40.0
        self.core_temp = 40.0
        self.graining = False
        self.blistering = False
        self.total_distance_km = 0.0

    def get_state(self) -> dict:
        return {
            "compound": self.compound,
            "wear_pct": round(self.wear * 100, 1),
            "surface_temp_c": round(self.surface_temp, 1),
            "core_temp_c": round(self.core_temp, 1),
            "grip": round(self.grip_coefficient, 3),
            "graining": self.graining,
            "blistering": self.blistering,
            "total_distance_km": round(self.total_distance_km, 2),
        }
