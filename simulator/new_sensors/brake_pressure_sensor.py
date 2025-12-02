# simulator/new_sensors/brake_pressure_sensor.py
from .noise_models import gaussian_noise, occasional_dropout

class BrakePressureSensor:
    def __init__(self, std=1.0, dropout_prob=0.0):
        self.std = std
        self.dropout_prob = dropout_prob

    def read(self, true_pressure_bar):
        if occasional_dropout(self.dropout_prob):
            return None
        noisy = true_pressure_bar + gaussian_noise(0, self.std)
        return round(max(0.0, noisy), 2)
