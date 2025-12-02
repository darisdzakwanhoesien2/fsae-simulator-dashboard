# simulator/physics/simple/steering_yaw.py

def compute_yaw_rate(steering, speed_kmh):
    """
    steering: -1..1
    speed_kmh: speed
    returns yaw rate in deg/s (signed)
    """
    base_sensitivity = 30.0   # deg/s at reference speed
    ref_speed = 40.0
    sensitivity = base_sensitivity / max(speed_kmh / ref_speed, 1.0)
    yaw = steering * sensitivity
    return yaw
