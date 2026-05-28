codex resume 019e6ebb-1fab-7641-ae4c-aad2dd126aba

# FSAE Simulator Dashboard - Code Review and Fix Report

This file replaces the previous project README (moved to `notes.md`) and records a targeted bug-fix pass.

## 1. Bugs, Errors, or Broken Logic Identified

1. **Hard syntax error in live recommendation engine**
- File: `simulator/live_recommendation.py`
- Issue: Function signature had an extra closing bracket:
  - `) -> Dict[str, Any]]:`
- Impact: Python cannot import/execute this module; runtime fails immediately with `SyntaxError: unmatched ']'`.

2. **Redundant/unused import**
- File: `simulator/live_recommendation.py`
- Issue: `import os` was unused.
- Impact: No runtime failure, but unnecessary noise and weaker readability.

## 2. Issues Fixed

### Fixed code (`simulator/live_recommendation.py`)

```python
import numpy as np
from typing import Dict, Any, List

from simulator.recommender import (
    load_all_sessions,
    build_segment_database,
)

# ============================================================
# PART 1 — Build Segment Reference From Historical Data
# ============================================================
def build_segment_reference(
    limit_sessions: int | None = None,
    min_samples_per_segment: int = 5,
) -> Dict[int, Dict[str, Any]]:
    ...

# ============================================================
# PART 2 — Live Recommendation Engine
# ============================================================
def recommend_for_packet(
    packet: Dict[str, Any],
    segment_ref: Dict[int, Dict[str, Any]],
    speed_margin: float = 8.0,
    throttle_margin: float = 0.2,
    brake_margin: float = 0.2,
) -> Dict[str, Any]:
    """
    Produce live coaching feedback for a telemetry packet.
    Used by Streamlit's real-time viewer.
    ...
    """

    messages: List[str] = []

    # "true" is the canonical source of simulator state in each packet.
    true = packet.get("true", {})
    idx = packet.get("track_index", None)

    ...
```

## 3. Code Cleanup Performed

1. Removed unused `os` import from `simulator/live_recommendation.py`.
2. Kept changes minimal and focused to avoid behavior regressions.

## 4. Inline Comments Added for Complex Logic

1. Added an inline comment clarifying why `packet["true"]` is used as the canonical telemetry source in live recommendation logic.

## 5. Verification and Summary of Changes

### Verification run
- Command: `python3 -m compileall -q .`
- Result: **Pass** (no syntax errors after fixes)

### Summary of what changed and why

1. **Syntax repair** in `recommend_for_packet` return annotation to restore module importability and runtime correctness.
2. **Readability cleanup** by removing an unused import.
3. **Maintainer clarity** improved with a focused inline comment where packet parsing could otherwise be ambiguous.

## Files changed

- `notes.md` (previous README content moved here)
- `README.md` (this report)
- `simulator/live_recommendation.py` (bug fix + cleanup + inline comment)

---

## Project Documentation

## 1. Project Overview

`fsae-simulator-dashboard` is a Formula SAE telemetry simulation and analysis project.

It simulates vehicle dynamics, synthetic sensors, lap progress, and driver inputs, then exposes that telemetry in a Streamlit dashboard for:
- realtime telemetry monitoring
- lap/session visualization
- driver profile comparison
- track selection/design experiments
- live coaching recommendations based on historical session data

### Problem it solves

FSAE teams often need a safe, repeatable environment to test telemetry pipelines, driver analysis logic, and coaching heuristics without requiring track time or hardware-in-the-loop every iteration. This project provides that offline simulation + visualization loop.

## 2. Tech Stack

### Languages
- Python 3

### Core libraries currently declared
- `numpy`
- `pyyaml`
- `tqdm`

### Libraries used in source code (install as needed)
- `streamlit`
- `pandas`
- `matplotlib`
- `scikit-learn` (optional, for recommender model training)

## 3. Architecture Overview

Top-level components:

1. `simulator/`
- simulation runners (`run_simulator_with_recommender.py`, etc.)
- physics (`simulator/physics/simple/*`)
- synthetic sensors (`simulator/new_sensors/*`, `simulator/sensors/*`)
- track generation/loading (`simulator/track_loader.py`)
- recommendation logic (`simulator/recommender.py`, `simulator/live_recommendation.py`)

2. `streamlit_app/`
- multi-page Streamlit UI for realtime telemetry, visualization, track tools, driver analysis, and coaching pages

3. `configs/`
- YAML config for simulation timestep/frequency and sensor/car parameters

4. `data/`
- runtime outputs (`realtime.json`, `sim_progress.json`, session logs, generated tracks)

5. `utils/`
- helpers for YAML loading and JSON writing

### Data flow

1. Simulator loop computes true vehicle state and sensor readings.
2. Latest packet is written to `data/realtime.json`.
3. Full session is appended to `data/logs/race_session_*.json`.
4. Streamlit pages read these files to render live metrics/charts and recommendations.
5. Recommendation modules build per-segment references from past logs and provide coaching text for incoming packets.

