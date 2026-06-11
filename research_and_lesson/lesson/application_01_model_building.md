# Application 01: Building the Model

## Objective

Combine physics and math into a usable simplified longitudinal vehicle model.

## Step 1: Start from Physics

Begin with the longitudinal force balance:

`F_drive - F_drag - F_roll - F_grade = m a`

This states that acceleration comes from the net longitudinal force.

## Step 2: Define the Forces

- `F_drive` comes from traction or braking
- `F_drag` represents aerodynamic resistance
- `F_roll` represents rolling resistance
- `F_grade` represents the gravitational effect of road slope

## Step 3: Convert to a Differential Equation

Since `a = dv/dt`, the model becomes:

`dv/dt = (1/m) (F_drive - F_drag - F_roll - F_grade)`

This is the mathematical form used for simulation.

## ASCII Sketch

```text
Physics inputs
  traction
  drag
  rolling resistance
  grade
      |
      v
Force balance equation
      |
      v
Differential equation
      |
      v
Simulation output: velocity and acceleration
```

## Step 4: Add Realistic Effects

To improve realism, the model can include:
- tire slip
- load transfer
- powertrain delay
- uncertain friction or grade

## Step 5: Choose the Level of Complexity

The model should be simple enough to run efficiently but detailed enough to capture important behavior. This is the main trade-off in the research.

## Example Problems

### Problem 1

Write the basic differential form of the longitudinal force-balance model.

Answer:
`dv/dt = (1/m) (F_drive - F_drag - F_roll - F_grade)`

### Problem 2

Why is tire slip often added after the basic force-balance model is built?

Answer:
Because the basic model gives a simple starting structure, while slip is an added effect that improves realism when stronger traction or braking behavior must be captured.

## Review Questions

1. What is the starting physical equation of the model?
2. How is acceleration converted into a differential equation?
3. Why might a simple force-balance model need extra effects such as slip or delay?
