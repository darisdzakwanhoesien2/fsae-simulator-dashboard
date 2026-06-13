%% Gear Ratio Optimization Sweep
% This script finds the optimal gear ratio for a given track.

clear; clc; close all;

% Add modular directories to path
addpath('config', 'track', 'vehicle', 'solver', 'analysis');

% --- 1. Load Base Configurations ---
veh   = vehicle_params();
tire  = tire_params();
aero  = aero_params();
motor_base = powertrain_params();
opts  = sim_options();

% --- 2. Track Setup ---
track_raw = track_loader('sample');
track = track_preprocess(track_raw, opts);

% --- 3. Optimization Setup ---
gr_range = linspace(2.5, 5.5, 15);
lap_times = zeros(size(gr_range));
max_temps = zeros(size(gr_range));

fprintf('Starting gear ratio sweep...\n');

for i = 1:length(gr_range)
    % Update gear ratio
    motor = motor_base;
    motor.GR = gr_range(i);
    
    % Run Simulation Pipeline
    v_max_apex = lateral_speed_limit(track, veh, tire, aero, opts);
    [v_fw, T_fw, ~] = forward_pass(track, v_max_apex, veh, tire, aero, motor, opts);
    v_bw = backward_pass(track, v_max_apex, veh, tire, aero, motor, opts);
    result = lap_time_solver(track, v_fw, v_bw);
    
    lap_times(i) = result.lap_time;
    max_temps(i) = max(T_fw);
    
    fprintf('  GR: %.2f | Lap Time: %.3f s | Max Temp: %.1f C\n', ...
            gr_range(i), lap_times(i), max_temps(i));
end

% --- 4. Find Optimal ---
[min_time, best_idx] = min(lap_times);
best_gr = gr_range(best_idx);

fprintf('\n--- SWEEP RESULTS ---\n');
fprintf('Optimal Gear Ratio: %.2f\n', best_gr);
fprintf('Minimum Lap Time  : %.3f s\n', min_time);

% --- 5. Plotting ---
figure('Name', 'Gear Ratio Optimization', 'NumberTitle', 'off');

subplot(2,1,1);
plot(gr_range, lap_times, 'b-o', 'LineWidth', 1.5);
hold on;
plot(best_gr, min_time, 'rx', 'MarkerSize', 10, 'LineWidth', 2);
grid on;
ylabel('Lap Time (s)');
title('Gear Ratio vs Lap Time');

subplot(2,1,2);
plot(gr_range, max_temps, 'r-o', 'LineWidth', 1.5);
grid on;
xlabel('Gear Ratio');
ylabel('Max Motor Temp (C)');
title('Gear Ratio vs Motor Thermal Stress');
