# Physics 04: Resistance Forces and Road Grade

## Objective

Understand the non-driving forces that resist or alter longitudinal motion.

## Core Idea

A vehicle does not move based on traction alone. Several resisting and environmental forces must also be considered.

## Rolling Resistance

Rolling resistance comes from tire deformation, road interaction, and small energy losses in motion. It is often important at low and medium speeds.

## Aerodynamic Drag

Drag is caused by air resistance. It grows strongly with speed and is commonly modeled using a term proportional to `v^2`.

## Road Grade

If the road is inclined:
- uphill motion requires more force
- downhill motion requires less force

## ASCII Sketch

```text
Uphill case:

          / car ->
---------/

Gravity creates a component that opposes forward motion.

Downhill case:

car -> \
------- \

Gravity creates a component that assists forward motion.
```

The grade effect is linked to gravity and must be included when modeling real roads.

## Why It Matters

These effects can significantly change the force balance. A model that ignores them may work only in limited conditions.

## Example Problems

### Problem 1

Why is aerodynamic drag more important at 30 m/s than at 10 m/s?

Answer:
Because drag increases strongly with speed, commonly with a `v^2` relation, so it becomes much larger at higher speeds.

### Problem 2

What happens to the required driving force when a car moves uphill?

Answer:
The required driving force increases because gravity adds a resisting component along the road slope.

## Review Questions

1. What is the difference between rolling resistance and aerodynamic drag?
2. Why does drag become more important at high speed?
3. How does uphill driving affect the required traction force?
