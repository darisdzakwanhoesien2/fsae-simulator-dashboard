function [v_fw, T_fw, theta_fw] = forward_pass(track, v_max_apex, veh, tire, aero, motor, opts)
    % FORWARD_PASS Acceleration integration with transient pitch.
    
    v_fw = zeros(size(track.s));
    T_fw = zeros(size(track.s));
    theta_fw = zeros(size(track.s));
    dtheta = 0;
    
    v_fw(1) = opts.v_start;
    T_fw(1) = motor.T_ambient;
    theta_fw(1) = 0;
    
    for i = 1:length(track.s)-1
        ds = track.ds(i);
        v_curr = v_fw(i);
        theta_curr = theta_fw(i);
        
        ay = v_curr^2 / track.r(i);
        
        % Get acceleration limit with current pitch
        ax = force_limits(v_curr, ay, 'accel', veh, tire, aero, motor, T_fw(i), theta_curr);
        
        % Predict next speed
        v_next = sqrt(v_curr^2 + 2 * ax * ds);
        v_fw(i+1) = min(v_next, v_max_apex(i+1));
        
        % Integration time step
        dt = ds / (v_curr + 1e-6);
        
        % Transient Pitch Dynamics
        % I_pitch*ddtheta + C_pitch*dtheta + K_pitch*theta = M_pitch
        M_pitch = veh.m * ax * veh.h_cg;
        ddtheta = (M_pitch - veh.C_pitch*dtheta - veh.K_pitch*theta_curr) / veh.I_pitch;
        dtheta = dtheta + ddtheta * dt;
        theta_fw(i+1) = theta_curr + dtheta * dt;
        
        % Motor Temperature
        [~, T_next] = motor_model(v_curr, T_fw(i), dt, motor, veh);
        T_fw(i+1) = T_next;
    end
end
