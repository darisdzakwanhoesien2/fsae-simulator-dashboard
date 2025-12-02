import random
import math

class IMUSimulator:
    def __init__(self):
        self.t = 0

    def step(self):
        self.t += 1
        ax = random.gauss(0, 0.2)
        ay = random.gauss(0, 0.2)
        yaw = math.sin(self.t / 50) * 3
        return {"ax": ax, "ay": ay, "yaw": yaw}
