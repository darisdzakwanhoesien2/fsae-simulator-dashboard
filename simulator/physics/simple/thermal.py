# simulator/physics/simple/thermal.py

def update_coolant_temp(temp_c, throttle, speed_kmh, dt=0.1,
                        heat_coeff=0.8, speed_heat_factor=0.01, cooling_coeff=0.08):
    """
    Simple thermal model:
      - heat generation ~ throttle
      - speed adds to heat (e.g., accessory load/friction)
      - cooling proportional to speed (airflow)
    """
    heat_gen = throttle * heat_coeff
    speed_heat = speed_kmh * speed_heat_factor
    cooling = cooling_coeff * (speed_kmh / 40.0)  # normalized
    temp_c += (heat_gen + speed_heat - cooling) * dt * 10.0
    return temp_c
