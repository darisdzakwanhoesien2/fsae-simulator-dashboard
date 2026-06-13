function track = track_loader(track_name)
    % TRACK_LOADER Loads track data from sample or CSV.
    
    if strcmp(track_name, 'sample')
        % s: distance along path (m), r: radius of curvature (m, Inf for straight)
        track.s_raw = [0, 50, 100, 150, 200];
        track.r_raw = [Inf, Inf, 15, Inf, Inf];
    elseif contains(track_name, '.csv')
        try
            data = readmatrix(track_name);
            % Expecting columns: [X, Y] or [s, r]
            if size(data, 2) == 2
                if any(data(:,2) > 1000) % Heuristic to detect X,Y vs s,r
                    % Assume X, Y
                    x = data(:,1);
                    y = data(:,2);
                    dx = [0; diff(x)]; dy = [0; diff(y)];
                    ds = sqrt(dx.^2 + dy.^2);
                    track.s_raw = cumsum(ds);
                    kappa = curvature_from_xy(x, y);
                    track.r_raw = 1 ./ (kappa + 1e-6);
                else
                    % Assume s, r
                    track.s_raw = data(:,1);
                    track.r_raw = data(:,2);
                end
            else
                error('CSV must have 2 columns ([X, Y] or [s, r]).');
            end
        catch ME
            error('Failed to load CSV: %s', ME.message);
        end
    else
        error('Track "%s" not found. Use "sample" or a .csv file.', track_name);
    end
end
