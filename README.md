gemini --resume 1ec88865-c24f-496a-8b6e-a4505419dd82
# FSAE Simulator Dashboard - Code Audit, Fixes, and IP Landscape

Previous `README.md` has been moved to `notes.md`.

## 1. Bugs, Errors, and Broken Logic Identified

### A. `simulator/live_recommendation.py`
1. Syntax error in function signature:
- `) -> Dict[str, Any]]:` had an extra `]`.
- Impact: module import fails with `SyntaxError`, breaking recommendation features.

2. Unused import:
- `import os` was unused.
- Impact: readability/maintenance noise.

### B. `simulator/run_simulator.py`
1. Fragile imports:
- Used `from sensors...` instead of package-safe `from simulator.sensors...`.
- Impact: fails depending on current working directory / launch method.

2. Fragile relative file output:
- Wrote realtime output to `../data/realtime.json`.
- Impact: incorrect output path when launched from project root.

3. Redundant commented legacy block:
- Large dead code block at file end.
- Impact: lowers readability and increases confusion.

### C. `simulator/run_race_simulator.py`
1. Same fragile import pattern as above.
2. Relative `data/logs` path not rooted at repository path.

## 2. Issues Fixed

## Files changed
- `simulator/live_recommendation.py`
- `simulator/run_simulator.py`
- `simulator/run_race_simulator.py`
- `notes.md` (previous README content)
- `README.md` (this new file)

### `simulator/live_recommendation.py`
- Fixed return annotation to valid Python:
  - `) -> Dict[str, Any]:`
- Removed unused `os` import.

### `simulator/run_simulator.py`
- Replaced grouped imports with explicit, readable imports.
- Added `ROOT` resolution from `__file__` and safe `sys.path` append.
- Switched to package imports from `simulator.sensors.*`.
- Re-rooted paths to `ROOT/data/...` for deterministic behavior.
- Removed redundant commented legacy code block.

### `simulator/run_race_simulator.py`
- Applied same package import and root-path fixes.

## 3. Cleanup Performed (Redundancy + Readability)

1. Normalized import style in simulator entry scripts.
2. Removed dead/commented-out duplicate logic.
3. Standardized path resolution through `ROOT` for scripts that may run from different CWDs.

## 4. Inline Comments Added for Complex Logic

1. `simulator/live_recommendation.py`:
- Added comment clarifying why `packet["true"]` is treated as the canonical state source.

2. `simulator/run_simulator.py` / `simulator/run_race_simulator.py`:
- Structure and naming improved so additional comments were not necessary beyond existing clear labels.

## 5. Verification and Summary

### Validation run
```bash
python3 -m compileall -q simulator streamlit_app utils
```
Result: pass (no syntax errors).

### Why these changes
- Restore runtime correctness (syntax/import/path issues).
- Make scripts robust when run from different locations.
- Reduce maintenance friction by removing stale duplicate code.
=======
# FSAE Telemetry Simulator + Streamlit Dashboard

This repo contains a small telemetry simulation pipeline and a Streamlit dashboard for viewing the generated data.

- Simulator outputs JSON packets to `data/realtime.json` and session logs in `data/logs/`
- Streamlit app reads those packets for live viewing + analysis pages

## Quick start

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
>>>>>>> c07c010 (restructuring)

> Note: The Streamlit UI requires `streamlit` (and some pages use `pandas` / `matplotlib`). They aren’t currently listed in `requirements.txt`.

<<<<<<< HEAD
## Extended Patent Landscape (Telemetry, Driver Coaching, Digital Twin, PINN)

Important: this is a technical landscape overview, not legal advice and not a freedom-to-operate opinion.

## A. Vehicle telemetry and remote monitoring
1. WO2003073394A2 - Vehicle telemetry system and method  
https://patents.google.com/patent/WO2003073394A2/en

2. WO2004106883A1 - Vehicle tag used for transmitting vehicle telemetry data  
https://patents.google.com/patent/WO2004106883A1/en

3. WO2006110786A3 - Real-time on-board automotive telemetry analysis/reporting  
https://patents.google.com/patent/WO2006110786A3/en

4. US7593999B2 - Automotive telemetry protocol  
https://patents.google.com/patent/US7593999B2

5. US20080197992A1 - Method/system for remotely monitoring vehicle operations  
https://patents.google.com/patent/US20080197992A1/en

6. WO2000052485A1 - Telemetry system for EMI susceptibility testing of vehicles  
https://patents.google.com/patent/WO2000052485A1/en

## B. Driver coaching and feedback systems
1. US9645970B2 - Driver coaching system  
https://patents.google.com/patent/US9645970B2/en

2. US20230267399A1 - Feedback for vehicle driver self-coaching  
https://patents.google.com/patent/US20230267399A1/en

3. WO2007140232A8 - Haptic coaching method for improving fuel economy  
https://patents.google.com/patent/WO2007140232A8/en

## C. Motorsports / race-related monitoring context
1. US6020851A - Auto race monitoring system  
https://patents.google.com/patent/US6020851A/en

