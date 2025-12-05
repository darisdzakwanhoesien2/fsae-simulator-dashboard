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

import pandas as pd
import os

import pandas as pd
import numpy as np
import math

def load_track_csv(path):
    df = pd.read_csv(path)
    return list(zip(df["x"], df["y"]))


def compute_track_length(points):
    """Compute total track length in meters."""
    length = 0.0
    for i in range(1, len(points)):
        x1, y1 = points[i-1]
        x2, y2 = points[i]
        length += math.dist((x1, y1), (x2, y2))
    return length


def estimate_turns(points, threshold=0.02):
    """
    Estimate number of turns using curvature sign changes.
    threshold = minimal curvature to count as a turn.
    """
    turns = 0
    prev_sign = 0
    
    for i in range(1, len(points)-1):
        x0, y0 = points[i-1]
        x1, y1 = points[i]
        x2, y2 = points[i+1]

        # curvature: cross product sign
        dx1, dy1 = x1 - x0, y1 - y0
        dx2, dy2 = x2 - x1, y2 - y1
        cross = dx1*dy2 - dy1*dx2
        
        curv = abs(cross)

        sign = 1 if cross > threshold else -1 if cross < -threshold else 0

        if sign != 0 and sign != prev_sign:
            turns += 1
        
        if sign != 0:
            prev_sign = sign

    return turns


def compute_difficulty(length, turns, curvature_score):
    """Produce a difficulty score 0–100."""
    score = (
        0.4 * min(turns / 20, 1.0) * 100 +
        0.3 * min(curvature_score / 0.1, 1.0) * 100 +
        0.3 * min(length / 1500, 1.0) * 100
    )
    return round(score, 2)

