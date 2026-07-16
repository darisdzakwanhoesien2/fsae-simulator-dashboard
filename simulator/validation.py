"""
Comprehensive validation framework for comparing simulated vs real telemetry.

Metrics:
  - Lap time MAE
  - Sector time MAE (3 sectors)
  - Speed RMSE (overall + per sector)
  - Acceleration RMSE
  - Braking point detection and error
  - Corner entry / apex / exit speed error
  - Racing line deviation
  - Steering RMSE
  - Correlation metrics (Pearson, Spearman)
  - Statistical confidence intervals (bootstrapped)
"""

import numpy as np
import math

try:
    from scipy.stats import pearsonr, spearmanr, ttest_rel
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# ---------------------------------------------------------------------------
#  SPEED METRICS
# ---------------------------------------------------------------------------

def compute_speed_rmse(sim_speeds: np.ndarray, real_speeds: np.ndarray) -> float:
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return float("nan")
    return float(np.sqrt(np.mean((sim_speeds[:n] - real_speeds[:n]) ** 2)))


def compute_speed_mae(sim_speeds: np.ndarray, real_speeds: np.ndarray) -> float:
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return float("nan")
    return float(np.mean(np.abs(sim_speeds[:n] - real_speeds[:n])))


def compute_speed_max_error(sim_speeds: np.ndarray, real_speeds: np.ndarray) -> float:
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return float("nan")
    return float(np.max(np.abs(sim_speeds[:n] - real_speeds[:n])))


def compute_speed_mape(sim_speeds: np.ndarray, real_speeds: np.ndarray) -> float:
    """Mean Absolute Percentage Error."""
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return float("nan")
    mask = real_speeds[:n] > 1.0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((sim_speeds[:n][mask] - real_speeds[:n][mask]) / real_speeds[:n][mask])))


# ---------------------------------------------------------------------------
#  SECTOR METRICS
# ---------------------------------------------------------------------------

def compute_sector_errors(sim_speeds: np.ndarray, real_speeds: np.ndarray, n_sectors: int = 3) -> dict:
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return {}
    sector_size = n // n_sectors
    errors = {}
    for s in range(n_sectors):
        start = s * sector_size
        end = start + sector_size if s < n_sectors - 1 else n
        sector_mae = float(np.mean(np.abs(sim_speeds[start:end] - real_speeds[start:end])))
        sector_rmse = float(np.sqrt(np.mean((sim_speeds[start:end] - real_speeds[start:end]) ** 2)))
        errors[f"sector_{s+1}_mae"] = sector_mae
        errors[f"sector_{s+1}_rmse"] = sector_rmse
    return errors


# ---------------------------------------------------------------------------
#  ACCELERATION METRICS
# ---------------------------------------------------------------------------

def compute_acceleration(speeds_kmh: np.ndarray, dt: float = 0.1) -> np.ndarray:
    """Compute longitudinal acceleration from speed trace."""
    speeds_ms = speeds_kmh / 3.6
    accel = np.diff(speeds_ms) / dt
    return np.concatenate([accel, [0.0]])


def compute_acceleration_rmse(sim_speeds: np.ndarray, real_speeds: np.ndarray, dt: float = 0.1) -> float:
    n = min(len(sim_speeds), len(real_speeds))
    if n < 2:
        return float("nan")
    sim_accel = compute_acceleration(sim_speeds[:n], dt)
    real_accel = compute_acceleration(real_speeds[:n], dt)
    return float(np.sqrt(np.mean((sim_accel - real_accel) ** 2)))


# ---------------------------------------------------------------------------
#  BRAKING POINT DETECTION
# ---------------------------------------------------------------------------

def detect_braking_points(brake_trace: np.ndarray, threshold: float = 0.1) -> list:
    """Detect braking event start indices (where brake rises above threshold)."""
    points = []
    in_brake = False
    for i in range(len(brake_trace)):
        if brake_trace[i] > threshold and not in_brake:
            points.append(i)
            in_brake = True
        elif brake_trace[i] <= threshold:
            in_brake = False
    return points


