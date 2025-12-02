# simulator/physics/simple/dynamics.py
from .vehicle_model import CAR

def compute_drag(v_ms):
    rho = CAR["air_density"]
    Cd = CAR["drag_coeff"]
    A = CAR["frontal_area"]
    return 0.5 * rho * Cd * A * (v_ms ** 2)

def compute_rolling_resistance():
    return CAR["rolling_resistance"] * CAR["mass"] * 9.81

def update_speed(v_ms, throttle, brake, dt=0.1):
    """
    v_ms: speed in m/s
    throttle: 0..1
    brake: 0..1
    returns new v_ms
    """
    engine_force = CAR["max_engine_force"] * throttle
    brake_force = CAR["max_brake_force"] * brake
    drag = compute_drag(v_ms)
    roll = compute_rolling_resistance()

    net_F = engine_force - brake_force - drag - roll
    a = net_F / CAR["mass"]
    v_new = max(0.0, v_ms + a * dt)
    return v_new
