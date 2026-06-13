function powertrain = powertrain_params()
    % POWERTRAIN_PARAMS Returns the motor and battery parameters.
    
    % Motor Map (EMRAX)
    powertrain.rpm_map = [0 500 1000 2000 3000 4000 5000 5500 6000 6500];
    powertrain.torque_map = [230 230 230 230 230 230 230 210 190 180];
    
    powertrain.GR = 3.5;         % Gear Ratio
    powertrain.eta = 0.90;       % Drivetrain efficiency
    
    % EMRAX Thermal Parameters
    powertrain.T_ambient = 25;   % degC, Ambient temperature
    powertrain.T_limit   = 100;  % degC, Temperature to start derating
    powertrain.T_max     = 130;  % degC, Temperature for zero torque
    powertrain.C_thermal = 2500; % J/K, Thermal mass
    powertrain.R_thermal = 0.05; % K/W, Thermal resistance to ambient
    powertrain.R_winding = 0.015; % Ohms, Winding resistance
    
    % Battery Parameters (Sample 600V Accumulator)
    powertrain.V_nom = 600;      % V, Nominal voltage
    powertrain.C_cap = 15;       % Ah, Capacity
    powertrain.R_internal = 0.15; % Ohms, Internal resistance
    powertrain.E_total = powertrain.V_nom * powertrain.C_cap * 3600; % Joules
    powertrain.regen_limit = 0.5; % Max fraction of braking force that can be regenerated
end
