function veh = vehicle_params()
    % VEHICLE_PARAMS Returns the vehicle physical parameters.
    veh.m = 300;            % kg, mass
    veh.g = 9.81;           % m/s^2, gravity
    veh.L = 1.530;          % m, wheelbase
    veh.a_cg = 0.765;       % m, CG from front axle
    veh.h_cg = 0.280;       % m, CG height
    veh.track = 1.20;       % m, track width
    veh.h_rc = 0.05;        % m, roll center height
    veh.K_pitch = 50000;    % Nm/rad, pitch stiffness
    veh.C_pitch = 4500;     % Nms/rad, pitch damping
    veh.I_pitch = 220;      % kgm^2, pitch inertia
    veh.K_roll = 40000;     % Nm/rad, roll stiffness
    veh.r_wheel = 0.229;    % m, wheel radius
    veh.J_wheel = 0.60;     % kgm^2, wheel inertia
    veh.Crr = 0.012;        % -, rolling resistance coefficient
end
