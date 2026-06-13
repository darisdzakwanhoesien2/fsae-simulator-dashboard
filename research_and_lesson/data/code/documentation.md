# FSAE Simulator Dashboard - Modular MATLAB Framework

This document provides a comprehensive overview of the modular MATLAB framework developed for high-fidelity Formula SAE lap time simulation.

## 1. Modular Architecture

The simulation is organized into logical directories to separate configuration, physics, and solvers.

### 1.1 Directory Structure
- **`config/`**: Contains parameter functions (Vehicle, Powertrain, Tire, Aero, Sim Options).
- **`vehicle/`**: Physical models (Tire Magic Formula, Aero Maps, Motor Thermal, Battery, Force Limits).
- **`track/`**: Track data loading (CSV/Sample) and preprocessing (interpolation, curvature).
- **`solver/`**: The core simulation engine (Apex Optimization, Forward/Backward Passes, Energy integration).
- **`analysis/`**: Unified plotting, optimization sweeps, and sensitivity tools.

### 1.2 User Feedback & Progress
Long-running simulation tasks now provide real-time console feedback using a text-based progress bar:
`[==========----------] 50% | Forward Pass`
This allows for monitoring progress during complex apex optimizations or high-resolution endurance laps.

---

## 2. Core Physical Models

### 2.1 Tire Model (`vehicle/tire_model.m`)
Uses the **Pacejka Magic Formula** with dynamic load sensitivity.
- **Combined Slip**: Longitudinal and lateral capacities are coupled via a friction ellipse in `force_limits.m`.
- **Load Sensitivity**: Friction coefficients scale with normal load $F_z$.

### 2.2 Aerodynamics (`vehicle/aero_model.m`)
- **Attitude Sensitivity**: Downforce ($C_l$) and Drag ($C_d$) are mapped against the chassis pitch angle ($\theta$).
- **Dynamic Calculation**: Forces scale with the square of velocity and air density.

### 2.3 Powertrain & Thermal (`vehicle/motor_model.m`)
- **Thermal Derating**: Tracks motor temperature based on winding losses ($I^2R$). Torque is automatically derated when the motor exceeds $100^\circ C$.
- **Battery Model**: Calculates battery power and voltage drop using an internal resistance model ($V = V_{oc} - I \cdot R_{int}$).

### 2.4 Transient Chassis Pitch
The solver integrates a second-order pitch model in real-time during the forward pass:
$$I_{pitch} \ddot{\theta} + C_{pitch} \dot{\theta} + K_{pitch} \theta = M_{chassis}$$
This captures the impact of acceleration-induced weight transfer on aerodynamic performance and traction.

---

## 3. Engineering & Analysis Tools

### 3.1 G-G Diagram (`analysis/plot_gg_diagram.m`)
Visualizes the vehicle's available grip envelopes (G-G-V) at different speeds and overlays the actual simulation trace. This is critical for identifying whether the car is powertrain-limited or grip-limited in specific track sectors.

### 3.2 Gear Ratio Optimization (`analysis/gear_ratio_sweep.m`)
An automated sweep tool that simulates entire laps over a range of gear ratios to identify the setup that minimizes lap time while respecting motor thermal limits.

### 3.3 Sensitivity Analysis (`analysis/sensitivity_analysis.m`)
Evaluates the impact of engineering changes (e.g., $+10\%$ mass or $-5\%$ tire grip) on final lap performance, helping the team prioritize development efforts.

---

## 4. Specialized Event Models

### 4.1 Skidpad (`SimpleSkippadModel.m`)
Simulates the steady-state cornering event. It leverages the modular `tire_model` and `aero_model` to calculate the maximum achievable velocity on a constant radius, accounting for lateral load transfer.

### 4.2 Acceleration (`StraightLineAccelerationModel.m`)
Simulates the 75m dash. It uses the unified `forward_pass` solver to account for transient pitch "squat," thermal derating, and traction limits under maximum longitudinal demand.

---

## 5. Usage & Standards
- **Units**: All calculations strictly use SI units (meters, seconds, kilograms, Newtons, radians).
- **Standardization**: All results and track vectors are oriented as **column vectors** to ensure robust matrix operations and prevent concatenation errors.
- **Entry Point**: Execute `main.m` for a standard simulation run with all modules active.
