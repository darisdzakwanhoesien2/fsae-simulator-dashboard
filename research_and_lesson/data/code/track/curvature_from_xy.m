function kappa = curvature_from_xy(x, y)
    % CURVATURE_FROM_XY Calculates curvature (1/R) from X-Y coordinates.
    % Based on the Menger curvature formula.
    
    N = length(x);
    kappa = zeros(N, 1);
    
    for i = 2:N-1
        x1 = x(i-1); y1 = y(i-1);
        x2 = x(i);   y2 = y(i);
        x3 = x(i+1); y3 = y(i+1);
        
        % Area of triangle formed by three points
        area = 0.5 * abs(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2));
        
        % Lengths of sides
        side1 = sqrt((x1-x2)^2 + (y1-y2)^2);
        side2 = sqrt((x2-x3)^2 + (y2-y3)^2);
        side3 = sqrt((x3-x1)^2 + (y3-y1)^2);
        
        % Curvature = 4 * area / (side1 * side2 * side3)
        if area < 1e-9 || (side1*side2*side3) < 1e-9
            kappa(i) = 0; % Straight
        else
            kappa(i) = (4 * area) / (side1 * side2 * side3);
        end
    end
    
    % Edge cases: copy neighboring values
    kappa(1) = kappa(2);
    kappa(end) = kappa(end-1);
end