def compute_braking_point_error(
    sim_brakes: np.ndarray, real_brakes: np.ndarray, threshold: float = 0.1
) -> dict:
    """Compare braking point locations between sim and real."""
    sim_points = detect_braking_points(sim_brakes, threshold)
    real_points = detect_braking_points(real_brakes, threshold)

    n = min(len(sim_points), len(real_points))
    if n == 0:
        return {"braking_point_count_error": abs(len(sim_points) - len(real_points))}

    errors = np.array(sim_points[:n]) - np.array(real_points[:n])
    return {
        "braking_point_mae": float(np.mean(np.abs(errors))),
        "braking_point_rmse": float(np.sqrt(np.mean(errors ** 2))),
        "braking_point_max_error": float(np.max(np.abs(errors))),
        "sim_braking_events": len(sim_points),
        "real_braking_events": len(real_points),
    }


# ---------------------------------------------------------------------------
#  CORNER SPEED METRICS
# ---------------------------------------------------------------------------

def detect_corners(yaw_deg: np.ndarray, threshold: float = 5.0, min_gap: int = 10) -> list:
    """Detect corner regions from yaw trace."""
    above = np.abs(yaw_deg) > threshold
    corners = []
    in_corner = False
    start = 0
    for i in range(len(above)):
        if above[i] and not in_corner:
            start = i
            in_corner = True
        elif not above[i] and in_corner:
            if i - start >= min_gap:
                corners.append((start, i))
            in_corner = False
    if in_corner and len(above) - start >= min_gap:
        corners.append((start, len(above) - 1))
    return corners


def compute_corner_speed_errors(
    sim_speeds: np.ndarray, real_speeds: np.ndarray,
    sim_yaw: np.ndarray, real_yaw: np.ndarray,
) -> dict:
    """Compare corner entry / apex / exit speeds."""
    # Use real yaw to define corners
    corners = detect_corners(real_yaw)
    if not corners:
        return {}

    entry_errors = []
    apex_errors = []
    exit_errors = []

    for start, end in corners:
        if end >= min(len(sim_speeds), len(real_speeds)):
            continue
        mid = (start + end) // 2

        entry_errors.append(abs(sim_speeds[start] - real_speeds[start]))
        apex_errors.append(abs(sim_speeds[mid] - real_speeds[mid]))
        exit_errors.append(abs(sim_speeds[end] - real_speeds[end]))

    if not entry_errors:
        return {}

    return {
        "corner_entry_speed_mae": float(np.mean(entry_errors)),
        "corner_apex_speed_mae": float(np.mean(apex_errors)),
        "corner_exit_speed_mae": float(np.mean(exit_errors)),
        "corners_detected": len(corners),
    }


# ---------------------------------------------------------------------------
#  RACING LINE DEVIATION
# ---------------------------------------------------------------------------

def compute_racing_line_deviation(
    sim_gps: np.ndarray, real_gps: np.ndarray
) -> dict:
    """
    Compute lateral deviation between simulated and real racing lines.

    Parameters
    ----------
    sim_gps : np.ndarray of shape (N, 2) — (x, y) positions
    real_gps : np.ndarray of shape (M, 2)

    Returns
    -------
    dict with mean, max, rmse deviation.
    """
    n = min(len(sim_gps), len(real_gps))
    if n == 0:
        return {}

    sim = sim_gps[:n]
    real = real_gps[:n]
    distances = np.sqrt(np.sum((sim - real) ** 2, axis=1))

    return {
        "line_deviation_mean": float(np.mean(distances)),
        "line_deviation_max": float(np.max(distances)),
        "line_deviation_rmse": float(np.sqrt(np.mean(distances ** 2))),
    }


# ---------------------------------------------------------------------------
#  STEERING METRICS
# ---------------------------------------------------------------------------

def compute_steering_rmse(sim_steering: np.ndarray, real_steering: np.ndarray) -> float:
    n = min(len(sim_steering), len(real_steering))
    if n == 0:
        return float("nan")
    return float(np.sqrt(np.mean((sim_steering[:n] - real_steering[:n]) ** 2)))


# ---------------------------------------------------------------------------
#  CORRELATION METRICS
# ---------------------------------------------------------------------------

