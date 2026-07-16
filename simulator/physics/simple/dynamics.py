# simulator/physics/simple/dynamics.py
from .vehicle_model import CAR

def compute_drag(v_ms, aero_model=None):
    rho = CAR["air_density"]
    Cd = CAR["drag_coeff"]
    A = CAR["frontal_area"]
    drag = 0.5 * rho * Cd * A * (v_ms ** 2)
    if aero_model is not None:
        drag = aero_model.compute_drag(v_ms)
    return drag

def compute_rolling_resistance(mass=None):
    m = mass if mass is not None else CAR["mass"]
    return CAR["rolling_resistance"] * m * 9.81

def compute_downforce(v_ms, aero_model=None):
    if aero_model is not None:
        return aero_model.compute_downforce(v_ms)
    return 0.0

def update_speed(v_ms, throttle, brake, dt=0.1, mass=None, aero_model=None):
    """
    v_ms: speed in m/s
    throttle: 0..1
    brake: 0..1
    mass: vehicle mass (kg) — varies with fuel load
    aero_model: optional AeroModel for downforce-inclusive drag
    returns new v_ms
    """
    m = mass if mass is not None else CAR["mass"]

    engine_force = CAR["max_engine_force"] * throttle
    brake_force = CAR["max_brake_force"] * brake
    drag = compute_drag(v_ms, aero_model)
    roll = compute_rolling_resistance(mass=m)

    net_F = engine_force - brake_force - drag - roll
    a = net_F / m
    v_new = max(0.0, v_ms + a * dt)
    return v_new
