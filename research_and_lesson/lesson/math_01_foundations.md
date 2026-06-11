# Math 01: Foundations

## Objective

Build the basic mathematical tools needed for longitudinal vehicle modeling.

## Core Idea

Before writing a vehicle model, we need clean algebra, correct units, and basic trigonometry.

## Algebra and Units

Vehicle equations mix physical quantities such as:
- force in newtons
- mass in kilograms
- velocity in meters per second
- acceleration in meters per second squared

Unit consistency is essential. If the units do not match, the equation is wrong.

## Trigonometry for Grade

Road slope introduces gravity terms involving:
- `sin(beta)`
- `cos(beta)`

These terms describe how gravity acts along and perpendicular to the slope.

## Linear and Nonlinear Terms

Some terms are linear, while others are nonlinear.

Examples:
- `m a` is linear in acceleration
- aerodynamic drag often includes `v^2`, which is nonlinear

## Why It Matters

These tools help us read, build, and verify the model correctly before using simulation or estimation methods.

## Example Problems

### Problem 1

If force is in newtons and mass is in kilograms, what should the unit of acceleration be in `F = m a`?

Answer:
It should be meters per second squared, `m/s^2`.

### Problem 2

Why is the drag term `v^2` nonlinear?

Answer:
Because the variable is squared, so the output does not change in direct proportion to velocity.

## Review Questions

1. Why is unit consistency important?
2. What physical effect introduces `sin(beta)` and `cos(beta)`?
3. Why is `v^2` considered nonlinear?