## 4. Installation & Setup

### Prerequisites
- Python 3.10+ recommended
- `pip`

### Step-by-step

1. Clone repository and enter it.
2. Create and activate a virtual environment.
3. Install dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install streamlit pandas matplotlib scikit-learn
```

Notes:
- `scikit-learn` is optional unless you use `--train-models`.
- `streamlit/pandas/matplotlib` are required for the dashboard pages.

## 5. Usage Guide

### A. Run dashboard

```bash
streamlit run streamlit_app/app.py
```

Then open the app URL shown by Streamlit (typically `http://localhost:8501`).

### B. Run simulator directly

From project root:

```bash
python3 simulator/run_simulator_with_recommender.py \
  --driver-id driver_normal \
  --target-laps 3 \
  --track default_track.csv
```

Optional flags:
- `--use-policy` use loaded driver policy
- `--train-models` train segment models from logs first
- `--limit-sessions N` limit training session count
- `--data-dir`, `--track-dir`, `--log-dir`, `--progress-file` override runtime paths

### C. Live workflow example

1. Start Streamlit app.
2. Open live simulation page (track selector/live telemetry page).
3. Start simulation from UI.
4. Observe speed/brake/coolant/yaw + position updates.
5. Open driving assistant page to view per-segment coaching.

## 6. API Reference

This project does **not** expose an HTTP/REST API by default.

Instead, it uses file-based interfaces:

### `data/realtime.json` (latest packet)

Producer: simulator
Consumer: Streamlit pages

Example shape:

```json
{
  "timestamp": 1760000000.0,
  "t": 12.3,
  "lap": 1,
  "track_index": 42,
  "driver_id": "driver_normal",
  "gps": { "x": 10.2, "y": -3.4 },
  "true": {
    "speed_kmh": 71.5,
    "coolant_temp": 78.1,
    "brake_cmd": 0.12,
    "throttle": 0.64,
    "yaw_deg": 1.4
  },
  "sensors": {
    "wheel_speed": 71.2,
    "brake_pressure": 11.7,
    "coolant_temp": 78.0,
    "imu": { "ax": 0.0, "ay": 0.0, "yaw": 1.38 }
  }
}
```

### `data/sim_progress.json` (progress)

Example:

```json
{
  "lap": 2,
  "target": 5
}
```

### `data/logs/race_session_*.json` (session logs)

Array of packets collected during a run, used for replay/analysis/recommendation training.

## 7. Environment Variables

No required `.env` variables are currently implemented in code.

Current behavior:
- paths/config are supplied via CLI flags and YAML files
- Streamlit pages derive paths from repository root

If you want `.env` support, a typical extension would be variables like:
- `FSAE_DATA_DIR`
- `FSAE_TRACK_DIR`
- `FSAE_LOG_DIR`
- `FSAE_REALTIME_FILE`

## 8. Contributing Guide

### Development workflow

1. Create a feature branch.
2. Make focused changes.
3. Run quick validation:

```bash
python3 -m compileall -q .
```

4. Manually test critical flows:
- run simulator
- run Streamlit app
- verify realtime page reads `data/realtime.json`

5. Open a PR with:
- problem statement
- approach
- test evidence
- screenshots for UI changes (if applicable)

### Contribution standards

- Keep patches small and cohesive.
- Prefer explicit paths and clear naming.
- Add comments only where logic is non-obvious.
- Avoid breaking file-based data contracts used by Streamlit pages.

## 9. License

No license file is currently present in this repository.

Until a license is added, treat the code as all-rights-reserved by default. Add a `LICENSE` file (for example MIT/Apache-2.0) to define usage terms.

---

## Scaling Guide

This section describes how to scale this project from a local MVP to a production-grade system.

## 1. Current Bottlenecks

What will break first under load in the current implementation:

1. File-based state sharing (`data/realtime.json`, `data/sim_progress.json`)  
- Multiple writers/readers can race or read partial writes.
- No concurrency control, no transactional guarantees.

2. Streamlit runtime model  
- Streamlit is excellent for internal tools, but it is not ideal as a high-concurrency app server.
- Long-running loops in pages can block per-session execution.

3. Session log growth (`data/logs/*.json`)  
- Large JSON arrays become slow to write/read.
- Full-file rewrites are expensive and fragile.

4. In-process recommendation/training  
- Model prep and segment-reference building happen in app/runtime process.
- CPU-heavy operations contend with request/UI responsiveness.

5. Single-node architecture  
- No queueing, no stateless API tier, no autoscaling boundary.

## 2. Database Scaling

Current state: no production database; telemetry is stored in JSON files.

Recommended progression:

1. Move telemetry to a managed relational DB for metadata + time-series store for telemetry.
- PostgreSQL (RDS/Cloud SQL/Azure Database for PostgreSQL) for sessions, drivers, tracks, aggregates.
- TimescaleDB extension (or ClickHouse/BigQuery) for high-volume telemetry points.

