# Lesson Plan: Longitudinal Vehicle Dynamics Modeling

This lesson plan is derived from `research_based/notes.tex` and is organized to help a learner move from the research motivation to the modeling, validation, and interpretation workflow.

## Learning Goal

Understand how to build, simplify, validate, and interpret a longitudinal vehicle dynamics model that is accurate enough for simulation and efficient enough for real-time use.

## Lesson 1: Problem Framing and Research Gap

### Focus
- Why longitudinal vehicle modeling matters
- Why there is a trade-off between model fidelity and computational cost
- Why pure rolling assumptions can fail

### Key ideas to understand
- Difference between high-fidelity nonlinear models and simplified real-time models
- Limits of pure physical models
- Limits of pure data-driven models
- Need for a reduced but reliable modeling framework

### Suggested outcomes
- Explain the main research gap in one paragraph
- Describe why tire slip, load transfer, and road conditions matter

## Lesson 2: Research Questions and Objectives

### Focus
- What the research is trying to answer
- How objectives translate into modeling tasks

### Key ideas to understand
- Real-time feasibility vs. physical realism
- Effect of tire slip and load transfer on accuracy
- Use of validation metrics such as RMSE and MAPE
- Importance of parameter identifiability under changing road grade and friction

### Suggested outcomes
- Restate each research question in simpler engineering language
- Match each research objective to a concrete modeling or validation activity

## Lesson 3: Fundamentals of Longitudinal Vehicle Dynamics

### Focus
- Core longitudinal motion concepts
- Main forces acting on the vehicle

### Key ideas to understand
- Vehicle mass and longitudinal acceleration
- Traction and braking force
- Aerodynamic drag
- Rolling resistance
- Road grade effects

### Suggested outcomes
- Draw a free-body diagram for straight-line vehicle motion
- Write a force balance equation for longitudinal motion

## Lesson 4: Kinematic vs. Dynamic Models

### Focus
- Two major modeling approaches introduced in the literature review

### Key ideas to understand
- What a kinematic model captures
- What a dynamic model captures
- Why dynamic models are more suitable for force-based performance analysis
- Why reduced-order dynamic models are attractive for control and estimation

### Suggested outcomes
- Compare kinematic and dynamic models in a short table
- Explain when a kinematic model is insufficient

## Lesson 5: Tire Slip and Tire-Road Friction

### Focus
- Why tire-road interaction is central to longitudinal accuracy

### Key ideas to understand
- Slip ratio concept
- Friction coefficient behavior
- Pacejka-style nonlinear tire behavior
- Why simplified tire models may be needed for real-time use

### Suggested outcomes
- Define slip ratio qualitatively
- Explain how ignoring slip can distort acceleration or energy prediction

## Lesson 6: Load Transfer and Resistance Effects

### Focus
- Secondary effects that strongly influence model quality

### Key ideas to understand
- Normal load transfer during acceleration and braking
- Interaction between normal load and available tire force
- Combined effect of drag, rolling resistance, and grade

### Suggested outcomes
- Explain why load transfer changes traction capability
- Identify which resistive forces dominate at low and high speed

## Lesson 7: Powertrain and Reduced-Order Modeling

### Focus
- How the model is simplified without losing core behavior

### Key ideas to understand
- First-order approximation of powertrain dynamics
- Reduced-order nonlinear state-space modeling
- Trade-off between simplicity and predictive quality

### Suggested outcomes
- Explain what a reduced-order model is
- Describe why a first-order inertial approximation is useful

## Lesson 8: Governing Equation and Model Construction

### Focus
- The mathematical model proposed in the methodology

### Key ideas to understand
- Structure of the longitudinal acceleration equation
- Meaning of each parameter:
- `m`, `rho`, `C_d`, `A_ref`, `mu`, `beta`, and applied force `F`
- Assumptions used in the model

### Suggested outcomes
- Interpret each term in the governing equation physically
- Identify which terms are controllable, estimated, or environmental

## Lesson 9: Parameter Estimation and Identifiability

### Focus
- How unknown parameters are estimated and why this is hard

### Key ideas to understand
- Sensitivity of model accuracy to mass, drag, and rolling resistance
- Recursive Least Squares as an adaptive estimation method
- Role of Fisher information in identifiability
- Why road grade can interfere with parameter estimation

### Suggested outcomes
- Explain parameter identifiability in plain language
- Describe why varying grade can both help and complicate estimation

## Lesson 10: Experimental Validation Workflow

### Focus
- How to compare the simplified model with real or high-fidelity data

### Key ideas to understand
- Sensor data collection
- Wheel speed and longitudinal acceleration measurements
- Standardized drive cycles
- Simulation-to-experiment comparison

### Suggested outcomes
- Outline a validation pipeline from data acquisition to error analysis
- Explain why sampling rate and test conditions matter

## Lesson 11: Performance Metrics

### Focus
- How model quality is judged quantitatively

### Key ideas to understand
- Root Mean Square Error (RMSE)
- Mean Absolute Percentage Error (MAPE)
- Variance Accounted For (VAF)
- Tracking error interpretation

### Suggested outcomes
- Explain what each metric tells you
- State which metric is more useful for absolute error versus relative error

## Lesson 12: Results Interpretation

### Focus
- How to read and evaluate the expected findings

### Key ideas to understand
- Model fit and predictive reliability
- Tracking performance
- Parameter convergence
- Transient response and bandwidth relevance

### Suggested outcomes
- Explain what good validation results would look like
- Interpret whether a model is suitable for real-time applications

## Lesson 13: Discussion of Robustness

### Focus
- What makes the model reliable or fragile in real conditions

### Key ideas to understand
- Friction variation and uncertainty
- Observer robustness
- Input-to-State Stability motivation
- Terrain fluctuation effects

### Suggested outcomes
- Explain why robustness matters beyond nominal accuracy
- Identify the main uncertainty sources in longitudinal modeling

## Lesson 14: Research Contribution and Big Picture

### Focus
- Why the work matters in a broader engineering context

### Key ideas to understand
- Bridging research and deployable real-time systems
- Virtual proving ground concept
- Relevance to ADAS, control design, and autonomous systems

### Suggested outcomes
- Summarize the contribution of the research in a short abstract
- Explain how this model could support simulator or controller development

## Recommended Study Order

1. Lesson 1 to understand the motivation
2. Lesson 3 and Lesson 4 to build fundamentals
3. Lesson 5 to Lesson 8 to understand the model components
4. Lesson 9 to Lesson 11 to understand estimation and validation
5. Lesson 12 to Lesson 14 to interpret impact and limitations

## Suggested Deliverables for the Lesson Folder

- `lesson_plan.md` for the full roadmap
- `lesson_01_problem_framing.md`
- `lesson_02_modeling_fundamentals.md`
- `lesson_03_tire_and_load_effects.md`
- `lesson_04_model_construction.md`
- `lesson_05_validation_and_metrics.md`
- `lesson_06_results_discussion.md`

## Next Step

The current file is a roadmap. The next practical step is to expand each lesson into a short teaching note with:
- learning objectives
- explanation
- key equations
- terminology
- review questions
