function [T_out, T_motor_new] = motor_model(v, T_motor, dt, powertrain, veh)
    % MOTOR_MODEL EMRAX motor model with thermal derating.
    
    % RPM calculation
    omega_w = v / veh.r_wheel;
    RPM = (omega_w * powertrain.GR) * 60 / (2*pi);
    
    % Base torque from map
    T_base = interp1(powertrain.rpm_map, powertrain.torque_map, ...
                     min(max(RPM, 0), max(powertrain.rpm_map)));
    
    % Thermal Integration
    I_est = 250; % Simplified current estimation (A)
    P_loss = I_est^2 * powertrain.R_winding; % Copper losses
    dT_dt = (P_loss - (T_motor - powertrain.T_ambient)/powertrain.R_thermal) / powertrain.C_thermal;
    T_motor_new = T_motor + dT_dt * dt;
    
    % Thermal Derating Logic
    derate_factor = 1.0;
    if T_motor_new > powertrain.T_limit
        derate_factor = max(0, 1 - (T_motor_new - powertrain.T_limit) / ...
                               (powertrain.T_max - powertrain.T_limit));
    end
    
    T_out = T_base * derate_factor;
end
