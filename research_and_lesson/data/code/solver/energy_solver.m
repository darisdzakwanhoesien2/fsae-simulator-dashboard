function energy = energy_solver(track, result, veh, powertrain)
    % ENERGY_SOLVER Calculates power and SoC over the lap.
    
    N = length(track.s);
    energy.P_motor = zeros(N, 1);
    energy.P_batt = zeros(N, 1);
    energy.E_used = zeros(N, 1);
    
    % Re-calculate acceleration for force estimation
    v = result.v_final(:); % Force column
    s = track.s(:);        % Force column
    dv2 = [diff(v.^2); 0];
    ds = [diff(s); track.ds(end)];
    ax = dv2 ./ (2 * ds);
    
    current_energy = 0;
    
    for i = 1:N
        % Mechanical power required
        % F_net = m*ax
        % F_motor = m*ax + F_drag + F_roll
        pitch = 0; % Assume zero pitch for energy if not available
        aero_forces = aero_model(v(i), pitch, aero_params());
        Fz_total = veh.m * veh.g + aero_forces.F_down;
        
        F_motor_req = veh.m * ax(i) + aero_forces.F_drag + (veh.Crr * Fz_total);
        
        if F_motor_req > 0
            % Traction
            P_mech = F_motor_req * v(i);
            P_elec = P_mech / powertrain.eta;
        else
            % Braking/Regen
            P_mech = F_motor_req * v(i);
            % Limit regen by motor efficiency and regen_limit
            P_elec = P_mech * powertrain.eta * powertrain.regen_limit;
        end
        
        [P_batt, ~] = battery_model(P_elec, powertrain);
        
        energy.P_motor(i) = P_elec;
        energy.P_batt(i) = P_batt;
        
        % Integration
        if i < N
            dt = ds(i) / (v(i) + 1e-6);
            current_energy = current_energy + P_batt * dt;
            energy.E_used(i+1) = current_energy;
        end
    end
    
    energy.total_joules = current_energy;
    energy.total_kWh = current_energy / (3600 * 1000);
    energy.SoC_drop = (current_energy / powertrain.E_total) * 100;
end
