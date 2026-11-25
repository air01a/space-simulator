import time
from constants import max_speed_before_crash
from flightinfo import flight_info
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
    def attractors_list(self, attractor):
        self.attractors.append(attractor)
        for child in attractor.child:
            self.attractors_list(child)

    def show_info(self):
        orbiter = self.orbiters.get_current_orbiter()
        altitude = (orbiter.r.norm() - orbiter.attractor.radius) / 1000
        (perigee, apogee) = orbiter.orbit.get_limit()
        perigee = int((perigee - orbiter.attractor.radius) / 1000)
        apogee = int((apogee - orbiter.attractor.radius) / 1000)
        perigee = max(0, perigee)
        apogee = max(0, apogee)
        velocity = orbiter.v.norm() / 1000
        print(
            "%is %.2fkN %.2fkm %.2fkm/s %ikg %ideg [%ikm, %ikm]"
            % (
                int(self.time_controller.t),
                orbiter.thrust,
                altitude,
                velocity,
                int(orbiter.stages.get_carburant_mass()),
                int(orbiter.orientation1 * 180 / 3.141592),
                perigee,
                apogee,
            )
        )

    def __init__(self, file_name, control_info=None):
        logging.basicConfig(format="Debug:%(message)s", level=logging.INFO)
        # Kivy installs its handlers on the root logger before us, so basicConfig
        # does nothing and the root level stays NOTSET (= every DEBUG is written)
        logging.getLogger().setLevel(logging.INFO)
        self.event_listener = EventListener()

        scene = Scenery(file_name)
        self.main_attractor = scene.read_attractor("MAIN")

        (self.zoom, self.zoom_min, self.zoom_max) = scene.read_zoom()

        self.time_controller = TimeController(1, self.event_listener, 0)
        self.orbiters = scene.read_orbiters(self.time_controller)

        self.pilot = PilotOrbiter(self.orbiters, self.event_listener)

        self.controller = scene.read_mission(self.time_controller)
        self.attractors = []
        self.attractors_list(self.main_attractor)

    def __del__(self):
        if self.controller:
            self.controller.stop()

    # Information bar: shown with or without a mission
    def get_info(self):
        return flight_info(self.orbiters, self.time_controller)

    def update(self, dt=0):
        self.orbiters.apply_remove()
        thrust = False
        for name in list(self.orbiters.get_orbiters().keys()):
            #      self.show_info()
            orbiter = self.orbiters.get_orbiter(name)
            burning = orbiter.is_burning()
            # Engine pushing or moving in an atmosphere: numerical integration
            # (Kepler propagation ignores the thrust, the drag and the heating)
            numerical = burning or orbiter.in_atmosphere()
            if numerical:
                thrust = True
            if self.time_controller.t_increment <= 10 or numerical:
                crashed = orbiter.update_position(
                    self.time_controller, self.time_controller.delta_t()
                )
            else:
                crashed = orbiter.update_position_delta_t(self.time_controller)
            if crashed:
                if orbiter.destroyed:
                    print("Orbiter %s destroyed by the atmospheric reentry" % name)
                else:
                    print("Orbiter Crash")
                self.orbiters.remove(name)

            if thrust and self.time_controller.t_increment > 10:
                self.time_controller.set_time_increment(10)

        self.main_attractor.update_position(self.time_controller.t)
        self.time_controller.update_time()
