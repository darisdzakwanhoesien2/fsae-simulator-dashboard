# simulator/physics/simple/gps_simulator.py
import math

class GPSMock:
    def __init__(self, track_points):
        self.track = track_points
        self.n = len(track_points)
        self.index = 0
        self.pos = track_points[0] if self.n > 0 else (0.0, 0.0)
        self.finished_laps = 0

    def advance(self, distance_m):
        while distance_m > 0 and self.n > 1:
            x0, y0 = self.track[self.index]
            x1, y1 = self.track[(self.index + 1) % self.n]
            seg_len = math.hypot(x1 - x0, y1 - y0)
            if seg_len == 0:
                self.index = (self.index + 1) % self.n
                continue

            if distance_m >= seg_len:
                distance_m -= seg_len
                self.index = (self.index + 1) % self.n
                if self.index == 0:
                    self.finished_laps += 1
                self.pos = self.track[self.index]
            else:
                frac = distance_m / seg_len
                nx = x0 + frac * (x1 - x0)
                ny = y0 + frac * (y1 - y0)
                self.pos = (nx, ny)
                distance_m = 0

        return self.pos, self.index, self.finished_laps
