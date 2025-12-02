# 📦 Project Directory Structure

**Root:** `/Users/darisdzakwanhoesien/Documents/fsae`

  📄 .DS_Store<br>
  📄 README.md<br>
<details><summary>📁 configs/</summary>
    📄 car_simple.yaml<br>
    📄 sensors.yaml<br>
    📄 simulation.yaml<br>
</details>
<details><summary>📁 data/</summary>
    📄 .DS_Store<br>
  <details><summary>📁 logs/</summary>
      📄 race_session_20251202_093416.json<br>
      📄 session_20251202_081531.json<br>
      📄 session_20251202_081639.json<br>
      📄 session_20251202_092654.json<br>
  </details>
    📄 realtime.json<br>
  <details><summary>📁 tracks/</summary>
      📄 default_track.csv<br>
  </details>
</details>
<details><summary>📁 old_code/</summary>
    📄 1_Realtime_Telemetry.py<br>
    📄 app.py<br>
</details>
  📄 project_directory.md<br>
  📄 requirements.txt<br>
<details><summary>📁 simulator/</summary>
    📄 __init__.py<br>
    📄 driver_profiles.py<br>
  <details><summary>📁 new_sensors/</summary>
      📄 __init__.py<br>
      📄 brake_pressure_sensor.py<br>
      📄 coolant_temp_sensor.py<br>
      📄 imu_sensor.py<br>
      📄 noise_models.py<br>
      📄 wheel_speed_sensor.py<br>
  </details>
  <details><summary>📁 physics/</summary>
      📄 __init__.py<br>
    <details><summary>📁 simple/</summary>
        📄 __init__.py<br>
        📄 dynamics.py<br>
        📄 gps_simulator.py<br>
        📄 steering_yaw.py<br>
        📄 thermal.py<br>
        📄 vehicle_model.py<br>
    </details>
  </details>
    📄 run_race_simulator.py<br>
    📄 run_simulator.py<br>
    📄 run_simulator_stage_1.py<br>
  <details><summary>📁 sensors/</summary>
      📄 brake_pressure.py<br>
      📄 coolant_temp.py<br>
      📄 imu.py<br>
      📄 wheel_speed.py<br>
  </details>
    📄 track_loader.py<br>
</details>
<details><summary>📁 streamlit_app/</summary>
    📄 app.py<br>
  <details><summary>📁 pages/</summary>
      📄 2_Data_Visualization.py<br>
      📄 3_Lap_Visualization.py<br>
  </details>
</details>
  📄 structure_code.py<br>
<details><summary>📁 utils/</summary>
    📄 __init__.py<br>
    📄 config_loader.py<br>
    📄 json_writer.py<br>
</details>