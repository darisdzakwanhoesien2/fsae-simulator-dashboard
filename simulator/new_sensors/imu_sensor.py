# simulator/new_sensors/imu_sensor.py
from .noise_models import gaussian_noise, occasional_dropout

class IMUSensor:
    def __init__(self, accel_std=0.05, yaw_std=0.01, dropout_prob=0.0):
        self.accel_std = accel_std
        self.yaw_std = yaw_std
        self.dropout_prob = dropout_prob

    def read(self, true_ax, true_ay, true_yaw):
        if occasional_dropout(self.dropout_prob):
            return None
        ax = true_ax + gaussian_noise(0, self.accel_std)
        ay = true_ay + gaussian_noise(0, self.accel_std)
        yaw = true_yaw + gaussian_noise(0, self.yaw_std)
        return {"ax": round(ax, 3), "ay": round(ay, 3), "yaw": round(yaw, 3)}
