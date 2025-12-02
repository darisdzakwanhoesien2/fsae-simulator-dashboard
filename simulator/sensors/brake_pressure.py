import random

class BrakePressureSimulator:
    def __init__(self):
        self.press = 0

    def step(self):
        if random.random() < 0.05:
            self.press = random.uniform(40, 90)
        else:
            self.press *= 0.85  # decay

        return round(self.press, 2)
