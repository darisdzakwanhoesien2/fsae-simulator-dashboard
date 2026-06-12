%% FSAE Quasi-Steady State Lap Time Simulator (Phase 2)
% This script implements a path-following simulation using G-G-V envelopes,
% apex optimization, and forward-backward integration.

clear; clc;

% --- VEHICLE PARAMETERS (Consistent with Phase 1) ---
veh.m = 300; veh.g = 9.81; veh.L = 1.530; veh.h_cg = 0.280;
veh.track = 1.20; veh.h_rc = 0.05; veh.K_pitch = 50000;
veh.rho = 1.225; veh.A = 1.1; veh.Crr = 0.012;
veh.r_wheel = 0.229; veh.GR = 3.5; veh.eta = 0.90;

% Motor Map (EMRAX)
veh.rpm_map = [0 500 1000 2000 3000 4000 5000 5500 6000 6500];
veh.torque_map = [230 230 230 230 230 230 230 210 190 180];

% High-Fidelity Functions
getPacejka = @(Fz) [10*(1-0.00002*Fz), 1.9, (1.80-0.00004*Fz)*Fz, 0.97*(1+0.00001*Fz)];
getAero = @(theta) struct('Cl', 2.8*(1+0.8*sin(theta)), 'Cd', 1.3*(1+0.5*sin(theta)));

% --- TRACK DEFINITION (Sample: Straight -> Curve -> Straight) ---
% s: distance along path (m), r: radius of curvature (m, Inf for straight)
track_s = [0, 50, 100, 150, 200];
track_r = [Inf, Inf, 15, Inf, Inf]; 

% Interpolate track for integration
s_steps = linspace(0, 200, 400);
r_steps = interp1(track_s, track_r, s_steps, 'previous');

% --- PHASE 2.1: G-G-V ENVELOPE GENERATION ---
% Function to get max ax (accel/decel) for a given v and ay
getGGCapability = @(v, ay, mode) calculateGGCapability(v, ay, mode, veh, getPacejka, getAero);

% --- PHASE 2.2: APEX OPTIMIZATION ---
v_max_apex = zeros(size(s_steps));
for i = 1:length(s_steps)
    if isinf(r_steps(i))
        v_max_apex(i) = 60; % Assume a top speed limit
    else
        % Optimization: Find max v such that ay_required <= ay_available
        v_max_apex(i) = optimizeApexSpeed(r_steps(i), veh, getPacejka, getAero);
    end
end

% --- PHASE 2.3: VELOCITY PROFILING (Forward-Backward Integration) ---
v_fw = zeros(size(s_steps));
v_bw = zeros(size(s_steps));

% Forward Pass (Acceleration)
v_fw(1) = 0.1; % Start speed
for i = 1:length(s_steps)-1
    ds = s_steps(i+1) - s_steps(i);
    ay = v_fw(i)^2 / r_steps(i);
    ax_max = getGGCapability(v_fw(i), ay, 'accel');
    
    % v^2 = u^2 + 2*a*s
    v_next = sqrt(v_fw(i)^2 + 2 * ax_max * ds);
    v_fw(i+1) = min(v_next, v_max_apex(i+1));
end

% Backward Pass (Braking)
v_bw(end) = v_max_apex(end);
for i = length(s_steps):-1:2
    ds = s_steps(i) - s_steps(i-1);
    ay = v_bw(i)^2 / r_steps(i);
    ax_decel = getGGCapability(v_bw(i), ay, 'decel'); % Negative value
    
    % v^2 = u^2 - 2*a*s (driving backwards, decel becomes accel)
    v_prev = sqrt(v_bw(i)^2 + 2 * abs(ax_decel) * ds);
    v_bw(i-1) = min(v_prev, v_max_apex(i-1));
end

% Final Velocity Profile (Minimum of forward and backward)
v_final = min(v_fw, v_bw);
lap_time = sum(diff(s_steps) ./ (v_final(1:end-1) + 1e-6));

% --- OUTPUTS ---
fprintf('\n--- PHASE 2: LAP TIME SIMULATION RESULTS ---\n');
fprintf('Track Length   : %.0f m\n', max(s_steps));
fprintf('Estimated Lap  : %.3f s\n', lap_time);
fprintf('Max Velocity   : %.1f km/h\n', max(v_final)*3.6);
fprintf('Apex Velocity  : %.1f km/h (at r=%.0fm)\n', min(v_max_apex)*3.6, min(track_r));

% --- HELPER FUNCTIONS ---

function ax = calculateGGCapability(v, ay, mode, veh, fPacejka, fAero)
    % Simplified friction ellipse logic
    theta = (veh.m * 0 * veh.h_cg) / veh.K_pitch; % Assume pitch for steady state is small or iterative
    aero = fAero(theta);
    F_down = 0.5 * veh.rho * aero.Cl * veh.A * v^2;
    Fz_total = veh.m * veh.g + F_down;
    
    % Total lateral force available (Phase 1 logic)
    % For simplicity in G-G-V, we use a single effective axle
    params = fPacejka(Fz_total/2);
    Fy_max = params(3) * 2; % Peak lateral force (D * 2 tires)
    
    Fy_req = veh.m * ay;
    Fx_avail = sqrt(max(Fy_max^2 - Fy_req^2, 0));
    
    if strcmp(mode, 'accel')
        % Motor/Powertrain Limit
        RPM = (v / veh.r_wheel * veh.GR) * 60 / (2*pi);
        T_motor = interp1(veh.rpm_map, veh.torque_map, min(max(RPM, 0), 6500));
        Fx_powertrain = (T_motor * veh.GR * veh.eta) / veh.r_wheel;
        
        Fx_net = min(Fx_powertrain, Fx_avail) - (0.5*veh.rho*aero.Cd*veh.A*v^2) - (veh.Crr*Fz_total);
        ax = Fx_net / veh.m;
    else
        % Braking Limit (simplified)
        ax = -Fx_avail / veh.m;
    end
end

function v_max = optimizeApexSpeed(r, veh, fPacejka, fAero)
    v_test = linspace(1, 60, 100);
    v_max = 1;
    for v = v_test
        aero = fAero(0); % Zero pitch at apex steady state
        Fz = veh.m * veh.g + 0.5 * veh.rho * aero.Cl * veh.A * v^2;
        Fy_max = fPacejka(Fz/2); Fy_max = Fy_max(3) * 2;
        if (veh.m * v^2 / r) > Fy_max
            break;
        end
        v_max = v;
    end
end
