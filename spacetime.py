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
from scenery import Scenery


class SpaceTime:
    def show_info(self):
        orbiter = self.orbiters.get_current_orbiter()
        altitude = (orbiter.r.norm() - orbiter.attractor.radius)/1000
        (perigee,apogee) = orbiter.orbit.get_limit()
        perigee = int((perigee-orbiter.attractor.radius)/1000)
        apogee = int((apogee - orbiter.attractor.radius)/1000)
        perigee = max(0,perigee)
        apogee = max(0,apogee)
        velocity = orbiter.v.norm()/1000
        print("%is %.2fkN %.2fkm %.2fkm/s %ikg %ideg [%ikm, %ikm]"%(int(self.time_controller.t),orbiter.thrust,altitude, velocity,int(orbiter.stages.get_carburant_mass()),int(orbiter.orientation1*180/3.141592),perigee,apogee))

    def __init__(self,file_name,control_info = None):
        logging.basicConfig(format='Debug:%(message)s', level=logging.INFO)
        self.event_listener = EventListener()
        
        scene = Scenery(file_name)
        self.main_attractor = scene.read_attractor('MAIN')

        self.time_controller = TimeController(1,self.event_listener,0)
        self.orbiters = scene.read_orbiters(self.time_controller)

        self.pilot = PilotOrbiter(self.orbiters, self.event_listener)

        self.controller = scene.read_mission(self.time_controller)



    def __init__2(self,control_info = None):
        logging.basicConfig(format='Debug:%(message)s', level=logging.INFO)
        self.event_listener = EventListener()
        
 
        earth = Attractor("Earth",6378140.0,constants.earth_mu)
        earth.set_atmosphere_condition(1.39,7900,120000)
        earth.set_picture("images/earth.png")
        earth.set_soir(925000000)
        #earth.set_soir(384000*1000 - 66100000)

        moon = Attractor("Moon",1737400,constants.moon_mu)
        moon.set_picture("images/moon.png")
        moon.set_soir(66100000)
        moon.set_orbit_parameters(constants.earth_mu, 384000*1000,0,pi,pi,0,2.91*pi/3)

        moon.update_position(0)
        earth.add_child(moon)


        (orbiter_name,orbiter) = Load_Orbiters.get_orbiter("rockets/saturne5.rocket")
        orbiter.set_attractor(earth)

        self.time_controller = TimeController(1,self.event_listener,0)
        self.orbiters = Orbiters(self.time_controller)
        self.orbiters.add_orbiter(orbiter_name,orbiter)
        self.pilot = PilotOrbiter(self.orbiters, self.event_listener)
        self.main_attractor = earth

        self.controller = Controller('missions/apollo/apollo.orbit',self.orbiters, self.time_controller)
        #orbiter.set_controller(self.controller)
        #orbiter.r = Vector( -6524563.104025579, 3706639.4519880684, -4.5163113759516555e-10 )
        #orbiter.v = Vector( 2693.983421383506, 9844.606589058822, -1.1739868065716526e-12 )
        #orbiter.r = Vector( 0, earth.radius, 0 )
        #orbiter.v = Vector( 0, 0, 0 )
        #orbiter.r = Vector( -6490850.607718132, 3828728.176957996, -4.661190726332874e-10)
        #orbiter.v = Vector( 2769.2699383839617, 9958.979418659352, -1.1739868065716526e-12)

        #orbiter.r = Vector( -6305069.872293199, 4544958.402749465, -5.548446001105239e-10)
        #orbiter.v = Vector(1989.0579153083816, 9224.919681644054, -1.1739868065716526e-12)
        #orbiter.set_state(orbiter.r,orbiter.v,0)

        orbiter.r = Vector( -2440038.190849225, 6300272.642030265, -7.715608724818002e-10)
        orbiter.v = Vector( 9212.087393355065, 5585.145747212256, -6.839830862094941e-13)
        orbiter.set_state(orbiter.r,orbiter.v,0)
        orbiter.orbit_projection.calculate_time_series()

    def __del__(self):
        self.controller.stop()

    def update(self,dt=0):
        self.orbiters.apply_remove()
        thrust = False
        for name in list(self.orbiters.get_orbiters().keys()):
      #      self.show_info()
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
                self.time_controller.set_time_increment(10)

        self.main_attractor.update_position(self.time_controller.t)
        #print(self.time_controller.t, self.main_attractor.child[0].r)
        self.time_controller.update_time()