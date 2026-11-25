########################################
# Information bar of the current orbiter (with or without a mission)
########################################

from math import sqrt

import reentry

G0 = 9.80665  # m/s2, for the acceleration in g
# US Standard Atmosphere 1976: (base altitude m, base temperature K, gradient K/m)
ATMOSPHERE_LAYERS = (
    (0, 288.15, -0.0065),
    (11000, 216.65, 0.0),
    (20000, 216.65, 0.001),
    (32000, 228.65, 0.0028),
    (47000, 270.65, 0.0),
    (51000, 270.65, -0.0028),
    (71000, 214.65, -0.002),
    (86000, 186.87, 0.0),
)


def speed_of_sound(altitude):
    """m/s, US Standard Atmosphere 1976 temperature (Earth air)"""
    base, temperature, gradient = ATMOSPHERE_LAYERS[0]
    for layer in ATMOSPHERE_LAYERS:
        if altitude >= layer[0]:
            base, temperature, gradient = layer
    temperature += gradient * (max(altitude, 0.0) - base)
    return sqrt(1.4 * 287.05 * temperature)


def mach_text(orbiter):
    """Mach number in an atmosphere, "-" out of it"""
    h = orbiter.altitude()
    if orbiter.attractor.atmosphere_limit == 0 or h >= orbiter.attractor.atmosphere_limit:
        return "-"
    return "%.2f" % (orbiter.v.norm() / speed_of_sound(h))


def columns(pairs):
    """Two lines (titles, values), each value starting under its title.
    For a fixed width font"""
    widths = [max(len(title), len(value)) for title, value in pairs]
    titles = " ".join(title.ljust(w) for (title, _), w in zip(pairs, widths))
    values = " ".join(value.ljust(w) for (_, value), w in zip(pairs, widths))
    return titles.rstrip() + "\n" + values.rstrip()


def heat_text(orbiter):
    """Flux (kW/m2) and heat load (% of the burn-up limit) of the orbiter"""
    text = "%dkW/m2 %d%%" % (
        round(orbiter.heat_flux / 1000),
        round(100 * orbiter.heat_load / reentry.HEAT_LOAD_MAX),
    )
    if orbiter.has_heat_shield():
        text += " shield"
    return text


def flight_info(orbiters, time):
    """Text of the information bar: time, thrust, altitude, speed, fuel..."""
    orbiter = orbiters.get_current_orbiter()
    if orbiter == None:
        return "No Orbiter found"
    altitude = (orbiter.r.norm() - orbiter.attractor.radius) / 1000
    velocity = orbiter.v.norm() / 1000
    ground_range = orbiter.ground_range()
    pairs = [
        ("time", "%is" % int(time.t)),
        ("thrust", "%.2fkN" % orbiter.thrust),
        ("altitude", "%.2fkm" % altitude),
        ("velocity", "%.2fkm/s" % velocity),
        ("carburant", "%ikg" % int(orbiter.stages.get_carburant_mass())),
        ("orientation", "%ideg" % int(orbiter.orientation1 * 180 / 3.141592)),
        ("acceleration", "%.2fg" % (orbiter.felt_acceleration / G0)),
        ("mach", mach_text(orbiter)),
        ("mass", "%.1ft" % (orbiter.stages.get_total_mass() / 1000)),
        ("distance", "%ikm" % int(orbiter.distance / 1000)),
        ("range", "-" if ground_range is None else "%ikm" % int(ground_range / 1000)),
        ("heat", heat_text(orbiter)),
    ]
    if velocity > 0.005:
        (perigee, apogee) = orbiter.orbit.get_limit()
        perigee = max(0, int((perigee - orbiter.attractor.radius) / 1000))
        apogee = max(0, int((apogee - orbiter.attractor.radius) / 1000))
        # Lowest and highest points of the orbit (perigee/apogee around the Earth)
        pairs.append(("periapsis apoapsis", "[%ikm, %ikm]" % (perigee, apogee)))
    return columns(pairs)
