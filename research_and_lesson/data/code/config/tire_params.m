function tire = tire_params()
    % TIRE_PARAMS Returns tire model parameters and functions.
    
    % Pacejka Coefficients as functions of Fz
    % Based on: Miranda et al. (2021)
    % Returns [B, C, D, E]
    tire.getPacejka = @(Fz) [ ...
        10 * (1 - 0.00002 * Fz), ... % B: Stiffness reduces slightly with load
        1.9, ...                    % C: Shape factor (often constant)
        (1.80 - 0.00004 * Fz) * Fz, ... % D: Peak force (D = mu * Fz)
        0.97 * (1 + 0.00001 * Fz) ... % E: Curvature factor
    ];
end
