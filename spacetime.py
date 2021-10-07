import time
import constants
from vector import Vector
from attractor import Attractor
from orbiter import Orbiter, Stages, Stage_Composant, Orbiters, Load_Orbiters
from pilotorbiter import PilotOrbiter
from timecontroller import TimeController
from event import EventListener
import logging
from controller import Controller
from numpy import pi
from kivy.clock import Clock



class SpaceTime:
    def __init__(self,control_info = None):
        logging.basicConfig(format='Debug:%(message)s', level=logging.INFO)
        self.event_listener = EventListener()
        
        earth = Attractor("Earth",Vector(0,0,0),6378140.0,constants.earth_mu)
        earth.set_atmosphere_condition(1.39,7900,120000)
        earth.set_picture("images/earth.png")

        earth = Attractor("Earth",Vector(0,0,0),6378140.0,constants.earth_mu)
        earth.set_atmosphere_condition(1.39,7900,120000)
        earth.set_picture("images/earth.png")

        moon = Attractor("Moon",Vector(384000*1000,0,0),1737400,constants.moon_mu)
        moon.set_picture("images/moon.png")
        moon.set_soir(66100000)
        moon.set_orbit_parameters(constants.earth_mu, 384000*1000,0,pi,pi,0,2.9*pi/3)

        moon.update_position(0)
        earth.add_child(moon)


        (orbiter_name,orbiter) = Load_Orbiters.get_orbiter("rockets/ariane5.rocket")
        orbiter.set_attractor(earth)

        self.time_controller = TimeController(1,self.event_listener,0)
        self.orbiters = Orbiters(self.time_controller)
        self.orbiters.add_orbiter(orbiter_name,orbiter)
        self.pilot = PilotOrbiter(self.orbiters, self.event_listener)
        self.main_attractor = earth

        self.controller = Controller('missions/ariane5/geo.orbit',self.orbiters, self.time_controller, control_info)


        #orbiter.r = Vector( -6524563.104025579, 3706639.4519880684, -4.5163113759516555e-10 )
        #orbiter.v = Vector( 2693.983421383506, 9844.606589058822, -1.1739868065716526e-12 )
        orbiter.r = Vector( 0, earth.radius, 0 )
        orbiter.v = Vector( 0, 0, 0 )
        orbiter.set_state(orbiter.r,orbiter.v,0)
        orbiter.orbit.calculate_time_series()

    def __del__(self):
        self.controller.stop()

    def update(self,dt=0):
        self.orbiters.apply_remove()
        thrust = False
        for name in list(self.orbiters.get_orbiters().keys()):
            
            orbiter = self.orbiters.get_orbiter(name)
            if orbiter.thrust:
                thrust=True
            if self.time_controller.t_increment<=1 or orbiter.thrust!=0:
                landed = orbiter.update_position(self.time_controller,self.time_controller.delta_t())
            else:
                landed = orbiter.update_position_delta_t(self.time_controller)
            if landed :
                if (orbiter.v.norm()>10):
                    print("Orbiter Crash")
                    self.orbiters.remove(name)
                else:
                    print("Orbiter Landed") 
                    orbiter.v = Vector(0,0,0) 
                    orbiter.r = orbiter.attractor.radius * orbiter.r/orbiter.r.norm() 

            if thrust and self.time_controller.t_increment>10:
                self.time_controller.t_increment = 10

        self.main_attractor.update_position(self.time_controller.t)
        self.time_controller.update_time()