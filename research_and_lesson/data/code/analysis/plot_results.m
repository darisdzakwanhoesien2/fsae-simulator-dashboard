function plot_results(result)
    % PLOT_RESULTS Generates standard plots for simulation results.
    
    figure('Name', 'FSAE Simulation Results', 'NumberTitle', 'off');
    
    % Velocity Profile
    subplot(3,1,1);
    plot(result.s, result.v_final * 3.6, 'b', 'LineWidth', 2);
    grid on;
    ylabel('Velocity (km/h)');
    title('Velocity Profile');
    
    % Motor Temperature
    subplot(3,1,2);
    plot(result.s, result.T_fw, 'r', 'LineWidth', 2);
    grid on;
    ylabel('Temp (°C)');
    title('Motor Temperature');
    
    % Pitch Angle
    subplot(3,1,3);
    plot(result.s, rad2deg(result.theta_fw), 'g', 'LineWidth', 2);
    grid on;
    xlabel('Distance (m)');
    ylabel('Pitch (deg)');
    title('Chassis Pitch (Forward Pass)');
end