def compute_correlation(sim_speeds: np.ndarray, real_speeds: np.ndarray) -> dict:
    n = min(len(sim_speeds), len(real_speeds))
    if n < 2:
        return {}

    result = {}
    if SCIPY_AVAILABLE:
        pearson_r, pearson_p = pearsonr(sim_speeds[:n], real_speeds[:n])
        spearman_r, spearman_p = spearmanr(sim_speeds[:n], real_speeds[:n])
        result["pearson_r"] = round(float(pearson_r), 4)
        result["pearson_p"] = float(pearson_p)
        result["spearman_r"] = round(float(spearman_r), 4)
        result["spearman_p"] = float(spearman_p)
    else:
        result["pearson_r"] = round(float(np.corrcoef(sim_speeds[:n], real_speeds[:n])[0, 1]), 4)

    return result


# ---------------------------------------------------------------------------
#  CONFIDENCE INTERVALS (Bootstrap)
# ---------------------------------------------------------------------------

def bootstrap_ci(errors: np.ndarray, n_bootstrap: int = 1000, ci: float = 0.95) -> dict:
    """
    Compute confidence intervals for error metrics via bootstrapping.

    Parameters
    ----------
    errors : np.ndarray
        Per-sample errors.
    n_bootstrap : int
        Number of bootstrap samples.
    ci : float
        Confidence level (e.g., 0.95).

    Returns
    -------
    dict with lower, upper, mean, std.
    """
    if len(errors) < 2:
        return {}

    means = np.zeros(n_bootstrap)
    n = len(errors)
    for i in range(n_bootstrap):
        sample = np.random.choice(errors, size=n, replace=True)
        means[i] = np.mean(sample)

    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(means, alpha * 100))
    upper = float(np.percentile(means, (1 - alpha) * 100))

    return {
        "ci_lower": round(lower, 3),
        "ci_upper": round(upper, 3),
        "ci_mean": round(float(np.mean(means)), 3),
        "ci_std": round(float(np.std(means)), 3),
        "ci_level": ci,
        "n_bootstrap": n_bootstrap,
    }


# ---------------------------------------------------------------------------
#  MASTER VALIDATION
# ---------------------------------------------------------------------------

def validate_lap(
    sim_packets: list,
    real_packets: list,
    dt: float = 0.1,
    compute_cis: bool = False,
) -> dict:
    """
    Comprehensive validation of a simulated lap against real telemetry.

    Parameters
    ----------
    sim_packets : list[dict]
        Simulated session log packets.
    real_packets : list[dict]
        Real telemetry packets (same format).
    dt : float
        Simulation timestep.
    compute_cis : bool
        If True, compute bootstrap confidence intervals.

    Returns
    -------
    dict with all validation metrics.
    """
    # Extract traces
    sim_speed = np.array([p["true"]["speed_kmh"] for p in sim_packets])
    real_speed = np.array([p["true"]["speed_kmh"] for p in real_packets])
    sim_brake = np.array([p["true"]["brake_cmd"] for p in sim_packets if "true" in p])
    real_brake = np.array([p["true"]["brake_cmd"] for p in real_packets if "true" in p])
    sim_yaw = np.array([p["true"]["yaw_deg"] for p in sim_packets if "true" in p])
    real_yaw = np.array([p["true"]["yaw_deg"] for p in real_packets if "true" in p])

    # GPS for line deviation
    sim_gps = np.array([(p.get("gps", {}) or {}).get("x", 0) for p in sim_packets])
    sim_gps_y = np.array([(p.get("gps", {}) or {}).get("y", 0) for p in sim_packets])
    real_gps = np.array([(p.get("gps", {}) or {}).get("x", 0) for p in real_packets])
    real_gps_y = np.array([(p.get("gps", {}) or {}).get("y", 0) for p in real_packets])

    sim_gps_xy = np.column_stack([sim_gps, sim_gps_y])
    real_gps_xy = np.column_stack([real_gps, real_gps_y])

    # Steering
    sim_steering = np.array([
        p.get("true", {}).get("steering", 0) for p in sim_packets
    ])
    real_steering = np.array([
        p.get("true", {}).get("steering", 0) for p in real_packets
    ])

    n = min(len(sim_speed), len(real_speed))
    sim_speed = sim_speed[:n]
    real_speed = real_speed[:n]

    # Speed metrics
    metrics = {
        "mae_kmh": compute_speed_mae(sim_speed, real_speed),
        "rmse_kmh": compute_speed_rmse(sim_speed, real_speed),
        "max_error_kmh": compute_speed_max_error(sim_speed, real_speed),
        "mape_pct": compute_speed_mape(sim_speed, real_speed) * 100 if not np.isnan(compute_speed_mape(sim_speed, real_speed)) else None,
        "n_samples": n,
    }

    # Sector errors
    metrics.update(compute_sector_errors(sim_speed, real_speed))

    # Acceleration RMSE
    metrics["acceleration_rmse_ms2"] = compute_acceleration_rmse(sim_speed, real_speed, dt)

    # Braking points
    metrics.update(compute_braking_point_error(sim_brake, real_brake))

    # Corner speed errors
    metrics.update(compute_corner_speed_errors(sim_speed, real_speed, sim_yaw, real_yaw))

    # Racing line deviation
    metrics.update(compute_racing_line_deviation(sim_gps_xy, real_gps_xy))

    # Steering RMSE
    metrics["steering_rmse"] = compute_steering_rmse(sim_steering, real_steering)

    # Correlation
    metrics.update(compute_correlation(sim_speed, real_speed))

    # Confidence intervals (bootstrap on speed errors)
    if compute_cis:
        errors = np.abs(sim_speed - real_speed)
        metrics["mae_ci"] = bootstrap_ci(errors)

    return metrics


