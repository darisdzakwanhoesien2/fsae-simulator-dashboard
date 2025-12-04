# 🚗 FSAE Telemetry Simulator & Streamlit Dashboard

A complete Formula SAE–style telemetry system consisting of:

* **Real-time data simulator** (10 Hz)
* **Race simulation generator** (multi-lap, fast generation)
* **Streamlit telemetry dashboard** (real-time, replay, track map)
* **Sensor models** for coolant, brake pressure, wheel speed, and IMU
* **Lap-based visualization tools** for performance analysis

This project is fully standalone and can be used for FSAE simulation, driver training analytics, experiment logging, or educational demos.

---

## 📁 Project Structure (Stage 2)

```
fsae-telemetry-physics/
│
├── README.md
├── requirements.txt
│
├── data/
│   ├── realtime.json
│   ├── logs/
│   └── tracks/
│       ├── default_track.csv
│       ├── track_map.png
│       └── track_metadata.json
│
├── configs/
│   ├── simulation.yaml            # timestep, duration, randomness
│   ├── sensors.yaml               # noise, dropout, frequency
│   ├── car_simple.yaml            # Option A physics parameters
│   ├── car_intermediate.yaml      # Option B parameters
│   └── car_advanced.yaml          # Option C full dynamics
│
├── simulator/
│   ├── run_simulator.py           # selects physics engine A/B/C
│   ├── driver_profiles.py         # throttle/brake/steer functions
│   ├── track_loader.py            # loads CSV or synthetic tracks
│   │
│   ├── physics/
│   │   ├── core/                  # shared mathematical functions
│   │   │   ├── units.py
│   │   │   └── integrators.py     # RK4, Euler integrators (for upgrades)
│   │   │
│   │   ├── simple/                # Option A simplified physics
│   │   │   ├── vehicle_model.py
│   │   │   ├── dynamics.py
│   │   │   ├── thermal.py
│   │   │   └── steering_yaw.py
│   │   │
│   │   ├── intermediate/          # Option B more detailed
│   │   │   ├── vehicle_model.py
│   │   │   ├── dynamics_longitudinal.py
│   │   │   ├── dynamics_lateral.py
│   │   │   ├── thermal_full.py
│   │   │   └── aero_map.py
│   │   │
│   │   └── advanced/              # Option C racing simulator style
│   │       ├── vehicle_model.py
│   │       ├── pacejka_tire.py
│   │       ├── combined_slip.py
│   │       ├── suspension_model.py
│   │       ├── powertrain_model.py
│   │       └── cooling_aero_model.py
│   │
│   └── new_sensors/
│       ├── imu_sensor.py
│       ├── wheel_speed_sensor.py
│       ├── brake_pressure_sensor.py
│       ├── coolant_temp_sensor.py
│       ├── motor_temp_sensor.py
│       └── noise_models.py
│
├── streamlit_app/
│   ├── app.py
│   ├── pages/
│   │   ├── 1_Realtime_Telemetry.py
│   │   ├── 2_Data_Visualization.py
│   │   ├── 3_Lap_Overview.py
│   │   ├── 4_Track_Map.py
│   │   └── 5_Session_Comparison.py
│   └── components/
│       ├── matplotlib_utils.py
│       ├── summary_cards.py
│       └── telemetry_plots.py
│
├── analysis/
│   ├── notebooks/
│   │   ├── physics_model_validation.ipynb
│   │   ├── sensor_noise_analysis.ipynb
│   │   └── track_simulation_demo.ipynb
│   └── scripts/
│       ├── export_to_csv.py
│       └── session_cleaner.py
│
└── utils/
    ├── json_writer.py
    ├── logger.py
    ├── config_loader.py
    ├── lap_timer.py
    └── math_utils.py

```

## 📁 Project Structure

