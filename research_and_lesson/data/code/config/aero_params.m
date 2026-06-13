function aero = aero_params()
    % AERO_PARAMS Returns aerodynamic parameters and maps.
    
    aero.rho = 1.225;       % kg/m^3, Air density
    aero.A = 1.1;           % m^2, Frontal area
    
    % Attitude-Sensitive Aerodynamics (Aero Map)
    % Based on: Zhang et al. (2022)
    aero.getAero = @(pitch) struct(...
        'Cl', 2.8 * (1 + 0.8 * sin(pitch)), ... % Downforce varies with pitch
        'Cd', 1.3 * (1 + 0.5 * sin(pitch)) ...  % Drag increases with attitude change
    );
end
