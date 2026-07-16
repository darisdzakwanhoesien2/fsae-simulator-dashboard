"""
Aerodynamic model including downforce.

Extends the simple drag-only model with:
  - Downforce proportional to v^2
  - Increased cornering grip from downforce
  - Drag and downforce tradeoffs
  - Optional aero balance (front/rear distribution)
"""

import numpy as np
from .vehicle_model import CAR


class AeroModel:
    def __init__(
        self,
        downforce_coeff: float = 1.2,
        aero_balance: float = 0.5,
        drag_coeff: float = None,
        frontal_area: float = None,
        air_density: float = None,
    ):
        """
        Parameters
        ----------
        downforce_coeff : float
            Downforce coefficient (Cl * A equivalent).
        aero_balance : float
            Front aero balance (0..1). 0.5 = balanced.
        drag_coeff : float, optional
            Override CAR drag_coeff.
        frontal_area : float, optional
            Override CAR frontal_area.
        air_density : float, optional
            Override air density.
        """
        self.downforce_coeff = downforce_coeff
        self.aero_balance = aero_balance
        self._Cd = drag_coeff if drag_coeff is not None else CAR["drag_coeff"]
        self._A = frontal_area if frontal_area is not None else CAR["frontal_area"]
        self._rho = air_density if air_density is not None else CAR["air_density"]

    def compute_drag(self, v_ms: float) -> float:
        """Aerodynamic drag force (N)."""
        return 0.5 * self._rho * self._Cd * self._A * (v_ms ** 2)

    def compute_downforce(self, v_ms: float) -> float:
        """Downforce (N) — positive = pressing car to ground."""
        return 0.5 * self._rho * self.downforce_coeff * self._A * (v_ms ** 2)

    def compute_lift_drag_ratio(self) -> float:
        """Lift-to-drag ratio (downforce / drag in coefficient terms)."""
        if self._Cd <= 0:
            return float("inf")
        return self.downforce_coeff / self._Cd

    def effective_grip_multiplier(self, v_ms: float, mass_kg: float) -> float:
        """
        Effective grip increase from downforce.

        Without downforce: max_lateral_force = mu * m * g
        With downforce:    max_lateral_force = mu * (m * g + downforce)

        Returns multiplier (>1.0 at speed).
        """
        weight = mass_kg * 9.81
        downforce = self.compute_downforce(v_ms)
        if weight <= 0:
            return 1.0
        return (weight + downforce) / weight

    def max_corner_speed(self, radius: float, mu: float, mass_kg: float) -> float:
        """
        Maximum speed (m/s) through a corner of given radius,
        accounting for downforce-enhanced grip.

        Forces:
            centripetal = m * v^2 / r
            friction = mu * (m * g + downforce(v))

        At limit:
            m * v^2 / r = mu * (m * g + 0.5 * rho * Cl * A * v^2)
            v^2 * (m/r - 0.5 * mu * rho * Cl * A) = mu * m * g
            v = sqrt(mu * m * g / (m/r - 0.5 * mu * rho * Cl * A))
        """
        if radius <= 0 or mu <= 0:
            return 0.0

        term = mass_kg / radius - 0.5 * mu * self._rho * self.downforce_coeff * self._A
        if term <= 0:
            return float("inf")

        v_sq = mu * mass_kg * 9.81 / term
        if v_sq <= 0:
            return 0.0
        return np.sqrt(v_sq)

    def get_state(self) -> dict:
        return {
            "downforce_coeff": self.downforce_coeff,
            "drag_coeff": self._Cd,
            "aero_balance": self.aero_balance,
            "lift_drag_ratio": round(self.compute_lift_drag_ratio(), 2),
        }