```
fsae-telemetry-streamlit/
│
├── README.md
├── requirements.txt
│
├── simulator/
│   ├── __init__.py
│   ├── run_simulator.py             # real-time simulator (10 Hz)
│   ├── run_race_simulator.py        # fast multi-lap race simulator
│   └── sensors/
│       ├── coolant_temp.py
│       ├── brake_pressure.py
│       ├── wheel_speed.py
│       └── imu.py
│
├── data/
│   ├── realtime.json                # real-time bridge between simulator and dashboard
│   └── logs/
│       ├── session_001.json
│       ├── session_002.json
│       └── race_session_YYYYMMDD.json
│
├── streamlit_app/
│   ├── app.py                       # main dashboard entry point
│   ├── pages/
│   │   ├── 1_Realtime_Telemetry.py  # live updates from realtime.json
│   │   ├── 2_Track_Map.py           # visual track map (optional)
│   │   └── 3_Replay_Data.py         # load and visualize recorded logs
│   └── components/
│       ├── gauges.py                # speed, temp, brake UI widgets
│       ├── charts.py                # matplotlib/plotly visualization modules
│       └── status_card.py           # UI component for sensor status
│
└── utils/
    ├── config.py                    # shared constants and settings
    └── data_loader.py               # JSON/streaming data parser
```

---

## 🔧 Installation

### **1. Clone the repository**

```bash
git clone https://github.com/<your-username>/fsae-telemetry-streamlit.git
cd fsae-telemetry-streamlit
```

### **2. Install dependencies**

Recommend using a virtual environment.

```bash
pip install -r requirements.txt
```

---

## 🏎️ Running the Simulators

### **A) Real-Time Simulator (10 Hz continuous)**

Writes values to:

```
data/realtime.json
data/logs/session_*.json
```

Run:

```bash
python simulator/run_simulator.py
```

Press **CTRL+C** to stop and save the session.

---

### **B) Multi-Lap Race Generator (fast, non-real-time)**

Generates 10-lap simulation instantly (with tqdm progress).

Run:

```bash
python simulator/run_race_simulator.py
```

Outputs to:

```
data/logs/race_session_YYYYMMDD_HHMMSS.json
```

---

## 📊 Running the Streamlit Dashboard

Launch the telemetry interface:

```bash
streamlit run streamlit_app/app.py
```

This opens a dashboard with:

### **1. Real-Time Telemetry**

Pulls the latest frame from `data/realtime.json`.

### **2. Track Map View**

(If implemented) Displays IMU/Yaw + wheel speed on a track map.

### **3. Session Replay & Lap Analysis**

Loads log files from `data/logs/*.json` and renders:

* Time-series coolant, speed, brake pressure, IMU
* Lap-by-lap comparison
* Overlay plots (speed comparison between laps)
* Mini-multiples lap grid
* Correlation heatmaps

---

## 🛠️ Sensor Models Included

| Sensor         | Description                                          | File                |
| -------------- | ---------------------------------------------------- | ------------------- |
| Coolant Temp   | Thermal dynamics, load oscillation, cooling behavior | `coolant_temp.py`   |
| Wheel Speed    | Sinusoidal + noise speedCurve                        | `wheel_speed.py`    |
| Brake Pressure | Random braking events with decay                     | `brake_pressure.py` |
| IMU            | Lateral acceleration, yaw oscillation                | `imu.py`            |

All sensors expose a simple API:

```python
value = sensor.step()
```

---

## 📈 Data Format

Each simulator output frame contains:

```json
{
  "lap": 1,
  "lap_progress": 0.42,
  "coolant_temp": 68.55,
  "wheel_speed": 74.3,
  "brake_pressure": 22.41,
  "imu": {
    "ax": 0.01,
    "ay": -0.12,
    "yaw": 1.27
  }
}
```

Real-time simulator also includes UNIX timestamp:

```json
"timestamp": 1733124234.022
```

---

## 🚀 Roadmap / Future Features

* Real GPS-based track maps (CSV or GPX import)
* Driver inputs (throttle, steering, gear)
* G-G acceleration plot
* Lap time prediction via ML
* Interactive replay scrubber
* CAN-Bus ingestion module
* MQTT / WebSocket live telemetry

---

## 🤝 Contributions

Pull requests are welcome!
If you’d like help adding new visualizations, sensors, or ML models, feel free to ask.

---

## 📜 License

MIT License — free to use, modify, and share.


There are 4 different stages, which is
1. General Simulation
2. Simplified Physics (Easier, fast, still realistic)

