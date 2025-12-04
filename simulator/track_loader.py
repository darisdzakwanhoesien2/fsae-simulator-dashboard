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

# simulator/track_loader.py

import numpy as np

def generate_turn_sequence(n_left, n_right):
    """
    Creates a turn sequence like:
    [L, R, L, L, R, ...] with random mixing
    """
    seq = ["L"] * n_left + ["R"] * n_right
    np.random.shuffle(seq)
    return seq


def generate_custom_track(n_left=6, n_right=6,
                          seg_length=20.0,
                          radius_range=(30, 60),
                          points_per_turn=40):
    """
    Generate a parametric track with given numbers of left + right turns.

    Returns:
        track: list of (x, y)
    """

    turn_seq = generate_turn_sequence(n_left, n_right)

    # Starting pose
    x, y = 0.0, 0.0
    heading = 0.0  # radians

    points = [(x, y)]

    for turn in turn_seq:
        # random turn radius
        radius = np.random.uniform(*radius_range)

        # fixed arc angle (e.g. 45–90 degrees)
        arc_angle = np.deg2rad(np.random.uniform(30, 90))

        # left = +angle, right = -angle
        direction = 1 if turn == "L" else -1

        # simulate points along the arc
        for i in range(points_per_turn):
            dtheta = direction * (arc_angle / points_per_turn)
            heading += dtheta

            # arc step
            dx = np.cos(heading) * (seg_length / points_per_turn)
            dy = np.sin(heading) * (seg_length / points_per_turn)

            x += dx
            y += dy
            points.append((x, y))

    return points
