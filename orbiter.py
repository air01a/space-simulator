from vector import Vector
from math import atan2, cos, sin, log
import numpy as np
from orbit import Orbit
import logging, inspect

class Stage_Composant:
    def __init__(self,motor_flow, motor_speed, empty_mass, carburant_mass,payload=False):
        self.motor_flow = motor_flow
        self.motor_speed = motor_speed
        self.empty_mass = empty_mass
        self.carburant_mass = carburant_mass
        self.throttle = 1
        self.payload = payload

    def thrust(self,dt):
        if (self.carburant_mass>0):
            t = dt*self.motor_flow * self.motor_speed * self.throttle
            self.carburant_mass -= dt*self.motor_flow
            return (t,self.carburant_mass)
        return (0,0)

class Stages:
    def __init__(self):
        self.stages = []
        self.empty_part = []
        self.total_empty_mass = 0
        self.carburant_mass = 0

    def add_stage(self):
        self.stages.append({})
    
    def add_part(self, name, part):
        self.stages[-1][name]=part
        self.total_empty_mass += part.empty_mass
        if len(self.stages)>1:
            self.total_empty_mass += part.carburant_mass
        else:
            self.carburant_mass += part.carburant_mass
    
    def sep_part(self,name):
        part = self.stages[0][name]
        self.total_empty_mass -= part.empty_mass
        self.carburant_mass -= part.carburant_mass
        del self.stages[0][name]
        if len(self.stages[0])==0:
            del self.stages[0]
            for part in self.stages[0].values():
                self.total_empty_mass -= part.carburant_mass
                self.carburant_mass += part.carburant_mass

    def set_thrust(self,name, throttle):
        self.stages[0][name].throttle = throttle

    def get_thrust(self,dt):
        thrust = 0
        carburant_mass = 0
        for part in self.stages[0].keys():
            (thr,carb) = self.stages[0][part].thrust(dt)
            carburant_mass+=carb
            thrust+=thr
            if thr+carb==0 and part not in self.empty_part and not self.stages[0][part].payload:
                self.empty_part.append(part)
        self.carburant_mass = carburant_mass
        return thrust

    def get_total_mass(self):
        return self.total_empty_mass + self.carburant_mass

    def get_carburant_mass(self):
        return self.carburant_mass

class Orbiter:
    def __init__(self,stages):
        self.orbit = None
        self.empty_mass = 0
        self.r = Vector(0.0,0.0,0.0)
        self.v = Vector(0.0,0.0,0.0)
        self.attractor = None
        self.orientation1 = np.pi/2
        self.orientation2 = 0
        self.last_E = 0
        self.dv = Vector(0.0,0.0,0.0)
        self.stages = stages
        self.thrust = 0

    def set_state(self,r,v,t):
        self.r = r
        self.v = v
        if (self.r.norm()-self.attractor.radius>1000):
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
        friction = self.attractor.get_drag_force(self.r.norm()-self.attractor.radius,self.v,50,0.5)
        if friction!=0:
            dv = Vector(0,0,0)
            self.v += dt * friction/(self.stages.get_total_mass()) 
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

        v_direction = Vector(cos(self.orientation1), sin(self.orientation1),0)
        
        mass = self.stages.get_total_mass()
        thrust = self.stages.get_thrust(dt)
        self.thrust = thrust/(1000*dt)
        self.dv = v_direction * thrust/mass
        
        #v_eject = Vector(-self.motor_speed*cos(self.orientation1), -self.motor_speed*sin(self.orientation1),0)
        #carburant_ejected_mass = self.motor_flow * thrust * dt
        #self.dv = -1 * v_eject * (carburant_ejected_mass/(mass))
        #self.carburant_mass -= carburant_ejected_mass
        #self.thrust = (self.dv.norm()/dt)*mass/1000
        #print(int(t),int(self.thrust),self.dv.norm(), self.r.norm() - int(self.attractor.radius), int(self.v.norm()))

        self.update_position(t,dt, self.dv)


if __name__ == '__main__':
    s1 = Stages()
    booster1 = Stage_Composant(1,2000,2000,6000)
    booster2 = Stage_Composant(1,2000,2000,6000)
    stage1 = Stage_Composant(1,2000,2000,2000)
    s1.add_stage()
    s1.add_part("Booster1",booster1)
    s1.add_part("Booster2",booster2)
    s1.add_part("Stage1",stage1)
    s1.add_stage()
    stage2 = Stage_Composant(1,3000,5000,5000)
    s1.add_part("Stage2",stage2)
    s1.add_stage()
    stage3 = Stage_Composant(0,0,5000,0)
    s1.add_part("Payload",stage3)

    s1.get_thrust(100)
    print(s1.stages)
    print(s1.get_total_mass())


    s1.sep_part("Booster1")
    print(s1.stages)
    s1.sep_part("Booster2")
    print(s1.stages)
    print(s1.get_total_mass())

    s1.sep_part("Stage1")
    print(s1.stages)
    print(s1.get_total_mass())
