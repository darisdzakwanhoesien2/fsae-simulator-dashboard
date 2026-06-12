
m   = 300;
g   = 9.81;


mu0  = 1.80;        % nominal tyre friction coefficient
k_mu = 0.00004;     % load sensitivity factor

Cd   = 1.3;
Cl   = 2.8;
A    = 1.1;
rho  = 1.225;

r = 9; 

%{
Crr = 0.012;

%test many possible cornering speeds
v_test = linspace(1,40,2000); 

lat_required = [];
lat_available = [];
mu_log = [];


for i = 1:length(v_test)

    v = v_test(i);

    % A. AERODYNAMIC FORCES
    F_down = 0.5 * rho * Cl * A * v^2;
    F_drag = 0.5 * rho * Cd * A * v^2;

    Fz_total = m*g + F_down;% vertical load

    % C. LOAD-SENSITIVE TYRE MODEL
    mu_eff = mu0 - k_mu * Fz_total;
    mu_eff = max(mu_eff,1.0);

    % D. LATERAL FORCE
    F_lat_available = mu_eff * Fz_total; %MMax Avaialbale
    F_lat_required = m * v^2 / r; %required; F = mv^2/r



    lat_available(end+1) = F_lat_available;
    lat_required(end+1) = F_lat_required;
    mu_log(end+1) = mu_eff;

end

% Maximum corner speed:
% required lateral force = available tyre force

difference = abs(lat_available - lat_required);
[~, idx] = min(difference);
v_max = v_test(idx);


% FSAE skidpad: two full circles
distance_total = 2 * 2*pi*r;
time_skidpad = distance_total / v_max;




fprintf('Max Corner Speed : %.2f m/s\n', v_max);

fprintf('Max Corner Speed : %.1f km/h\n', ...
    v_max*3.6);

fprintf('Lateral Accel    : %.2f g\n', ...
    (v_max^2/r)/g);

fprintf('Estimated Time   : %.2f s\n', ...
    time_skidpad);


%}



% Chassis
h_cg  = 0.280;   
track = 1.20; 

% Approximate roll center height
h_rc = 0.05;  

v_test = linspace(1,40,2000);

lat_required  = [];
lat_available = [];
mu_log        = [];
load_transfer_log = [];
 
for i = 1:length(v_test)

    v = v_test(i);

    % A. AERODYNAMICS
    F_down = 0.5 * rho * Cl * A * v^2;
    F_drag = 0.5 * rho * Cd * A * v^2;


    Fz_total = m*g + F_down; % total vertical load
    ay = v^2 / r; % req lat accel
    load_transfer =  m * ay * (h_cg - h_rc) / track; %lateral


    % B. TIRE LOADS
    Fz_static_per_tire = Fz_total / 4;

    % Outside tires gain load
    Fz_outside = Fz_static_per_tire + load_transfer/2;

    % Inside tires lose load
    Fz_inside = Fz_static_per_tire - load_transfer/2;

    % Prevent negative loads
    Fz_inside = max(Fz_inside,50);

    % C. LOAD-SENSITIVE FRICTION
    mu_outside = mu0 - k_mu*Fz_outside;
    mu_inside  = mu0 - k_mu*Fz_inside;

    mu_outside = max(mu_outside,1.0);
    mu_inside  = max(mu_inside,1.0);

    % D. AVAILABLE LATERAL FORCE
    Fy_outside = mu_outside * Fz_outside;
    Fy_inside  = mu_inside  * Fz_inside;

    % Total force from all four tires
    F_lat_available = 2*Fy_outside + 2*Fy_inside;

    F_lat_required = m*v^2/r; % req lat


    lat_available(end+1) = F_lat_available;
    lat_required(end+1)  = F_lat_required;

    mu_log(end+1) = ...
        (2*mu_outside + 2*mu_inside)/4;

    load_transfer_log(end+1) = load_transfer;

end

% FIND MAX CORNER SPEED
difference = abs(lat_available - lat_required);

[~,idx] = min(difference);

v_max = v_test(idx);

% SKIDPAD TIME
distance_total = 2 * 2*pi*r;
time_skidpad = distance_total / v_max;



fprintf('\n');
fprintf('Max Corner Speed : %.2f m/s\n', v_max);

fprintf('Max Corner Speed : %.1f km/h\n', ...
    v_max*3.6);

fprintf('Lateral Accel    : %.2f g\n', ...
    (v_max^2/r)/g);

fprintf('Skidpad Time     : %.2f s\n', ...
    time_skidpad);

fprintf('Peak Load Transfer : %.0f N\n', ...
    max(load_transfer_log));
