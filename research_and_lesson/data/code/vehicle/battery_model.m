function [P_batt, I_batt] = battery_model(P_motor, powertrain)
    % BATTERY_MODEL Calculates battery power and current.
    % P_motor: Electrical power at motor (W)
    % powertrain: powertrain parameters struct
    
    % Simple internal resistance model: P_batt = P_motor + I^2 * R
    % P_motor = V * I - I^2 * R => R*I^2 - V*I + P_motor = 0
    % I = (V - sqrt(V^2 - 4*R*P_motor)) / (2*R)
    
    V = powertrain.V_nom;
    R = powertrain.R_internal;
    
    discriminant = V^2 - 4 * R * P_motor;
    if discriminant < 0
        % Voltage collapse or power limit exceeded
        I_batt = V / (2 * R); % Max current
        P_batt = V * I_batt - I_batt^2 * R;
    else
        I_batt = (V - sqrt(discriminant)) / (2 * R);
        P_batt = P_motor + I_batt^2 * R;
    end
end
