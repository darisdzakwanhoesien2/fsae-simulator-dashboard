"""
Fuel load model.

Tracks fuel mass over a stint. Fuel consumption depends on throttle position.
Total vehicle mass = base_mass + fuel_mass → affects acceleration.

Fuel mass decreases over laps, improving performance.
"""

import numpy as np


class FuelModel:
    def __init__(
        self,
        initial_fuel_kg: float = 80.0,
        max_fuel_kg: float = 100.0,
        consumption_rate: float = 0.5,
    ):
        """
        Parameters
        ----------
        initial_fuel_kg : float
            Fuel mass at start of stint (kg).
        max_fuel_kg : float
            Maximum fuel capacity (kg).
        consumption_rate : float
            Base fuel consumption (kg/s) at full throttle.
        """
        self.fuel_mass = np.clip(initial_fuel_kg, 0.0, max_fuel_kg)
        self.max_fuel = max_fuel_kg
        self.consumption_rate = consumption_rate
        self.total_consumed_kg = 0.0

    def step(self, throttle: float, dt: float = 0.1):
        """
        Consume fuel based on throttle position.

        fuel_flow = consumption_rate * throttle * dt
        """
        flow = self.consumption_rate * throttle * dt
        consumed = min(flow, self.fuel_mass)
        self.fuel_mass -= consumed
        self.total_consumed_kg += consumed
        self.fuel_mass = max(0.0, self.fuel_mass)

    @property
    def fuel_load_kg(self) -> float:
        return self.fuel_mass

    @property
    def fuel_pct(self) -> float:
        if self.max_fuel <= 0:
            return 0.0
        return (self.fuel_mass / self.max_fuel) * 100.0

    @property
    def is_empty(self) -> bool:
        return self.fuel_mass <= 0.0

    def refuel(self, amount_kg: float = None):
        """Refuel to full or to specified amount."""
        if amount_kg is None:
            self.fuel_mass = self.max_fuel
        else:
            self.fuel_mass = np.clip(self.fuel_mass + amount_kg, 0.0, self.max_fuel)

    def get_state(self) -> dict:
        return {
            "fuel_kg": round(self.fuel_mass, 2),
            "fuel_pct": round(self.fuel_pct, 1),
            "total_consumed_kg": round(self.total_consumed_kg, 2),
        }
