########################################
# Atmospheric reentry: heating of the orbiters, parachutes
# (no Kivy, no orbiter: pure formulas, testable)
########################################

from math import exp, pi, sqrt

# Sutton-Graves stagnation point heat flux, Earth air (SI units)
SUTTON_GRAVES_K = 1.7415e-4
# Sutton-Graves assumes a cold wall. The flux is proportional to (recovery
# enthalpy v^2/2 - wall enthalpy): x (1 - WALL_SPEED^2 / v^2). 1500 m/s = wall
# at ~1100 K (v = sqrt(2 cp T), cp = 1005): a falling booster does not burn
WALL_SPEED = 1500.0
# Heat load: q accumulated (J/m2), cooling down with this time constant (s).
# Calibrated (tests/test_reentry.py): a bare stage reentering from a low orbit
# breaks up between 70 and 85 km, the nominal ascents stay below half the limit
# Measured: S-IVB 77-79 km, SM 81-82 km, S-IC 74-75 km (perigee 60 to 0 km)
HEAT_TAU = 30.0
HEAT_LOAD_MAX = 1e7
# Plasma visible on the rocket panel above this flux (W/m2)
PLASMA_MIN_FLUX = 50e3


def heat_flux(rho, v, nose_radius):
    """Stagnation point heat flux (W/m2), density rho (kg/m3), speed v (m/s)"""
    if rho <= 0 or nose_radius <= 0 or v <= WALL_SPEED:
        return 0.0
    return SUTTON_GRAVES_K * sqrt(rho / nose_radius) * v ** 3 * (1 - WALL_SPEED ** 2 / v ** 2)


def update_heat_load(load, flux, dt, tau=None):
    """Heat load after dt seconds under the flux: accumulates, cools down"""
    tau = HEAT_TAU if tau is None else tau
    return load * exp(-dt / tau) + flux * dt


# Parachutes: drag coefficient of a canopy, opening time (s)
PARACHUTE_CD = 0.8
PARACHUTE_OPENING = 3.0


def should_deploy(chute, altitude, speed, descending):
    """Automatic deployment: low enough, slow enough, going down"""
    if chute is None or not descending:
        return False
    return altitude < chute.deploy_altitude and speed < chute.max_speed


def opening_progress(progress, dt):
    """Opening progress (0..1) of a deployed parachute after dt seconds"""
    return min(1.0, progress + dt / PARACHUTE_OPENING)


def parachute_area(chute, progress):
    """Drag area (Cd x surface, m2) of the parachute, opening progress 0..1"""
    if chute is None:
        return 0.0
    return PARACHUTE_CD * chute.count * pi * (chute.diameter / 2) ** 2 * progress
