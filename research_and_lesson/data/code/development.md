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

### Phase 2: Integration into Quasi-Steady State LTS
The simulation has evolved from single-event models to a full-track integration:
- **G-G-V Envelope Generation:** Integrated the Phase 1 tire and aero models into a 3D acceleration capability map. The longitudinal acceleration ($a_x$) now respects the "friction ellipse," reducing traction/braking potential as lateral demand ($a_y$) increases (Bianco et al., 2018).
- **Apex Optimization:** The simulator automatically calculates the physical limit ($V_{max}$) for any given track curvature ($r$) by iterating through the high-fidelity force balance.
- **Path-Following Simulation:** Implemented a **Forward-Backward Integration** scheme. The "Forward Pass" integrates acceleration from the start/apex points, while the "Backward Pass" integrates braking limits from the next entry point, ensuring optimal transition and lap time (Costa & Bortolussi, 2016).
- **Consolidated Architecture:** Created `LapTimeSimulator.m` as the top-level orchestrator for full-lap performance analysis.

## 3. Impact of Improvements

| Feature | Impact on Accuracy | Impact on Simulation Speed |
| :--- | :--- | :--- |
| **Aero Downforce** | High (Critical for high-speed aero cars) | Low |
| **Load Sensitivity** | Medium (Refines peak grip estimation) | Low |
| **Pacejka Model** | Very High (Captures realistic tire limits) | Medium |
| **Rotational Dynamics** | High (Captures wheel spin and traction loss) | Medium |

---
*Date of Update: June 12, 2026*
