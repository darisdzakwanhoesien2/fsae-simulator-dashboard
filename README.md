# 🚗 FSAE Telemetry Simulator & Streamlit Dashboard

A complete Formula SAE–style telemetry system consisting of:

* **Real-time data simulator** (10 Hz)
* **Race simulation generator** (multi-lap, fast generation)
* **Streamlit telemetry dashboard** (real-time, replay, track map)
* **Sensor models** for coolant, brake pressure, wheel speed, and IMU
* **Lap-based visualization tools** for performance analysis

This project is fully standalone and can be used for FSAE simulation, driver training analytics, experiment logging, or educational demos.

---

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