function Fy = tire_model(Fz, slip, tire)
    % TIRE_MODEL Magic Formula (Pacejka) tire model.
    %
    % SYNOPSIS:
    %   Fy = tire_model(Fz, slip, tire)
    %
    % INPUTS:
    %   Fz    - Normal load on the tire [N]
    %   slip  - Lateral slip angle or longitudinal slip ratio [rad or -]
    %   tire  - Struct containing Pacejka coefficients function (getPacejka)
    %
    % OUTPUTS:
    %   Fy    - Resulting lateral or longitudinal force [N]
    %
    % DESCRIPTION:
    %   Implements the standard Pacejka Magic Formula: y = D*sin(C*atan(Bx - E(Bx-atan(Bx)))).
    %   The coefficients B, C, D, and E are derived from Fz-sensitive functions.
    
    params = tire.getPacejka(Fz);
    B = params(1); C = params(2); D = params(3); E = params(4);
    
    % Magic Formula: y = D * sin(C * atan(B * x - E * (B * x - atan(B * x))))
    Fy = D * sin(C * atan(B * kappa - E * (B * kappa - atan(B * kappa))));
end
