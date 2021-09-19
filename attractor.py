import math
from vector import Vector
from orbit import Orbit
import logging, inspect


class Attractor:

    def __init__(self, r, diameter, mu=None, mass=None, soi=None):
        self.mass = mass
        self.soi =  soi
        self.parent = None
        self.child = []
        self.r = r
        self.mu = mu
        self.diameter = diameter
        self.atmosphere_limit = 0
        self.orbit = None

    def set_orbit_parameters(self,a, e , i, raan, arg_pe, f):
        self.orbit = Orbit(self.mu)
        self.orbit.set_elements(a, e, i , raan, arg_pe, f)
        

    def set_atmosphere_condition(self, p0, h0, atmosphere_limit):
        self.p0 = p0
        self.atmosphere_limit = atmosphere_limit
        self.h0 = h0

    def set_pos(self,r):
        self.r = r

    def set_mass(self, mass):
        self.mass = mass
    
    def set_soir(self, soi):
        self.soi = soi

    def get_pos(self):
        return self.r

    def get_density(self, h):
        if self.atmosphere_limit !=None and h<self.atmosphere_limit:
            return self.p0 * math.exp(-h/self.h0)
        return 0

    def get_drag_force(self,h, v, cross_section, drag_coefficient):
        density = self.get_density(h)

        if density ==0:
            return 0
        if v.norm()==0:
            return 0

        f = 1/2 * density * v.norm()**2 * cross_section * drag_coefficient
        F = -(1/v.norm()) * v * f

        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("Friction "+str(F)+" " + str(F.norm()))
        logging.debug("Altitude " + str(h))
        logging.debug("Speed "+str(v.norm()))
        logging.debug("CSV;%i;%i" % (h,v.norm()))
        logging.debug("----------------------------")

        return F



if __name__ == '__main__':
    import constants
    earth = Attractor(Vector(0,0,0),6378140.0,constants.earth_mu)

    v = Vector(1,1,1)
    earth.set_atmosphere_condition(1.39,7.9,120)

    print(earth.get_density(10))
    print(earth.get_drag_force(0, v, 1,1))

    print(v.cross(Vector(4,9,2)))
    print(v+Vector(1,2,3))    
    print(v-Vector(1,2,30))
    print(v.dot(Vector(4,-2,-1)))
    print(v/3.0)
    print(v.norm())

    


        
