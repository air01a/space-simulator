from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

import time
import constants
from vector import Vector
from attractor import Attractor
from orbiter import Orbiter, Stages, Stage_Composant, Orbiters, Load_Orbiters
from pilotorbiter import PilotOrbiter
from timecontroller import TimeController
from event import EventListener
from display import Graphics
import logging
from controller import Controller
from numpy import pi



class SpaceSimulator(Widget):
    def __init__(self):
        super(SpaceSimulator, self).__init__()
        self.event_listener = EventListener()
        logging.basicConfig(format='Debug:%(message)s', level=logging.INFO)
        
        earth = Attractor("Earth",Vector(0,0,0),6378140.0,constants.earth_mu)
        earth.set_atmosphere_condition(1.39,7900,120000)
        earth.set_picture("images/earth.png")
        (orbiter_name,orbiter) = Load_Orbiters.get_orbiter("rockets/ariane5.rocket")

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
        zoom_ratio = 0.5

        self.time_controller = TimeController(1,self.event_listener,0)

        orbiter.r = Vector( 7478398.636344926, -3390921.6392330034, 4.152681331646193e-10)
        orbiter.v = Vector( -84.15524311869103, -8961.860683358305, 1.097511400027926e-12)


        self.orbiters = Orbiters(self.time_controller)
        self.orbiters.add_orbiter(orbiter_name,orbiter)
        #display = Display(earth,event_listener,zoom_ratio)
        self.pilot = PilotOrbiter(self.orbiters, self.event_listener)
        self.main_attractor = earth

        self.controller = Controller('missions/ariane5/geo.orbit',self.orbiters, self.time_controller)

        self.display = Graphics(self.orbiters,  self.event_listener, zoom_ratio)

        self.add_widget(self.display)

        orbiter.r = Vector( -6524563.104025579, 3706639.4519880684, -4.5163113759516555e-10 )
        orbiter.v = Vector( 2693.983421383506, 9844.606589058822, -1.1739868065716526e-12 )
        orbiter.set_state(orbiter.r,orbiter.v,0)
        orbiter.orbit.calculate_time_series()

    def update_space(self,dt):
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

    def draw(self,dt):
        self.display.draw()

class SpaceSimulatorApp(App):
    def build(self):
        

        window_manager =  SpaceSimulator()

        event = Clock.schedule_interval(window_manager.update_space, 1 / 60.)
        display = Clock.schedule_interval(window_manager.draw, 1 / 24.)

        return window_manager

if __name__ == '__main__':
    SpaceSimulatorApp().run()