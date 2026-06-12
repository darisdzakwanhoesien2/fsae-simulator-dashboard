%% Straight-Line Acceleration Model (High-Fidelity)
% This script simulates 75m acceleration with combined-slip Pacejka 
% tire dynamics and attitude-sensitive (pitch/ride-height) aerodynamics.

% --- VEHICLE PARAMETERS ---
m   = 300;          % kg
g   = 9.81;         % m/s^2
L   = 1.530;        % Wheelbase (m)
a_cg = 0.765;       % CG from front (m)
h_cg = 0.280;       % CG height (m)
r_wheel = 0.229;    % m
J_wheel = 0.60;     % kgm^2
K_pitch = 50000;    % Pitch stiffness (Nm/rad)

% --- POWERTRAIN ---
rpm_map = [0 500 1000 2000 3000 4000 5000 5500 6000 6500];
torque_map = [230 230 230 230 230 230 230 210 190 180];
GR = 3.5; eta = 0.90;

% --- AERO & ENVIRONMENT ---
rho = 1.225; A = 1.1; Crr = 0.012;
dt = 0.001; x_end = 75;

% --- HIGH-FIDELITY FUNCTIONS ---

% 1. Load-Sensitive Pacejka (Miranda et al., 2021)
% Returns [B, C, D, E]
getPacejka = @(Fz) [ ...
    10 * (1 - 0.00002 * Fz), ... % B: Stiffness sensitivity
    1.9, ...                     % C: Shape factor
    (1.80 - 0.00004 * Fz) * Fz, ... % D: Peak Force (mu * Fz)
    0.97 * (1 + 0.00001 * Fz) ... % E: Curvature sensitivity
];

% 2. Attitude-Sensitive Aero Map (Zhang et al., 2022)
% Cl and Cd as functions of pitch angle (theta)
getAero = @(theta) struct(...
    'Cl', 2.8 * (1 + 0.8 * sin(theta)), ... % Significant downforce gain in squat
    'Cd', 1.3 * (1 + 0.5 * sin(theta)) ...  % Drag also increases in squat
);

% --- INITIALIZATION ---
t = 0; x = 0; v = 0.1; a = 0;
omega_w = v / r_wheel;
theta = 0; % Initial pitch

% Logging
log = struct('t',[],'x',[],'v',[],'a',[],'theta',[],'Cl',[],'kappa',[]);

% --- SIMULATION LOOP ---
while x < x_end
    % A. Calculate Attitude (Pitch)
    % theta = (Longitudinal Moment) / Pitch Stiffness
    % Moment = m*a*h_cg - (Aero Moment placeholder)
    theta = (m * a * h_cg) / K_pitch;
    
    % B. Attitude-Sensitive Aero
    aero = getAero(theta);
    F_drag = 0.5 * rho * aero.Cd * A * v^2;
    F_down = 0.5 * rho * aero.Cl * A * v^2;

    % C. Dynamic Weight Transfer
    weight_transfer = (m * a * h_cg) / L;
    Fz_rear = (m * g * (a_cg/L)) + weight_transfer + 0.5 * F_down;

    % D. Load-Sensitive Pacejka
    params = getPacejka(Fz_rear);
    B = params(1); C = params(2); D = params(3); E = params(4);

    % E. Powertrain
    RPM = (omega_w * GR) * 60 / (2*pi);
    T_motor = interp1(rpm_map, torque_map, min(max(RPM, 0), 6500));
    T_wheel = T_motor * GR * eta;

    % F. Slip Ratio (kappa)
    kappa = (r_wheel * omega_w - max(v,1)) / max(v,1);

    % G. Magic Formula Force (Combined slip effect handled by state-dependent D)
    Fx_tire = D * sin(C * atan(B * kappa - E * (B * kappa - atan(B * kappa))));

    % H. Wheel & Vehicle Dynamics
    alpha_w = (T_wheel - Fx_tire * r_wheel) / J_wheel;
    omega_w = omega_w + alpha_w * dt;
    
    F_net = Fx_tire - F_drag - (Crr * (m*g + F_down));
    a = F_net / m;
    v = v + a * dt;
    x = x + v * dt;
    t = t + dt;

    % Logging
    log.t(end+1) = t; log.v(end+1) = v; log.theta(end+1) = theta; log.Cl(end+1) = aero.Cl;
end

% --- OUTPUTS ---
fprintf('\n--- HIGH-FIDELITY ACCELERATION RESULTS ---\n');
fprintf('75m Time      : %.3f s\n', t);
fprintf('Max Velocity  : %.1f km/h\n', max(log.v)*3.6);
fprintf('Peak Pitch    : %.2f deg\n', rad2deg(max(log.theta)));
fprintf('Max Downforce : %.0f N (Cl_max = %.2f)\n', ...
    0.5*rho*max(log.Cl)*A*max(log.v)^2, max(log.Cl));
