import numpy as np
import math
from numpy import cos, sin, pi, tan, arccos, arctan, arcsin, cross, sinh, tanh, cosh
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
        self.epoch = 0
        self.SMALL_NUMBER = 1e-15
        self.MAX_ITERATIONS = 100
        self.polar = []
        self.cartesien = []

    def set_attractor(self, attractor):
        self.attractor = attractor

    def get_limit(self):
        max = self.a*(1+self.e)
        min = self.a*(1-self.e)
        return(min,max)

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

    def get_period(self):
        return self.get_orbital_period()

    def set_epoch(self, epoch):
        self.epoch = epoch

    def get_node_vector(self, h):
        k = Vector(0.0,0.0,1.0)
        return k.cross(h)


    def get_eccentric_from_true_anomaly(self):
        if self.e<1:
            return 2 * arctan( tan (self.f / 2) / ((1+self.e)/(1-self.e)) ** 0.5 )
        if self.e!=1:
            return 2 * arctan( tanh (self.f / 2) / ((1+self.e)/(self.e-1)) ** 0.5 )
        return 0
            
    def get_eccentricity(self,r,v):
        return ((v.norm() ** 2 - self.mu / r.norm()) * r - r.dot(v) * v ) / self.mu

    def get_energy(self,r,v):
        return v.norm() ** 2 / 2 - self.mu / r.norm()


    # Coordonnates from ellipse reference to global axis
    def get_eci(self,v):
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
        if self.e<1:
            r = self.a*(1-self.e**2)/(1+self.e*cos(angle))
        elif self.e==1:
            r = self.a/(1+self.e*cos(angle))
        else:
            r = self.a*(1-self.e**2)/(1+self.e*cos(angle))

        return r

    # return ellipse points
    def calculate_time_series(self):
        series=[]
        series_cartesien=[]

        if (self.a==0):
            return (series, series_cartesien)
        angle = 0
        increment = 2*pi / 30 
        angle_max = 2*pi

        max = self._get_polar_ellipse(pi/2)
        min = self._get_polar_ellipse(0)


        if self.e==1:
            angle = 0
            angle_max = pi/3
        elif self.e>1:
            angle = -arccos(-1/self.e)
            angle_max = -angle


        while angle<=angle_max:
            r=self._get_polar_ellipse(angle)
            series.append((angle,r))
            rv = Vector(r*cos(angle),r*sin(angle),0)
    
            pos = self.get_eci(rv)
            series_cartesien.append(pos)

            inc = increment * min/r
            if (inc<pi/400):
                inc = pi/400
            angle+=inc
        

        min = self._get_polar_ellipse(0)
        series.append((0,min))
        series_cartesien.append((self.get_eci(Vector(min,0,0))))
        if self.e<1:
            max = self._get_polar_ellipse(pi)
            series.append((pi,max))
            series_cartesien.append((self.get_eci(Vector(-max,0,0))))
        else:
            series.append((None,None))
            series_cartesien.append(None)
        self.polar = series
        self.cartesien = series_cartesien

    # get orbit period
    def get_orbital_period(self):
        return 2*np.pi*((self.a**3/self.mu)**0.5)


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
            
            while abs(E-En) > tolerance and counter<100:
                En = E
                E = En - (En - e*sin(En) - M)/(1 - e*cos(En))
                counter+=1
            #sv = ((1 - e * e) **0.5)* sin(E)
            #cv = cos(E) - e
            #v = atan2(sv, cv)

        # Parabolic trajectory
        elif (self.e == 1):
            E = En - (En+En*En*En/3- M)/(En*En+1)
            while (abs(E-En) > 1e-12) and counter<100:
                En = E
                E = En - (En+En*En*En/3- M)/(En*En+1)
                counter+=1
            #v=2*arctan(E)

        # Hyperbolic trajectory
        elif self.e>1:
            E = En - (e*sinh(En)-En- M)/(e*cosh(En)-1)
            while abs(E-En) > 1e-12 and counter<100:
                En = E
                E = En - (e*sinh(En)-En- M)/(e*cosh(En)-1)
                counter+=1

            #sv = ((e * e - 1) ** 0.5) * sinh(E)
            #cv = e - cosh(E)
            #v = atan2(sv, cv)

        return E



    '''def get_eccentricity_from_mean(self, M, tolerance=1e-15):
        if self.e==0:
            return M

        if self.e<1:
            mysin = sin
            mycos = cos
        else:
            mysin = sinh
            mycos = cosh

        m_norm = math.fmod(M, 2 * np.pi)
        E0 = M + (-1 / 2 * self.e ** 3 + self.e + (self.e ** 2 + 3 / 2 * mycos(M) * self.e ** 3) * mycos(M)) * mysin(M)
        dE = tolerance + 1
        count = 0
        
        while dE > tolerance:
            t1 = mycos(E0)
            t2 = -1 + self.e * t1
            t3 = mysin(E0)
            t4 = self.e * t3
            t5 = -E0 + t4 + m_norm
            t6 = t5 / (1 / 2 * t5 * t4 / t2 + t2)
            E = E0 - t5 / ((1 / 2 * t3 - 1 / 6 * t1 * t6) * self.e * t6 + t2)
            dE = abs(E - E0)
            E0 = E
            count += 1
            if count == self.MAX_ITERATIONS:
                raise Exception('Did not converge after {n} iterations. (e={e!r}, M={M!r})'.format(n=self.MAX_ITERATIONS, e=self.e, M=M))
        print("meth 1 : %r" % E)
        return E '''

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