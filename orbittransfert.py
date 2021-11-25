from math import pi, sin


class OrbitTransfert:
    def __init__(self, orbiter_name, source_orbit, target_orbit, hohmann):
        self.orbiter_name = orbiter_name
        self.source_orbit = source_orbit.orbit
        self.target_orbit = target_orbit.orbit
        self.source = source_orbit
        self.target = target_orbit
        self.hohmann = hohmann
        self.v_at_target = None
        self.t_burn = None
        self.active = False
        self.current_time = 0
        self.source_angle = source_orbit.r.angle2D()
        self.target_angle = target_orbit.r.angle2D()

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
        dt = (self.current_time + self.t_burn) - t
        if dt < 0:
            dt = 0
        return dt

    def reset(self):
        self.active = False

    def calculate(self, current_time):
        # Return to parent means escape from attractor SOI
        # Calculate liberation speed and orientation to decrease velocity relative to earth
        if (
            self.source.attractor.parent
            and self.source.attractor.parent.name == self.target.name
        ):
            self.v_at_target = (
                2 * self.source.orbit.mu / (self.source.r.norm())
            ) ** 0.5
            r = self.source.attractor.r
            parent_angle = (-r).angle2D()
            if parent_angle < 0:
                parent_angle += 2 * pi

            diff_angle = parent_angle - self.source_angle
            if diff_angle < 0:
                diff_angle += 2 * pi
            w_source = (self.source.orbit.mu / self.source.r.norm() ** 3) ** 0.5

            diff_i = (self.source_orbit.i - pi / 2) * (
                self.source.attractor.orbit.i - pi / 2
            ) < 0
            if diff_i:
                diff_angle = (diff_angle + pi) % (2 * pi)

            self.t_burn = diff_angle / w_source
            self.time_to_target = (
                pi * (self.source.attractor.r.norm() ** 3 / self.target.mu) ** 0.5
            )
            self.current_time = current_time

            return

        # Else, calculate orbital transfert parameters
        source_a = self.source_orbit.a
        dest_a = self.target_orbit.a
        mu = self.source_orbit.mu
        self.current_time = current_time
        (perigee, apogee) = self.source_orbit.get_limit()
        # Transfert semi axe
        a = (dest_a + source_a) / 2
        self.time_to_target = pi * (a ** 3 / mu) ** 0.5

        # Phasis calcul
        w_target = (mu / dest_a ** 3) ** 0.5
        w_source = (mu / source_a ** 3) ** 0.5
        alpha_init = self.target_angle - self.source_angle

        # Time
        alpha = (-alpha_init + w_target * self.time_to_target) - pi
        w_diff = w_source - w_target
        self.t_burn = alpha / w_diff
        if self.t_burn < 0:
            self.t_burn += 2 * pi / abs(w_diff)

        self.v_at_target = (mu * (2 / perigee - 1 / a)) ** 0.5
        # delta V

    def get_time_to_reach(self, t):
        return (self.current_time + self.t_burn) - t + self.time_to_target

    def calculate_not_circular(self, current_time):
        self.active = True

        self.current_time = current_time
        if self.source_orbit.e < 0.1:
            return self.calculate(current_time)

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

        # Get time of departure
        dt = t - self.time_to_target
        M_departure = (
            self.target_orbit.M0
            + (dt - self.target_orbit.t0) * (mu / (abs(dest_a) ** 3)) ** 0.5
        )
        dt = self.get_time_at_encounter(M_departure)

        if dt < 0:
            dt = dt + self.target_orbit.get_period()
        self.t_burn = dt
        print(dt)

    def get_current_delta_v(self):
        return self.target.v.norm() - self.source.v.norm()

    def get_current_distance(self):
        return (self.target.r - self.source.r).norm()


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
