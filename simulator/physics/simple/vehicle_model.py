# simulator/physics/simple/vehicle_model.py
CAR = {
    "mass": 210.0,
    "drag_coeff": 0.9,
    "frontal_area": 1.0,
    "air_density": 1.225,
    "rolling_resistance": 0.015,
    "wheelbase": 1.5,
    "cg_height": 0.25,
    "max_engine_force": 6000.0,
    "max_brake_force": 1500.0,
    "initial_coolant_temp": 60.0,
    # Aero
    "downforce_coeff": 1.2,
    "aero_balance": 0.5,
    # Tire
    "tire_compound": "medium",
    "tire_initial_wear": 0.0,
    "tire_mu": 1.2,
    # Fuel
    "fuel_capacity_kg": 100.0,
    "fuel_initial_kg": 80.0,
    "fuel_consumption_rate": 0.5,
}
