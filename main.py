import time
import sys
import constants
from vector import Vector
from attractor import Attractor
from orbiter import Orbiter, Stages, Stage_Composant, Orbiters, Load_Orbiters
from pilotorbiter import PilotOrbiter
from timecontroller import TimeController
from event import EventListener
from display import Display
import logging
from controller import Controller
from numpy import pi



logging.basicConfig(format='Debug:%(message)s', level=logging.INFO)


earth = Attractor(Vector(0,0,0),6378140.0,constants.earth_mu)
earth.set_atmosphere_condition(1.39,7900,120000)
(orbiter_name,orbiter) = Load_Orbiters.get_orbiter("rockets/ariane5.rocket")

moon = Attractor(Vector(384000*1000,0,0),constants.moon_mass,constants.moon_mu)
moon.set_orbit_parameters(384000*1000,0,pi,0,0,0)
moon.orbit.update_position(0)
earth.add_child(moon)
#r = Vector([42162.0 * 1000, 0.0, 0.0])
#v = Vector([-200.0,-3074.0*1.1,0.0])
#r = Vector([ -6203109.232224876, 2731162.6194017506, 249585.2228845337])
#v = Vector( [ -1757.6448117882119, -9897.455983053283, -445.53566889162994])
#r = Vector([ 0, 6378140, 0])
#v = Vector( [ 0, 0, 0])
#r = Vector([ 6498140, 0, 0])
#v = Vector( [ 7800, 7800, 0])
#r = Vector([0 , 6378140, 0])
#v = Vector( [ 0, 0, 0])
orbiter.set_attractor(earth)
zoom_ratio = 50

event_listener = EventListener()
time_controller = TimeController(1,event_listener,0)



orbiters = Orbiters(time_controller)
orbiters.add_orbiter(orbiter_name,orbiter)
display = Display(event_listener,zoom_ratio)
pilot = PilotOrbiter(orbiters, event_listener)

done = False
clockinit = time.time()
loop = 0

controller = Controller('missions/ariane5/geo.orbit',orbiters, time_controller)
while not done:
    loop +=1
    thrust = False
    done = event_listener.pop_event()
    orbiters.apply_remove()
    for name in list(orbiters.get_orbiters().keys()):
        if orbiter.thrust:
            thrust=True
        orbiter = orbiters.get_orbiter(name)
        if time_controller.t_increment<=1 or orbiter.thrust!=0:
            landed = orbiter.update_position(time_controller.t,time_controller.delta_t())
        else:
            landed = orbiter.update_position_delta_t(time_controller.t)
        if landed :
            if (orbiter.v.norm()>10):
                print("Orbiter Crash")
                orbiters.remove(name)
            else:
                print("Orbiter Landed") 
                orbiter.v = Vector(0,0,0) 
                orbiter.r = orbiter.attractor.radius * orbiter.r/orbiter.r.norm() 

        if thrust and time_controller.t_increment>10:
            time_controller.t_increment = 10
    moon.update_position(time_controller.t)

    display.draw(orbiters)
    time_controller.update_time()
    
   
controller.stop()
clock = time.time()

delta = clock - clockinit 
print("Temps : %r, Loop : %r, iteration/s : %r" % (delta, loop, int(loop/(delta))))


