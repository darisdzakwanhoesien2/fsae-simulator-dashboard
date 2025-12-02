# simulator/track_loader.py
import math

def generate_oval_track(n_points=200, a=80.0, b=40.0):
    pts = []
    for i in range(n_points):
        theta = 2 * math.pi * i / n_points
        x = a * math.cos(theta)
        y = b * math.sin(theta)
        pts.append((x, y))
    return pts
