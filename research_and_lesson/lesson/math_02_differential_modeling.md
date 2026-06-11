# Math 02: Differential Modeling

## Objective

Understand how longitudinal vehicle behavior is written as a time-based mathematical model.

## Core Idea

A vehicle model is usually written as a differential equation because speed changes over time.

## Differential Equation View

The symbol `dv/dt` means the rate of change of velocity with respect to time. In longitudinal modeling, this is the acceleration.

A simple model may look like:

`dv/dt = (1/m) (F_drive - F_drag - F_roll - F_grade)`

This means acceleration depends on the balance of longitudinal forces.

## First-Order Dynamics

Some subsystems, especially powertrain response, are simplified using first-order models with a time constant and sometimes delay. This is useful when full physical detail is unnecessary.

## State-Space Form

A model can also be written using:
- states
- inputs
- outputs
- disturbances

For a simple case:
- state: vehicle velocity
- input: driving or braking force
- disturbance: grade or friction change

## Why It Matters

Differential equations and state-space form are standard ways to prepare a model for simulation, control, and estimation.

## Example Problems

### Problem 1

If `dv/dt` is positive, what does that mean physically?

Answer:
The vehicle velocity is increasing, so the car is accelerating.

### Problem 2

In a simple state-space model of longitudinal motion, what could be used as the state?

Answer:
Vehicle velocity can be used as the state because it changes over time and describes the system behavior.

## Review Questions

1. What does `dv/dt` represent physically?
2. Why is a vehicle model usually time-based?
3. What is a state in a state-space model?
