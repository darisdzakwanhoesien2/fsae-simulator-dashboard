# simulator/driver_profiles.py
import random

def simple_lap_profile(t, lap_time=20.0):
    """
    Returns throttle (0..1), brake (0..1), steering (-1..1)
    based on lap progress fraction.
    """
    p = (t % lap_time) / lap_time
    throttle = 0.8
    brake = 0.0
    steering = 0.0

    if 0.12 < p < 0.18:
        throttle = 0.25
        brake = 0.8
        steering = -0.9
    elif 0.32 < p < 0.38:
        throttle = 0.25
        brake = 0.6
        steering = 0.85
    elif 0.57 < p < 0.63:
        throttle = 0.2
        brake = 0.75
        steering = -0.8
    elif 0.82 < p < 0.88:
        throttle = 0.3
        brake = 0.65
        steering = 0.8
    else:
        throttle = max(0.3, 0.9 * (1.0 - 0.2 * random.random()))
        brake = 0.0
        steering = 0.02 * (random.random() - 0.5)

    return throttle, brake, steering
