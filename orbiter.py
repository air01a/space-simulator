from vector import Vector
from math import atan2, cos, sin, log
import numpy as np
from orbit import Orbit
import logging, inspect

class Orbiter:
    def __init__(self, empty_mass, carburant_mass):
        self.orbit = None
        self.empty_mass = empty_mass
        self.carburant_mass = carburant_mass
        self.r = Vector(0.0,0.0,0.0)
        self.v = Vector(0.0,0.0,0.0)
        self.motor_flow = 1
        self.motor_speed = 20000
        self.attractor = None
        self.orientation1 = 0
        self.orientation2 = 0
        self.last_E = 0

    def set_state(self,r,v,t):
        self.r = r
        self.v = v
        if (self.v.norm()!=0):
            self.orbit.set_from_state_vector(r,v)
            E = self.orbit.get_eccentric_from_true_anomaly()
            self.M0 = self.orbit.get_m0(E)
            self.t0 = t

    def set_attractor(self, attractor):
        self.attractor = attractor
        self.orbit = Orbit(attractor.mu)

    def change_orientation(self, o1, o2):
        self.orientation1 = o1
        self.orientation2 = o2

    def get_force(self):
        ra = self.r.norm()
        angle = atan2(self.r.y,self.r.x)
        return Vector(ra*cos(angle), ra*sin(angle),0)

    def update_position(self, t,dt, dv=None):
        if (self.r.norm() > self.attractor.radius):
            ra = (self.r.x**2+self.r.y**2)**0.5
            angle = atan2(self.r.y,self.r.x)
            a = Vector(-cos(angle)*self.attractor.mu/ra**2,-sin(angle)*self.attractor.mu/ra**2,0)
            self.v = self.v + a * dt


        if dv!=None:
            self.v += dv
        friction = self.attractor.get_drag_force(self.r.norm()-self.attractor.radius,self.v,50,1)
        if friction!=0:
            dv = Vector(0,0,0)
            self.v += dt * friction/(self.empty_mass+self.carburant_mass) 
        self.r = self.r + self.v * dt

        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("Position "+str(self.r))
        logging.debug("Distance "+str(self.r.norm()))
        logging.debug("Velocity "+str(self.v))
        logging.debug("Velocity "+str(self.v.norm()))
        logging.debug("----------------------------")

        if dv!=None and self.r.norm() > self.attractor.radius and self.v.norm()>0:
            self.set_state(self.r,self.v,t)
            return True
            #self.M0 = mathutils.get_m0(self.orbit.f,self.orbit.e)
        return False

    def update_position_delta_t(self, t):
        dt = t-self.t0
        M = self.M0 + (dt)*(self.attractor.mu/(abs(self.orbit.a)**3))**0.5
        try:  
            E = self.orbit.get_eccentricity_from_mean(M)
            self.last_E = E
        except:
            E = self.last_E

        self.M0 = M
        self.t0 = t

        (r,v) = self.orbit.get_state(E)
        self.r = self.orbit.get_eci(r)
        self.v = self.orbit.get_eci(v)


        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("dt %i" % dt)
        logging.debug("E %r" % E)
        logging.debug("r %s" % str(self.r))
        logging.debug("v %s" % str(self.v))
        logging.debug("----------------------------")


    def delta_v(self, t, dt, thrust):
        if self.carburant_mass < 0:
            print("Empty")
            return
        v_eject = Vector(-self.motor_speed*cos(self.orientation1), -self.motor_speed*sin(self.orientation1),0)
        mass = self.empty_mass + self.carburant_mass
        carburant_ejected_mass = self.motor_flow * thrust
        dv = -1 * v_eject * log(mass/(mass-carburant_ejected_mass))
        #self.carburant_mass -= carburant_ejected_mass
        self.update_position(t,dt, dv)


