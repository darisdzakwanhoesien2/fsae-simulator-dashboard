function v_bw = backward_pass(track, v_max_apex, veh, tire, aero, motor, opts)
    % BACKWARD_PASS Braking integration.
    
    v_bw = zeros(size(track.s));
    v_bw(end) = v_max_apex(end);
    
    for i = length(track.s):-1:2
        ds = track.ds(i-1);
        ay = v_bw(i)^2 / track.r(i);
        
        % Braking (deceleration) limit
        ax_decel = force_limits(v_bw(i), ay, 'decel', veh, tire, aero, motor);
        
        % v^2 = u^2 + 2*a*s => u = sqrt(v^2 - 2*a*s)
        % Moving backward, decel (negative) acts as acceleration
        v_prev = sqrt(v_bw(i)^2 + 2 * abs(ax_decel) * ds);
        v_bw(i-1) = min(v_prev, v_max_apex(i-1));
    end
end
