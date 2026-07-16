"""
Physics calibration pipeline — tune FSAE simulator parameters using real F1 telemetry.

Strategy:
  1. Load real lap telemetry (FastF1 or OpenF1)
  2. Run the FSAE physics model with candidate parameters
  3. Optimize parameters to minimize error vs real telemetry
  4. Save calibrated parameters back to config

Usage:
    python simulator/calibrate_from_f1.py --lap-file data/logs/f1_VER_*.json --train
    python simulator/calibrate_from_f1.py --lap-file data/logs/f1_VER_*.json --calibrate
"""

import os
import sys
import json
import copy
import math
import yaml
import numpy as np

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

# Project physics
from simulator.physics.simple.dynamics import update_speed, compute_drag
from simulator.physics.simple.vehicle_model import CAR as DEFAULT_CAR
from simulator.physics.simple.steering_yaw import compute_yaw_rate
from simulator.physics.simple.thermal import update_coolant_temp

# Config
from utils.config_loader import load_yaml

CAR_CONFIG_PATH = os.path.join(ROOT, "configs", "car_simple.yaml")

OPTIM_AVAILABLE = False
try:
    from scipy.optimize import minimize
    OPTIM_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
#  DATA LOADING
# ---------------------------------------------------------------------------

def load_lap_file(path: str):
    """Load a project session log JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def extract_lap_packets(packets: list, lap_number: int = 1):
    """Extract packets for a specific lap from a session log."""
    return [p for p in packets if p["lap"] == lap_number]


def extract_speed_trace(packets: list):
    """Extract the speed trace from packets."""
    return np.array([p["true"]["speed_kmh"] for p in packets])


def extract_throttle_brake_trace(packets: list):
    """Extract throttle and brake traces."""
    throttles = np.array([p["true"]["throttle"] for p in packets])
    brakes = np.array([p["true"]["brake_cmd"] for p in packets])
    return throttles, brakes


# ---------------------------------------------------------------------------
#  SIMULATOR WRAPPER
# ---------------------------------------------------------------------------

def run_simulated_lap(
    car_params: dict,
    throttle_trace: np.ndarray,
    brake_trace: np.ndarray,
    dt: float = 0.1,
    initial_speed: float = 0.0,
):
    """
    Run the FSAE physics model with given throttle/brake traces.

    Parameters
    ----------
    car_params : dict
        Keys: mass, drag_coeff, frontal_area, air_density, rolling_resistance,
              max_engine_force, max_brake_force.
    throttle_trace : np.ndarray
    brake_trace : np.ndarray
    dt : float
    initial_speed : float

    Returns
    -------
    speeds_kmh : np.ndarray
    """
    n = len(throttle_trace)
    speeds = np.zeros(n)
    v_ms = initial_speed

    for i in range(n):
        engine_force = car_params["max_engine_force"] * throttle_trace[i]
        brake_force = car_params["max_brake_force"] * brake_trace[i]
        drag = 0.5 * car_params["air_density"] * car_params["drag_coeff"] * car_params["frontal_area"] * (v_ms ** 2)
        roll = car_params["rolling_resistance"] * car_params["mass"] * 9.81

        net_F = engine_force - brake_force - drag - roll
        a = net_F / car_params["mass"]
        v_ms = max(0.0, v_ms + a * dt)

        speeds[i] = v_ms * 3.6

    return speeds


# ---------------------------------------------------------------------------
#  ERROR METRICS
# ---------------------------------------------------------------------------

def compute_errors(sim_speeds: np.ndarray, real_speeds: np.ndarray):
    """Compute MAE, RMSE, and peak error between two speed traces."""
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return {"mae": float("inf"), "rmse": float("inf"), "max_error": float("inf")}

    sim = sim_speeds[:n]
    real = real_speeds[:n]

    mae = float(np.mean(np.abs(sim - real)))
    rmse = float(np.sqrt(np.mean((sim - real) ** 2)))
    max_err = float(np.max(np.abs(sim - real)))

    return {"mae": mae, "rmse": rmse, "max_error": max_err}


def compute_sector_errors(sim_speeds: np.ndarray, real_speeds: np.ndarray, n_sectors: int = 3):
    """Compute per-sector MAE."""
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return {}
    sector_size = n // n_sectors
    errors = {}
    for s in range(n_sectors):
        start = s * sector_size
        end = start + sector_size if s < n_sectors - 1 else n
        errors[f"sector_{s+1}_mae"] = float(np.mean(np.abs(sim_speeds[start:end] - real_speeds[start:end])))
    return errors


# ---------------------------------------------------------------------------
#  PARAMETER OPTIMIZATION
# ---------------------------------------------------------------------------

def _objective(
    params: np.ndarray,
    param_names: list,
    base_params: dict,
    throttle_trace: np.ndarray,
    brake_trace: np.ndarray,
    real_speeds: np.ndarray,
    dt: float,
) -> float:
    """Objective function for optimization: minimize RMSE."""
    car_params = copy.deepcopy(base_params)
    for name, value in zip(param_names, params):
        car_params[name] = value

    sim_speeds = run_simulated_lap(car_params, throttle_trace, brake_trace, dt)
    n = min(len(sim_speeds), len(real_speeds))
    if n == 0:
        return 1e10
    return float(np.sqrt(np.mean((sim_speeds[:n] - real_speeds[:n]) ** 2)))


def calibrate_parameters(
    packets: list,
    car_params: dict = None,
    dt: float = 0.1,
    optimize: bool = True,
):
    """
    Calibrate car parameters against real telemetry data.

    Parameters
    ----------
    packets : list[dict]
        Session log packets with throttle, brake, speed traces.
    car_params : dict, optional
        Base car parameters to start from. Defaults to car_simple.yaml values.
    dt : float
    optimize : bool
        If True, run scipy optimization. If False, just evaluate current params.

    Returns
    -------
    dict with:
      - calibrated_params: best-fit parameters
      - errors: error metrics
      - per_lap_errors: dict of lap_number -> errors
    """
    if car_params is None:
        car_params = load_yaml(CAR_CONFIG_PATH)

    # Group by lap
    laps = {}
    for p in packets:
        ln = p["lap"]
        if ln not in laps:
            laps[ln] = []
        laps[ln].append(p)

    # Evaluate per-lap
    per_lap_errors = {}
    all_throttles = []
    all_brakes = []
    all_speeds = []

    for ln, lap_packets in sorted(laps.items()):
        throttles, brakes = extract_throttle_brake_trace(lap_packets)
        speeds = extract_speed_trace(lap_packets)

        # Run sim with current params
        sim_speeds = run_simulated_lap(car_params, throttles, brakes, dt)
        errors = compute_errors(sim_speeds, speeds)
        errors.update(compute_sector_errors(sim_speeds, speeds))
        per_lap_errors[ln] = errors

        all_throttles.extend(throttles)
        all_brakes.extend(brakes)
        all_speeds.extend(speeds)

    all_throttles = np.array(all_throttles)
    all_brakes = np.array(all_brakes)
    all_speeds = np.array(all_speeds)

    print("\n[Calibration] Baseline errors (before optimization):")
    avg_mae = np.mean([e["mae"] for e in per_lap_errors.values()])
    avg_rmse = np.mean([e["rmse"] for e in per_lap_errors.values()])
    print(f"  Avg MAE:  {avg_mae:.2f} km/h")
    print(f"  Avg RMSE: {avg_rmse:.2f} km/h")

    best_params = dict(car_params)

    if optimize and OPTIM_AVAILABLE:
        print("\n[Calibration] Running scipy optimization...")

        # Parameter bounds and scaling
        param_config = [
            ("mass", 150, 400),
            ("drag_coeff", 0.3, 1.5),
            ("frontal_area", 0.5, 2.0),
            ("rolling_resistance", 0.005, 0.04),
            ("max_engine_force", 3000, 12000),
            ("max_brake_force", 500, 3000),
        ]

        x0 = []
        bounds = []
        param_names = []
        for name, lo, hi in param_config:
            param_names.append(name)
            x0.append(car_params.get(name, (lo + hi) / 2))
            bounds.append((lo, hi))

        result = minimize(
            _objective,
            x0=x0,
            args=(param_names, car_params, all_throttles, all_brakes, all_speeds, dt),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 200, "ftol": 1e-6},
        )

        if result.success:
            for name, value in zip(param_names, result.x):
                best_params[name] = float(value)

            # Re-evaluate
            per_lap_errors = {}
            for ln, lap_packets in sorted(laps.items()):
                throttles, brakes = extract_throttle_brake_trace(lap_packets)
                speeds = extract_speed_trace(lap_packets)
                sim_speeds = run_simulated_lap(best_params, throttles, brakes, dt)
                errors = compute_errors(sim_speeds, speeds)
                errors.update(compute_sector_errors(sim_speeds, speeds))
                per_lap_errors[ln] = errors

            new_avg_mae = np.mean([e["mae"] for e in per_lap_errors.values()])
            new_avg_rmse = np.mean([e["rmse"] for e in per_lap_errors.values()])
            print(f"  Optimized Avg MAE:  {new_avg_mae:.2f} km/h (was {avg_mae:.2f})")
            print(f"  Optimized Avg RMSE: {new_avg_rmse:.2f} km/h (was {avg_rmse:.2f})")
        else:
            print(f"  Optimization failed: {result.message}")

    return {
        "calibrated_params": best_params,
        "errors": {"mae": avg_mae, "rmse": avg_rmse},
        "per_lap_errors": per_lap_errors,
    }


# ---------------------------------------------------------------------------
#  SAVE CALIBRATED PARAMS
# ---------------------------------------------------------------------------

def save_calibrated_params(params: dict, output_path: str = None):
    """Save calibrated parameters to a YAML config file."""
    if output_path is None:
        output_path = CAR_CONFIG_PATH.replace(".yaml", "_calibrated.yaml")

    with open(output_path, "w") as f:
        yaml.dump(params, f, default_flow_style=False)

    print(f"Calibrated parameters saved to {output_path}")
    return output_path


def apply_calibrated_params(params: dict):
    """Apply calibrated parameters to the live car config."""
    output_path = CAR_CONFIG_PATH
    with open(output_path, "w") as f:
        yaml.dump(params, f, default_flow_style=False)
    print(f"Applied calibrated parameters to {output_path}")


# ---------------------------------------------------------------------------
#  VALIDATION REPORT
# ---------------------------------------------------------------------------

def generate_validation_report(packets: list, calibrated_params: dict, dt: float = 0.1):
    """Generate a detailed validation report comparing real vs simulated."""
    import pandas as pd

    laps = {}
    for p in packets:
        ln = p["lap"]
        if ln not in laps:
            laps[ln] = []
        laps[ln].append(p)

    rows = []
    for ln, lap_packets in sorted(laps.items()):
        throttles, brakes = extract_throttle_brake_trace(lap_packets)
        real_speeds = extract_speed_trace(lap_packets)
        sim_speeds = run_simulated_lap(calibrated_params, throttles, brakes, dt)
        errors = compute_errors(sim_speeds, real_speeds)
        errors.update(compute_sector_errors(sim_speeds, real_speeds))
        errors["lap"] = ln
        errors["real_mean_speed"] = float(np.mean(real_speeds))
        errors["sim_mean_speed"] = float(np.mean(sim_speeds))
        rows.append(errors)

    report = pd.DataFrame(rows)
    report = report.set_index("lap")
    return report


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Calibrate physics model from real F1 telemetry")

    parser.add_argument("--lap-file", type=str, required=True, help="Path to session log JSON")
    parser.add_argument("--calibrate", action="store_true", help="Run optimization")
    parser.add_argument("--eval", action="store_true", help="Evaluate baseline only")
    parser.add_argument("--save", type=str, default=None, help="Save calibrated params to path")
    parser.add_argument("--apply", action="store_true", help="Apply params to car_simple.yaml")
    parser.add_argument("--report", action="store_true", help="Print validation report")
    parser.add_argument("--dt", type=float, default=0.1)

    args = parser.parse_args()

    if not os.path.exists(args.lap_file):
        print(f"File not found: {args.lap_file}")
        return

    packets = load_lap_file(args.lap_file)
    print(f"Loaded {len(packets)} packets")

    car_params = load_yaml(CAR_CONFIG_PATH)
    print(f"Base params: {car_params}")

    result = calibrate_parameters(
        packets, car_params=car_params, dt=args.dt,
        optimize=args.calibrate,
    )

    print("\nCalibrated params:")
    for k, v in result["calibrated_params"].items():
        print(f"  {k}: {v:.4f}")

    if args.save:
        save_calibrated_params(result["calibrated_params"], args.save)

    if args.apply:
        apply_calibrated_params(result["calibrated_params"])

    if args.report:
        report = generate_validation_report(packets, result["calibrated_params"], args.dt)
        print("\nValidation Report:")
        print(report.to_string())


if __name__ == "__main__":
    cli()
