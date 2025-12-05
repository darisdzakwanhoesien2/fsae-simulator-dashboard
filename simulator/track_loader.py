# simulator/track_loader.py
import pandas as pd
import numpy as np
import math
import os

# ============================================================
#  BASIC SHAPES (STRAIGHT + CORNERS)
# ============================================================

def add_straight(x, y, heading, length, step=1.0):
    pts = []
    n = max(1, int(length / step))
    for _ in range(n):
        x += math.cos(heading) * step
        y += math.sin(heading) * step
        pts.append((x, y))
    return pts, x, y, heading


def add_corner(x, y, heading, radius, angle, step_angle=0.01):
    pts = []
    n = max(1, int(abs(angle) / step_angle))
    sign = 1.0 if angle >= 0 else -1.0

    for _ in range(n):
        heading += step_angle * sign
        x += math.cos(heading) * radius * step_angle
        y += math.sin(heading) * radius * step_angle
        pts.append((x, y))

    return pts, x, y, heading


# ============================================================
#  SMOOTH LOOPING UTILITIES
# ============================================================

def close_loop(points, smooth_points=50):
    """Bezier-based loop closer used by generate_custom_track()."""
    p_start = np.array(points[0])
    p_end = np.array(points[-1])

    c1 = p_end + (p_start - p_end) * 0.3
    c2 = p_end + (p_start - p_end) * 0.6

    new_pts = []
    for t in np.linspace(0, 1, smooth_points):
        pt = (
            (1 - t) ** 3 * p_end
            + 3 * (1 - t) ** 2 * t * c1
            + 3 * (1 - t) * t ** 2 * c2
            + t ** 3 * p_start
        )
        new_pts.append((pt[0], pt[1]))

    return points + new_pts


def smooth_close_loop(pts, resolution=80):
    """Cleaner loop closure used by realistic / FIA generator."""
    pts = np.array(pts)
    start = pts[0]
    end = pts[-1]

    control1 = end + (start - end) * 0.33
    control2 = end + (start - end) * 0.66

    curve = []
    for t in np.linspace(0, 1, resolution):
        p = (
            (1 - t) ** 3 * end
            + 3 * (1 - t) ** 2 * t * control1
            + 3 * (1 - t) * t * t * control2
            + t ** 3 * start
        )
        curve.append((p[0], p[1]))

    return list(pts) + curve


# ============================================================
#  TURN SEQUENCE UTILITIES
# ============================================================

def generate_turn_sequence(n_left, n_right):
    seq = ["L"] * n_left + ["R"] * n_right
    np.random.shuffle(seq)
    return seq


# ============================================================
#  LEGACY CUSTOM TRACK (YOUR ORIGINAL, LOOP-FIXED)
# ============================================================

def generate_custom_track(
    n_left,
    n_right,
    seg_length,
    radius_range,
    points_per_turn,
    max_extent=150,
):
    pts = []
    heading = 0.0
    x, y = 0.0, 0.0

    turns = ["L"] * n_left + ["R"] * n_right
    np.random.shuffle(turns)

    for tdir in turns:
        radius = np.random.uniform(*radius_range)
        angle = seg_length / radius
        if tdir == "R":
            angle = -angle

        angles = np.linspace(0, angle, points_per_turn)
        for a in angles:
            heading += a
            x += math.cos(heading)
            y += math.sin(heading)

            x = np.clip(x, -max_extent, max_extent)
            y = np.clip(y, -max_extent, max_extent)

            pts.append((x, y))

    # --- recenter to origin ---
    xs, ys = zip(*pts)
    xs = np.array(xs) - np.mean(xs)
    ys = np.array(ys) - np.mean(ys)
    centered = list(zip(xs, ys))

    # --- tighten final part towards start ---
    last_vec = np.array(centered[-1]) - np.array(centered[0])
    if np.linalg.norm(last_vec) > 20:
        N = len(centered)
        start_idx = int(N * 0.85)
        for i in range(start_idx, N):
            r = (i - start_idx) / max(N - start_idx, 1)
            newp = (
                centered[i][0] - last_vec[0] * r * 0.7,
                centered[i][1] - last_vec[1] * r * 0.7,
            )
            centered[i] = newp

    return close_loop(centered, smooth_points=120)


