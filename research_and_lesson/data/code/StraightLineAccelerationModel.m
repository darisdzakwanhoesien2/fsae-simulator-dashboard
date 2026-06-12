%% Straight-Line Acceleration Model (Improved)
% This script simulates a vehicle's performance in a 75m acceleration event.
% It includes a Pacejka tire model, wheel rotational dynamics, motor torque
% mapping, and longitudinal weight transfer.

% --- VEHICLE PARAMETERS ---
m   = 300;          % Total mass (kg)
g   = 9.81;         % Gravity (m/s^2)
L   = 1.530;        % Wheelbase (m)
a_cg = 0.765;       % CG distance from front axle (m)
h_cg = 0.280;       % CG height (m)
r_wheel = 0.229;    % Wheel radius (m)
J_wheel = 0.60;     % Wheel rotational inertia (kg*m^2)

% --- TIRE PARAMETERS (PACEJKA & SENSITIVITY) ---
mu0  = 1.80;        % Nominal friction coefficient
k_mu = 0.00004;     % Load sensitivity factor (1/N)
B = 10;             % Pacejka Stiffness Factor
C = 1.9;            % Pacejka Shape Factor
E = 0.97;           % Pacejka Curvature Factor

% --- POWERTRAIN (EMRAX MOTOR) ---
rpm_map    = [0 500 1000 2000 3000 4000 5000 5500 6000 6500];
torque_map = [230 230 230 230 230 230 230 210 190 180];
GR  = 3.5;          % Gear Ratio
eta = 0.90;         % Drivetrain Efficiency

% --- AERODYNAMICS & RESISTANCE ---
Cd   = 1.3;         % Drag coefficient
Cl   = 2.8;         % Downforce coefficient
A    = 1.1;         % Frontal area (m^2)
rho  = 1.225;       % Air density (kg/m^3)
Crr  = 0.012;       % Rolling Resistance Coefficient

% --- SIMULATION SETUP ---
dt    = 0.001;      % Time step (s)
x_end = 75;         % Target distance (m)

% Initial states
t = 0;
x = 0;
v = 0.1;            % Small initial velocity to avoid division by zero in slip
a = 0;
omega_w = v / r_wheel; % Assuming pure rolling at start

% Logs
log_t = []; log_x = []; log_v = []; log_a = [];
log_rpm = []; log_mu = []; log_Fz = []; log_kappa = []; log_Fx = [];

% --- SIMULATION LOOP ---
while x < x_end
    % A. Aerodynamic Forces
    F_drag = 0.5 * rho * Cd * A * v^2;
    F_down = 0.5 * rho * Cl * A * v^2;

    % B. Longitudinal Weight Transfer
    weight_transfer = (m * a * h_cg) / L;
    Fz_static_rear  = (m * g) * (a_cg / L);
    Fz_rear = Fz_static_rear + weight_transfer + 0.5 * F_down;

    % C. Load-Sensitive Friction
    mu_eff = max(mu0 - k_mu * Fz_rear, 1.0);

    % D. Motor Torque Calculation
    omega_motor = omega_w * GR;
    RPM = omega_motor * 60 / (2 * pi);
    RPM_clamped = min(max(RPM, rpm_map(1)), rpm_map(end));
    T_motor = interp1(rpm_map, torque_map, RPM_clamped);
    T_wheel = T_motor * GR * eta;

    % E. Longitudinal Slip Ratio (kappa)
    v_safe = max(v, 1.0); % Avoid singularity at zero speed
    kappa = (r_wheel * omega_w - v_safe) / v_safe;

    % F. Pacejka Magic Formula for Longitudinal Tire Force
    D = mu_eff * Fz_rear; % Peak force
    Fx_tire = D * sin(C * atan(B * kappa - E * (B * kappa - atan(B * kappa))));

    % G. Wheel Rotational Dynamics
    % alpha_w = (Net Torque) / Inertia
    alpha_w = (T_wheel - Fx_tire * r_wheel) / J_wheel; 
    omega_w = omega_w + alpha_w * dt;

    % H. Vehicle Linear Dynamics
    F_roll = Crr * (m * g + F_down);
    F_net  = Fx_tire - F_drag - F_roll;
    a = F_net / m;
    
    v = max(v + a * dt, 0);
    x = x + v * dt;
    t = t + dt;

    % Data Logging
    log_t(end+1)     = t;
    log_x(end+1)     = x;
    log_v(end+1)     = v;
    log_a(end+1)     = a;
    log_rpm(end+1)   = RPM;
    log_mu(end+1)    = mu_eff;
    log_Fz(end+1)    = Fz_rear;
    log_kappa(end+1) = kappa;
    log_Fx(end+1)    = Fx_tire;
end

% --- OUTPUTS ---
fprintf('\n--- ACCELERATION MODEL RESULTS ---\n');
fprintf('75 m Time        : %.3f s\n', t);
fprintf('Top Speed        : %.1f km/h\n', max(log_v) * 3.6);
fprintf('Peak Acceleration: %.2f g\n', max(log_a) / g);
fprintf('Peak Rear Load   : %.0f N\n', max(log_Fz));
fprintf('Peak Slip Ratio  : %.2f\n', max(log_kappa));
fprintf('Peak Tire Force  : %.0f N\n', max(log_Fx));