Speed = engine - brake - drag

Yaw = steering sensitivity

Coolant = heat from speed + throttle

GPS along simple oval track

Perfect starter + good for visualization

3. Intermediate Physics (More detailed)

Longitudinal & lateral acceleration

Tire cornering stiffness

Weight transfer (braking & cornering)

Yaw integrates over time

Engine power curve

Brake fade

Cooling airflow model

Still real-time friendly (100 Hz OK)

4. Advanced Physics (Almost racing sim level)

Pacejka tire model

Combined slip forces

Suspension kinematics

Torque curves & shift logic

Brake torque distribution

Aero map

Differential model

Not needed for telemetry dashboard unless FSAE team uses it for simulation research

🏁 You now have a full motorsport-grade visualization module

This is aligned with real F1/FSAE data engineering practices:

Lap segmentation

Lap progress normalization

Multi-lap overlays

Mini-map style small multiples

Per-lap sensor stack

🚀 Want to go even further?

I can add:

🔥 Optimal Lap Comparison (find fastest lap + overlay)
🔥 Sector Times (S1/S2/S3 auto-segmentation)
🔥 Braking zone detection (peak brake-pressure triggers)
🔥 G-G Diagram (longitudinal vs lateral accelerations)
🔥 Dashboard Export (PDF/PNG/CSV per lap)

Just tell me what you want next.

🎉 What this final version gives you
✔ No more errors

Thanks to IMU-safe flattening.

✔ Correct lap progress

Based on track_index.

✔ Multi-channel lap analysis

Speed, coolant, brake, yaw.

✔ Multi-lap overlay

Compare any laps.

✔ Small multiples (“sparklines”)

Classic motorsport visualization.

✔ GPS colored by lap

Very useful for consistency checks.

✔ Clean, maintainable, future-proof code

This is now production-grade FSAE telemetry visualization.

🚀 Want to upgrade next?

I can add:

🔥 Delta-Time comparison (F1 style)

Compare any lap vs fastest lap.

📍 Corner detection

Based on yaw or curvature.

🟦 Sector times

S1 / S2 / S3 automatically generated.

🧊 Cooling-performance analysis

Temp vs throttle vs speed correlation.

🛠 Sensor dropout visualization

Just tell me:
👉 “Add delta-time comparison”
or
👉 “Add sector timing”
or
👉 “Add corner detection”

# ✔ Example Usage

Run sim with aggressive driver:

```bash
python simulator/run_simulator_with_recommender.py --driver-id driver_aggressive --target-laps 5
```

Run with recommendations:

```bash
python simulator/run_simulator_with_recommender.py --use-policy --target-laps 5
```

Train regressors too:

```bash
python simulator/run_simulator_with_recommender.py --use-policy --train-models --target-laps 5
```

---

# 🧠 What’s next?

I can help you extend this into a **Driver Behavior Analytics** dashboard:

### 🚦 Driver Modeling Features

* consistent throttle/brake signature analysis
* steering smoothness score
* braking efficiency index
* jerk (rate of change of acceleration)
* corner-entry & exit speed comparison
* best-line estimation from GPS clusters

### 🧠 Recommendation Engine 2.0

* ML → regression & clustering per driver style
* RL → Q-learning / PPO for lap-time optimization
* Ghost racing line generation

If you want these features, tell me:

👉 *“Let’s add driver analytics”*
or
👉 *“Let’s build RL-based racing optimization”*

I can generate the entire pipeline for you.

🎁 BONUS FEATURE

If you want, I can also automatically generate:

✔ Track difficulty scoring

Based on:

average corner radius

number of transitions

length of straights

speed profiles

✔ Best racing line estimation

Using spline smoothing and curvature minimization.

✔ Lap-time estimation based on your physics model

Using:

simulated throttle/brake

simulated grip limit

simple lateral acceleration model

✔ "Suggest optimal driver strategy for this track"
🚀 What next?

Which would you like me to build next?

1️⃣ Racing line optimizer
2️⃣ Lap-time predictor
3️⃣ Track difficulty map (color-coded)
4️⃣ Best braking zones detection
5️⃣ Driver coaching system (“Brake later at T3”, etc)