# ============================================================
#  REALISTIC CIRCUIT GENERATOR (MID-LEVEL)
# ============================================================

# def generate_realistic_track(
#     n_left=4,
#     n_right=4,
#     min_straight=15,
#     max_straight=40,
#     min_radius=12,
#     max_radius=60,):
#     x = y = 0.0
#     heading = 0.0
#     pts = []

#     turns = ["L"] * n_left + ["R"] * n_right
#     np.random.shuffle(turns)

#     for turn in turns:
#         # straight
#         L = np.random.uniform(min_straight, max_straight)
#         segment, x, y, heading = add_straight(x, y, heading, L)
#         pts += segment

#         # corner
#         radius = np.random.uniform(min_radius, max_radius)
#         angle = np.random.uniform(math.radians(20), math.radians(100))
#         if turn == "R":
#             angle = -angle

#         segment, x, y, heading = add_corner(x, y, heading, radius, angle)
#         pts += segment

#     # final straight
#     segment, x, y, heading = add_straight(x, y, heading, 30)
#     pts += segment

#     return smooth_close_loop(pts)

def generate_realistic_track(
    n_left=4,
    n_right=4,
    min_straight=15,
    max_straight=40,
    min_radius=12,
    max_radius=60,):
    x = y = 0.0
    heading = 0.0
    pts = []

    turns = ["L"] * n_left + ["R"] * n_right
    np.random.shuffle(turns)

    for turn in turns:
        # straight
        L = np.random.uniform(min_straight, max_straight)
        segment, x, y, heading = add_straight(x, y, heading, L)
        pts += segment

        # corner
        radius = np.random.uniform(min_radius, max_radius)
        angle = np.random.uniform(math.radians(20), math.radians(100))
        if turn == "R":
            angle = -angle

        segment, x, y, heading = add_corner(x, y, heading, radius, angle)
        pts += segment

    # final straight
    segment, x, y, heading = add_straight(x, y, heading, 30)
    pts += segment

    return smooth_close_loop(pts)

# ============================================================
#  FIA / ADVANCED TRACK GENERATOR
# ============================================================

def _add_s_curve(x, y, heading, radius, angle, spacing):
    """S-curve: left then right (or vice versa)."""
    pts = []

    # first corner
    seg, x, y, heading = add_corner(x, y, heading, radius, angle)
    pts += seg

    # small straight
    seg, x, y, heading = add_straight(x, y, heading, spacing)
    pts += seg

    # opposite corner
    seg, x, y, heading = add_corner(x, y, heading, radius, -angle)
    pts += seg

    return pts, x, y, heading


def _add_chicane(x, y, heading, radius, angle, spacing):
    """Tighter S-curve (chicane)."""
    return _add_s_curve(x, y, heading, radius, angle, spacing)


def _add_hairpin(x, y, heading, radius):
    """Hairpin: 140–180 degree tight corner."""
    pts = []
    angle = np.random.uniform(math.radians(140), math.radians(180))
    # choose random direction
    if np.random.rand() < 0.5:
        angle = -angle
    seg, x, y, heading = add_corner(x, y, heading, radius, angle)
    pts += seg
    return pts, x, y, heading


