import numpy as np
import math
from numpy import cos, sin, pi, tan, arccos, arctan, arcsin, cross, sinh
from vector import Vector
import constants

class Orbit:
    def __init__(self,mu = constants.earth_mu):
        self.mu = mu
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (0,0,0,0,0,0)
        self.attractor = None
        self.epoch = 0
        self.SMALL_NUMBER = 1e-15
        self.MAX_ITERATIONS = 100

    def set_attractor(self, attractor):
        self.attractor = attractor


    def set_elements(self, a, e, i, raan, arg_pe, f):
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (a, e, i , raan, arg_pe, f)

    def set_from_state_vector(self,r,v):
        mu = self.mu

        h = r.cross(v)
        n = self.get_node_vector(h)

        ev = self.get_eccentricity(r,v)
        E = self.get_energy(r,v)

        a = -mu / (2 * E)
        e = ev.norm()

        SMALL_NUMBER = 1e-15

        # Inclination is the angle between the angular
        # momentum vector and its z component.
        i = np.arccos(h.z / h.norm())

        if abs(i - 0) < SMALL_NUMBER:
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
                #arg_pe = np.arccos(ev.x / ev.norm())
                arg_pe = math.atan2(ev.y,ev.x)
                if (h.z<0):
                    arg_pe=2*pi-arg_pe
                
        else:
            # Right ascension of ascending node is the angle
            # between the node vector and its x component.
            raan = np.arccos(n.x/ n.norm())
            if n.y < 0:
                raan = 2 * np.pi - raan

            # Argument of periapsis is angle between
            # node and eccentricity vectors.
            arg_pe = np.arccos(n.dot(ev) / (n.norm() * ev.norm()))

        if abs(e - 0) < SMALL_NUMBER:
            if abs(i - 0) < SMALL_NUMBER:
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

            if ev.z < 0:
                arg_pe = 2 * np.pi - arg_pe

            # True anomaly is angle between eccentricity
            # vector and position vector.
            f = np.arccos(ev.dot(r) / (ev.norm() * r.norm()))

            if r.dot(v) < 0:
                f = 2 * np.pi - f
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (a, e, i, raan, arg_pe, f)

    def get_period(self):
        return self.get_orbital_period()

    def set_epoch(self, epoch):
        self.epoch = epoch

    def get_time_series(self):
        return self.get_time_series()


    def get_node_vector(self, h):
        k = Vector(0.0,0.0,1.0)
        return k.cross(h)


    def get_eccentric_from_true_anomaly(self):
        return 2 * arctan( tan (self.f / 2) / ((1+self.e)/(1-self.e)) ** 0.5 )

    def get_eccentricity(self,r,v):
        return ((v.norm() ** 2 - self.mu / r.norm()) * r - r.dot(v) * v ) / self.mu

    def get_energy(self,r,v):
        return v.norm() ** 2 / 2 - self.mu / r.norm()


    # Coordonnates from ellipse reference to global axis
    def change_axe(self,v):
        ret = Vector(0.0,0.0,0.0)
        rx = v.x
        ry = v.y
        cos_arg_pe = cos(self.arg_pe)
        sin_arg_pe = sin(self.arg_pe)
        cos_raan = cos(self.raan)
        sin_raan = sin(self.raan)
        cos_i = cos(self.i)
        sin_i = sin(self.i)


        ret.x = 0.0 + rx*(cos_arg_pe * cos_raan - sin_arg_pe * cos_i * sin_raan) - ry*( sin_arg_pe * cos_raan+ cos_arg_pe * cos_i * sin_raan)
        ret.y = 0.0 + rx*(cos_arg_pe * sin_raan + sin_arg_pe * cos_i * cos_raan) + ry*(cos_arg_pe * cos_i * cos_raan - sin_arg_pe * sin_raan) 
        ret.z = 0.0 + rx*(sin_arg_pe *  sin_i) + ry*cos_arg_pe *  sin_i
        return ret
        
        
    # Get r from angle
    def _get_polar_ellipse(self,angle):
        r = self.a*(1-self.e**2)/(1+self.e*cos(angle))
        return r

    # return ellipse points
    def get_time_series(self):
        series=[]
        series_cartesien=[]
        angle = 0
        increment = 2*pi / (90 )
        angle_max = 2*pi
        if self.e>1:
            angle = -arccos(-1/self.e)
            angle_max = -angle

        while angle<=angle_max:

            r=self._get_polar_ellipse(angle)
            series.append((angle,r))

            r = Vector(r*cos(angle),r*sin(angle),0)

            pos = self.change_axe(r)

            series_cartesien.append(pos)
            angle+=increment
        return (series,series_cartesien)

    # get orbit period
    def get_orbital_period(self):
        return 2*np.pi*((self.a**3/self.mu)**0.5)

    # get real anomaly from mean anomaly
    # 
    def get_eccentricity_from_mean(self, M, tolerance=1e-15):
        m_norm = math.fmod(M, 2 * np.pi)
        E0 = M + (-1 / 2 * self.e ** 3 + self.e + (self.e ** 2 + 3 / 2 * np.cos(M) * self.e ** 3) * np.cos(M)) * np.sin(M)
        dE = tolerance + 1
        count = 0
        if self.e<1:
            mysin = sin
        else:
            mysin = sinh
        while dE > tolerance:
            t1 = np.cos(E0)
            t2 = -1 + self.e * t1
            t3 = np.sin(E0)
            t4 = self.e * t3
            t5 = -E0 + t4 + m_norm
            t6 = t5 / (1 / 2 * t5 * t4 / t2 + t2)
            E = E0 - t5 / ((1 / 2 * t3 - 1 / 6 * t1 * t6) * self.e * t6 + t2)
            dE = abs(E - E0)
            E0 = E
            count += 1
            if count == self.MAX_ITERATIONS:
                raise Exception('Did not converge after {n} iterations. (e={e!r}, M={M!r})'.format(n=self.MAX_ITERATIONS, e=self.e, M=M))
        return E

    def get_velocity(self, a, r, e, mu):
        v = Vector(0.0,0.0,0.0)
        ra = (r.x**2+r.y**2)**0.5
        v.x = -a/ra * 1/((1-e**2)**0.5)*r.y*(mu/a**3)**0.5
        v.y = a/ra * ((1-e**2)**0.5)*(r.x+a*e)*(mu/a**3)**0.5
        return v

    def true_anomaly_from_eccentric(self, e, E):
        """Convert eccentric anomaly to true anomaly."""
        return 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))

    def get_mean_from_time(self, period, t, t0=0):
        return 2 * np.pi * (t-t0)/period

    def get_period(self, a,mu):
        return (4 * np.pi**2  * a**3/ mu) ** 0.5

    def get_m0(self, f,e):
        E = self.get_eccentric_from_true_anomaly()
        M0 = E-e*np.sin(E)
        return M0