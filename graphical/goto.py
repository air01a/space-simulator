from orbittransfert import OrbitTransfert
from kivy.uix.popup import Popup
from math import pi


class Goto(Popup):
    def __init__(self, **kwargs):
        super(Goto, self).__init__(**kwargs)
        self.select = 0
        self.display = []
        self.orbit_transfert = None

    def set_world(self, world):
        self.world = world

    def on_show(self):
        self.ids.goto_orbiter_control = self.display[self.select]

    def init(self):
        attractors = self.world.main_attractor
        current_orbiter = self.world.orbiters.get_current_orbiter()
        if current_orbiter.attractor.name != attractors.name:
            self.display.append(attractors.name)
        for att in attractors.child:
            if current_orbiter.attractor.name != att.name:
                self.display.append(att.name)
        for orb in self.world.orbiters.get_orbiters().values():
            if (
                orb.attractor.name == current_orbiter.attractor.name
                and orb.name != current_orbiter.name
            ):
                self.display.append(orb.name)

        self.ids.goto_orbiter_control.text = self.display[self.select]

    def on_goto_touch(self, direction):
        self.select += direction
        if self.select < 0:
            self.select = len(self.display) - 1
        if self.select > len(self.display) - 1:
            self.select = 0
        self.ids.goto_orbiter_control.text = self.display[self.select]

    def validate(self):
        chosen_orbit_name = self.display[self.select]
        chosen_orbit = None
        for attractor in self.world.attractors:
            if attractor.name == chosen_orbit_name:
                chosen_orbit = attractor
                break
        if chosen_orbit == None:
            for orb in self.world.orbiters.get_orbiters().values():
                if orb.name == chosen_orbit_name:
                    chosen_orbit = orb
                    break

        orbiter = self.world.orbiters.get_current_orbiter()
        self.orbit_transfert = OrbitTransfert(
            orbiter.name,
            orbiter,
            chosen_orbit,
            self.ids.hohmann,
        )
        self.orbit_transfert.calculate(self.world.time_controller.t)
        delta_t = self.orbit_transfert.get_dt(0)
        self.world.time_controller.set_timespeed_limiter(delta_t - 60, 0, delta_t - 58)
        self.dismiss()

    def cancel(self):
        self.orbit_transfert = None
        self.dismiss()
