# Documentation Step

This file documents the lesson-material creation flow from the chat request to the generated output files.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Assistant
    participant Notes as research_based/notes.tex
    participant LessonDir as lesson/
    participant Doc as documentation_step.md

    User->>Assistant: Request lesson plan based on notes.tex
    Assistant->>Notes: Read research content
    Notes-->>Assistant: Research topics and structure
    Assistant->>LessonDir: Create lesson/lesson_plan.md
    Assistant-->>User: Provide roadmap summary

    User->>Assistant: Reorganize by Physics and Math
    Assistant->>LessonDir: Create physics_math_lesson_plan.md
    Assistant-->>User: Provide Physics/Math structure

    User->>Assistant: Expand into separate lesson files
    Assistant->>LessonDir: Create physics_01_basic_motion.md
    Assistant->>LessonDir: Create physics_02_forces.md
    Assistant->>LessonDir: Create physics_03_tires_and_friction.md
    Assistant->>LessonDir: Create physics_04_resistance_and_grade.md
    Assistant->>LessonDir: Create physics_05_powertrain_and_uncertainty.md
    Assistant->>LessonDir: Create math_01_foundations.md
    Assistant->>LessonDir: Create math_02_differential_modeling.md
    Assistant->>LessonDir: Create math_03_estimation_and_validation.md
    Assistant->>LessonDir: Create application_01_model_building.md
    Assistant->>LessonDir: Create application_02_validation_workflow.md
    Assistant-->>User: Deliver lesson file set

    User->>Assistant: Add example problems and answers
    Assistant->>LessonDir: Update all lesson files with examples
    Assistant-->>User: Confirm worked examples added

    User->>Assistant: Add diagrams and document the workflow
    Assistant->>LessonDir: Add ASCII diagrams to core lessons
    Assistant->>Doc: Create Mermaid sequence diagram
    Doc-->>User: documentation_step.md saved
```

## Output Files Produced

- `lesson/lesson_plan.md`
- `lesson/physics_math_lesson_plan.md`
- `lesson/physics_01_basic_motion.md`
- `lesson/physics_02_forces.md`
- `lesson/physics_03_tires_and_friction.md`
- `lesson/physics_04_resistance_and_grade.md`
- `lesson/physics_05_powertrain_and_uncertainty.md`
- `lesson/math_01_foundations.md`
- `lesson/math_02_differential_modeling.md`
- `lesson/math_03_estimation_and_validation.md`
- `lesson/application_01_model_building.md`
- `lesson/application_02_validation_workflow.md`
- `documentation_step.md`

## Summary

The workflow followed three stages:
1. Extract structure from `research_based/notes.tex`
2. Reorganize the material into Physics, Math, and Application lessons
3. Expand the lessons with examples and diagrams for teaching use
