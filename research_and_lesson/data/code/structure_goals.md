A good Formula SAE lap time simulation in MATLAB usually has this structure:

fsae_lap_time_sim/
│
├── main.m
├── config/
│   ├── vehicle_params.m
│   ├── tire_params.m
│   ├── aero_params.m
│   ├── powertrain_params.m
│   └── sim_options.m
│
├── track/
│   ├── track_loader.m
│   ├── track_preprocess.m
│   ├── curvature_from_xy.m
│   └── example_tracks/
│       ├── skidpad.csv
│       ├── autocross.csv
│       └── endurance.csv
│
├── vehicle/
│   ├── vehicle_model.m
│   ├── tire_model.m
│   ├── aero_model.m
│   ├── brake_model.m
│   ├── motor_model.m
│   └── force_limits.m
│
├── solver/
│   ├── forward_pass.m
│   ├── backward_pass.m
│   ├── lateral_speed_limit.m
│   ├── lap_time_solver.m
│   └── energy_solver.m
│
├── analysis/
│   ├── plot_speed_profile.m
│   ├── plot_accel_profile.m
│   ├── plot_forces.m
│   ├── plot_gg_diagram.m
│   └── compare_setups.m
│
└── results/
    ├── speed_profile.csv
    ├── lap_summary.csv
    └── figures/

The simulation should be built around this pipeline:

Track XY points
      ↓
Track distance + curvature
      ↓
Maximum cornering speed from lateral grip
      ↓
Forward acceleration pass
      ↓
Backward braking pass
      ↓
Final velocity profile
      ↓
Lap time integration
      ↓
Plots + setup comparison

For a first version, I would not start with a full 14-DOF vehicle model. Start with a quasi-steady point-mass lap simulator, because it is easier to debug and already useful for Formula SAE setup comparison.

The core model looks like this:

Inputs:
- Vehicle mass
- Tire friction coefficient
- Downforce
- Drag
- Power / torque curve
- Brake force
- Track curvature
Outputs:
- Speed vs distance
- Acceleration vs distance
- Braking zones
- Cornering speed limits
- Lap time
- Energy consumption

A simplified main.m could look like this:

clear; clc; close all;
vehicle = vehicle_params();
tire    = tire_params();
aero    = aero_params();
motor   = powertrain_params();
opts    = sim_options();
track = track_loader("track/example_tracks/autocross.csv");
track = track_preprocess(track);
v_lat_limit = lateral_speed_limit(track, vehicle, tire, aero);
v_forward = forward_pass(track, v_lat_limit, vehicle, tire, aero, motor, opts);
v_final   = backward_pass(track, v_forward, vehicle, tire, aero, opts);
result = lap_time_solver(track, v_final);
plot_speed_profile(track, result);
plot_accel_profile(track, result);
plot_gg_diagram(result);
fprintf("Estimated lap time: %.3f seconds\n", result.lap_time);

Your vehicle parameter file could be like this:

function vehicle = vehicle_params()
vehicle.mass = 250;              % kg, car + driver
vehicle.g = 9.81;                % m/s^2
vehicle.wheelbase = 1.55;        % m
vehicle.track_width = 1.20;      % m
vehicle.cg_height = 0.28;        % m
vehicle.weight_distribution = 0.48; % front fraction
vehicle.max_brake_accel = 1.6 * vehicle.g;
vehicle.drivetrain_efficiency = 0.92;
end

Your tire model can begin very simply:

function Fy_max = tire_model(Fz, tire)
Fy_max = tire.mu * Fz;
end

Then later you can upgrade it to:

Level 1: constant friction coefficient
Level 2: load-sensitive tire model
Level 3: friction ellipse
Level 4: Pacejka / Magic Formula
Level 5: tire temperature and transient behavior

For the lateral speed limit, the basic idea is:

function v_lim = lateral_speed_limit(track, vehicle, tire, aero)
N = length(track.s);
v_lim = zeros(N,1);
for i = 1:N
    kappa = abs(track.curvature(i));
    if kappa < 1e-6
        v_lim(i) = 100; % effectively straight
    else
        % Basic cornering estimate:
        % v = sqrt(mu * g / curvature)
        v_lim(i) = sqrt(tire.mu * vehicle.g / kappa);
    end
end
end

A more realistic version includes downforce:

Fz_total = vehicle.mass * vehicle.g + 0.5 * rho * aero.ClA * v^2;
Fy_max = tire.mu * Fz_total;
ay_max = Fy_max / vehicle.mass;
v_max = sqrt(ay_max / curvature);

The forward pass calculates how fast the car can accelerate from point to point:

At each distance step:
1. Get current speed
2. Compute available motor force
3. Compute drag
4. Compute rolling resistance
5. Compute traction limit
6. Compute acceleration
7. Predict next speed
8. Do not exceed lateral speed limit

The backward pass enforces braking feasibility:

Starting from the end of the lap:
1. Look at next allowed speed
2. Calculate maximum braking deceleration
3. Compute previous allowable speed
4. Limit current speed if needed

This is the most important structure for lap simulation:

Forward pass = acceleration constraint
Backward pass = braking constraint
Lateral limit = cornering constraint

The final lap time is computed by integrating distance over speed:

dt = ds ./ v;
lap_time = sum(dt);

A cleaner formula is:

dt(i) = 2 * ds(i) / (v(i) + v(i+1));

For Formula SAE, your main research/engineering questions should be:

1. How does vehicle mass affect lap time?
2. How much does downforce improve autocross/endurance time?
3. Is the car power-limited or grip-limited?
4. Which corners are braking-limited?
5. Which straights are acceleration-limited?
6. How sensitive is lap time to tire friction?
7. How much benefit comes from better braking?
8. How much energy is consumed per lap?
9. What setup gives the best trade-off between drag and downforce?
10. How does track curvature shape the speed profile?

For your first version, I suggest this development order:

Version 1: Point-mass model
- Track curvature
- Constant tire friction
- Forward/backward speed solver
- Lap time output
Version 2: Add aero
- Downforce
- Drag
- Drag/downforce trade-off
Version 3: Add powertrain
- Motor torque curve
- Gear ratio
- Battery power limit
- Regeneration if EV
Version 4: Add tire realism
- Load sensitivity
- Friction ellipse
- Combined braking/cornering
Version 5: Add setup comparison
- Mass sensitivity
- Tire sensitivity
- Aero package sensitivity
- Brake balance
- Gear ratio sweep
Version 6: Add Simulink/Vehicle Dynamics Blockset
- More detailed longitudinal/lateral vehicle model
- Controller behavior
- Driver model
- Validation against telemetry

The best initial folder to build is:

main.m
vehicle_params.m
track_loader.m
track_preprocess.m
lateral_speed_limit.m
forward_pass.m
backward_pass.m
lap_time_solver.m
plot_speed_profile.m

That gives you a working “minimum viable” Formula SAE lap time simulator. After that, you can slowly make it more realistic.