def generate_fia_style_track(
    n_corners=6,
    n_s_curves=2,
    n_chicanes=1,
    n_hairpins=1,
    min_straight=25,
    max_straight=80,
    min_radius=15,
    max_radius=80,
):
    """
    Advanced track:
    - mix of normal corners, S-curves, chicanes, hairpins
    - returns list[(x,y)]
    """
    x = y = 0.0
    heading = 0.0
    pts = []

    building_blocks = []

    # normal corners
    for _ in range(n_corners):
        building_blocks.append(("CORNER", np.random.choice(["L", "R"])))
    # S-curves
    for _ in range(n_s_curves):
        building_blocks.append(("S", None))
    # chicanes
    for _ in range(n_chicanes):
        building_blocks.append(("CHICANE", None))
    # hairpins
    for _ in range(n_hairpins):
        building_blocks.append(("HAIRPIN", None))

    np.random.shuffle(building_blocks)

    for kind, direction in building_blocks:
        # pre-straight before each complex
        L = np.random.uniform(min_straight * 0.6, max_straight)
        seg, x, y, heading = add_straight(x, y, heading, L)
        pts += seg

        if kind == "CORNER":
            radius = np.random.uniform(min_radius, max_radius)
            angle = np.random.uniform(math.radians(25), math.radians(90))
            if direction == "R":
                angle = -angle
            seg, x, y, heading = add_corner(x, y, heading, radius, angle)
            pts += seg

        elif kind == "S":
            radius = np.random.uniform(min_radius, max_radius)
            angle = np.random.uniform(math.radians(20), math.radians(45))
            spacing = np.random.uniform(10, 25)
            seg, x, y, heading = _add_s_curve(x, y, heading, radius, angle, spacing)
            pts += seg

        elif kind == "CHICANE":
            radius = np.random.uniform(min_radius * 0.6, min_radius * 1.2)
            angle = np.random.uniform(math.radians(30), math.radians(60))
            spacing = np.random.uniform(5, 15)
            seg, x, y, heading = _add_chicane(x, y, heading, radius, angle, spacing)
            pts += seg

        elif kind == "HAIRPIN":
            radius = np.random.uniform(min_radius * 0.5, min_radius * 1.2)
            seg, x, y, heading = _add_hairpin(x, y, heading, radius)
            pts += seg

    # final straight and loop close
    seg, x, y, heading = add_straight(x, y, heading, min_straight)
    pts += seg

    return smooth_close_loop(pts)


# ============================================================
#  GENERIC TRACK UTILITIES
# ============================================================

def generate_oval_track(n_points=200, a=80.0, b=40.0):
    pts = []
    for i in range(n_points):
        theta = 2 * math.pi * i / n_points
        x = a * math.cos(theta)
        y = b * math.sin(theta)
        pts.append((x, y))
    return pts


def load_track_csv(path):
    df = pd.read_csv(path)
    return list(zip(df["x"], df["y"]))


def compute_track_length(points):
    length = 0.0
    for i in range(1, len(points)):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        length += math.dist((x1, y1), (x2, y2))
    return length


def estimate_turns(points, threshold=0.02):
    turns = 0
    prev_sign = 0

    for i in range(1, len(points) - 1):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        dx1, dy1 = x1 - x0, y1 - y0
        dx2, dy2 = x2 - x1, y2 - y1
        cross = dx1 * dy2 - dy1 * dx2

        sign = 1 if cross > threshold else -1 if cross < -threshold else 0
        if sign != 0 and sign != prev_sign:
            turns += 1
        if sign != 0:
            prev_sign = sign

    return turns


def compute_difficulty(length, turns, curvature_score):
    score = (
        0.4 * min(turns / 20, 1.0) * 100
        + 0.3 * min(curvature_score / 0.1, 1.0) * 100
        + 0.3 * min(length / 1500, 1.0) * 100
    )
    return round(score, 2)



# def generate_custom_track(n_left=6, n_right=6,
#                           seg_length=20.0,
#                           radius_range=(30, 60),
#                           points_per_turn=40):
#     """
#     Generate a parametric track with given numbers of left + right turns.

#     Returns:
#         track: list of (x, y)
#     """

#     turn_seq = generate_turn_sequence(n_left, n_right)

#     # Starting pose
#     x, y = 0.0, 0.0
#     heading = 0.0  # radians

#     points = [(x, y)]

#     for turn in turn_seq:
#         # random turn radius
#         radius = np.random.uniform(*radius_range)

#         # fixed arc angle (e.g. 45–90 degrees)
#         arc_angle = np.deg2rad(np.random.uniform(30, 90))

#         # left = +angle, right = -angle
#         direction = 1 if turn == "L" else -1

#         # simulate points along the arc
#         for i in range(points_per_turn):
#             dtheta = direction * (arc_angle / points_per_turn)
#             heading += dtheta

#             # arc step
#             dx = np.cos(heading) * (seg_length / points_per_turn)
#             dy = np.sin(heading) * (seg_length / points_per_turn)

#             x += dx
#             y += dy
#             points.append((x, y))

#     return points
