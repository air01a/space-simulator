import numpy as np
import math
from numpy import cos, sin, pi, tan, arccos, arctan, arcsin, cross
from vector import Vector

SMALL_NUMBER = 1e-15
MAX_ITERATIONS = 100


def get_node_vector(h):
    k = Vector(0.0,0.0,1.0)
    return k.cross(h)

def norm(v):
    return np.linalg.norm(v)

def get_eccentric_from_true_anomaly(f,e):
    return 2 * arctan( tan (f / 2) / ((1+e)/(1-e)) ** 0.5 )

def get_eccentricity(r,v,mu):
    return ((v.norm() ** 2 - mu / r.norm()) * r - r.dot(v) * v ) / mu

def get_energy(r,v,mu):
    return v.norm() ** 2 / 2 - mu / r.norm()

def change_axe(v, arg_pe, raan, i):
    ret = Vector(0.0,0.0,0.0)
    rx = v.x
    ry = v.y
    ret.x = 0.0 + rx*(cos(arg_pe) * cos(raan) - sin(arg_pe) * cos(i) * sin(raan)) - ry*( sin(arg_pe) * cos(raan)+ cos(arg_pe) * cos(i) * sin(raan))
    ret.y = 0.0 + rx*(cos(arg_pe) * sin(raan) + sin(arg_pe) * cos(i) * cos(raan)) + ry*(cos(arg_pe) * cos(i) * cos(raan) - sin(arg_pe) * sin(raan)) 
    ret.z = 0.0 + rx*(sin(arg_pe) * sin(i)) + ry*cos(arg_pe) * sin(i)
    return ret



def get_orbit_from_initials(r,v,mu):
    h = r.cross(v)
    n = get_node_vector(h)

    ev = get_eccentricity(r,v,mu)
    E = get_energy(r,v,mu)

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

    return (a, e, i, raan, arg_pe, f)



def _get_polar_ellipse(a,e,angle):
    r = a*(1-e**2)/(1+e*cos(angle))
    return r

def get_time_series(a,e,arg_pe, raan, i):
    
    series=[]
    series_cartesien=[]
    angle = 0
    increment = 2*pi / (50 + (50 + int(a/1000000)))
    while angle<=2*pi:
        r=_get_polar_ellipse(a,e,angle)
        series.append((angle,r))
        r = Vector(r*cos(angle),r*sin(angle),0)
        pos = change_axe(r,arg_pe,raan,i)
        series_cartesien.append(pos)
        angle+=increment
    return (series,series_cartesien)


def get_orbital_period(a,mu):
    return 2*np.pi*((a**3/mu)**0.5)

def get_eccentricity_from_mean(e, M, tolerance=1e-15):
    m_norm = math.fmod(M, 2 * np.pi)
    E0 = M + (-1 / 2 * e ** 3 + e + (e ** 2 + 3 / 2 * np.cos(M) * e ** 3) * np.cos(M)) * np.sin(M)
    dE = tolerance + 1
    count = 0
    while dE > tolerance:
        t1 = np.cos(E0)
        t2 = -1 + e * t1
        t3 = np.sin(E0)
        t4 = e * t3
        t5 = -E0 + t4 + m_norm
        t6 = t5 / (1 / 2 * t5 * t4 / t2 + t2)
        E = E0 - t5 / ((1 / 2 * t3 - 1 / 6 * t1 * t6) * e * t6 + t2)
        dE = abs(E - E0)
        E0 = E
        count += 1
        if count == MAX_ITERATIONS:
            raise Exception('Did not converge after {n} iterations. (e={e!r}, M={M!r})'.format(n=MAX_ITERATIONS, e=e, M=M))
    return E

def get_velocity(a, r, e, mu):
    v = Vector(0.0,0.0,0.0)
    ra = (r.x**2+r.y**2)**0.5
    v.x = -a/ra * 1/((1-e**2)**0.5)*r.y*(mu/a**3)**0.5
    v.y = a/ra * ((1-e**2)**0.5)*(r.x+a*e)*(mu/a**3)**0.5
    return v

def true_anomaly_from_eccentric(e, E):
    """Convert eccentric anomaly to true anomaly."""
    return 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))

def get_mean_from_time(period, t, t0=0):
    return 2 * np.pi * (t-t0)/period

def get_period(a,mu):
    return (4 * np.pi**2  * a**3/ mu) ** 0.5

def get_m0(f,e):
    E = get_eccentric_from_true_anomaly(f,e)
    M0 = E-e*np.sin(E)
    return M0


if __name__ == '__main__':
    import constants

    # Random orbit
    r = Vector(-6045*1000.0, -3490*1000.0, 2500*1000.0)
    v = Vector(-3.457*1000.0, 6.618*1000.0, 2.533*1000.0)
    print(r,v)
    print(r.dot(v))
    (a, e, i, raan, arg_pe, f) = (get_orbit_from_initials(r,v,constants.earth_mu))
    print("Major Axis : %i" % int(a*(1+e)/1000))
    print("Minor Axis : %i" % int(a*(1-e)/1000))
    print("Inclinaison : %i" % int(i*180/np.pi))
    print((a, e, i, raan, arg_pe, f))
    print("period %r" % (get_orbital_period(a,constants.earth_mu)/3600))


    #GEO
    r = Vector(42162 * 1000, 0, 0) 
    v = Vector(0,3074,0)

    o = 0
    (a, e, i, raan, arg_pe, f) = (get_orbit_from_initials(r,v,constants.earth_mu))
    p = get_orbital_period(a,constants.earth_mu)
    print("period %r" % (p/3600))
    M = get_mean_from_time(p, 6*3600,0)
    print(get_eccentricity_from_mean(e,M))
