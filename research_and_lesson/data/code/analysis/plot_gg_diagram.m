function plot_gg_diagram(track, result, veh, tire, aero, motor)
    % PLOT_GG_DIAGRAM Visualizes the G-G-V envelope and actual vehicle trace.
    
    v_range = [10, 20, 30, 40]; % Speeds to plot envelopes for
    theta = linspace(0, 2*pi, 100);
    
    figure('Name', 'G-G-V Diagram', 'NumberTitle', 'off');
    hold on;
    
    colors = lines(length(v_range));
    
    for i = 1:length(v_range)
        v = v_range(i);
        
        % Enforce downforce at this speed
        aero_forces = aero_model(v, 0, aero);
        Fz = veh.m * veh.g + aero_forces.F_down;
        params = tire.getPacejka(Fz/2);
        G_max = (params(3) * 2) / (veh.m * veh.g); % Peak Gs available
        
        % Draw ellipse
        plot(G_max * cos(theta), G_max * sin(theta), '--', 'Color', colors(i,:), ...
             'DisplayName', sprintf('%d km/h Envelope', v*3.6));
    end
    
    % Actual vehicle trace
    v = result.v_final;
    dv2 = [diff(v.^2); 0];
    ds = [diff(track.s), track.ds(end)];
    ax = dv2 ./ (2 * ds);
    ay = v.^2 ./ track.r;
    
    % Normalize to Gs
    ax_g = ax / veh.g;
    ay_g = ay / veh.g;
    
    plot(ay_g, ax_g, 'k', 'LineWidth', 1.5, 'DisplayName', 'Actual Trace');
    
    xlabel('Lateral Acceleration (g)');
    ylabel('Longitudinal Acceleration (g)');
    title('G-G Diagram');
    axis equal;
    grid on;
    legend('Location', 'bestoutside');
end
