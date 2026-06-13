function forces = aero_model(v, pitch, aero)
    % AERO_MODEL Computes Cl and Cd based on pitch, then returns forces.
    
    map = aero.getAero(pitch);
    forces.Cl = map.Cl;
    forces.Cd = map.Cd;
    forces.F_down = 0.5 * aero.rho * map.Cl * aero.A * v^2;
    forces.F_drag = 0.5 * aero.rho * map.Cd * aero.A * v^2;
end
