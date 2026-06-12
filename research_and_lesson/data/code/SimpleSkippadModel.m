%% FSAE Skidpad Performance Model (Improved)
% This script simulates a vehicle performing a skidpad maneuver.
% It accounts for aerodynamic forces, load-sensitive friction, and 
% lateral load transfer to estimate maximum cornering speed and time.

% --- CONSTANTS ---
m   = 300;          % Mass (kg)
g   = 9.81;         % Gravity (m/s^2)
r   = 9;            % Skidpad Radius (m)

% --- TIRE PARAMETERS ---
mu0  = 1.80;        % Nominal friction coefficient
k_mu = 0.00004;     % Load sensitivity factor (1/N)

% --- AERODYNAMICS ---
Cd   = 1.3;         % Drag coefficient
Cl   = 2.8;         % Downforce coefficient
A    = 1.1;         % Frontal Area (m^2)
rho  = 1.225;       % Air density (kg/m^3)

% --- CHASSIS GEOMETRY ---
h_cg  = 0.280;      % CG height (m)
track = 1.20;       % Track width (m)
h_rc  = 0.05;       % Roll center height (m)

% --- SIMULATION SETUP ---
v_test = linspace(1, 40, 2000); % Velocity range to test (m/s)

lat_required      = zeros(size(v_test));
lat_available     = zeros(size(v_test));
mu_log            = zeros(size(v_test));
load_transfer_log = zeros(size(v_test));

% --- SIMULATION LOOP ---
for i = 1:length(v_test)
    v = v_test(i);

    % A. Aerodynamic Forces
    F_down = 0.5 * rho * Cl * A * v^2;
    F_drag = 0.5 * rho * Cd * A * v^2;

    % B. Vertical Loads and Load Transfer
    Fz_total = m*g + F_down; 
    ay = v^2 / r; % Required lateral acceleration
    
    % Lateral Load Transfer calculation
    load_transfer = m * ay * (h_cg - h_rc) / track;

    Fz_static_per_tire = Fz_total / 4;
    Fz_outside = Fz_static_per_tire + load_transfer/2;
    Fz_inside  = Fz_static_per_tire - load_transfer/2;

    % Prevent negative loads (simple clamping)
    Fz_inside = max(Fz_inside, 50);

    % C. Load-Sensitive Friction Model
    mu_outside = max(mu0 - k_mu * Fz_outside, 1.0);
    mu_inside  = max(mu0 - k_mu * Fz_inside, 1.0);

    % D. Available vs Required Lateral Force
    Fy_outside = mu_outside * Fz_outside;
    Fy_inside  = mu_inside  * Fz_inside;

    % Total lateral force from all four tires
    lat_available(i) = 2 * Fy_outside + 2 * Fy_inside;
    lat_required(i)  = m * v^2 / r;

    mu_log(i)            = (2*mu_outside + 2*mu_inside) / 4;
    load_transfer_log(i) = load_transfer;
end

% --- DATA ANALYSIS ---
% Find the maximum speed where required force is less than or equal to available force
difference = abs(lat_available - lat_required);
[~, idx] = min(difference);
v_max = v_test(idx);

% FSAE Skidpad: two full circles
distance_total = 2 * (2 * pi * r);
time_skidpad = distance_total / v_max;

% --- OUTPUTS ---
fprintf('\n--- SKIDPAD MODEL RESULTS ---\n');
fprintf('Max Corner Speed : %.2f m/s (%.1f km/h)\n', v_max, v_max*3.6);
fprintf('Lateral Accel    : %.2f g\n', (v_max^2/r)/g);
fprintf('Skidpad Time     : %.2f s\n', time_skidpad);
fprintf('Peak Load Transfer : %.0f N\n', max(load_transfer_log));
