# Development of FSAE Vehicle Dynamics Models

This document tracks the evolution and improvements made to the vehicle dynamics simulation models in the FSAE Simulator Dashboard project.

## 1. Evolution of the Skidpad Model

### Initial Phase: Point Mass Balance
The first iteration focused on a simple balance between required lateral force ($F = mv^2/r$) and available friction ($F = \mu \cdot m \cdot g$). This ignored aerodynamics and weight transfer.

### Second Phase: Aerodynamics
Aerodynamic downforce ($C_l$) and drag ($C_d$) were added. This highlighted how speed increases vertical load, thereby increasing available traction, while drag reduces the net force.

### Final Improved Version: Load Transfer & Sensitivity
The current model incorporates:
- **Lateral Load Transfer:** Based on CG height and track width, the model now distinguishes between inside and outside tire loads.
- **Load Sensitivity:** Recognizes that the tire friction coefficient ($\mu$) is not constant but decreases as vertical load increases.
- **Improved Code Structure:** Constants are grouped at the top, and the simulation loop is optimized for clarity.

## 2. Evolution of the Acceleration Model

### Initial Phase: Constant Grip Limit
Earlier versions used a static friction limit to determine the maximum acceleration. It assumed the motor torque could always be transferred to the road up to a fixed $\mu \cdot F_z$.

### Second Phase: Motor Maps & Simple Weight Transfer
Introduced torque-RPM maps for the EMRAX motor and basic longitudinal weight transfer to the rear axle, acknowledging that acceleration shifts load backward.

### Final High-Fidelity Version: Component Modeling (Phase 1)
The latest implementation realizes the "High-Fidelity Component Modeling" roadmap:
- **Load-Sensitive Pacejka Coefficients:** The $B, C, D,$ and $E$ factors are no longer constants. They now scale dynamically with vertical load ($F_z$), capturing the non-linear "tire sensitivity" reported in literature (Miranda et al., 2021).
- **Attitude-Sensitive Aerodynamics (Aero Maps):** Static $C_l$ and $C_d$ coefficients have been replaced with state-dependent functions. These simulate how vehicle pitch (squat/dive) affects downforce and drag, capturing porpoising and attitude-driven performance gains (Zhang et al., 2022).
- **Combined-Slip Foundation:** The models now include the framework for combined dynamics, using longitudinal demand to reduce lateral capacity (friction ellipse logic) in the skidpad simulation.
- **Dynamic Pitch/Roll Estimation:** Suspensions stiffness ($K_{pitch}, K_{roll}$) is used to estimate the vehicle's attitude in real-time during the simulation.

## 3. Impact of Improvements

| Feature | Impact on Accuracy | Impact on Simulation Speed |
| :--- | :--- | :--- |
| **Aero Downforce** | High (Critical for high-speed aero cars) | Low |
| **Load Sensitivity** | Medium (Refines peak grip estimation) | Low |
| **Pacejka Model** | Very High (Captures realistic tire limits) | Medium |
| **Rotational Dynamics** | High (Captures wheel spin and traction loss) | Medium |

---
*Date of Update: June 12, 2026*
