# Physics and Math Lesson Plan for Longitudinal Vehicle Dynamics

This lesson plan reorganizes the material from `research_based/notes.tex` into two foundations:
- Physics concepts
- Math concepts

The goal is to help a learner understand the physical meaning first, then the mathematical formulation, and finally how both are combined in a vehicle dynamics model.

## Learning Goal

Understand the physics and mathematics behind a simplified longitudinal vehicle dynamics model used for simulation, estimation, and validation.

## Part A: Physics Materials

### 1. Basic Longitudinal Vehicle Motion

#### Topics
- Straight-line vehicle motion
- Position, velocity, and acceleration
- Difference between cruising, acceleration, and braking

#### Learning outcome
- Explain what longitudinal motion means in vehicle dynamics

### 2. Newton's Second Law in Vehicle Motion

#### Topics
- Force balance in the longitudinal direction
- Relationship between net force, mass, and acceleration
- Why acceleration changes when total force changes

#### Learning outcome
- Write and explain the basic equation `sum(F) = m a`

### 3. Traction and Braking Forces

#### Topics
- Driving force at the tire
- Braking force at the tire
- How torque becomes longitudinal force

#### Learning outcome
- Describe how engine or brake torque produces vehicle acceleration or deceleration

### 4. Tire Slip and Tire-Road Friction

#### Topics
- Concept of slip ratio
- Why tire force depends on slip
- Friction coefficient and road condition
- Why pure rolling is not always valid

#### Learning outcome
- Explain why tire slip is important for realistic modeling

### 5. Normal Load Transfer

#### Topics
- Load shifting during acceleration
- Load shifting during braking
- Effect of vertical load on tire force generation

#### Learning outcome
- Explain how load transfer changes available traction and braking performance

### 6. Rolling Resistance

#### Topics
- Origin of rolling resistance
- Dependence on tire and road characteristics
- Impact at low and medium speeds

#### Learning outcome
- Explain why rolling resistance must be included in a simple model

### 7. Aerodynamic Drag

#### Topics
- Air resistance as a speed-dependent force
- Dependence on drag coefficient, frontal area, and air density
- Why drag grows strongly with speed

#### Learning outcome
- Explain the physical meaning of the drag term in the model

### 8. Road Grade and Gravity

#### Topics
- Inclined-road force component
- Uphill and downhill effects
- Why road slope disturbs parameter estimation

#### Learning outcome
- Explain how road grade changes the required driving force

### 9. Powertrain Dynamics

#### Topics
- Engine or motor torque generation
- Driveline transmission effect
- Delay and inertia in force delivery

#### Learning outcome
- Explain why powertrain behavior is often simplified into a lower-order model

### 10. Real-World Uncertainties

#### Topics
- Friction changes
- Road condition variation
- Sensor measurement errors
- Environmental disturbances

#### Learning outcome
- Identify why real-world operation is harder than textbook modeling

## Part B: Math Materials

### 1. Algebra and Units

#### Topics
- Rearranging equations
- Consistent units
- Force, mass, acceleration, and velocity units

#### Learning outcome
- Check whether a vehicle dynamics equation is dimensionally consistent

### 2. Trigonometry for Road Grade

#### Topics
- Sine and cosine in slope modeling
- Small-angle interpretation
- Grade angle in force equations

#### Learning outcome
- Explain the terms involving `sin(beta)` and `cos(beta)`

### 3. Functions and Nonlinearity

#### Topics
- Linear versus nonlinear terms
- Quadratic drag term `v^2`
- Why nonlinear behavior matters in vehicle models

#### Learning outcome
- Identify which parts of the model are linear and nonlinear

### 4. Differential Equations

#### Topics
- Meaning of `dv/dt`
- Continuous-time system behavior
- Time evolution of vehicle speed

#### Learning outcome
- Interpret the vehicle model as a differential equation

### 5. First-Order System Modeling

#### Topics
- Time constant
- Delay
- First-order approximation of powertrain response

#### Learning outcome
- Explain why first-order dynamics are useful in simplified models

### 6. State-Space Representation

#### Topics
- State variables
- Inputs, outputs, and disturbances
- Writing the system in compact form

#### Learning outcome
- Express a simple longitudinal model in state-space form

### 7. Numerical Simulation Concepts

#### Topics
- Simulating equations over time
- Step-by-step update idea
- Importance of sampling time

#### Learning outcome
- Explain how a continuous vehicle model can be simulated on a computer

### 8. Error Metrics

#### Topics
- Root Mean Square Error (RMSE)
- Mean Absolute Percentage Error (MAPE)
- Variance Accounted For (VAF)
- Tracking error

#### Learning outcome
- Explain what each validation metric tells us

### 9. Parameter Estimation Basics

#### Topics
- Unknown parameters in the model
- Fitting the model to data
- Difference between known inputs and estimated quantities

#### Learning outcome
- Explain why parameters such as mass and drag must often be estimated

### 10. Recursive Least Squares

#### Topics
- Adaptive parameter estimation idea
- Updating estimates with incoming data
- Real-time estimation use case

#### Learning outcome
- Describe the purpose of Recursive Least Squares in one paragraph

### 11. Sensitivity and Identifiability

#### Topics
- Parameter sensitivity
- Fisher information intuition
- Why some parameters are hard to separate

#### Learning outcome
- Explain identifiability in plain engineering language

## Part C: Combined Application Lessons

### 1. Build the Longitudinal Force-Balance Equation

#### Combine
- Newton's law
- Traction and braking
- Drag
- Rolling resistance
- Grade force

#### Learning outcome
- Derive a simplified force-balance model for straight-line motion

### 2. Convert Physics into a Mathematical Model

#### Combine
- Physical assumptions
- Differential equation form
- Nonlinear terms
- State-space representation

#### Learning outcome
- Turn the physical vehicle description into a usable simulation model

### 3. Add Realistic Effects

#### Combine
- Tire slip
- Load transfer
- Powertrain response
- Uncertainty sources

#### Learning outcome
- Explain how a basic model is upgraded into a more realistic reduced-order model

### 4. Estimate Parameters from Data

#### Combine
- Experimental measurements
- Unknown parameter fitting
- Recursive Least Squares
- Identifiability concerns

#### Learning outcome
- Explain how model parameters are tuned from measured vehicle data

### 5. Validate the Model

#### Combine
- Experimental and simulated signals
- RMSE, MAPE, and VAF
- Tracking accuracy
- Result interpretation

#### Learning outcome
- Judge whether the model is accurate enough for simulation or control use

## Recommended Teaching Sequence

1. Start with Physics Materials 1 to 8
2. Continue with Math Materials 1 to 6
3. Introduce Physics Material 9 and 10
4. Continue with Math Materials 7 to 11
5. Finish with the Combined Application Lessons

## Suggested Output Files if Expanded Later

- `physics_01_basic_motion.md`
- `physics_02_forces.md`
- `physics_03_tires_and_friction.md`
- `physics_04_resistance_and_grade.md`
- `physics_05_powertrain_and_uncertainty.md`
- `math_01_foundations.md`
- `math_02_differential_modeling.md`
- `math_03_estimation_and_validation.md`
- `application_01_model_building.md`
- `application_02_validation_workflow.md`

## Short Summary

The material can be taught in three layers:
1. Physics: what forces and effects govern the vehicle
2. Math: how those effects are expressed and solved in equations
3. Application: how to build, estimate, and validate a practical model
