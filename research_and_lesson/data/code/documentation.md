# FSAE Simulator Dashboard - Modular MATLAB Framework

This document provides an overview of the modular MATLAB framework developed for high-fidelity FSAE lap time simulation.

## 1. Modular Architecture

The simulation is organized into logical directories to separate configuration, physics, and solvers.

### 1.1 Directory Structure
- `config/`: Contains functions that return parameter structs (Vehicle, Powertrain, Tire, Aero, Sim Options).
- `vehicle/`: Implements core physical models (Tire Magic Formula, Aero Maps, Motor Thermal Dynamics, Force Limits).
- `track/`: Handles track data loading and preprocessing (interpolation, curvature calculation).
- `solver/`: The core simulation engine (Lateral Speed Limit, Forward Pass, Backward Pass, Lap Time Solver).
- `analysis/`: Unified plotting and optimization tools.

### 1.2 The Simulation Pipeline (`main.m`)
The `main.m` script orchestrates the full simulation flow:
1. **Load Configurations**: Calls functions in `config/` to build the vehicle model.
2. **Track Preprocessing**: Loads raw track data and interpolates it to a defined distance step.
3. **Lateral Speed Limit**: Calculates the maximum cornering speed at every point on the track based on lateral grip and downforce.
4. **Forward Pass**: Integrates acceleration from the start, considering powertrain limits, traction, and **transient pitch dynamics**.
5. **Backward Pass**: Enforces braking limits by integrating backward from corner apexes or the lap end.
6. **Integration**: Combines the velocity profiles to calculate the final lap time and results.

---

## 2. Core Physical Models

### 2.1 Tire Model (`vehicle/tire_model.m`)
Uses the **Pacejka Magic Formula** ($y = D \sin(C \arctan(Bx ...))$).
- **Load Sensitivity**: Parameters $B, C, D, E$ are dynamic functions of normal load $F_z$.
- **Friction Ellipse**: Longitudinal and lateral capacities are coupled via a friction ellipse in `force_limits.m`.

### 2.2 Aerodynamics (`vehicle/aero_model.m`)
- **Attitude Sensitivity**: Downforce ($C_l$) and Drag ($C_d$) are mapped against the chassis pitch angle ($\theta$).
- **Dynamic Forces**: Calculates $F_{down}$ and $F_{drag}$ based on velocity and air density.

### 2.3 Motor & Thermal Dynamics (`vehicle/motor_model.m`)
- **EMRAX Map**: Torque is interpolated from a 2D RPM/Torque map.
- **Thermal Derating**: Tracks motor temperature based on current-squared losses and ambient cooling. Torque is automatically derated if temperature limits are exceeded.

### 2.4 Transient Chassis Pitch
The forward pass solver integrates a second-order pitch model:
$$I_{pitch} \ddot{\theta} + C_{pitch} \dot{\theta} + K_{pitch} \theta = M_{pitch}$$
Where $M_{pitch}$ is the longitudinal moment due to acceleration. This allows the simulation to capture the "squat" effect during acceleration and its impact on aero/traction.

---

## 3. Specialized Event Models

### 3.1 Skidpad (`SimpleSkippadModel.m`)
A specialized script refactored to use the modular components. It iterates through speeds to find the maximum steady-state cornering velocity on a 9m radius circle, accounting for lateral load transfer.

### 3.2 Acceleration (`StraightLineAccelerationModel.m`)
*(Pending Refactoring)* Simulates the 75m dash. The logic is currently being integrated into the modular solver to allow for unified "Acceleration" events using the same physics as the lap time simulator.
