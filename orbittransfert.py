from math import pi, sin


class OrbitTransfert:
    def __init__(self, orbiter_name, source_orbit, target_orbit, hohmann):
        self.orbiter_name = orbiter_name
        self.source_orbit = source_orbit
        self.target_orbit = target_orbit
        self.hohmann = hohmann
        self.v_at_target = None
        self.t_burn = None
        self.active = False
        self.current_time = 0

    def get_delta_v(self, orbit):
        (perigee, apogee) = orbit.get_limit()
        v_local = (orbit.mu * (2 / perigee - 1 / orbit.a)) ** 0.5
        return self.v_at_target - v_local

    def get_mean_anomaly_at_encounter(self, angle):
        return self.target_orbit.get_eccentric_from_true_anomaly(angle)

    def get_time_at_encounter(self, M):
        dM = M - self.target_orbit.M0
        t = (
            self.target_orbit.a ** 3 / self.target_orbit.mu
        ) ** 0.5 * dM + self.target_orbit.t0
        print(t)
        return t

    def get_dt(self, t):
        return (self.current_time + self.t_burn) - t

    def reset(self):
        self.active = False

    def calculate_circular_origin(self, current_time):
        source_a = self.source_orbit.a
        dest_a = self.target_orbit.a
        mu = self.source_orbit.mu
        (perigee, apogee) = self.source_orbit.get_limit()
        # Transfert semi axe
        a = (dest_a + source_a) / 2
        self.time_to_target = pi * (a ** 3 / mu) ** 0.5

        true_anomaly = self.target_orbit.get_true_anomaly_at_time(
            self.time_to_target + current_time
        )

        true_anomaly += (
            self.target_orbit.arg_pe
            + self.target_orbit.raan
            - self.source_orbit.arg_pe
            - self.source_orbit.raan
            + pi
        )
        mean_source = self.source_orbit.get_mean_from_true_anomaly(true_anomaly)
        dM = mean_source - self.source_orbit.M0
        t = (
            self.source_orbit.a ** 3 / self.source_orbit.mu
        ) ** 0.5 * dM + self.source_orbit.t0
        if t < 0:
            t += self.source_orbit.get_period()
        self.t_burn = t
        self.v_at_target = 0

    def calculate(self, current_time):
        self.active = True

        self.current_time = current_time
        if self.source_orbit.e < 0.1:
            return self.calculate_circular_origin(current_time)

        source_a = self.source_orbit.a
        dest_a = self.target_orbit.a
        mu = self.source_orbit.mu
        (perigee, apogee) = self.source_orbit.get_limit()

        # Velocity calculation
        #
        # Velocity at perihelion
        v_local = (mu * (2 / perigee - 1 / self.source_orbit.a)) ** 0.5
        # Transfert semi axe
        a = (dest_a + source_a) / 2
        # Velcocity at perihelion of transfert orbit
        self.v_at_target = (mu * (2 / perigee - 1 / a)) ** 0.5
        # delta V
        delta_v = self.v_at_target - v_local
        # Phase calculation
        #
        # Time to reach aphelion on transfert orbit
        self.time_to_target = pi * (a ** 3 / mu) ** 0.5
        print(self.time_to_target)
        # True anomaly at encouter
        true_anomaly = (
            self.source_orbit.arg_pe + self.source_orbit.raan
        )  # True anomaly of source in ellipse frame

        true_anomaly -= (
            self.target_orbit.arg_pe + self.target_orbit.raan
        )  # True anomaly of target in ellipse frame
        true_anomaly += pi  # at 0, the source is at perihelion, at pi, it is at aphelion (and we will reach target at aphelion)
        # Mean anomaly deivated from true_anomaly
        M = self.get_mean_anomaly_at_encounter(true_anomaly)
        # Get time at encouter
        t = self.get_time_at_encounter(M)

        print("t ", t)
        # Get time of departure
        dt = t - self.time_to_target
        print("dt ", dt)
        M_departure = (
            self.target_orbit.M0
            + (dt - self.target_orbit.t0) * (mu / (abs(dest_a) ** 3)) ** 0.5
        )
        print("M dep", M_departure)
        dt = self.get_time_at_encounter(M_departure)

        if dt < 0:
            dt = dt + self.target_orbit.get_period()
        self.t_burn = dt
        print(dt)


if __name__ == "__main__":
    from orbit import Orbit

    mu = 3.986004415e14

    orbit_moon = Orbit(mu)
    orbit_moon.set_elements(
        384000000, 0, 3.141592653589793, 3.141592653589793, 0, 5.2413448739820994
    )

    orbit_apollo = Orbit(mu)
    orbit_apollo.set_elements(
        6600236.795972201,
        0.4,
        3.141592653589793,
        6.233863179530692,
        0,
        5.85323186385278,
    )

    ot = OrbitTransfert("test", orbit_apollo, orbit_moon, True)
    ot.calculate()
