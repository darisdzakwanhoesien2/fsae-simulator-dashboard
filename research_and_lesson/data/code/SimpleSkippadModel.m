%% FSAE Skidpad Performance Model (High-Fidelity)
% This script simulates a vehicle performing a skidpad maneuver with 
% load-sensitive Pacejka tire dynamics and attitude-sensitive aerodynamics.

% --- CONSTANTS ---
m   = 300;          % Mass (kg)
g   = 9.81;         % Gravity (m/s^2)
r   = 9;            % Skidpad Radius (m)
rho  = 1.225;       % Air density (kg/m^3)
A    = 1.1;         % Frontal Area (m^2)

% --- CHASSIS & SUSPENSION ---
h_cg  = 0.280;      % CG height (m)
track = 1.20;       % Track width (m)
h_rc  = 0.05;       % Roll center height (m)
K_pitch = 50000;    % Pitch stiffness (Nm/rad) - representative
K_roll  = 40000;    % Roll stiffness (Nm/rad)

% --- SIMULATION SETUP ---
v_test = linspace(1, 40, 2000); 

% Results Logging
res.v_max = 0;
res.lat_accel = 0;
res.time = 0;

lat_req_log = [];
lat_ava_log = [];

% --- MODEL FUNCTIONS ---

% 1. Load-Sensitive Pacejka Parameters
% Based on: Miranda et al. (2021) - B, C, D, E as f(Fz)
getPacejka = @(Fz) struct(...
    'B', 10 * (1 - 0.00002 * Fz), ... % Stiffness reduces slightly with load
    'C', 1.9, ...                     % Shape factor (often constant)
    'D', (1.80 - 0.00004 * Fz) * Fz, ... % Peak force (D = mu * Fz)
    'E', 0.97 * (1 + 0.00001 * Fz) ... % Curvature factor
);

% 2. Attitude-Sensitive Aerodynamics (Aero Map)
% Based on: Zhang et al. (2022) - Cl sensitive to pitch
getAero = @(pitch) struct(...
    'Cl', 2.8 * (1 + 0.5 * sin(pitch)), ... % Downforce varies with pitch
    'Cd', 1.3 * (1 + 0.2 * abs(pitch)) ...  % Drag increases with attitude change
);

% --- SIMULATION LOOP ---
for i = 1:length(v_test)
    v = v_test(i);

    % Initial Aero (assuming zero pitch for first pass)
    aero = getAero(0);
    F_down = 0.5 * rho * aero.Cl * A * v^2;
    
    % Vertical Loads
    Fz_total = m*g + F_down;
    ay = v^2 / r;
    
    % Dynamics: Lateral Load Transfer
    load_transfer = m * ay * (h_cg - h_rc) / track;
    Fz_out = (Fz_total / 4) + load_transfer/2;
    Fz_in  = (Fz_total / 4) - load_transfer/2;
    Fz_in  = max(Fz_in, 50);

    % Update Aero based on pitch (simplified pitch from aero moment)
    % In skidpad, pitch is mainly from aero balance/drag
    pitch_est = (0.5 * rho * aero.Cd * A * v^2 * h_cg) / K_pitch;
    aero = getAero(pitch_est);
    
    % Tire Force Calculation (Pacejka)
    % We assume peak lateral force is reached (optimum slip angle)
    p_out = getPacejka(Fz_out);
    p_in  = getPacejka(Fz_in);
    
    % Peak Lateral Force (D parameter in Pacejka)
    Fy_out = p_out.D;
    Fy_in  = p_in.D;

    % Combined Dynamics check (Friction Ellipse)
    % F_available = sqrt(F_max^2 - F_long^2)
    % For skidpad at steady state, F_long = Drag + RollRes
    F_drag = 0.5 * rho * aero.Cd * A * v^2;
    F_roll = 0.012 * Fz_total;
    F_long_req = (F_drag + F_roll) / 2; % Required per driving axle (approx)
    
    % Reduction in lateral capacity due to longitudinal demand
    Fy_out_avail = sqrt(max(Fy_out^2 - F_long_req^2, 0));
    Fy_in_avail  = sqrt(max(Fy_in^2 - F_long_req^2, 0));

    F_lat_available = 2 * (Fy_out_avail + Fy_in_avail);
    F_lat_required  = m * v^2 / r;

    lat_req_log(end+1) = F_lat_required;
    lat_ava_log(end+1) = F_lat_available;
end

% --- ANALYSIS ---
[~, idx] = min(abs(lat_ava_log - lat_req_log));
v_max = v_test(idx);

% Outputs
fprintf('\n--- HIGH-FIDELITY SKIDPAD RESULTS ---\n');
fprintf('Max Speed      : %.2f m/s\n', v_max);
fprintf('Lateral Accel  : %.2f g\n', (v_max^2/r)/g);
fprintf('Skidpad Time   : %.2f s\n', (2 * 2*pi*r) / v_max);
fprintf('Aero Cl (Peak) : %.2f\n', getAero((0.5*rho*1.3*A*v_max^2*h_cg)/K_pitch).Cl);
