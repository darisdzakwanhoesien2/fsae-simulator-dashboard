%% Sensitivity Analysis Tool
% This script evaluates the impact of mass, aero, and grip on lap time.

clear; clc; close all;

% Add modular directories to path
addpath('config', 'track', 'vehicle', 'solver', 'analysis');

% --- 1. Load Base Configurations ---
veh_base   = vehicle_params();
tire_base  = tire_params();
aero_base  = aero_params();
motor_base = powertrain_params();
opts       = sim_options();

% --- 2. Track Setup ---
track_raw = track_loader('sample');
track = track_preprocess(track_raw, opts);

% --- 3. Sensitivity Parameters ---
mass_mod = [0.8, 0.9, 1.0, 1.1, 1.2]; % Mass multipliers
grip_mod = [0.8, 0.9, 1.0, 1.1, 1.2]; % Grip multipliers

lap_times_mass = zeros(size(mass_mod));
lap_times_grip = zeros(size(grip_mod));

fprintf('Starting Sensitivity Analysis...\n');

% 3.1 Mass Sensitivity
for i = 1:length(mass_mod)
    veh = veh_base;
    veh.m = veh_base.m * mass_mod(i);
    
    v_max_apex = lateral_speed_limit(track, veh, tire_base, aero_base, opts);
    [v_fw, ~, ~] = forward_pass(track, v_max_apex, veh, tire_base, aero_base, motor_base, opts);
    v_bw = backward_pass(track, v_max_apex, veh, tire_base, aero_base, motor_base, opts);
    res = lap_time_solver(track, v_fw, v_bw);
    lap_times_mass(i) = res.lap_time;
end

% 3.2 Grip Sensitivity
for i = 1:length(grip_mod)
    tire = tire_base;
    % Hack: Modify the D parameter in the anonymous function
    tire.getPacejka = @(Fz) tire_base.getPacejka(Fz) .* [1, 1, grip_mod(i), 1];
    
    v_max_apex = lateral_speed_limit(track, veh_base, tire, aero_base, opts);
    [v_fw, ~, ~] = forward_pass(track, v_max_apex, veh_base, tire, aero_base, motor_base, opts);
    v_bw = backward_pass(track, v_max_apex, veh_base, tire, aero_base, motor_base, opts);
    res = lap_time_solver(track, v_fw, v_bw);
    lap_times_grip(i) = res.lap_time;
end

% --- 4. Plotting ---
figure('Name', 'Sensitivity Analysis', 'NumberTitle', 'off');

subplot(2,1,1);
plot(mass_mod * 100, lap_times_mass, 'b-o', 'LineWidth', 1.5);
grid on;
xlabel('Mass % of Base');
ylabel('Lap Time (s)');
title('Sensitivity: Vehicle Mass');

subplot(2,1,2);
plot(grip_mod * 100, lap_times_grip, 'g-o', 'LineWidth', 1.5);
grid on;
xlabel('Tire Grip % of Base');
ylabel('Lap Time (s)');
title('Sensitivity: Tire Friction');
