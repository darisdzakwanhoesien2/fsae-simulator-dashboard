# Application 02: Validation Workflow

## Objective

Understand how to test whether the simplified model is reliable.

## Step 1: Collect Data

The model should be compared against measured or high-fidelity data. Useful signals include:
- vehicle speed
- wheel speed
- longitudinal acceleration
- input torque or throttle/brake command

## Step 2: Run the Simulation

Use the same operating conditions in the model and generate predicted speed or acceleration signals.

## Step 3: Compare Signals

The simulated outputs are compared with measured outputs over time. This can be done using plots and numerical metrics.

## Step 4: Measure Error

Typical metrics:
- RMSE for overall magnitude of error
- MAPE for relative error
- VAF for fit quality

## Step 5: Interpret the Result

If error is small and tracking is stable, the model is useful. If error is large, the model may be missing important effects such as slip, grade variation, or parameter mismatch.

## Step 6: Refine if Needed

Possible refinements include:
- better parameter estimation
- better friction modeling
- improved powertrain dynamics
- more representative test conditions

## Example Problems

### Problem 1

Why is wheel speed data useful during validation?

Answer:
It helps compare tire rotational behavior with vehicle motion and can reveal slip-related effects.

### Problem 2

If the simulated velocity consistently stays below the measured velocity, what are two possible causes?

Answer:
The model may overestimate resisting forces, or the driving force and parameter estimates may be too low.

## Review Questions

1. What data is useful for validating a longitudinal vehicle model?
2. Why are both plots and metrics helpful?
3. What can cause validation error even if the main equation is correct?
