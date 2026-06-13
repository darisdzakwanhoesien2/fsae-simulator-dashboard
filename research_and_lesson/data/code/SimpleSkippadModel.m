%% FSAE Skidpad Performance Model (Modular)
% This script simulates a vehicle performing a skidpad maneuver.

clear; clc;

% Add modular directories to path
addpath('config', 'vehicle');

% --- 1. Load Configurations ---
veh   = vehicle_params();
tire  = tire_params();
aero  = aero_params();
motor = powertrain_params();
opts  = sim_options();

% --- 2. Simulation Setup ---
r = 9; % Skidpad Radius (m)
v_test = linspace(1, 40, 1000); 

% Results Logging
lat_req_log = zeros(size(v_test));
lat_ava_log = zeros(size(v_test));

% --- 3. Simulation Loop ---
for i = 1:length(v_test)
    v = v_test(i);

    % Attitude-Sensitive Aero (assuming zero pitch initially)
    aero_forces = aero_model(v, 0, aero);
    
    % Vertical Loads
    Fz_total = veh.m * veh.g + aero_forces.F_down;
    ay = v^2 / r;
    
    % Dynamics: Lateral Load Transfer
    load_transfer = veh.m * ay * (veh.h_cg - veh.h_rc) / veh.track;
    Fz_out = (Fz_total / 4) + load_transfer/2;
    Fz_in  = (Fz_total / 4) - load_transfer/2;
    Fz_in  = max(Fz_in, 50);

    % Update Aero based on pitch (simplified pitch from aero moment)
    pitch_est = (aero_forces.F_drag * veh.h_cg) / veh.K_pitch;
    aero_forces = aero_model(v, pitch_est, aero);
    
    % Peak Lateral Force (Pacejka D parameter)
    p_out = tire.getPacejka(Fz_out);
    p_in  = tire.getPacejka(Fz_in);
    Fy_out = p_out(3);
    Fy_in  = p_in(3);

    % Combined Dynamics check (Friction Ellipse)
    F_long_req = (aero_forces.F_drag + (veh.Crr * Fz_total)) / 2; % Required per axle
    
    Fy_out_avail = sqrt(max(Fy_out^2 - F_long_req^2, 0));
    Fy_in_avail  = sqrt(max(Fy_in^2 - F_long_req^2, 0));

    lat_ava_log(i) = 2 * (Fy_out_avail + Fy_in_avail);
    lat_req_log(i) = veh.m * v^2 / r;
end

% --- 4. Analysis ---
[~, idx] = min(abs(lat_ava_log - lat_req_log));
v_max = v_test(idx);

% Outputs
fprintf('\n--- MODULAR SKIDPAD RESULTS ---\n');
fprintf('Max Speed      : %.2f m/s\n', v_max);
fprintf('Lateral Accel  : %.2f g\n', (v_max^2/r)/veh.g);
fprintf('Skidpad Time   : %.2f s\n', (2 * 2*pi*r) / v_max);