2. Indexing strategy
- Core indexes:
  - `(session_id, timestamp)`
  - `(driver_id, timestamp)`
  - `(track_id, lap, track_index)`
- Partition telemetry by day/week and optionally by `track_id`.

3. Caching
- Redis for hot reads:
  - latest packet per active session
  - leaderboard/aggregate panels
  - precomputed recommendation payloads

4. Read scaling
- Add read replicas for dashboard-heavy query workloads.
- Route writes to primary, analytics reads to replicas.

5. Sharding (later stage)
- Shard telemetry by tenant/team or time window when single-cluster IOPS/size becomes limiting.

## 3. Backend Scaling

Introduce a backend API service between UI and simulation data.

1. Separate services
- `ingest-service`: receives telemetry (HTTP/gRPC/Kafka consumer).
- `query-service`: serves dashboard/reports.
- `recommendation-service`: online inference + offline retraining jobs.

2. Horizontal vs vertical scaling
- Start vertical for simplicity (larger CPU/RAM instance).
- Move to horizontal scaling once CPU saturation or concurrency is sustained:
  - stateless API pods behind load balancer
  - autoscaling based on CPU/RPS/queue depth

3. Load balancing
- Use ALB (AWS) / Cloud Load Balancing (GCP) / Azure Application Gateway.
- Add health checks and graceful shutdown/drain.

4. Async processing
- Queue heavy work (feature extraction, model training, exports) via SQS/PubSub/Service Bus + worker pool.

## 4. Frontend Scaling

If staying with Streamlit:
- Put Streamlit behind reverse proxy + autoscaling compute.
- Offload static assets and plots to object storage + CDN when possible.

If moving to production web app:

1. CDN
- CloudFront / Cloud CDN / Azure CDN for static assets.

2. Lazy loading
- Defer heavy charts/tables and load by viewport/tab.

3. SSR/SSG options
- Next.js recommended:
  - SSR for live/role-based dashboards
  - SSG/ISR for docs, static metric pages

4. Real-time transport
- Use WebSocket/SSE for live telemetry instead of file polling.

## 5. Infrastructure Recommendation (Cloud)

Example AWS reference setup (equivalents available on GCP/Azure):

1. Compute
- API + workers on ECS Fargate or EKS.
- Optional Streamlit internal UI on separate service.

2. Data
- RDS PostgreSQL (+ read replicas).
- Redis (ElastiCache).
- S3 for raw logs, exports, model artifacts.

3. Streaming / queue
- Kinesis or SQS (start with SQS).

4. Networking & edge
- ALB + CloudFront + Route53 + ACM TLS.

5. Observability
- CloudWatch metrics/logs, X-Ray tracing, alarms.

6. Security
- IAM least privilege, Secrets Manager, private subnets, WAF on public edge.

Equivalent services:
- GCP: Cloud Run/GKE, Cloud SQL, Memorystore, GCS, Pub/Sub, Cloud Load Balancing, Cloud Armor.
- Azure: Container Apps/AKS, Azure Database for PostgreSQL, Azure Cache for Redis, Blob Storage, Service Bus/Event Hubs, Front Door.

## 6. Cost Estimate (Rough)

Assumptions:
- Users are monthly active users (MAU), moderate telemetry usage.
- Includes app compute, DB, cache, storage, CDN, monitoring.
- Excludes engineering salaries/support.

1. 1k users
- Approx: **$150-$600/month**
- Typical stack: 1-2 small app instances, single DB instance, small Redis, light object storage/CDN.

2. 10k users
- Approx: **$800-$3,500/month**
- Typical stack: autoscaled app tier, medium DB + 1 read replica, larger Redis, queue workers, higher CDN egress.

3. 100k users
- Approx: **$6,000-$30,000+/month**
- Typical stack: multi-AZ services, multiple replicas, managed streaming/queues, stronger observability/security, significant data transfer.

Cost drivers that spike fastest:
- telemetry write volume
- dashboard query complexity
- egress/CDN bandwidth
- retention period for raw telemetry

## 7. Roadmap (MVP to Production-Grade)

1. MVP hardening (now)
- Remove file-based shared state for live data.
- Add API layer and structured DB schema.
- Add centralized logging + basic metrics.

2. Early scale
- Introduce Redis cache and background worker queue.
- Add DB indexes + partitioning.
- Containerize services and deploy with load balancer.

3. Growth stage
- Add read replicas and query optimization.
- Move heavy analytics/recommendation training to async jobs.
- Add autoscaling policies and SLO-based alerting.

4. Production-grade
- Multi-AZ deployment, backup/restore drills, disaster recovery plan.
- WAF, secrets rotation, audit logging, tighter IAM.
- CI/CD with canary or blue/green deploys.

5. Large-scale optimization
- Time-series optimized storage/sharding strategy.
- WebSocket/SSE live channel.
- Cost controls: lifecycle policies, cold storage, per-feature usage budgets.