def validate_multi_lap(
    sim_packets: list,
    real_packets: list,
    dt: float = 0.1,
) -> dict:
    """Run validation per lap and aggregate results."""
    sim_laps = {}
    real_laps = {}

    for p in sim_packets:
        ln = p.get("lap", 1)
        sim_laps.setdefault(ln, []).append(p)
    for p in real_packets:
        ln = p.get("lap", 1)
        real_laps.setdefault(ln, []).append(p)

    per_lap = {}
    all_metrics = []

    for ln in set(sim_laps) & set(real_laps):
        result = validate_lap(sim_laps[ln], real_laps[ln], dt)
        per_lap[ln] = result
        all_metrics.append(result)

    if not all_metrics:
        return {"per_lap": {}, "aggregate": {}}

    # Aggregate across laps
    agg = {}
    for key in all_metrics[0]:
        if isinstance(all_metrics[0][key], (int, float)):
            values = [m[key] for m in all_metrics if isinstance(m.get(key), (int, float))]
            if values:
                agg[f"mean_{key}"] = float(np.mean(values))
                agg[f"std_{key}"] = float(np.std(values))
                agg[f"min_{key}"] = float(np.min(values))
                agg[f"max_{key}"] = float(np.max(values))

    return {"per_lap": per_lap, "aggregate": agg}


def print_validation_report(metrics: dict, title: str = "Validation Report"):
    """Pretty-print validation results."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

    if "aggregate" in metrics:
        print("\n  Aggregate (multi-lap):")
        agg = metrics["aggregate"]
        for key in sorted(agg):
            print(f"    {key}: {agg[key]:.4f}")
        print(f"\n  Per-lap:")
        for ln, lap_m in metrics.get("per_lap", {}).items():
            print(f"    Lap {ln}: MAE={lap_m.get('mae_kmh', 'N/A'):.2f} km/h, "
                  f"RMSE={lap_m.get('rmse_kmh', 'N/A'):.2f} km/h, "
                  f"R={lap_m.get('pearson_r', 'N/A')}")
    else:
        for key in sorted(metrics):
            val = metrics[key]
            if isinstance(val, dict):
                print(f"\n  {key}:")
                for k, v in val.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {val:.4f}" if isinstance(val, float) else f"  {key}: {val}")

    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Validate simulation against real telemetry")
    parser.add_argument("--sim-file", type=str, required=True, help="Simulated session log")
    parser.add_argument("--real-file", type=str, required=True, help="Real telemetry session log")
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--ci", action="store_true", help="Compute confidence intervals")
    parser.add_argument("--output", type=str, default=None, help="Save report as JSON")

    args = parser.parse_args()

    from calibrate_from_f1 import load_lap_file

    sim = load_lap_file(args.sim_file)
    real = load_lap_file(args.real_file)

    metrics = validate_lap(sim, real, dt=args.dt, compute_cis=args.ci)
    print_validation_report(metrics, f"Validation: {args.sim_file} vs {args.real_file}")

    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"Report saved to {args.output}")


if __name__ == "__main__":
    cli()
