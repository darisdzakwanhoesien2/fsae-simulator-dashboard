fsae-telemetry-streamlit/
│
├── README.md
├── requirements.txt
│
├── simulator/
│   ├── __init__.py
│   ├── run_simulator.py          # generates data + writes to shared JSON or socket
│   └── sensors/
│       ├── coolant_temp.py
│       ├── brake_pressure.py
│       ├── wheel_speed.py
│       └── imu.py
│
├── data/
│   ├── realtime.json             # simulator writes, dashboard reads 
│   └── logs/
│       ├── session_001.json
│       ├── session_002.json
│
├── streamlit_app/
│   ├── app.py                    # main dashboard
│   ├── pages/
│   │   ├── 1_Realtime_Telemetry.py
│   │   ├── 2_Track_Map.py
│   │   └── 3_Replay_Data.py
│   └── components/
│       ├── gauges.py
│       ├── charts.py
│       └── status_card.py
│
└── utils/
    ├── config.py
    └── data_loader.py

simulator/sensors/coolant_temp.py# fsae-simulator-dashboard
