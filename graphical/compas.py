from kivy.uix.widget import Widget
from kivy.graphics import *
from constants import altitude_speeding_help, max_speed_before_crash
from kivy.core.text import Label as CoreLabel
import numpy as np
from kivy.uix.button import Button
from math import degrees, atan2, pi
from kivy.core.window import Window


class Compas(Button):
    def init(self, spacetime):
        self.prev_angle = 180
        self.orbiters = spacetime.orbiters
        self.angle = 180
        self.tmp = 180

    def on_touch_down(self, touch):
        # self.size=(200,200)
        if self.collide_point(*touch.pos):
            y = touch.y - self.center[1]
            x = touch.x - self.center[0]
            calc = 0.5 * degrees(atan2(y, x))
            self.prev_angle = calc if calc > 0 else 360 + calc
            self.tmp = self.angle

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            y = touch.y - self.center[1]
            x = touch.x - self.center[0]
            calc = 0.5 * degrees(atan2(y, x))
            new_angle = calc if calc > 0 else 360 + calc

            self.angle = (self.tmp + (new_angle - self.prev_angle)) % 360
            self.orbiters.get_current_orbiter().change_orientation(
                (self.angle * 2 * pi / 180 + pi / 2) % (2 * pi), 0
            )
            self.draw()

    def on_touch_up(self, touch):
        # Animation(angle=0).start(self)
        self.draw()

    def draw(self):
        with self.canvas.before:
            PushMatrix()
            Rotate(origin=(120, Window.height - 60), angle=-self.angle - 90)
            PopMatrix()

    def repos(self):
        self.canvas.clear()
        self.draw()
