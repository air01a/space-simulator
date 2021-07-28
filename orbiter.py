from vector import Vector
from math import atan2, cos, sin, log
import numpy as np
import mathutils
from orbit import Orbit


class Orbiter:
    def __init__(self, empty_mass, carburant_mass):
        self.orbit = None
        self.empty_mass = empty_mass
        self.carburant_mass = empty_mass
        self.r = Vector(0.0,0.0,0.0)
        self.v = Vector(0.0,0.0,0.0)
        self.motor_flow = 1
        self.motor_speed = 1000
        self.attractor = None
        self.orientation1 = 0
        self.orientation2 = 0
        self.last_E = 0

    def set_state(self,r,v,t):
        self.r = r
        self.v = v
        self.orbit.set_from_state_vector(r,v)
        E = mathutils.get_eccentric_from_true_anomaly(self.orbit.f,self.orbit.e)
        #self.M0 = E-self.orbit.e*np.sin(E)
        #self.M0 = mathutils.get_m0(self.orbit.f,self.orbit.e)

        self.M0 = E-self.orbit.e*np.sin(E)
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
        ra = (self.r.x**2+self.r.y**2)**0.5
        angle = atan2(self.r.y,self.r.x)
        a = Vector(-cos(angle)*self.attractor.mu/ra**2,-sin(angle)*self.attractor.mu/ra**2,0)
        self.v = self.v + a * dt
        if dv!=None:
            self.v += dv

        self.r = self.r + self.v * dt

        if dv!=None:
            self.orbit.set_from_state_vector(self.r,self.v)
   

            #self.M0 = mathutils.get_m0(self.orbit.f,self.orbit.e)


    def update_position_delta_t(self, t):

        dt = t-self.t0
        M = self.M0 + (dt)*(self.attractor.mu/(self.orbit.a**3))**0.5
        try:  
            E = mathutils.get_eccentricity_from_mean(self.orbit.e,M)
            self.last_E = E
        except:
            E = self.last_E
        self.M0 = M
        self.t0 = t

        anomaly = mathutils.true_anomaly_from_eccentric(self.orbit.e,E)
        ra = self.orbit.a*(1-self.orbit.e**2)/(1+self.orbit.e*np.cos(anomaly))

        rx = ra * np.cos(anomaly)
        ry = ra * np.sin(anomaly)
        r = mathutils.change_axe(Vector(rx,ry,0), self.orbit.arg_pe, self.orbit.raan, self.orbit.i)



        vx = (self.attractor.mu * self.orbit.a)**0.5 / ra*-np.sin(E) + .0
        vy = (self.attractor.mu * self.orbit.a)**0.5 / ra*(1-self.orbit.e**2)**0.5*np.cos(E)
        v = mathutils.change_axe(Vector(vx,vy,0), self.orbit.arg_pe, self.orbit.raan, self.orbit.i)

        self.r = r
        self.v = v

    def delta_v(self, t, dt, thrust):
        if self.carburant_mass < 0:
            print("Empty")
            return
        v_eject = Vector(-self.motor_speed*cos(self.orientation1), -self.motor_speed*sin(self.orientation1),0)
        mass = self.empty_mass + self.carburant_mass
        carburant_ejected_mass = self.motor_flow * thrust
        dv = -1 * v_eject * log(mass/(mass-carburant_ejected_mass))
        self.carburant_mass -= carburant_ejected_mass
        self.update_position(t,dt, dv)


