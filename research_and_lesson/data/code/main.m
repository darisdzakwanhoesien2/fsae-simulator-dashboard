%% FSAE Modular Lap Time Simulator
% Main entry point for the simulation.

clear; clc; close all;

% Add modular directories to path
addpath('config', 'track', 'vehicle', 'solver', 'analysis');

% 1. Load Configurations
fprintf('Loading configurations...\n');
veh   = vehicle_params();
tire  = tire_params();
aero  = aero_params();
motor = powertrain_params();
opts  = sim_options();

% 2. Track Processing
fprintf('Processing track...\n');
track_raw = track_loader('sample');
track = track_preprocess(track_raw, opts);

% 3. Simulation Pipeline
fprintf('Running simulation pipeline...\n');

% 3.1 Lateral Speed Limit (Apex Optimization)
fprintf('  > Calculating lateral speed limits...\n');
v_max_apex = lateral_speed_limit(track, veh, tire, aero, opts);

% 3.2 Forward Pass (Acceleration + Thermal + Transient Pitch)
fprintf('  > Running forward pass...\n');
[v_fw, T_fw, theta_fw] = forward_pass(track, v_max_apex, veh, tire, aero, motor, opts);

% 3.3 Backward Pass (Braking)
fprintf('  > Running backward pass...\n');
v_bw = backward_pass(track, v_max_apex, veh, tire, aero, motor, opts);

% 3.4 Final Results Integration
fprintf('  > Integrating results...\n');
result = lap_time_solver(track, v_fw, v_bw);
result.T_fw = T_fw;
result.theta_fw = theta_fw;

% 3.5 Energy Analysis
fprintf('  > Calculating energy consumption...\n');
energy = energy_solver(track, result, veh, motor);
result.energy = energy;

% 4. Output Results
fprintf('\n--- SIMULATION RESULTS ---\n');
fprintf('Lap Time      : %.3f s\n', result.lap_time);
fprintf('Max Velocity  : %.1f km/h\n', result.max_v_kmh);
fprintf('Max Motor Temp: %.1f degC\n', max(result.T_fw));
fprintf('Peak Pitch    : %.2f deg\n', rad2deg(max(abs(result.theta_fw))));
fprintf('Energy Used   : %.3f kWh\n', energy.total_kWh);
fprintf('SoC Drop      : %.2f %%\n', energy.SoC_drop);

% 5. Analysis & Plotting
plot_results(result);
plot_gg_diagram(track, result, veh, tire, aero, motor);
