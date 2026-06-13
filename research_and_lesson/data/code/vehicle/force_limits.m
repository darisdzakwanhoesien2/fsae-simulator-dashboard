function ax = force_limits(v, ay, mode, veh, tire, aero, motor, T_motor, theta)
    % FORCE_LIMITS Calculates max longitudinal acceleration/deceleration.
    % Based on friction ellipse and powertrain limits.
    
    if nargin < 8; T_motor = 25; end
    if nargin < 9; theta = 0; end

    % 1. Aero and Downforce (Attitude-sensitive)
    aero_forces = aero_model(v, theta, aero);
    
    % 2. Normal Load (Fz) with Pitch-based weight transfer
    % Simplified: Fz_total includes downforce
    Fz_total = veh.m * veh.g + aero_forces.F_down;
    
    % For longitudinal limits, we care about the driving/braking axle load
    % In acceleration, rear load is critical. In braking, front load is critical.
    % Fz_rear = (m*g*a_cg/L) + (K_pitch*theta/L) + 0.5*F_down
    Fz_rear = (veh.m * veh.g * (veh.a_cg/veh.L)) + (veh.K_pitch * theta / veh.L) + 0.5 * aero_forces.F_down;
    Fz_front = Fz_total - Fz_rear;
    
    % 3. Lateral Force Capacity (Pacejka at peak)
    % Using effective axle logic for G-G-V
    params = tire.getPacejka(Fz_total/2);
    Fy_max = params(3) * 2; 
    
    % 4. Friction Ellipse
    Fy_req = veh.m * ay;
    Fx_avail_tire = sqrt(max(Fy_max^2 - Fy_req^2, 0));
    
    if strcmp(mode, 'accel')
        % Rear traction limit (assuming RWD for EMRAX)
        params_rear = tire.getPacejka(Fz_rear/2);
        Fx_traction_limit = params_rear(3) * 2; % Peak longitudinal approx by peak lateral mu
        
        % Motor/Powertrain Limit
        [T_motor_out, ~] = motor_model(v, T_motor, 0, motor, veh); 
        Fx_powertrain = (T_motor_out * motor.GR * motor.eta) / veh.r_wheel;
        
        % Net available force
        Fx_max = min([Fx_powertrain, Fx_avail_tire, Fx_traction_limit]);
        Fx_net = Fx_max - aero_forces.F_drag - (veh.Crr * Fz_total);
        ax = Fx_net / veh.m;
    else
        % Braking Limit (simplified total grip)
        ax = -Fx_avail_tire / veh.m;
    end
end
