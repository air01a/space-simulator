import time
import sys
import constants
from vector import Vector
from attractor import Attractor
from orbiter import Orbiter, Stages, Stage_Composant
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





stages = Stages()
booster1 = Stage_Composant(1800,3600,38000,237000)
booster2 = Stage_Composant(1800,3600,38000,237000)
stage1 = Stage_Composant(270,4200,12300,220000)
stages.add_stage()
stages.add_part("Booster1",booster1)
stages.add_part("Booster2",booster2)
stages.add_part("Stage1",stage1)
stages.add_stage()
stage2 = Stage_Composant(17,4800,2100,10500)
stages.add_part("Stage2",stage2)
stages.add_stage()
stage3 = Stage_Composant(0,0,5000,0,True)
stages.add_part("Payload",stage3)
orbiter = Orbiter(stages)
orbiter.set_attractor(earth)

r = Vector([42162.0 * 1000, 0.0, 0.0])
v = Vector([-200.0,-3074.0*1.1,0.0])
zoom_ratio = 50
#r = Vector([ -6203109.232224876, 2731162.6194017506, 249585.2228845337])
#v = Vector( [ -1757.6448117882119, -9897.455983053283, -445.53566889162994])
#r = Vector([ 0, 6378140, 0])
#v = Vector( [ 0, 0, 0])
#r = Vector([ 6498140, 0, 0])
#v = Vector( [ 7800, 7800, 0])
r = Vector([0 , 6378140, 0])
v = Vector( [ 0, 0, 0])

zoom_ratio = 50
orbiter.set_state(r,v,0)
(polar_orbit,cartesien_orbit) = orbiter.orbit.get_time_series()


event_listener = EventListener()

display = Display(event_listener,zoom_ratio)
pilot = PilotOrbiter(orbiter, event_listener)
time_controller = TimeController(1,event_listener,0)

done = False
clockinit = time.time()
loop = 0

controller = Controller(orbiter, time_controller)
while not done:
    loop +=1
    done = event_listener.pop_event()
    if time_controller.delta_t()<=1:
        if pilot.thrust:
            orbiter.delta_v(time_controller.t,time_controller.delta_t(),0.9)
            (polar_orbit,cartesien_orbit) = orbiter.orbit.get_time_series()
        else:
            if orbiter.update_position(time_controller.t,time_controller.delta_t()):
                (polar_orbit,cartesien_orbit) = orbiter.orbit.get_time_series()
            time.sleep(0.1)

    else:
        orbiter.update_position_delta_t(time_controller.t)

    display.draw(orbiter, cartesien_orbit)
    time_controller.update_time()
    
    if orbiter.r.norm()<=earth.radius:
        if (orbiter.v.norm()>10):
            done = True
            print("Crash on earth")
        else:
            r.v = Vector(0,0,0)

controller.stop()
clock = time.time()

delta = clock - clockinit 
print("Temps : %r, Loop : %r, iteration/s : %r" % (delta, loop, int(loop/(delta))))


