# Math 03: Estimation and Validation

## Objective

Understand how unknown model parameters are estimated and how model accuracy is measured.

## Core Idea

A model is only useful if its parameters are reasonable and its predictions match data.

## Parameter Estimation

Important parameters may include:
- vehicle mass
- rolling resistance coefficient
- aerodynamic drag coefficient

These values may not be known exactly, so they are estimated from measured data.

## Recursive Least Squares

Recursive Least Squares updates parameter estimates as new data arrives. This makes it useful for real-time applications.

## Identifiability

Identifiability means whether different parameters can be distinguished from the available data. For example, changes in road grade can look similar to changes in force demand, making some parameters difficult to estimate separately.

## Validation Metrics

Common metrics include:
- RMSE for absolute error magnitude
- MAPE for percentage error
- VAF for how well the model explains measured variation

## Why It Matters

Good estimation and validation are what turn a theoretical model into a practical engineering tool.

## Example Problems

### Problem 1

Why might vehicle mass need to be estimated instead of treated as fixed?

Answer:
Because the real vehicle mass can change with driver, fuel, cargo, or test conditions.

### Problem 2

If a model has low RMSE but poor VAF, what does that suggest?

Answer:
It suggests the absolute error may be small on average, but the model may still fail to capture the measured variation or dynamic behavior well.

## Review Questions

1. Why do model parameters need to be estimated?
2. What is the main idea of Recursive Least Squares?
3. What is the difference between RMSE and MAPE?
