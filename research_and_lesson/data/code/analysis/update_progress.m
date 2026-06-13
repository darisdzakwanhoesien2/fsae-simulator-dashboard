function update_progress(current, total, label)
    % UPDATE_PROGRESS Displays a text-based progress bar in the console.
    % current: current iteration index
    % total: total number of iterations
    % label: string to display before the bar
    
    persistent last_update
    if isempty(last_update); last_update = 0; end
    
    % Only update every 2% to save console overhead
    percent = floor(100 * current / total);
    if percent > last_update || current == total
        bar_length = 20;
        filled = floor(bar_length * current / total);
        bar = [repmat('=', 1, filled), repmat('-', 1, bar_length - filled)];
        
        % \r returns to start of line. Use pause(0) to force flush in some envs.
        fprintf('\r  [%s] %d%% | %s', bar, percent, label);
        
        if current == total
            fprintf('\n'); % Move to next line when done
            last_update = 0;
        else
            last_update = percent;
        end
    end
end
