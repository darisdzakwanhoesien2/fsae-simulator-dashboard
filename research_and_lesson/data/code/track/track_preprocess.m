function track = track_preprocess(track_raw, opts)
    % TRACK_PREPROCESS Interpolates track and prepares for solver.
    
    track.s = (0:opts.ds:max(track_raw.s_raw))'; % Force column
    track.r = interp1(track_raw.s_raw, track_raw.r_raw, track.s, 'previous');
    track.ds = [diff(track.s); opts.ds]; % Force column
end
