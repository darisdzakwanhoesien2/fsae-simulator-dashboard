from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class NormalizedRow:
    timestamp: Optional[float]
    # Optional simulation time within session (seconds).
    t: Optional[float]
    # Lap counter (0/1-based depending on source).
    lap: Optional[int]
    lap_progress: Optional[float]
    track_index: Optional[int]

    gps_x: Optional[float]
    gps_y: Optional[float]

    # "True" physics values (Stage-1+).
    true_speed_kmh: Optional[float]
    true_coolant_temp: Optional[float]
    true_brake_cmd: Optional[float]
    true_throttle: Optional[float]
    true_yaw_deg: Optional[float]

    # Sensor-style values.
    wheel_speed: Optional[float]
    brake_pressure: Optional[float]
    coolant_temp: Optional[float]
    imu_ax: Optional[float]
    imu_ay: Optional[float]
    imu_yaw: Optional[float]

    raw: Dict[str, Any]


def _get(d: Any, *path: str) -> Any:
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def normalize_session_rows(rows: Iterable[Dict[str, Any]]) -> List[NormalizedRow]:
    """
    Accepts multiple log schemas:
    - Stage-0/legacy: top-level `coolant_temp`, `wheel_speed`, `brake_pressure`, `imu:{ax,ay,yaw}`
    - Stage-1 physics: nested `true:{...}`, `sensors:{...}`, plus gps/lap/track_index
    - Race generator: `lap`, `lap_progress` top-level + Stage-0 sensor fields
    """
    normalized: List[NormalizedRow] = []
    for row in rows:
        sensors = _get(row, "sensors") or {}
        true = _get(row, "true") or {}

        # Prefer nested Stage-1 sensors, otherwise fall back to Stage-0 top-level fields.
        imu_obj = sensors.get("imu")
        legacy_imu = _get(row, "imu") or {}

        wheel_speed = sensors.get("wheel_speed")
        if wheel_speed is None:
            wheel_speed = row.get("wheel_speed")

        brake_pressure = sensors.get("brake_pressure")
        if brake_pressure is None:
            brake_pressure = row.get("brake_pressure")

        coolant_temp = sensors.get("coolant_temp")
        if coolant_temp is None:
            coolant_temp = row.get("coolant_temp")

        gps_x = _get(row, "gps", "x")
        gps_y = _get(row, "gps", "y")

        imu_ax = _get(imu_obj, "ax") if isinstance(imu_obj, dict) else None
        imu_ay = _get(imu_obj, "ay") if isinstance(imu_obj, dict) else None
        imu_yaw = _get(imu_obj, "yaw") if isinstance(imu_obj, dict) else None
        if imu_ax is None:
            imu_ax = legacy_imu.get("ax")
        if imu_ay is None:
            imu_ay = legacy_imu.get("ay")
        if imu_yaw is None:
            imu_yaw = legacy_imu.get("yaw")

        normalized.append(
            NormalizedRow(
                timestamp=row.get("timestamp"),
                t=row.get("t"),
                lap=row.get("lap"),
                lap_progress=row.get("lap_progress"),
                track_index=row.get("track_index"),
                gps_x=gps_x,
                gps_y=gps_y,
                true_speed_kmh=true.get("speed_kmh"),
                true_coolant_temp=true.get("coolant_temp"),
                true_brake_cmd=true.get("brake_cmd"),
                true_throttle=true.get("throttle"),
                true_yaw_deg=true.get("yaw_deg"),
                wheel_speed=wheel_speed,
                brake_pressure=brake_pressure,
                coolant_temp=coolant_temp,
                imu_ax=imu_ax,
                imu_ay=imu_ay,
                imu_yaw=imu_yaw,
                raw=row,
            )
        )
    return normalized

