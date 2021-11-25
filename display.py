# THE UGLY part

from math import log
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout

import time
from vector import Vector
from constants import (
    altitude_landing_help,
    default_earth_size,
)

from graphical.ship import DrawTrajectory
from graphical.goto import Goto
from graphical.compas import Compas
from graphical.attractor import DrawAttractor


class Graphics(BoxLayout):
    def on_orbiter_touch(self, direction):
        orbiters = self.orbiters.get_current_orbiter_names()
        self.orbiter_index += direction
        if self.orbiter_index < 0:
            self.orbiter_index = len(orbiters) - 1

        if self.orbiter_index >= len(orbiters):
            self.orbiter_index = 0

        if self.orbiter_index >= 0:
            self.ids.orbiter_control.text = orbiters[self.orbiter_index]
        else:
            self.ids.orbiter_control.text = "None"

    def change_orbiter(self):
        self.orbiters.current_orbiter = self.ids.orbiter_control.text

    def drop_payload(self):
        self.world.pilot.drop_payload()

    def init_zoom(self):
        if self.world.zoom:
            self.change_zoom(self.world.zoom)
        else:
            self.zoom_ratio = 50
        if self.world.zoom_min:
            self.ids.zoom.min = self.world.zoom_min
        if self.world.zoom_max:
            self.ids.zoom.max = self.world.zoom_max
        self.set_zoom_display()

    def init(self, world):

        self.lock = False
        self.orbiter_index = 0
        self.goto = None
        self.orbiters = world.orbiters
        self.world = world
        orbiter_name = self.orbiters.get_current_orbiter_name()
        if not orbiter_name:
            orbiter_name = "None"
        self.ids.orbiter_control.text = orbiter_name

        self.orbit_factor = default_earth_size / (2 * 6378140)
        self.width, self.height = Window.size
        self.police_size = int(self.height / 800 * 18)
        self.slider_hold = False

        self.draw_attractors = DrawAttractor()
        self.draw_attractors.init(world.main_attractor, self.orbit_factor)
        self.draw_trajectory = DrawTrajectory()
        self.draw_trajectory.set_ratio(self.orbit_factor)
        self.draw_trajectory.police_size = self.police_size
        self.ids.dynamics.add_widget(self.draw_attractors)
        self.ids.dynamics.add_widget(self.draw_trajectory)
        self.ids.compas.init(world)
        world.event_listener.add_key_event(
            112, self.change_center, "Change screen center (attractor vs ship)"
        )

        world.event_listener.add_key_event(97, self.zoom_out, "Zoom out")
        world.event_listener.add_key_event(113, self.zoom_in, "Zoom in")

        if self.world.controller:
            self.world.controller.add_control_callback(self.control_info)
            self.world.pilot.control_info_callback = self.control_info
        self.world.time_controller.set_call_back(self.on_time_change)
        self.goto = Goto()
        self.goto.set_world(world)
        self.init_zoom()

    def orbiter_orientation_lock(self, lock):
        if lock == "pro":
            self.world.orbiters.get_current_orbiter().lock_orientation_prograde()
        else:
            self.world.orbiters.get_current_orbiter().lock_orientation_retrograde()

    def control_info(self, message, thrust, orientation, engine=None):
        if message:
            self.parent.parent.ids.controlInfoLabel.text = message
        elif thrust != None and orientation != None:
            self.parent.parent.ids.controlInfoLabel.text = (
                "+++ Attitude Control Angle %s +++" % str(orientation)
            )
        elif message != None:
            print(message, thrust, orientation)

        if engine != None:
            self.ids.switch.active = engine

    def engine_on(self, active):
        if active:
            self.world.pilot.engine_on()
        else:
            self.world.pilot.engine_off()

    def rcs_push(self):
        self.world.orbiters.get_current_orbiter().rcs_push()

    def drop_stage(self):
        self.orbiters.separate_full_stage(self.orbiters.get_current_orbiter())
        self.engine_on(False)

    def adapt_zoom(self):
        self.earth_diameter = self.zoom_ratio * default_earth_size / 2
        self.x_center = self.width / 2 - self.earth_diameter
        self.y_center = self.height / 2 - self.earth_diameter

    def change_zoom(self, value):
        while self.lock:
            time.sleep(0.01)
        value = 10 - value
        if value < 0:
            self.zoom_ratio = 1 / 1.1 ** abs(value)
        else:
            self.zoom_ratio = 1 + 2 ** abs(value)
        self.adapt_zoom()
        self.update()

    def set_zoom_display(self):
        if self.zoom_ratio < 1:
            value = 10 + log(1 / self.zoom_ratio) / log(1.1)
        else:
            value = 10 + log(self.zoom_ratio - 1) / log(2)
        self.ids.zoom.value = value

    def zoom_out(self):
        while self.lock:
            time.sleep(0.01)
        self.zoom_ratio = (
            self.zoom_ratio + 1.0 if self.zoom_ratio > 1 else self.zoom_ratio * 1.1
        )
        self.adapt_zoom()
        self.set_zoom_display()

    def zoom_in(self):
        while self.lock:
            time.sleep(0.01)
        self.zoom_ratio = (
            self.zoom_ratio - 1.0 if self.zoom_ratio > 1 else self.zoom_ratio * 0.9
        )
        self.adapt_zoom()
        self.set_zoom_display()

    def change_center(self):
        self.draw_attractors.change_center()

    def update(self, *args):
        self.width, self.height = Window.size
        self.earth_diameter = self.zoom_ratio * default_earth_size / 2
        self.draw_attractors.set_window_size(self.width, self.height)
        self.x_center = self.width / 2 - self.earth_diameter
        self.y_center = self.height / 2 - self.earth_diameter

    def change_thrust(self, value):
        self.world.pilot.set_thrust(value)

    def change_time(self, value):
        if value < 10:
            self.world.time_controller.t_increment = value
        else:
            self.world.time_controller.t_increment = 5 * (1.2 ** value)

    def on_time_change(self):
        value = self.world.time_controller.t_increment
        self.set_time_slider(value)

    def set_time_slider(self, value):
        if value > 10:
            value = int(log(value / 5) / log(1.2))
        self.ids.time.value = value

    def center_orbit(self, x, y, force_earth_center=False, xearth=0, yearth=0):
        if not force_earth_center:
            x = (
                x * self.orbit_factor * self.zoom_ratio
                + self.x_center
                + self.earth_diameter
            )
            y = (
                y * self.orbit_factor * self.zoom_ratio
                + self.y_center
                + self.earth_diameter
            )
        else:
            x = x * self.orbit_factor * self.zoom_ratio + xearth
            y = y * self.orbit_factor * self.zoom_ratio + yearth

        return (x, y)

    def draw(self, dt):
        orbiters = self.world.orbiters
        current_orbiter = orbiters.get_current_orbiter()
        self.lock = True
        attractor_display_coordinates = self.draw_attractors.draw_attractor(
            self.zoom_ratio, current_orbiter
        )
        self.draw_trajectory.clear()

        for orbiter_name in orbiters.get_orbiters().keys():
            orbiter = orbiters.get_orbiter(orbiter_name)

            (x, y) = attractor_display_coordinates[orbiter.attractor.name]
            (x_orbiter, y_orbiter) = self.draw_attractors.get_ship_coordinates(
                orbiter, self.zoom_ratio
            )

            if current_orbiter != orbiter:
                self.draw_trajectory.draw_ship(x_orbiter, y_orbiter, None, orbiter_name)
                if (
                    self.goto.orbit_transfert != None
                    and orbiter.name == self.goto.orbit_transfert.target.name
                ):
                    orbit_values = orbiter.orbit_projection.orbit_values
                    self.draw_trajectory.draw_trajectory(
                        orbit_values, x, y, self.zoom_ratio, True
                    )
            else:

                orbit_values = orbiter.orbit_projection.orbit_values
                self.draw_trajectory.draw_trajectory(
                    orbit_values, x, y, self.zoom_ratio
                )
                if orbit_values and orbit_values.child != None:
                    (x2, y2) = attractor_display_coordinates[
                        orbit_values.child.attractor.name
                    ]
                    self.draw_trajectory.draw_trajectory(
                        orbit_values.child.orbit_values, x2, y2, self.zoom_ratio, True
                    )

                speed_indicator = (
                    orbiter.r.norm() - orbiter.attractor.radius
                ) < altitude_landing_help

                self.draw_trajectory.draw_velocity(
                    x_orbiter,
                    y_orbiter,
                    orbiter.r.norm() - orbiter.attractor.radius,
                    orbiter.v,
                    speed_indicator,
                )
                self.draw_trajectory.draw_ship(
                    x_orbiter, y_orbiter, orbiter.orientation1
                )

        if self.goto.orbit_transfert != None:
            dt = self.goto.orbit_transfert.get_dt(self.world.time_controller.t)
            dv = self.goto.orbit_transfert.get_delta_v(
                self.world.orbiters.get_current_orbiter().orbit
            )
            if dt == 0:
                dt = self.goto.orbit_transfert.get_time_to_reach(
                    self.world.time_controller.t
                )
                self.ids.goto_time.text = "Time to reach : " + str(int(dt))
            else:
                self.ids.goto_time.text = "dt : " + str(int(dt))
            self.ids.goto_deltav.text = "dV : " + str(int(dv))
            self.ids.goto_deltavtarget.text = "dv Target " + str(
                int(self.goto.orbit_transfert.get_current_delta_v())
            )
            self.ids.goto_distance.text = "distance " + str(
                int(self.goto.orbit_transfert.get_current_distance())
            )

        self.lock = False
