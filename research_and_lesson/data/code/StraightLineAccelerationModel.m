%% Straight-Line Acceleration Model (Modular)
% This script simulates a 75m acceleration event.

clear; clc; close all;

% Add modular directories to path
addpath('config', 'track', 'vehicle', 'solver', 'analysis');

% --- 1. Load Configurations ---
veh   = vehicle_params();
tire  = tire_params();
aero  = aero_params();
motor = powertrain_params();
opts  = sim_options();

% --- 2. Track Setup (75m Straight) ---
track_raw.s_raw = [0, 75];
track_raw.r_raw = [Inf, Inf];
track = track_preprocess(track_raw, opts);

% --- 3. Simulation ---
% Apex limit is top speed for a straight
v_max_apex = opts.v_top_limit * ones(size(track.s));

fprintf('Running 75m acceleration simulation...\n');
[v_fw, T_fw, theta_fw] = forward_pass(track, v_max_apex, veh, tire, aero, motor, opts);

% --- 4. Results ---
result.s = track.s;
result.v_final = v_fw; % For acceleration, final is forward pass
result.T_fw = T_fw;
result.theta_fw = theta_fw;
result.max_v = max(v_fw);
result.max_v_kmh = result.max_v * 3.6;

% Calculate 75m time
[~, idx_end] = min(abs(track.s - 75));
% Simple integration for time
v_avg = (v_fw(1:idx_end-1) + v_fw(2:idx_end)) / 2;
dt = diff(track.s(1:idx_end)) ./ (v_avg + 1e-6);
total_time = sum(dt);

fprintf('\n--- MODULAR ACCELERATION RESULTS ---\n');
fprintf('75m Time      : %.3f s\n', total_time);
fprintf('Max Velocity  : %.1f km/h\n', result.max_v_kmh);
fprintf('Max Motor Temp: %.1f degC\n', max(T_fw));
fprintf('Peak Pitch    : %.2f deg\n', rad2deg(max(abs(theta_fw))));

% --- 5. Plotting ---
plot_results(result);
