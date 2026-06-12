%{
%clear; clc;
m   = 300;
g   = 9.81;

L     = 1.530;      % wheelbase
a_cg  = 0.765;      % CG from front axle
h_cg  = 0.280;      % CG height


mu0   = 1.80;       % nominal friction coefficient
k_mu  = 0.00004;    % load sensitivity factor

r_wheel = 0.229;

% --- EMRAX  ---
rpm_map    = [0 500 1000 2000 3000 4000 5000 5500 6000 6500];
torque_map = [230 230 230 230 230 230 230 210 190 180];

% --- Drivetrain ---
GR   = 3.5;
eta  = 0.90;

% --- Aero ---
Cd   = 1.3;
Cl   = 2.8;          % downforce coefficient
A    = 1.1;
rho  = 1.225;

% --- Rolling Resistance ---
Crr  = 0.012;

omega_w = v / r_wheel;
dt      = 0.001;
x_end   = 75;

t = 0;
x = 0;
v = 0.01;
a = 0;

log_t   = [];
log_x   = [];
log_v   = [];
log_a   = [];
log_rpm = [];
log_mu  = [];
log_Fz  = [];


while x < x_end
    % A. AERODYNAMIC FORCES

    F_drag = 0.5 * rho * Cd * A * v^2;

    F_down = 0.5 * rho * Cl * A * v^2;

    % B. LONGITUDINAL WEIGHT TRANSFER
    weight_transfer = (m * a * h_cg) / L;
    % Rear axle load: static rear load + dynamic transfer
    Fz_static_rear = (m*g) * (a_cg/L);

    Fz_rear = Fz_static_rear + weight_transfer + 0.5*F_down;

    % C. LOAD-SENSITIVE TYRE MODEL
    % Effective friction coefficient decreases, vertical load increases.
    mu_eff = mu0 - k_mu * Fz_rear;

    mu_eff = max(mu_eff, 1.0);

    F_grip_limit = mu_eff * Fz_rear;     % Maximum rear traction


    % D. MOTOR RPM
    omega_wheel = v / r_wheel;
    omega_motor = omega_wheel * GR;

    RPM = omega_motor * 60 / (2*pi);
    RPM_clamped = min(max(RPM, rpm_map(1)), rpm_map(end));


    % E. MOTOR TORQUE
    T_motor = interp1(rpm_map, torque_map, RPM_clamped);

    
    F_engine = T_motor * GR * eta / r_wheel;
    F_drive = min(F_engine, F_grip_limit);

    F_roll = Crr * (m*g + F_down);

    F_net = F_drive - F_drag - F_roll;

    a = F_net / m;



    v = v + a*dt;
    x = x + v*dt;
    t = t + dt;

    log_t(end+1)   = t;
    log_x(end+1)   = x;
    log_v(end+1)   = v;
    log_a(end+1)   = a;
    log_rpm(end+1) = RPM;
    log_mu(end+1)  = mu_eff;
    log_Fz(end+1)  = Fz_rear;

end


fprintf('75 m Time      : %.3f s\n', t);
fprintf('Top Speed      : %.1f km/h\n', ...
    max(log_v)*3.6);

fprintf('Peak Accel     : %.2f g\n', ...
    max(log_a)/g);

fprintf('Peak Rear Load : %.0f N\n', ...
    max(log_Fz));

%}

%clear;clc;
m   = 300;  
g   = 9.81;    

L     = 1.530;      % wheelbase
a_cg  = 0.765;      % CG distance from front axle
h_cg  = 0.280;      % CG height

r_wheel = 0.229; 

mu0   = 1.80;       % nominal friction coefficient
k_mu  = 0.00004;    % load sensitivity coefficient

% Pacejka coefficients
B = 10;             % stiffness factor
C = 1.9;            % shape factor
E = 0.97;           % curvature factor

J_wheel = 0.60;     % wheel rotational inertia 


%  EMRAX
rpm_map = [0 500 1000 2000 3000 4000 5000 5500 6000 6500];

torque_map = [230 230 230 230 230 230 230 210 190 180];


%  DRIVETRAIN
GR  = 3.5;          % gear ratio
eta = 0.90;         % drivetrain efficiency

%  AERO
Cd   = 1.3;         % drag coefficient
Cl   = 2.8;         % downforce coefficient
A    = 1.1;         % frontal area
rho  = 1.225;       % air density 

Crr = 0.012; % rolling resitance


dt    = 0.001; 
x_end = 75;  

t = 0;
x = 0;

v = 0.1;  
a = 0;

omega_w = v / r_wheel; % Initial wheel speed assuming pure rolling


log_t      = [];
log_x      = [];
log_v      = [];
log_a      = [];
log_rpm    = [];
log_mu     = [];
log_Fz     = [];
log_kappa  = [];
log_Fx     = [];


while x < x_end

    %  A. AERODYNAMIC FORCES
    F_drag = 0.5 * rho * Cd * A * v^2;
    F_down = 0.5 * rho * Cl * A * v^2;

    %  B. LONGITUDINAL WEIGHT TRANSFER
    weight_transfer = (m * a * h_cg) / L;

    
    Fz_static_rear = (m * g) * (a_cg / L);

    % Total rear axle vertical load
    Fz_rear = Fz_static_rear + weight_transfer + 0.5 * F_down;


    %  C. LOAD-SENSITIVE FRICTION MODEL
    mu_eff = mu0 - k_mu * Fz_rear;
    mu_eff = max(mu_eff, 1.0);

    %  D. MOTOR RPM
    omega_motor = omega_w * GR;
    RPM = omega_motor * 60 / (2*pi);

    RPM_clamped = min(max(RPM, rpm_map(1)), rpm_map(end));


    %  E. MOTOR TORQUE
    T_motor = interp1( rpm_map, torque_map, RPM_clamped);

    T_wheel = T_motor * GR * eta;

    %  F. LONGITUDINAL SLIP RATIO
    v_safe = max(v, 1.0);
    kappa = (r_wheel * omega_w - v_safe) / v_safe;


    %  G. PACEJKA MODEL
    D = mu_eff * Fz_rear;
    Fx_tire = D * sin(C * atan(B * kappa - E * (B * kappa - atan(B * kappa))));

    %  H. WHEEL ROTATIONAL DYNAMICS
    alpha_w = (T_wheel - Fx_tire * r_wheel) / J_wheel;     % Wheel angular acceleration

    omega_w = omega_w + alpha_w * dt;


    F_roll = Crr * (m * g + F_down);
    F_net = Fx_tire  - F_drag  - F_roll;
    a = F_net / m;


    v = v + a * dt;
    v = max(v, 0);

    x = x + v * dt;

    t = t + dt;

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

fprintf('75 m Time        : %.3f s\n', t);

fprintf('Top Speed        : %.1f km/h\n', ...
    max(log_v) * 3.6);

fprintf('Peak Acceleration: %.2f g\n', ...
    max(log_a) / g);

fprintf('Peak Rear Load   : %.0f N\n', ...
    max(log_Fz));

fprintf('Peak Slip Ratio  : %.2f\n', ...
    max(log_kappa));

fprintf('Peak Tire Force  : %.0f N\n', ...
    max(log_Fx));

