import time
import sys
import constants
from vector import Vector
from attractor import Attractor
from orbiter import Orbiter
from pilotorbiter import PilotOrbiter
from timecontroller import TimeController
from event import EventListener
from display import Display


earth = Attractor(Vector(0,0,0),6378140.0,constants.earth_mu)
earth.set_atmosphere_condition(1.39,7900,120000)

orbiter = Orbiter(2000,8000)
orbiter.set_attractor(earth)

r = Vector([42162.0 * 1000, 0.0, 0.0])
v = Vector([200.0,3074.0*1.1,100.0])

#r = Vector([ -6203109.232224876, 2731162.6194017506, 249585.2228845337])
#v = Vector( [ -1757.6448117882119, -9897.455983053283, -445.53566889162994])
orbiter.set_state(r,v,0)
(polar_orbit,cartesien_orbit) = orbiter.orbit.get_time_series()


event_listener = EventListener()

display = Display(event_listener,1)
pilot = PilotOrbiter(orbiter, event_listener)
time_controller = TimeController(1,event_listener,0)

done = False
clockinit = time.time()
loop = 0
while not done:
    loop +=1
    done = event_listener.pop_event()
    # print(orbiter.r,orbiter.v)
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
    
    if orbiter.r.norm()<earth.diameter:
        done = True
    
clock = time.time()

delta = clock - clockinit 
print("Temps : %r, Loop : %r, iteration/s : %r" % (delta, loop, int(loop/(delta))))


