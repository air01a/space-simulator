import time
import sys
import constants
import numpy as np
from vector import Vector
from attractor import Attractor
from orbiter import Orbiter
from pilotorbiter import PilotOrbiter
from timecontroller import TimeController
from event import EventListener
from display import Display
import math



earth = Attractor(Vector(0,0,0),6378140.0,constants.earth_mu)
orbiter = Orbiter(2000,1000)
orbiter.set_attractor(earth)

r = Vector([42162.0 * 1000, 0.0, 0.0])
v = Vector([200.0,3074.0*1.1,0.0])
orbiter.set_state(r,v,0)
(polar_orbit,cartesien_orbit) = orbiter.orbit.get_time_series()


event_listener = EventListener()

display = Display(event_listener)
pilot = PilotOrbiter(orbiter, event_listener)
time_controller = TimeController(0,event_listener)

done = False

while not done:
    done = event_listener.pop_event()
    if time_controller.delta_t()==1:
        if pilot.thrust:
            orbiter.delta_v(time_controller.t,time_controller.delta_t(),0.9)
            (polar_orbit,cartesien_orbit) = orbiter.orbit.get_time_series()
        else:
            orbiter.update_position(time_controller.t,time_controller.delta_t())
    else:
        orbiter.update_position_delta_t(time_controller.t)

    display.draw(orbiter, cartesien_orbit)
    time_controller.update_time()
