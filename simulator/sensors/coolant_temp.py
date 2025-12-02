import random
import math

class CoolantTempSimulator:
    def __init__(self, base=60):
        self.temp = base
        self.t = 0

    def step(self):
        # engine load = oscillating + random behavior
        load = math.sin(self.t / 10) * 0.5 + 0.6
        noise = random.uniform(-0.3, 0.3)

        self.temp += load * 0.5 + noise

        # Radiator cooling effect
        if self.temp > 70:
            self.temp -= 0.2

        self.t += 1
        return round(self.temp, 2)
