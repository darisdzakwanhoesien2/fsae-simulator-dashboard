function result = lap_time_solver(track, v_fw, v_bw)
    % LAP_TIME_SOLVER Combines passes and calculates final lap time.
    
    result.v_final = min(v_fw(:), v_bw(:));
    result.s = track.s(:);
    
    % Integration: dt = ds / v_avg
    s = result.s;
    v = result.v_final;
    v_avg = (v(1:end-1) + v(2:end)) / 2;
    dt = diff(s) ./ (v_avg + 1e-6);
    
    result.lap_time = sum(dt);
    result.max_v = max(result.v_final);
    result.max_v_kmh = result.max_v * 3.6;
end
