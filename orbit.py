########################################
# Orbit management (kepler)
########################################


import numpy as np
import math
from numpy import cos, sin, pi, tan, arccos, arctan, arcsin, cross, sinh, tanh, cosh, arctanh, arccos
from math import atan2
from vector import Vector
import constants
import os
import inspect
import logging

class Orbit:
    def __init__(self,mu = constants.earth_mu):
        self.mu = mu
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (0,0,0,0,0,0)
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
        max = self.a*(1+self.e)
        min = self.a*(1-self.e)
        return(min,max)

    # Define kepler elements
    def set_elements(self, a, e, i, raan, arg_pe, f):
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (a, e, i , raan, arg_pe, f)
        E = self.get_eccentric_from_true_anomaly()
        self.M0 = self.get_m0(E)
        



    # Calculate kelpler from velocity and position
    def set_from_state_vector(self,r,v, t = 0):
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

        if abs(i - 0) < SMALL_NUMBER or (abs(i-pi) < SMALL_NUMBER):
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
            if abs(i - 0) < SMALL_NUMBER or (abs(i-pi) < SMALL_NUMBER):
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
           # if ev.z < 0 :
            #    arg_pe = 2 * np.pi - arg_pe
            #    print("ev.z<0")
            
            
            # True anomaly is angle between eccentricity
            # vector and position vector.
            f = np.arccos(ev.dot(r) / (ev.norm() * r.norm()))

            if r.dot(v) < 0:
                f = 2 * np.pi - f


        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("a "+str(a))
        logging.debug("e " + str(e))
        logging.debug("i "+str(i))
        logging.debug("raan " + str(raan))
        logging.debug("arg_pe " + str(arg_pe))
        logging.debug("f " + str(f))
        logging.debug("----------------------------")
        (self.a, self.e, self.i, self.raan, self.arg_pe, self.f) = (a, e, i, raan, arg_pe, f)
        
        E = self.get_eccentric_from_true_anomaly()

        if self.e < 1:
            self.M0 = E - self.e * sin(E)
        elif self.e == 1:
            self.M0 = E - self.e * sin(E)
        else:
            self.M0 = self.e * sinh(E) - E
        self.t0 = t
        self.last_E = E

    # Return period 
    def get_period(self):
        return self.get_orbital_period()

    def set_epoch(self, epoch):
        self.t0 = epoch

    # Calculate node vector
    def get_node_vector(self, h):
        k = Vector(0.0,0.0,1.0)
        return k.cross(h)

    # Calculate eccentricity from true anomaly
    def get_eccentric_from_true_anomaly(self,f = None):
        if f==None:
            f = self.f
        if self.e<1:
            return 2 * arctan( tan (f / 2) / ((1+self.e)/(1-self.e)) ** 0.5 )
        if self.e!=1:
            return 2 * arctanh( tan (f / 2) / ((self.e+1)/(self.e-1)) ** 0.5 )
        return 0

    def get_eccentricity(self,r,v):
        return ((v.norm() ** 2 - self.mu / r.norm()) * r - r.dot(v) * v ) / self.mu

    # Calculate orbiter energy
    def get_energy(self,r,v):
        return v.norm() ** 2 / 2 - self.mu / r.norm()

    # get orbit period
    def get_orbital_period(self):
        return 2*np.pi*((self.a**3/self.mu)**0.5)

    # Calculate R and V with Eccentric anomaly
    def get_state(self, E):
        anomaly = self.true_anomaly_from_eccentric(E)

        ra = self.a*(1-self.e**2)/(1+self.e*cos(anomaly))

        rx = ra * cos(anomaly)
        ry = ra * sin(anomaly)
        r = Vector(rx,ry,0)

        if self.e<1:
            vx = (self.mu * self.a)**0.5 / ra *-sin(E) + .0
            vy = (self.mu * self.a)**0.5 / ra*(1-self.e**2)**0.5*cos(E)
        else:
            angle = arctan(self.e*sin(anomaly)/(1+self.e*cos(anomaly)))
            v = (self.mu*(2/r.norm()-1/self.a))**0.5
            vrx = v * sin(angle)
            vry = v * cos(angle)
            vx = cos(-anomaly) * vrx + sin(-anomaly) * vry
            vy = -sin(-anomaly) * vrx + cos(-anomaly) * vry

        return(r, Vector(vx,vy,0))

    # get real anomaly from mean anomaly
    # 
    def get_eccentricity_from_mean(self, M, tolerance=1e-15):
        En = M
        e = abs(self.e)
        E = M
        v = M
        counter = 0

        # Perfect circle, Mean anomaly = true anomaly
        if self.e==0:
            return M

        # Elliptic trajectory
        elif self.e<1:
            E = En - (En-e*sin(En)- M)/(1 - e*cos(En))
            
            while abs(E-En) > tolerance and counter<self.MAX_ITERATIONS:
                En = E
                E = En - (En - e*sin(En) - M)/(1 - e*cos(En))
                counter+=1
            #sv = ((1 - e * e) **0.5)* sin(E)
            #cv = cos(E) - e
            #v = atan2(sv, cv)

        # Parabolic trajectory
        elif (self.e == 1):
            E = En - (En+En*En*En/3- M)/(En*En+1)
            while (abs(E-En) > 1e-12) and counter<self.MAX_ITERATIONS:
                En = E
                E = En - (En+En*En*En/3- M)/(En*En+1)
                counter+=1
            #v=2*arctan(E)

        # Hyperbolic trajectory
        elif self.e>1:
            E = En - (e*sinh(En)-En- M)/(e*cosh(En)-1)
            while abs(E-En) > 1e-12 and counter<self.MAX_ITERATIONS:
                En = E
                E = En - (e*sinh(En)-En- M)/(e*cosh(En)-1)
                counter+=1

            #sv = ((e * e - 1) ** 0.5) * sinh(E)
            #cv = e - cosh(E)
            #v = atan2(sv, cv)

        return E

    # Calculate velocity from Eccentricity
    def get_velocity(self, E, r):
        ra = (r.x**2+r.y**2)**0.5

        f = ((self.mu * self.a)**0.5)/ra
        v = f*Vector(-sin(E),(1-self.e**2)**0.5*cos(E),0.0)

        return v

    def true_anomaly_from_eccentric(self, E):
        """Convert eccentric anomaly to true anomaly."""
        if self.e<1:
            return 2 * math.atan2(math.sqrt(1 + self.e) * math.sin(E / 2), math.sqrt(1 - self.e) * math.cos(E / 2))
        return 2 * math.atan( math.sqrt ((1+self.e)/(self.e-1)) * tanh(E/2))

    def get_mean_from_time(self, period, t, t0=0):
        return 2 * np.pi * (t-t0)/period

    def get_period(self, a,mu):
        return (4 * np.pi**2  * a**3/ mu) ** 0.5

    def get_m0(self,E):
        if (self.e<1):
            M0 = E-self.e*np.sin(E) 
        else:
            M0 = self.e*sinh(E)-E
        return M0


    def get_mean_from_t(self,t):
        dt = t-self.t0 
        M = self.M0 + (dt)*(self.mu/(abs(self.a)**3))**0.5
        return M

    def get_true_anomaly_at_time(self,t):
        M = self.get_mean_from_t(t)
        E = self.get_eccentricity_from_mean(M)
        return self.true_anomaly_from_eccentric(E)

    # Propagate kepler equation to calculate Velocity and position
    # Use for time acceleration
    def update_angle(self,t):
        M = self.get_mean_from_t(t)
        try:  
            E = self.get_eccentricity_from_mean(M)
            self.last_E = E
        except:
            E = self.last_E
            print("non convergent")
        self.M0 = M
        self.t0 = t
        return E


    def update_position(self, t):
        if self.a !=0:
            E = self.update_angle(t)
            (r,v) = self.get_state(E)
            r = self.get_eci(r)
            v = self.get_eci(v)
 
            logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
            logging.debug("dt %i" % (t-self.t0))
            logging.debug("E %r" % E)
            logging.debug("r %s" % str(r))
            logging.debug("v %s" % str(v))
            logging.debug("----------------------------")
            return (r,v)
        return (Vector(0,0,0),Vector(0,0,0))

# Coordonnates from ellipse reference to global axis
    def get_eci(self,v):
        cos_arg_pe = cos(self.arg_pe)
        sin_arg_pe = sin(self.arg_pe)
        cos_raan = cos(self.raan)
        sin_raan = sin(self.raan)
        cos_i = cos(self.i)
        sin_i = sin(self.i)

        result=[]
        if not isinstance(v,list):
            v_tab = [v]
        else:
            v_tab = v

        for vec in v_tab:
            ret = Vector(0.0,0.0,0.0)
            rx = vec.x
            ry = vec.y

            ret.x = 0.0 + rx*(cos_arg_pe * cos_raan - sin_arg_pe * cos_i * sin_raan) - ry*( sin_arg_pe * cos_raan+ cos_arg_pe * cos_i * sin_raan)
            ret.y = 0.0 + rx*(cos_arg_pe * sin_raan + sin_arg_pe * cos_i * cos_raan) + ry*(cos_arg_pe * cos_i * cos_raan - sin_arg_pe * sin_raan) 
            ret.z = 0.0 + rx*(sin_arg_pe *  sin_i) + ry*cos_arg_pe *  sin_i
            result.append(ret)

        if not isinstance(v,list):
            return result[0]
        return result