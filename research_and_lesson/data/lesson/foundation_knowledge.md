# Foundational Knowledge for FSAE Vehicle Dynamics

This document lists the essential mathematical and physical principles required to understand and build longitudinal vehicle dynamics models, as extracted from the lesson materials.

## 1. Mathematics

### Algebra and Units
- **Unit Consistency:** All calculations must use consistent SI units:
    - Force: Newtons (N)
    - Mass: Kilograms (kg)
    - Velocity: Meters per second (m/s)
    - Acceleration: Meters per second squared (m/s²)
- **Linear vs. Nonlinear:** Distinguishing between linear terms (e.g., $m \cdot a$) and nonlinear terms (e.g., aerodynamic drag $\propto v^2$).

### Trigonometry
- **Road Slope Effects:** Using $\sin(\beta)$ and $\cos(\beta)$ to resolve gravity components along and perpendicular to the road surface.

### Calculus and Modeling
- **Differential Equations:** Modeling the rate of change of velocity ($dv/dt$) to describe vehicle acceleration.
- **Reduced-Order Modeling:** Techniques for simplifying complex physical systems into low-order state-space models suitable for real-time simulation.

### Statistics and Validation
- **Performance Metrics:** Using Root Mean Square Error (RMSE) and Mean Absolute Percentage Error (MAPE) to quantify model accuracy.
- **Parameter Identifiability:** Understanding which parameters can be reliably estimated from available sensor data.

## 2. Physics

### Mechanics
- **Newton's Second Law:** The fundamental governing equation $\sum F = m \cdot a$.
- **Kinematics vs. Dynamics:** 
    - *Kinematics:* Focuses on motion (position, velocity) without considering forces.
    - *Dynamics:* Focuses on the forces that cause motion.

### Force Balance
- **Traction/Braking Force:** The primary driving and stopping forces.
- **Aerodynamic Drag:** Resistance from air, increasing with the square of velocity.
- **Rolling Resistance:** Resistance due to tire deformation and road interaction.
- **Grade Force:** The component of gravity acting along the slope (assisting or resisting motion).

### Tire and Road Interaction
- **Slip Ratio:** The difference between wheel speed and vehicle speed, crucial for determining available traction.
- **Tire-Road Friction ($\mu$):** The relationship between normal load and longitudinal force.
- **Pacejka Magic Formula:** A standard semi-empirical model for tire forces.
- **Load Transfer:** The shift of vertical load between axles (longitudinal) or wheels (lateral) during acceleration, braking, or cornering.

### Powertrain Dynamics
- **Torque Conversion:** How engine/motor torque is converted to tire force via the gearbox and driveline.
- **Inertia and Delay:** Representing powertrain response using first-order dynamic approximations to capture time delays and rotational inertia.

## 3. Systems Engineering
- **Model Fidelity vs. Cost:** Balancing physical realism with the computational efficiency required for real-time applications.
- **Uncertainty Management:** Accounting for noise, changing road conditions, and unknown parameters (e.g., varying vehicle mass).
