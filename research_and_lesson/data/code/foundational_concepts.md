# Foundational Concepts: FSAE Vehicle Dynamics & Simulation

This document explains the core engineering principles and mathematical foundations implemented in the FSAE Simulator modular framework.

---

## 0. Pre-requisite Knowledge: Understanding the Data

Before diving into complex dynamics, it is essential to understand how a race car "speaks" through data. In this simulator, every data point represents a snapshot of the vehicle's state at a specific moment in time.

### 0.1 State vs. Control Variables
In telemetry, we distinguish between what the **Driver** does and what the **Vehicle** does:

*   **Control Variables (Inputs)**: These are the driver's actions.
    *   `throttle`: A value from 0 to 1 (0% to 100%) representing power demand.
    *   `brake_cmd`: The driver's intent to slow down.
*   **State Variables (Outputs)**: These are the results of physics acting on the car.
    *   `speed_kmh`: The resulting velocity.
    *   `yaw_deg`: The orientation of the car in the world.
    *   `coolant_temp`: The thermodynamic state of the powertrain.

### 0.2 The "Truth" vs. The "Sensor"
A unique feature of this simulation is the distinction between `true` and `sensors` data blocks:

1.  **Ground Truth (`true`)**: The perfect, mathematical state calculated by the physics engine. In the real world, we NEVER have access to this.
2.  **Sensor Data (`sensors`)**: What the car's electronics actually measure. This includes:
    *   **Noise**: Real sensors have electrical interference or mechanical vibration.
    *   **Latency**: Sensors take time to process and send data.
    *   **Bias**: A sensor might be slightly "off" (e.g., an IMU that thinks 0.05g is zero).

*Foundational Rule*: To understand the data, you must realize that `sensors.wheel_speed` will always slightly differ from `true.speed_kmh`. Analyzing this difference is the key to **filtering** and **estimation**.

### 0.3 Coordinate Systems & Reference Frames
To map the car's motion, we use two primary frames:

1.  **Global Frame (GPS)**: Uses $X, Y$ coordinates relative to the track start. Useful for mapping the "line" the driver takes.
2.  **Local Frame (Body)**: Uses $a_x$ (Longitudinal) and $a_y$ (Lateral) accelerations relative to the driver's seat.
    *   $+a_x$: Acceleration (Forward)
    *   $-a_x$: Braking (Backward)
    *   $\pm a_y$: Cornering (Left/Right)

### 0.4 Sampling & Discretization: Time vs. Distance
Physics happens continuously, but computers record data in "chunks" or **samples**.

1.  **Time-Based (Telemetry)**: Data is recorded every $\Delta t$ seconds (e.g., 10Hz = 0.1s). This is how logs are stored (`t: 0.1, 0.2, 0.3...`).
*   **Distance-Based (Analysis)**: Engineers often care about *where* on the track something happened, not *when*. We map the time-based samples to a `track_index` or cumulative distance $s$.

*Critical Insight*: At high speeds (200 km/h), a 10Hz sample rate means the car travels ~5.5 meters between every data point. This "blind spot" is why high-speed sensors (like IMUs) often run at 100Hz or 1000Hz.

### 0.5 Signal Processing: Dealing with Noise
Because `sensors` data is noisy, we cannot use it directly for high-precision modeling without "cleaning" it.

1.  **Moving Average**: Taking the average of the last $N$ samples to smooth out spikes.
$$y_i = \frac{1}{N} \sum_{j=0}^{N-1} x_{i-j}$$
2.  **Kalman Filtering**: A more advanced method (used in high-fidelity dashboards) that combines the "Truth" of a physics model with the "Observation" of a sensor to find the most likely state.

*Application*: If `sensors.imu.ax` is jumping between -0.1 and +0.1 while the car is parked, a moving average helps "zero" the sensor so it doesn't show the car vibrating through the floor.

---

## 1. The A-Level Physics Bridge

To master this simulator, you can apply what you've learned in the **Cambridge A-Level Physics (9702)** syllabus. Each lesson below is a "Level Up" from a core school topic.

| Simulator Lesson | A-Level Syllabus Section | Key School Concept | The "Race" Extension |
| :--- | :--- | :--- | :--- |
| **Lesson 1: QSS** | 2. Kinematics | $v^2 = u^2 + 2as$ | Acceleration ($a$) is non-constant. |
| **Lesson 2: Tires** | 3. Dynamics | $F = ma$ & Friction | Friction coefficient ($\mu$) varies with load. |
| **Lesson 3: Aero** | 4. Forces | Drag & Terminal Velocity | Drag scales with $v^2$ and chassis pitch. |
| **Lesson 4: Thermal** | 19. Electricity / 11. Thermal | $P=VI$ & $\Delta Q = mc\Delta \theta$ | Internal resistance causes heat/derating. |
| **Lesson 5: Pitch** | 13. Oscillations | Damped SHM | Spring/Damper systems stabilize the car. |
| **Lesson 6: Track** | 12. Circular Motion | $a = v^2/r$ | Radius ($r$) is derived from GPS vectors. |

