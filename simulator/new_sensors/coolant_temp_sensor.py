# simulator/new_sensors/coolant_temp_sensor.py
from .noise_models import gaussian_noise, occasional_dropout

class CoolantTempSensor:
    def __init__(self, std=0.2, dropout_prob=0.0):
        self.std = std
        self.dropout_prob = dropout_prob

    def read(self, true_temp_c):
        if occasional_dropout(self.dropout_prob):
            return None
        noisy = true_temp_c + gaussian_noise(0, self.std)
        return round(noisy, 2)
