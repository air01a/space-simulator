########################################
# Define attractor (planets)
########################################


from math import atan2, sin, cos, exp
from vector import Vector
from orbit import Orbit
import logging, inspect
from orbitprojection import OrbitProjection


class Attractor:
    def __init__(self, name, radius, mu=None, mass=None, soi=0):
        self.mass = mass
        self.soi = soi
        self.name = name
        self.parent = None
        self.child = []
        self.r = Vector(0, 0, 0)
        self.v = Vector(0, 0, 0)

        self.mu = mu
        self.radius = radius
        self.atmosphere_limit = 0
        self.atmosphere_color = (0.44, 0.64, 0.94, 0.20)
        self.orbit = None
        self.picture = None
        self.orbit_projection = None
        self.orbit_color = (1, 1, 1, 1)

    def set_orbit_parameters(self, mu, a, e, i, raan, arg_pe, f):
        self.orbit = Orbit(mu)
        self.orbit.set_elements(a, e, i, raan, arg_pe, f)
        (self.r, self.v) = self.orbit.update_position(0)
        if self.parent:
            self.orbit_projection = OrbitProjection(self.parent, self.orbit)
            self.orbit_projection.calculate_time_series(0)

    def set_picture(self, picture):
        self.picture = picture

    def set_atmosphere_condition(self, p0, h0, atmosphere_limit):
        self.p0 = p0
        self.atmosphere_limit = atmosphere_limit
        self.h0 = h0

    def set_pos(self, r):
        self.r = r

    def set_mass(self, mass):
        self.mass = mass

    def set_soir(self, soi):
        self.soi = soi

    def get_pos(self):
        return self.r

    def get_density(self, h):
        if self.atmosphere_limit != 0 and h < self.atmosphere_limit:
            return self.p0 * exp(-h / self.h0)
        return 0

    def add_child(self, child):
        child.parent = self
        self.child.append(child)

    def get_drag_force(self, h, v, drag_x_surf):
        density = self.get_density(h)
        if density == 0:
            return 0
        if v.norm() == 0:
            return 0

        f = 1 / 2 * density * v.norm() ** 2 * drag_x_surf
        F = -(1 / v.norm()) * v * f

        logging.debug(
            "+++++ %s - %s"
            % (
                inspect.getfile(inspect.currentframe()),
                inspect.currentframe().f_code.co_name,
            )
        )
        logging.debug("Friction " + str(F) + " " + str(F.norm()))
        logging.debug("Altitude " + str(h))
        logging.debug("Speed " + str(v.norm()))
        logging.debug("CSV;%i;%i" % (h, v.norm()))
        logging.debug("----------------------------")

        return F

    def get_gravitationnal_field(self, r):
        ra = (r.x ** 2 + r.y ** 2) ** 0.5
        angle = atan2(r.y, r.x)
        g = Vector(-cos(angle) * self.mu / ra ** 2, -sin(angle) * self.mu / ra ** 2, 0)
        return g

    def update_position(self, t):
        if self.orbit:
            (self.r, self.v) = self.orbit.update_position(t)
        for attractor in self.child:
            attractor.update_position(t)

    def check_boundaries(self, r):
        dist = r.norm()
        if dist > self.soi and self.soi > 0 and self.parent:
            return self.parent
        for att in self.child:
            dist = (att.r - r).norm()
            if att.soi > 0 and dist < att.soi:
                return att

        return None

    def change_attractor(self, r, v, new, old):

        # print(r,v)
        if new == old.parent:
            print("change attractor to Parent")
            r += old.r
            v += old.v
        else:
            print("change attractor to child")
            r -= new.r
            v -= new.v
        return (r, v)
