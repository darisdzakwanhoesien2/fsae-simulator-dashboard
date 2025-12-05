# simulator/physics/simple/gps_simulator.py

import numpy as np
import math


class GPSMock:
    """
    Simple GPS simulator that moves along a list of (x, y) points.

    Guarantees:
    - Proper track index wrap: index = (index + 1) % len(track)
    - Lap counting increases only when we pass near the start line
    - Prevents double-counting by using a "cooldown" flag
    """

    def __init__(self, track_points, lap_threshold=2.0):
        """
        Args:
            track_points: list of (x, y) waypoints forming a loop
            lap_threshold: meters from start point to count a lap
        """
        self.track = np.array(track_points, dtype=float)
        self.N = len(self.track)

        self.index = 0
        self.lap = 0

        self.start_point = self.track[0]
        self.lap_threshold = lap_threshold

        # Used to avoid counting many laps while inside threshold
        self.passed_start_cooldown = False

    # --------------------------------------------------------------
    # Move forward along track by distance "d"
    # --------------------------------------------------------------
    def advance(self, d):
        """
        Move d meters along the track.

        Returns:
            (x, y)      : GPS coordinates
            track_index : int
            lap         : number of completed laps
        """
        if self.N < 2:
            return (self.track[self.index], self.index, self.lap)

        remaining = d

        while remaining > 0:
            p1 = self.track[self.index]
            p2 = self.track[(self.index + 1) % self.N]

            seg_len = np.linalg.norm(p2 - p1)

            if seg_len < 1e-6:
                self.index = (self.index + 1) % self.N
                continue

            if remaining < seg_len:
                # Interpolate within the segment
                t = remaining / seg_len
                x = p1[0] + t * (p2[0] - p1[0])
                y = p1[1] + t * (p2[1] - p1[1])
                remaining = 0
            else:
                # Move to next segment
                remaining -= seg_len
                self.index = (self.index + 1) % self.N
                x, y = p2[0], p2[1]

            # -----------------------------------------
            # L A P   D E T E C T I O N
            # -----------------------------------------
            dist_to_start = math.dist((x, y), self.start_point)

            if dist_to_start < self.lap_threshold:
                if not self.passed_start_cooldown:
                    self.lap += 1
                    self.passed_start_cooldown = True
            else:
                # Reset when far enough from start line
                self.passed_start_cooldown = False

        return (x, y), self.index, self.lap


# # simulator/physics/simple/gps_simulator.py
# import math

# class GPSMock:
#     def __init__(self, track_points):
#         self.track = track_points
#         self.n = len(track_points)
#         self.index = 0
#         self.pos = track_points[0] if self.n > 0 else (0.0, 0.0)
#         self.finished_laps = 0

#     def advance(self, distance_m):
#         while distance_m > 0 and self.n > 1:
#             x0, y0 = self.track[self.index]
#             x1, y1 = self.track[(self.index + 1) % self.n]
#             seg_len = math.hypot(x1 - x0, y1 - y0)
#             if seg_len == 0:
#                 self.index = (self.index + 1) % self.n
#                 continue

#             if distance_m >= seg_len:
#                 distance_m -= seg_len
#                 self.index = (self.index + 1) % self.n
#                 if self.index == 0:
#                     self.finished_laps += 1
#                 self.pos = self.track[self.index]
#             else:
#                 frac = distance_m / seg_len
#                 nx = x0 + frac * (x1 - x0)
#                 ny = y0 + frac * (y1 - y0)
#                 self.pos = (nx, ny)
#                 distance_m = 0

#         return self.pos, self.index, self.finished_laps
