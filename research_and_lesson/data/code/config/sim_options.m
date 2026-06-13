function opts = sim_options()
    % SIM_OPTIONS Returns simulation control parameters.
    
    opts.dt = 0.001;        % s, time step for transient simulations
    opts.ds = 0.5;          % m, distance step for lap time simulations
    opts.v_start = 0.1;     % m/s, initial velocity
    opts.v_top_limit = 60;  % m/s, assume a top speed limit
end
