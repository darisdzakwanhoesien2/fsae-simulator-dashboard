# FSAE Simulator - Technical Code Documentation

This document provides a detailed reference for all MATLAB functions and scripts within the modular FSAE simulation framework.

## 1. Root Directory

### `main.m`
- **Purpose**: The primary entry point for the lap time simulation.
- **Workflow**: 
    1. Loads configurations from `config/`.
    2. Processes track data from `track/`.
    3. Runs the Apex optimization, Forward pass (with pitch), and Backward pass solvers.
    4. Integrates results and calculates energy consumption.
    5. Generates performance plots and G-G diagrams.

---

## 2. Configuration Module (`config/`)

All files in this directory return a structure containing physical constants and maps.

- **`vehicle_params.m`**: Returns `veh` struct with mass, wheelbase, CG location, and pitch stiffness/damping.
- **`powertrain_params.m`**: Returns `motor` and battery parameters, including torque-RPM maps, thermal mass, and internal resistance.
- **`tire_params.m`**: Returns `tire` struct with an anonymous function `getPacejka(Fz)` that outputs Magic Formula coefficients.
- **`aero_params.m`**: Returns `aero` struct with `getAero(pitch)` anonymous function for attitude-sensitive $C_l$ and $C_d$.
- **`sim_options.m`**: Returns `opts` for integration steps (`ds`, `dt`) and velocity limits.

---

## 3. Track Module (`track/`)

- **`track_loader.m`**: 
    - *Input*: `track_name` (string, e.g., 'sample' or 'path/to/file.csv').
    - *Output*: `track_raw` struct.
    - *Logic*: Parses CSVs for X-Y or s-r data. Uses `curvature_from_xy` for raw coordinate files.
- **`track_preprocess.m`**:
    - *Input*: `track_raw`, `opts`.
    - *Output*: `track` (interpolated path).
    - *Logic*: Resamples the track to a constant distance step `ds`.
- **`curvature_from_xy.m`**:
    - *Input*: `x`, `y` vectors.
    - *Output*: Curvature $\kappa$ (1/R).
    - *Math*: Menger curvature (circumradius of three points).

---

## 4. Vehicle Physics Module (`vehicle/`)

- **`tire_model.m`**:
    - *Input*: `Fz` (N), `slip` (rad/-), `tire` struct.
    - *Output*: `Fy` or `Fx` (N).
    - *Logic*: Standard Pacejka Magic Formula.
- **`aero_model.m`**:
    - *Input*: `v`, `pitch`, `aero` struct.
    - *Output*: `forces` struct ($F_{down}, F_{drag}$).
- **`motor_model.m`**:
    - *Input*: `v`, `T_motor_prev`, `dt`, `powertrain`, `veh`.
    - *Output*: `T_out` (Nm), `T_motor_new`.
    - *Logic*: Interpolates torque map and integrates $I^2R$ thermal buildup/derating.
- **`battery_model.m`**:
    - *Input*: `P_motor` (W), `powertrain`.
    - *Output*: `P_batt`, `I_batt`.
    - *Logic*: Quadratic solution for internal resistance losses.
- **`force_limits.m`**:
    - *Input*: `v`, `ay`, `mode`, `veh`, `tire`, `aero`, `motor`, `T_motor`, `theta`.
    - *Output*: `ax` (max available acceleration/braking).
    - *Logic*: Coupled friction ellipse calculation.

---

## 5. Solver Module (`solver/`)

- **`lateral_speed_limit.m`**:
    - *Logic*: Iteratively solves for the maximum cornering speed at every track segment where $a_y$ required matches $a_y$ available.
- **`forward_pass.m`**:
    - *Logic*: Integrates velocity from $s=0$. Solves transient pitch ($\theta$) and motor temperature at each step.
- **`backward_pass.m`**:
    - *Logic*: Integrates braking limits backward from speed-constrained apexes to ensure feasible deceleration.
- **`lap_time_solver.m`**:
    - *Logic*: Combines pass results and performs $dt = ds/v$ integration for the final lap time.
- **`energy_solver.m`**:
    - *Logic*: Post-processes the velocity trace to calculate electrical power and SoC drop.

---

## 6. Analysis Module (`analysis/`)

- **`plot_results.m`**: Visualizes velocity, motor temp, and chassis pitch over distance.
- **`plot_gg_diagram.m`**: Overlays the simulation trace on the G-G-V friction envelopes.
- **`gear_ratio_sweep.m`**: Automation script that iterates over ratios to find the minimum lap time.
- **`sensitivity_analysis.m`**: Evaluates how changing mass or grip percentages shifts performance.
- **`update_progress.m`**: Console utility for the text-based progress bars.
