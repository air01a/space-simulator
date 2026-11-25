########################################
# Orbit management (kepler)
########################################


import numpy as np
import math
from numpy import (
    cos,
    sin,
    pi,
    tan,
    arccos,
    arctan,
    arcsin,
    cross,
    sinh,
    tanh,
    cosh,
    arctanh,
    arccos,
)
from math import atan2
from vector import Vector
import constants
import os
import inspect
import logging


class Orbit:
    def __init__(self, mu=constants.earth_mu):
        self.mu = mu
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (0, 0, 0, 0, 0, 0)
        self.attractor = None
        self.t0 = 0
        self.SMALL_NUMBER = 1e-15
        self.MAX_ITERATIONS = 100
        self.polar = []
        self.cartesien = []
        self.M0 = 0
        self.last_points = 0

    # Ratach orbit to a planet
    def set_attractor(self, attractor):
        self.attractor = attractor
        self.mu = attractor.mu

    # Define aphelion and perihelion
    def get_limit(self):
        max = self.a * (1 + self.e)
        min = self.a * (1 - self.e)
        return (min, max)

    def _init_elements(self, t):
        self.init_eci_coeff()
        E = self.get_eccentric_from_true_anomaly()

        if self.e < 1:
            self.M0 = E - self.e * sin(E)
        elif self.e == 1:
            self.M0 = E - self.e * sin(E)
        else:
            self.M0 = self.e * sinh(E) - E
        self.t0 = t
        self.last_E = E

    # Define kepler elements
    def set_elements(self, a, e, i, raan, arg_pe, f, t=0):
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (
            a,
            e,
            i,
            raan,
            arg_pe,
            f,
        )
        self._init_elements(t)

    # Internal trigo value store to accelerate calcul
    def init_eci_coeff(self):
        self.cos_arg_pe = cos(self.arg_pe)
        self.sin_arg_pe = sin(self.arg_pe)
        self.cos_raan = cos(self.raan)
        self.sin_raan = sin(self.raan)
        self.cos_i = cos(self.i)
        self.sin_i = sin(self.i)

    # Calculate kelpler from velocity and position
    def set_from_state_vector(self, r, v, t=0):
        mu = self.mu
        h = r.cross(v)
        n = self.get_node_vector(h)
        ev = self.get_eccentricity(r, v)
        E = self.get_energy(r, v)

        a = -mu / (2 * E)
        e = ev.norm()

        # The energy decides the kind of orbit. For a (nearly) radial trajectory
        # (vertical launch: angular momentum ~0), e is 1 up to rounding errors and
        # can be on the wrong side of 1: an ellipse (a > 0) with e = 1 + 2e-16 is
        # computed as a hyperbola -> NaN positions, no trajectory, frozen SOI search
        RADIAL_ECCENTRICITY_MARGIN = 1e-10
        if E < 0 and e > 1 - RADIAL_ECCENTRICITY_MARGIN:
            e = 1 - RADIAL_ECCENTRICITY_MARGIN
        elif E > 0 and e < 1 + RADIAL_ECCENTRICITY_MARGIN:
            e = 1 + RADIAL_ECCENTRICITY_MARGIN

        SMALL_NUMBER = 1e-15

        # Inclination is the angle between the angular
        # momentum vector and its z component.
        # Radial trajectory (h = 0): no orbital plane, equatorial by convention
        i = np.arccos(h.z / h.norm()) if h.norm() > 0 else 0.0
        if abs(i - 0) < SMALL_NUMBER or (abs(i - pi) < SMALL_NUMBER):
            # For non-inclined orbits, raan is undefined;
            # set to zero by convention
            raan = 0
            if abs(e - 0) < SMALL_NUMBER:
                # For circular orbits, place periapsis
                # at ascending node by convention
                arg_pe = 0
            else:
                # Argument of periapsis is the angle between
                # eccentricity vector and its x component.
                # arg_pe = np.arccos(ev.x / ev.norm())
                arg_pe = math.atan2(ev.y, ev.x)

                # a tester !!!
                if h.z < 0:
                    arg_pe = 2 * pi - arg_pe

        else:

            # Right ascension of ascending node is the angle
            # between the node vector and its x component.
            raan = np.arccos(n.x / n.norm())
            if n.y < 0:
                raan = 2 * np.pi - raan

            # Argument of periapsis is angle between
            # node and eccentricity vectors.

            arg_pe = np.arccos(n.dot(ev) / (n.norm() * ev.norm()))

        if abs(e - 0) < SMALL_NUMBER:
            if abs(i - 0) < SMALL_NUMBER or (abs(i - pi) < SMALL_NUMBER):
                # True anomaly is angle between position
                # vector and its x component.
                f = np.arccos(r.x / r.norm())
                if v.x > 0:
                    f = 2 * np.pi - f
            else:
                # True anomaly is angle between node
                # vector and position vector.
                f = np.arccos(n.dot(r) / (n.norm() * r.norm()))
                if np.dot(v) > 0:
                    f = 2 * np.pi - f
        else:
            # already managed by h.z<0???
            # Only for inclined orbits: for equatorial ones arg_pe comes from atan2
            # and ev.z is numerical noise
            equatorial = abs(i - 0) < SMALL_NUMBER or (abs(i - pi) < SMALL_NUMBER)
            if ev.z < 0 and h.z > 0 and not equatorial:
                arg_pe = 2 * np.pi - arg_pe
                # print("ev.z<0")

            # True anomaly is angle between eccentricity
            # vector and position vector.
            # Clipped: rounding can give a cosine just above 1 (radial fall)
            f = np.arccos(np.clip(ev.dot(r) / (ev.norm() * r.norm()), -1.0, 1.0))

            if r.dot(v) < 0:
                f = 2 * np.pi - f

        # Skip the (costly) message formatting when DEBUG is off
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(
                "+++++ %s - %s"
                % (
                    inspect.getfile(inspect.currentframe()),
                    inspect.currentframe().f_code.co_name,
                )
            )
            logging.debug("a " + str(a))
            logging.debug("e " + str(e))
            logging.debug("i " + str(i))
            logging.debug("raan " + str(raan))
            logging.debug("arg_pe " + str(arg_pe))
            logging.debug("f " + str(f))
            logging.debug("----------------------------")
        self.set_elements(a, e, i, raan, arg_pe, f, t)

    # Return period
    def get_period(self):
        return self.get_orbital_period()

    def set_epoch(self, epoch):
        self.t0 = epoch

    # Calculate node vector
    def get_node_vector(self, h):
        k = Vector(0.0, 0.0, 1.0)
        return k.cross(h)

    # Calculate eccentricity from true anomaly
    def get_eccentric_from_true_anomaly(self, f=None):
        if f == None:
            f = self.f
        if self.e < 1:
            return 2 * arctan(tan(f / 2) / ((1 + self.e) / (1 - self.e)) ** 0.5)
        if self.e != 1:
            return 2 * arctanh(tan(f / 2) / ((self.e + 1) / (self.e - 1)) ** 0.5)

        return 0

    def get_eccentricity(self, r, v):
        return ((v.norm() ** 2 - self.mu / r.norm()) * r - r.dot(v) * v) / self.mu

    # Calculate orbiter energy
    def get_energy(self, r, v):
        return v.norm() ** 2 / 2 - self.mu / r.norm()

    # get orbit period
    def get_orbital_period(self):
        return 2 * np.pi * ((self.a ** 3 / self.mu) ** 0.5)

    # Calculate R and V with Eccentric anomaly
    def get_state(self, E):
        anomaly = self.true_anomaly_from_eccentric(E)

        ra = self.a * (1 - self.e ** 2) / (1 + self.e * cos(anomaly))

        rx = ra * cos(anomaly)
        ry = ra * sin(anomaly)
        r = Vector(rx, ry, 0)

        if self.e < 1:
            vx = (self.mu * self.a) ** 0.5 / ra * -sin(E) + 0.0
            vy = (self.mu * self.a) ** 0.5 / ra * (1 - self.e ** 2) ** 0.5 * cos(E)
        else:
            angle = arctan(self.e * sin(anomaly) / (1 + self.e * cos(anomaly)))
            v = (self.mu * (2 / r.norm() - 1 / self.a)) ** 0.5
            vrx = v * sin(angle)
            vry = v * cos(angle)
            vx = cos(-anomaly) * vrx + sin(-anomaly) * vry
            vy = -sin(-anomaly) * vrx + cos(-anomaly) * vry

        return (r, Vector(vx, vy, 0))

    # get real anomaly from mean anomaly
    #
    # Newton's method safeguarded by bisection: the root is known to be in [lo, hi]
    # (f(lo) <= 0 <= f(hi), f increasing). When a Newton step goes outside the
    # bracket, the middle is used instead: convergence is guaranteed, whatever the
    # starting point (plain Newton diverges or is very slow for large mean anomaly
    # or near-parabolic orbits)
    def _solve_kepler(self, f, df, lo, hi, x, tolerance):
        tolerance = max(tolerance, 1e-15 * max(1.0, abs(lo), abs(hi)))
        for _ in range(self.MAX_ITERATIONS):
            fx = f(x)
            if fx == 0:
                return x
            if fx < 0:
                lo = x
            else:
                hi = x
            d = df(x)
            x_new = x - fx / d if d > 0 else lo - 1
            if not (lo < x_new < hi):
                x_new = (lo + hi) / 2
            if abs(x_new - x) <= tolerance or hi - lo <= tolerance:
                return x_new
            x = x_new
        return x

    def _get_eccentricity_from_mean(self, M, _e, tolerance=1e-15):
        En = M
        e = abs(_e)
        E = M
        v = M
        counter = 0

        # Perfect circle, Mean anomaly = true anomaly
        if self.e == 0:
            return M

        # Elliptic trajectory
        elif self.e < 1:
            # Solve with M in [-pi, pi] (E - M is 2pi periodic), root in [M-e, M+e]
            k = math.floor((M + pi) / (2 * pi))
            Mr = M - 2 * pi * k
            E = self._solve_kepler(
                lambda E: E - e * math.sin(E) - Mr,
                lambda E: 1 - e * math.cos(E),
                Mr - e,
                Mr + e,
                Mr + 0.85 * e * (1 if math.sin(Mr) >= 0 else -1),
                tolerance,
            )
            return E + 2 * pi * k

        # Parabolic trajectory
        elif self.e == 1:
            E = En - (En + En * En * En / 3 - M) / (En * En + 1)
            while (abs(E - En) > 1e-12) and counter < self.MAX_ITERATIONS:
                En = E
                E = En - (En + En * En * En / 3 - M) / (En * En + 1)
                counter += 1
            # v=2*arctan(E)

        # Hyperbolic trajectory
        elif self.e > 1:
            # Odd function: solve for |M|. As sinh(E) >= E for E >= 0:
            # e.sinh(E) = M + E >= M and (e - 1).sinh(E) <= M
            # => root in [asinh(M / e), asinh(M / (e - 1))]
            m = abs(M)
            lo = math.asinh(m / e)
            hi = math.asinh(m / (e - 1))
            E = self._solve_kepler(
                lambda E: e * math.sinh(E) - E - m,
                lambda E: e * math.cosh(E) - 1,
                lo,
                hi,
                lo,
                max(tolerance, 1e-12),
            )
            return E if M >= 0 else -E
        if counter >= self.MAX_ITERATIONS:
            return None
        return E

    def get_eccentricity_from_mean(self, M, tolerance=1e-15):
        return self._get_eccentricity_from_mean(M, self.e, tolerance)

    # Calculate velocity from Eccentricity
    def get_velocity(self, E, r):
        ra = (r.x ** 2 + r.y ** 2) ** 0.5

        f = ((self.mu * self.a) ** 0.5) / ra
        v = f * Vector(-sin(E), (1 - self.e ** 2) ** 0.5 * cos(E), 0.0)

        return v

    def true_anomaly_from_eccentric(self, E):
        """Convert eccentric anomaly to true anomaly."""
        if self.e < 1:
            return 2 * math.atan(tan(E / 2) * ((1 + self.e) / (1 - self.e)) ** 0.5)
            # eturn 2 * math.atan2(math.sqrt(1 + self.e) * math.sin(E / 2), math.sqrt(1 - self.e) * math.cos(E / 2))
        return 2 * math.atan(math.sqrt((1 + self.e) / (self.e - 1)) * tanh(E / 2))

    def get_mean_from_time(self, period, t, t0=0):
        return 2 * np.pi * (t - t0) / period

    def get_mean_from_true_anomaly(self, angle):
        E = self.get_eccentric_from_true_anomaly(angle)
        return self.get_mean_from_eccentric(E)

    # def get_period(self, a,mu):
    #    return (4 * np.pi**2  * a**3/ mu) ** 0.5

    def get_m0(self, E):
        if self.e < 1:
            M0 = E - self.e * np.sin(E)
        else:
            M0 = self.e * sinh(E) - E
        return M0

    def get_mean_from_eccentric(self, E):
        if self.e < 1:
            M0 = E - self.e * np.sin(E)
        else:
            M0 = self.e * sinh(E) - E
        return M0

    def get_mean_from_t(self, t):
        dt = t - self.t0
        M = self.M0 + (dt) * (self.mu / (abs(self.a) ** 3)) ** 0.5
        return M

    def get_true_anomaly_at_time(self, t):
        M = self.get_mean_from_t(t)
        E = self.get_eccentricity_from_mean(M)
        return self.true_anomaly_from_eccentric(E)

    # Propagate kepler equation to calculate Velocity and position
    # Use for time acceleration
    def update_angle(self, t, store=True):
        M = self.get_mean_from_t(t)
        E = self.get_eccentricity_from_mean(M)
        if E == None:
            E = self.last_E
            print("Non convergent")
        if store:
            self.last_E = E
            self.M0 = M
            self.t0 = t
        return E

    # Position and velocity (ECI) at absolute time t, WITHOUT modifying the orbit
    # Use for predictions (trajectory projection, encounters...)
    def get_state_at_time(self, t):
        M = self.get_mean_from_t(t)
        E = self.get_eccentricity_from_mean(M, 1e-12)
        if E == None:
            E = self.get_eccentricity_from_mean(M, 1e-9)
        (r, v) = self.get_state(E)
        return (self.get_eci(r), self.get_eci(v))

    def get_position_at_time(self, t):
        return self.get_state_at_time(t)[0]

    # Vectorized get_eci: x, y = arrays of coordinates in the orbit plane
    # Return a (N, 3) numpy array of ECI coordinates
    def get_eci_array(self, x, y):
        cw, sw = self.cos_arg_pe, self.sin_arg_pe
        cr, sr = self.cos_raan, self.sin_raan
        ci, si = self.cos_i, self.sin_i
        out = np.empty((len(x), 3))
        out[:, 0] = x * (cw * cr - sw * ci * sr) - y * (sw * cr + cw * ci * sr)
        out[:, 1] = x * (cw * sr + sw * ci * cr) + y * (cw * ci * cr - sw * sr)
        out[:, 2] = x * (sw * si) + y * (cw * si)
        return out

    # Vectorized positions (N, 3 numpy array) at absolute times ts, without
    # modifying the orbit (Kepler equation solved with Newton on all times at once)
    def get_positions_at_times(self, ts):
        ts = np.asarray(ts, dtype=float)
        e = self.e
        M = self.M0 + (ts - self.t0) * (self.mu / (abs(self.a) ** 3)) ** 0.5
        if e < 1:
            M = np.mod(M + pi, 2 * pi) - pi
            E = M if e < 0.8 else np.full_like(M, pi) * np.sign(M)
            for _ in range(50):
                dE = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
                E = E - dE
                if np.max(np.abs(dE)) < 1e-12:
                    break
            x = self.a * (np.cos(E) - e)
            y = self.a * (1 - e * e) ** 0.5 * np.sin(E)
        else:
            E = np.arcsinh(M / e)
            for _ in range(50):
                dE = (e * np.sinh(E) - E - M) / (e * np.cosh(E) - 1)
                E = E - dE
                if np.max(np.abs(dE)) < 1e-12:
                    break
            x = self.a * (np.cosh(E) - e)
            y = -self.a * (e * e - 1) ** 0.5 * np.sinh(E)
        return self.get_eci_array(x, y)

    # Time (seconds) from absolute time t to reach true anomaly f, moving forward.
    # Ellipse : always in [0, period[
    # Hyperbola : may be negative if f is already behind
    def time_to_true_anomaly(self, f, t):
        n = (self.mu / (abs(self.a) ** 3)) ** 0.5
        dM = self.get_mean_from_true_anomaly(f) - self.get_mean_from_t(t)
        if self.e < 1:
            dM = dM % (2 * pi)
        return dM / n

    def update_position(self, t, store=True):
        if self.a != 0:
            E = self.update_angle(t, store)
            (r, v) = self.get_state(E)
            r = self.get_eci(r)
            v = self.get_eci(v)
            # Skip the (costly) message formatting when DEBUG is off
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(
                    "+++++ %s - %s"
                    % (
                        inspect.getfile(inspect.currentframe()),
                        inspect.currentframe().f_code.co_name,
                    )
                )
                logging.debug("dt %i" % (t - self.t0))
                logging.debug("E %r" % E)
                logging.debug("r %s" % str(r))
                logging.debug("v %s" % str(v))
                logging.debug("----------------------------")
            return (r, v)
        return (None, None)

    # Coordonnates from ellipse reference to global axis
    def get_eci(self, v):

        result = []
        if not isinstance(v, list):
            v_tab = [v]
        else:
            v_tab = v

        for vec in v_tab:
            ret = Vector(0.0, 0.0, 0.0)
            rx = vec.x
            ry = vec.y

            ret.x = (
                0.0
                + rx
                * (
                    self.cos_arg_pe * self.cos_raan
                    - self.sin_arg_pe * self.cos_i * self.sin_raan
                )
                - ry
                * (
                    self.sin_arg_pe * self.cos_raan
                    + self.cos_arg_pe * self.cos_i * self.sin_raan
                )
            )
            ret.y = (
                0.0
                + rx
                * (
                    self.cos_arg_pe * self.sin_raan
                    + self.sin_arg_pe * self.cos_i * self.cos_raan
                )
                + ry
                * (
                    self.cos_arg_pe * self.cos_i * self.cos_raan
                    - self.sin_arg_pe * self.sin_raan
                )
            )
            ret.z = (
                0.0
                + rx * (self.sin_arg_pe * self.sin_i)
                + ry * self.cos_arg_pe * self.sin_i
            )
            result.append(ret)

        if not isinstance(v, list):
            return result[0]
        return result
