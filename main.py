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


earth = Attractor("Earth",Vector(0,0,0),6378140.0,constants.earth_mu)
earth.set_atmosphere_condition(1.39,7900,120000)
earth.set_picture("images/earth.png")
(orbiter_name,orbiter) = Load_Orbiters.get_orbiter("rockets/ariane5.rocket")




moon = Attractor("Moon",Vector(384000*1000,0,0),1737400,constants.moon_mu)
moon.set_picture("images/moon.png")
moon.set_soir(66100000)
moon.set_orbit_parameters(constants.earth_mu, 384000*1000,0,pi,pi,0,2.9*pi/3)

moon.update_position(0)
earth.add_child(moon)

orbiter.set_attractor(earth)
zoom_ratio = 0.1

event_listener = EventListener()
time_controller = TimeController(1,event_listener,0)

orbiter.r = Vector( 7478398.636344926, -3390921.6392330034, 4.152681331646193e-10)
orbiter.v = Vector( -84.15524311869103, -8961.860683358305, 1.097511400027926e-12)


orbiters = Orbiters(time_controller)
orbiters.add_orbiter(orbiter_name,orbiter)
display = Display(earth,event_listener,zoom_ratio)
pilot = PilotOrbiter(orbiters, event_listener)

done = False
clockinit = time.time()
loop = 0

controller = Controller('missions/ariane5/geo.orbit',orbiters, time_controller)

orbiter.r = Vector( -6524563.104025579, 3706639.4519880684, -4.5163113759516555e-10 )
orbiter.v = Vector( 2693.983421383506, 9844.606589058822, -1.1739868065716526e-12 )

time_controller.t_increment=327680/4
time_controller.t = 1000
orbiter.set_state(orbiter.r,orbiter.v,0)
orbiter.orbit.calculate_time_series()

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
            landed = orbiter.update_position(time_controller,time_controller.delta_t())
        else:
            landed = orbiter.update_position_delta_t(time_controller)
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


