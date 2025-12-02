# simulator/new_sensors/wheel_speed_sensor.py
from .noise_models import gaussian_noise, occasional_dropout

class WheelSpeedSensor:
    def __init__(self, std=0.5, dropout_prob=0.0):
        self.std = std
        self.dropout_prob = dropout_prob

    def read(self, true_speed_kmh):
        if occasional_dropout(self.dropout_prob):
            return None
        noisy = true_speed_kmh + gaussian_noise(0, self.std)
        return round(max(0.0, noisy), 2)
