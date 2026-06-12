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

### Phase 3: Transient Dynamics and Power Management
The latest update introduces time-dependent constraints and high-fidelity chassis response:
- **EMRAX Thermal Model:** Implemented a lumped-parameter thermal network ($dT/dt$) for the motor. It tracks heat buildup based on copper losses ($I^2R$) and dissipates heat to ambient (Liu et al., 2020).
- **Thermal Derating:** Integrated logic that automatically scales down motor torque as temperature approaches critical limits ($100^\circ C - 130^\circ C$). This allows for the simulation of endurance events where performance is limited by cooling capacity rather than peak power.
- **Transient Chassis Pitch:** Replaced the "instantaneous" weight transfer with a second-order differential equation model ($I, C, K$). This captures the **settling time** of the suspension, allowing for more realistic load fluctuations during rapid transitions (Siegler et al., 2000).
- **Transient Load Transfer:** Vertical loads ($F_z$) now account for suspension damping forces, providing a more accurate input to the Pacejka tire model during the first fractions of a second of an event.

## 3. Impact of Improvements

| Feature | Impact on Accuracy | Impact on Simulation Speed |
| :--- | :--- | :--- |
| **Aero Downforce** | High (Critical for high-speed aero cars) | Low |
| **Load Sensitivity** | Medium (Refines peak grip estimation) | Low |
| **Pacejka Model** | Very High (Captures realistic tire limits) | Medium |
| **Rotational Dynamics** | High (Captures wheel spin and traction loss) | Medium |

---
*Date of Update: June 12, 2026*
