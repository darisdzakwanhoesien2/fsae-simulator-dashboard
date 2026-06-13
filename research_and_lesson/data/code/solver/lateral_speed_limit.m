function v_max_apex = lateral_speed_limit(track, veh, tire, aero, opts)
    % LATERAL_SPEED_LIMIT Calculates max cornering speed at each point.
    
    v_max_apex = zeros(size(track.s));
    N = length(track.s);
    for i = 1:N
        update_progress(i, N, 'Lateral Limits');
        if isinf(track.r(i))
            v_max_apex(i) = opts.v_top_limit;
        else
            % Optimization: Find max v such that ay_required <= ay_available
            v_max_apex(i) = optimize_apex_speed(track.r(i), veh, tire, aero, opts);
        end
    end
end

function v_max = optimize_apex_speed(r, veh, tire, aero, opts)
    v_test = linspace(1, opts.v_top_limit, 100);
    v_max = 1;
    for v = v_test
        aero_forces = aero_model(v, 0, aero);
        Fz = veh.m * veh.g + aero_forces.F_down;
        params = tire.getPacejka(Fz/2); 
        Fy_max = params(3) * 2;
        if (veh.m * v^2 / r) > Fy_max
            break;
        end
        v_max = v;
    end
end
