import random
import math

class WheelSpeedSimulator:
    def __init__(self):
        self.t = 0

    def step(self):
        base_speed = max(0, math.sin(self.t / 15) * 60 + 40)
        noise = random.uniform(-2, 2)
        self.t += 1
        return round(base_speed + noise, 1)
