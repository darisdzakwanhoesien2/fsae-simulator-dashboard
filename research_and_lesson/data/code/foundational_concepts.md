# Foundational Concepts: FSAE Vehicle Dynamics & Simulation

This document explains the core engineering principles and mathematical foundations implemented in the FSAE Simulator modular framework.

---

## Lesson 1: Quasi-Steady State (QSS) Lap Simulation

A QSS simulator assumes that at any given distance $s$, the vehicle is in a state of local equilibrium. The complex problem of finding the fastest lap is decomposed into three primary constraints:

1.  **Lateral Limit**: How fast can the car go through a corner of radius $R$ without sliding?
    $$v_{max} = \sqrt{\frac{F_{y,max} \cdot R}{m}}$$
2.  **Forward Pass (Acceleration)**: Starting from an apex (minimum speed), how quickly can the powertrain and traction limits accelerate the car?
    $$v_{i+1} = \sqrt{v_i^2 + 2 \cdot a_x \cdot \Delta s}$$
3.  **Backward Pass (Braking)**: Working backward from a corner entry, how late can the driver brake to reach the required apex speed?
    $$v_{i-1} = \sqrt{v_i^2 + 2 \cdot |a_{decel}| \cdot \Delta s}$$

The final velocity profile is the **minimum** of these three curves at every point.

---

## Lesson 2: Tire Dynamics - The Magic Formula

Tires do not behave like simple friction blocks ($F = \mu F_z$). The **Pacejka Magic Formula** captures the non-linear relationship between slip and force:
$$F = D \sin(C \arctan(B\alpha - E(B\alpha - \arctan(B\alpha))))$$

### Key Concepts:
- **Load Sensitivity**: As the vertical load ($F_z$) increases, the tire's friction coefficient ($\mu$) effectively **decreases**. This is why weight transfer generally reduces total grip.
- **Friction Ellipse**: A tire has a limited "budget" of force. If you use 100% of the grip for cornering (lateral), you have 0% left for braking (longitudinal).
    $$\left(\frac{F_x}{F_{x,max}}\right)^2 + \left(\frac{F_y}{F_{y,max}}\right)^2 \leq 1$$

---

## Lesson 3: Aerodynamics & Attitude Sensitivity

Aerodynamic forces scale with the square of velocity:
$$F_{aero} = \frac{1}{2} \rho v^2 A C$$

In high-fidelity models, $C_l$ (Downforce) and $C_d$ (Drag) are not constant. They change based on the **Chassis Pitch Angle ($\theta$)**.
- **Dive/Squat**: When the car squats under acceleration, the front wing moves further from the ground, often changing the aerodynamic balance and total downforce.
- **Ground Effect**: FSAE cars use undertrays that are extremely sensitive to ride height and pitch.

---

## Lesson 4: Powertrain & Thermal Management

The motor's output is limited by two primary factors:
1.  **The Torque Curve**: At high RPMs, the available torque drops due to Back-EMF and power electronics limits.
2.  **Thermal Derating**: Electric motors generate heat ($P_{loss} = I^2 R$). As the motor gets hot, the controller must reduce (derate) the torque to prevent damage to the windings or permanent magnets.
    - *Logic*: If $T > 100^\circ C$, torque is scaled linearly down to zero at $130^\circ C$.

---

## Lesson 5: Transient Chassis Dynamics

While the lap simulator is "Quasi-Steady," we integrate **Transient Pitch** during the forward pass to capture dynamic effects:
$$I_{pitch} \ddot{\theta} + C_{pitch} \dot{\theta} + K_{pitch} \theta = M_{acceleration}$$

### Why this matters:
When a car accelerates, it doesn't just "be" at a new pitch angle. It oscillates and takes time to settle (damping). This settling time affects the instantaneous load on the rear tires, which in turn affects the traction limit ($F_{x,max}$) via the Pacejka model.

---

## Lesson 6: Track Mathematics - Menger Curvature

To find the radius $R$ from a set of GPS points $(X,Y)$, we use the **Menger Curvature** formula. Given three points $(P_1, P_2, P_3)$:
$$\kappa = \frac{4 \cdot \text{Area}(P_1, P_2, P_3)}{|P_1-P_2| \cdot |P_2-P_3| \cdot |P_3-P_1|}$$
Where Radius $R = 1/\kappa$. 

This allows the simulator to "read" a track map and determine exactly where the driver needs to slow down for tight hairpins vs. high-speed sweepers.