## D. Vehicle digital twin and cloud twin architectures
1. US11954651B2 - Sensor-based digital twin system for vehicular analysis  
https://patents.google.com/patent/US11954651B2/en

2. US20190287079A1 - Sensor-based digital twin system for vehicular analysis (publication)  
https://patents.google.com/patent/US20190287079A1/en

3. US9881430B1 - Digital twin system for a cooling system  
https://patents.google.com/patent/US9881430B1/en

4. US20230367688A1 - Cloud-based mobility digital twin for human/vehicle/traffic  
https://patents.google.com/patent/US20230367688A1/en

5. US12154391B2 - ITS with digital twin interface for passenger vehicle  
https://patents.google.com/patent/US12154391B2/en

6. US12340634B2 - Dual vehicle digital twins for model-based learning/remote ops  
https://patents.google.com/patent/US12340634B2/en

7. US20220055620A1 - In-vehicle safety analysis using digital twin  
https://patents.google.com/patent/US20220055620A1/en

8. EP4159621A3 - Digital twin for an autonomous vehicle  
https://patents.google.com/patent/EP4159621A3/en

## E. Physics-informed neural network (PINN) and related physics-informed ML patents
1. US20220414429A1 - Physics-informed attention-based neural network  
https://patents.google.com/patent/US20220414429A1/en

2. WO2024238788A1 - Training PINN with RANS turbulent-flow formulation  
https://patents.google.com/patent/WO2024238788A1/en

3. US20250165680A1 - 3D displacement using pre-trained PINNs  
https://patents.google.com/patent/US20250165680A1/en

4. US20230409877A1 - Learning-based nonlinear compensation with PINN  
https://patents.google.com/patent/US20230409877A1/en

5. WO2025101591A1 - Physics-informed ML for discrete nonlinear PDEs  
https://patents.google.com/patent/WO2025101591A1/en

6. EP1418541A3 - Physics-based neural network trend detector (earlier related concept)  
https://patents.google.com/patent/EP1418541A3/en

---

## How PINN Relates to This Project

Current project approach:
- rule-based/simple-physics simulator
- noisy sensor emulation
- heuristic/recommender logic from historical telemetry segments

Where PINN can fit:
1. **Physics-consistent state estimation**
- Replace/augment hand-tuned update equations with a PINN constrained by vehicle dynamics equations.
- Benefit: smoother and physically plausible estimates under sparse/noisy sensor input.

2. **Surrogate dynamics model for fast simulation**
- Train PINN to emulate high-fidelity dynamics while preserving conservation/kinematics constraints.
- Benefit: faster-than-CFD/rigid-body full models while maintaining physical structure.

3. **Fault-tolerant sensor fusion**
- Use PINN residuals to detect implausible telemetry packets (dropouts/spikes).
- Benefit: improved robustness for live recommendations.

4. **Trajectory and control recommendation**
- Use PINN-informed predictions for braking/throttle envelopes by track segment.
- Benefit: recommendations grounded in both data and physics constraints.

### Suggested PINN roadmap for this repo
1. Add formal state vector and governing equations (`v`, `yaw`, `temp`, track progress).
2. Log supervised + residual training data from simulation and replay logs.
3. Train baseline MLP and PINN side-by-side for next-state prediction.
4. Compare physically constrained residuals and lap-time prediction error.
5. Deploy PINN only behind feature flag in recommender path.

---

## Fixed Version Snapshot

Key corrected pattern now used in simulator scripts:

```python
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from simulator.sensors.coolant_temp import CoolantTempSimulator

log_path = os.path.join(ROOT, "data", "logs")
realtime_path = os.path.join(ROOT, "data", "realtime.json")
```

This removes CWD-dependent behavior and stabilizes imports/outputs.
=======
### 2) Run simulator (recommended)

Stage-1 physics simulator:

```bash
python simulator/run_simulator_stage_1.py
```

Legacy minimal simulator (kept for reference):

```bash
python simulator/run_simulator_legacy.py
```

### 3) Run dashboard

```bash
streamlit run streamlit_app/app.py
```

## What I changed (bugs + cleanup)

The previous `README.md` was moved to `notes.md`, and this `README.md` was rebuilt to reflect the current repo layout and entry points.

Code fixes / cleanup included:

- Standardized real-time JSON writing to always use `data/realtime.json` (repo-root relative), avoiding path bugs when running scripts from different working directories.
- Removed redundant/legacy simulator implementation and clarified which simulator scripts are current.
- Added inline comments in a few “easy to get wrong” sections (path handling and file writes) and reduced duplicated logic.

## Repo map

- `simulator/` – physics + sensors + scripts to generate data
- `streamlit_app/` – Streamlit UI (multiple pages under `streamlit_app/pages/`)
- `utils/` – helpers for config loading and safe JSON writes
- `notes.md` – the original long-form project notes that used to be the README
>>>>>>> c07c010 (restructuring)
