%% Straight-Line Acceleration Model (Transient & Thermal - Phase 3)
% This script simulates 75m acceleration with:
% 1. Transient Chassis Pitch (Damper + Inertia)
% 2. EMRAX Thermal Model & Derating
% 3. High-Fidelity Pacejka & Aero Maps

% --- VEHICLE PARAMETERS ---
m   = 300;          % kg
g   = 9.81;         % m/s^2
L   = 1.530;        % Wheelbase (m)
a_cg = 0.765;       % CG from front (m)
h_cg = 0.280;       % CG height (m)
r_wheel = 0.229;    % m
J_wheel = 0.60;     % kgm^2

% --- TRANSIENT CHASSIS PARAMETERS (Phase 3 Advancement) ---
K_pitch = 50000;    % Pitch stiffness (Nm/rad)
C_pitch = 4500;     % Pitch damping (Nms/rad)
I_pitch = 220;      % Pitch inertia (kgm^2)

% --- EMRAX THERMAL PARAMETERS (Phase 3 Advancement) ---
T_ambient = 25;     % degC
T_limit   = 100;    % degC (Start derating)
T_max     = 130;    % degC (Zero torque)
C_thermal = 2500;   % J/K (Thermal mass)
R_thermal = 0.05;   % K/W (Resistance to ambient)
R_winding = 0.015;  % Ohms (Approx)

% --- POWERTRAIN ---
rpm_map = [0 500 1000 2000 3000 4000 5000 5500 6000 6500];
torque_map = [230 230 230 230 230 230 230 210 190 180];
GR = 3.5; eta = 0.90;

% --- AERO & ENVIRONMENT ---
rho = 1.225; A = 1.1; Crr = 0.012;
dt = 0.001; x_end = 75;

% --- HIGH-FIDELITY FUNCTIONS ---
getPacejka = @(Fz) [10*(1-0.00002*Fz), 1.9, (1.80-0.00004*Fz)*Fz, 0.97*(1+0.00001*Fz)];
getAero = @(theta) struct('Cl', 2.8*(1+0.8*sin(theta)), 'Cd', 1.3*(1+0.5*sin(theta)));

% --- INITIALIZATION ---
t = 0; x = 0; v = 0.1; a = 0;
omega_w = v / r_wheel;
theta = 0; dtheta = 0; % Transient pitch states
T_motor = T_ambient;   % Initial motor temperature

% Logging
log = struct('t',[],'x',[],'v',[],'a',[],'theta',[],'T_motor',[],'T_avail',[],'kappa',[]);

% --- SIMULATION LOOP ---
while x < x_end
    % A. TRANSIENT PITCH DYNAMICS (Phase 3)
    % I_pitch*ddtheta + C_pitch*dtheta + K_pitch*theta = M_pitch
    M_pitch = m * a * h_cg; % Simplified longitudinal moment
    ddtheta = (M_pitch - C_pitch*dtheta - K_pitch*theta) / I_pitch;
    dtheta = dtheta + ddtheta * dt;
    theta = theta + dtheta * dt;
    
    % B. ATTITUDE-SENSITIVE AERO
    aero = getAero(theta);
    F_drag = 0.5 * rho * aero.Cd * A * v^2;
    F_down = 0.5 * rho * aero.Cl * A * v^2;

    % C. DYNAMIC WEIGHT TRANSFER (Using transient theta)
    % Note: In transient, Fz also depends on dtheta/suspension forces
    Fz_rear = (m * g * (a_cg/L)) + (K_pitch * theta / L) + 0.5 * F_down;

    % D. LOAD-SENSITIVE PACEJKA
    params = getPacejka(Fz_rear);
    B = params(1); C = params(2); D = params(3); E = params(4);

    % E. EMRAX THERMAL & POWERTRAIN (Phase 3)
    % Heat generation (Joules)
    I_est = 250; % Simplified current estimation (A)
    P_loss = I_est^2 * R_winding; % Copper losses
    dT_dt = (P_loss - (T_motor - T_ambient)/R_thermal) / C_thermal;
    T_motor = T_motor + dT_dt * dt;
    
    % Thermal Derating Logic
    derate_factor = 1.0;
    if T_motor > T_limit
        derate_factor = max(0, 1 - (T_motor - T_limit) / (T_max - T_limit));
    end

    RPM = (omega_w * GR) * 60 / (2*pi);
    T_base = interp1(rpm_map, torque_map, min(max(RPM, 0), 6500));
    T_motor_out = T_base * derate_factor; % Applied derating
    T_wheel = T_motor_out * GR * eta;

    % F. SLIP RATIO (kappa)
    kappa = (r_wheel * omega_w - max(v,1)) / max(v,1);

    % G. MAGIC FORMULA FORCE
    Fx_tire = D * sin(C * atan(B * kappa - E * (B * kappa - atan(B * kappa))));

    % H. WHEEL & VEHICLE DYNAMICS
    alpha_w = (T_wheel - Fx_tire * r_wheel) / J_wheel;
    omega_w = omega_w + alpha_w * dt;
    
    F_net = Fx_tire - F_drag - (Crr * (m*g + F_down));
    a = F_net / m;
    v = v + a * dt;
    x = x + v * dt;
    t = t + dt;

    % Logging
    log.t(end+1) = t; log.v(end+1) = v; log.theta(end+1) = theta; 
    log.T_motor(end+1) = T_motor; log.T_avail(end+1) = T_motor_out;
end

% --- OUTPUTS ---
fprintf('\n--- PHASE 3: TRANSIENT & THERMAL ACCELERATION RESULTS ---\n');
fprintf('75m Time      : %.3f s\n', t);
fprintf('Max Velocity  : %.1f km/h\n', max(log.v)*3.6);
fprintf('Peak Temp     : %.1f degC\n', max(log.T_motor));
fprintf('Final Torque  : %.1f Nm (Derated from peak if >100C)\n', log.T_avail(end));
fprintf('Peak Pitch    : %.2f deg (Transient settling included)\n', rad2deg(max(log.theta)));
