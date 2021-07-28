import mathutils
import constants
import mathutils

class Orbit:
    def __init__(self,mu = constants.earth_mu):
        self.mu = mu
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (0,0,0,0,0,0)
        self.attractor = None
        self.epoch = 0

    def set_attractor(self, attractor):
        self.attractor = attractor


    def set_elements(self, a, e, i, raan, arg_pe, f):
         (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (a, e, i , raan, arg_pe, f)

    def set_from_state_vector(self,r,v):
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = mathutils.get_orbit_from_initials(r,v,self.mu)

    def get_period(self):
        return mathutils.get_orbital_period(self.a,self.mu)

    def set_epoch(self, epoch):
        self.epoch = epoch

    def get_time_series(self):
        return mathutils.get_time_series(self.a, self.e,  self.arg_pe,self.raan,self.i)