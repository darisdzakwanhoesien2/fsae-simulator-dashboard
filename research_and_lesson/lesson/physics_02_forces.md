# Physics 02: Forces in Longitudinal Motion

## Objective

Understand the physical forces that cause a vehicle to accelerate, decelerate, or maintain speed.

## Core Idea

Vehicle motion changes because of forces. In straight-line motion, the most important idea is Newton's second law:

`sum(F) = m a`

This means the net longitudinal force determines the acceleration of the vehicle.

## Main Forces

- Traction force pushes the vehicle forward.
- Braking force opposes forward motion.
- Aerodynamic drag resists motion and grows with speed.
- Rolling resistance resists motion due to tire and road deformation.
- Grade force helps or opposes motion depending on road slope.

## Interpretation

If the forward force is larger than the resisting forces, the vehicle accelerates. If the resisting forces are larger, the vehicle decelerates.

## Example Force Balance

A simple longitudinal balance can be written as:

`F_drive - F_drag - F_roll - F_grade = m a`

## ASCII Sketch

```text
          forward motion
               -->

   [ traction ] ---> [ vehicle ] <--- [ drag ]
                                 <--- [ rolling resistance ]
                                 <--- [ grade resistance ]
```

The vehicle accelerates forward when the traction force is larger than the total resisting forces.

This equation is the physical starting point of many simplified vehicle models.

## Why It Matters

Every later model is built from this force balance. The quality of the model depends on which forces are included and how accurately they are represented.

## Example Problems

### Problem 1

A vehicle has 4000 N of driving force and 2500 N of total resisting force. If the mass is 1000 kg, what is the acceleration?

Answer:
The net force is `4000 - 2500 = 1500 N`.
The acceleration is `a = 1500 / 1000 = 1.5 m/s^2`.

### Problem 2

What happens if the total traction force is exactly equal to the total resisting force?

Answer:
The net force is zero, so acceleration is zero. The vehicle keeps a constant speed if it is already moving.

## Review Questions

1. What does `sum(F) = m a` mean in this context?
2. Which forces oppose vehicle motion?
3. What happens if traction force equals total resistance?