---

## Lesson 1: Quasi-Steady State (QSS) Lap Simulation

**A-Level Connection**: *Section 2 (Kinematics)*. In school, you solve for time or distance with constant acceleration. Here, we use the same equations but apply them thousands of times in small distance steps ($ds$), recalculating acceleration at every point.

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

**A-Level Connection**: *Section 3 (Dynamics)*. You know $F = \mu N$ (or $F = \mu R$). In racing, the "coefficient of friction" $\mu$ isn't a single number—it is a curve that changes based on how much the tire is sliding and how much weight ($N$) is on it.

Tires do not behave like simple friction blocks ($F = \mu F_z$). The **Pacejka Magic Formula** captures the non-linear relationship between slip and force:
$$F = D \sin(C \arctan(B\alpha - E(B\alpha - \arctan(B\alpha))))$$

### Key Concepts:
- **Load Sensitivity**: As the vertical load ($F_z$) increases, the tire's friction coefficient ($\mu$) effectively **decreases**. This is why weight transfer generally reduces total grip.
- **Friction Ellipse**: A tire has a limited "budget" of force. If you use 100% of the grip for cornering (lateral), you have 0% left for braking (longitudinal).
    $$\left(\frac{F_x}{F_{x,max}}\right)^2 + \left(\frac{F_y}{F_{y,max}}\right)^2 \leq 1$$

---

## Lesson 3: Aerodynamics & Attitude Sensitivity

**A-Level Connection**: *Section 4 (Forces)*. You've studied drag and terminal velocity ($F_d = W$ at equilibrium). In the simulator, drag is the primary force opposing the motor at high speeds, and we calculate how it changes as the car "dives" under braking.

Aerodynamic forces scale with the square of velocity:
$$F_{aero} = \frac{1}{2} \rho v^2 A C$$

In high-fidelity models, $C_l$ (Downforce) and $C_d$ (Drag) are not constant. They change based on the **Chassis Pitch Angle ($\theta$)**.
- **Dive/Squat**: When the car squats under acceleration, the front wing moves further from the ground, often changing the aerodynamic balance and total downforce.
- **Ground Effect**: FSAE cars use undertrays that are extremely sensitive to ride height and pitch.

---

## Lesson 4: Powertrain & Thermal Management

**A-Level Connection**: *Section 19 (Current of Electricity) & Section 11 (Thermal Physics)*. The motor heat comes from $P = I^2 R$ (Joule heating). The temperature rise follows $\Delta Q = mc\Delta \theta$. If the motor gets too hot, its resistance increases and performance drops.

The motor's output is limited by two primary factors:
1.  **The Torque Curve**: At high RPMs, the available torque drops due to Back-EMF and power electronics limits.
2.  **Thermal Derating**: Electric motors generate heat ($P_{loss} = I^2 R$). As the motor gets hot, the controller must reduce (derate) the torque to prevent damage to the windings or permanent magnets.
    - *Logic*: If $T > 100^\circ C$, torque is scaled linearly down to zero at $130^\circ C$.

---

## Lesson 5: Transient Chassis Dynamics

**A-Level Connection**: *Section 13 (Oscillations)*. The car's suspension is a mass-spring-damper system. When you accelerate, the car "squats"—this is an oscillation that must be damped so the tires stay in contact with the ground.

While the lap simulator is "Quasi-Steady," we integrate **Transient Pitch** during the forward pass to capture dynamic effects:
$$I_{pitch} \ddot{\theta} + C_{pitch} \dot{\theta} + K_{pitch} \theta = M_{acceleration}$$

### Why this matters:
When a car accelerates, it doesn't just "be" at a new pitch angle. It oscillates and takes time to settle (damping). This settling time affects the instantaneous load on the rear tires, which in turn affects the traction limit ($F_{x,max}$) via the Pacejka model.

---

## Lesson 6: Track Mathematics - Menger Curvature

**A-Level Connection**: *Section 12 (Circular Motion)*. You study $a = v^2/r$ for a perfect circle. In a real race, the "circle" (radius $r$) changes every meter. We use calculus and geometry to find that changing $r$ from GPS data.

To find the radius $R$ from a set of GPS points $(X,Y)$, we use the **Menger Curvature** formula. Given three points $(P_1, P_2, P_3)$:
$$\kappa = \frac{4 \cdot \text{Area}(P_1, P_2, P_3)}{|P_1-P_2| \cdot |P_2-P_3| \cdot |P_3-P_1|}$$
Where Radius $R = 1/\kappa$. 

This allows the simulator to "read" a track map and determine exactly where the driver needs to slow down for tight hairpins vs. high-speed sweepers.
