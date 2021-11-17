from kivy.uix.widget import Widget
from kivy.graphics import *
from constants import altitude_speeding_help, max_speed_before_crash
from kivy.core.text import Label as CoreLabel
import numpy as np


class DrawTrajectory(Widget):
    def draw_soi(self, x, y, radius, color):
        (r, g, b, a) = color
        with self.canvas:
            Color(r, g, b, a)
            Line(circle=(x, y, radius), width=1)

    def set_ratio(self, ratio):
        self.ratio = ratio

    def clear(self):
        self.canvas.before.clear()
        self.canvas.clear()

    def scale(self, x, zoom_ratio):
        return x * self.ratio * zoom_ratio

    # Draw trajectory of orbiter
    def draw_trajectory(
        self, orbit_values, attractor_x, attractor_y, zoom_ratio, secondary=False
    ):
        color_elipse = (200, 200, 200)
        color_lines = (218, 238, 241)
        if not orbit_values or len(orbit_values.points) < 1:
            return

        max = orbit_values.aphelion
        min = orbit_values.perihelion
        (x2, y2, z2) = orbit_values.points[0]

        with self.canvas.before:
            if not secondary:
                Color(color_elipse)
                dashed = 0
            else:
                Color(0, 1, 1)
                dashed = 4

            x2 = self.scale(x2, zoom_ratio) + attractor_x
            y2 = self.scale(y2, zoom_ratio) + attractor_y

            for (x, y, z) in orbit_values.points[1:-1]:
                x = self.scale(x, zoom_ratio) + attractor_x
                y = self.scale(y, zoom_ratio) + attractor_y
                Line(points=[x, y, x2, y2], dash_offset=dashed)
                (x2, y2) = (x, y)

            if max != None and not secondary:
                Color(1, 0, 0, 0.3)
                x = self.scale(max.x, zoom_ratio) + attractor_x
                y = self.scale(max.y, zoom_ratio) + attractor_y

                Line(points=[attractor_x, attractor_y, x, y])

                x = self.scale(min.x, zoom_ratio) + attractor_x
                y = self.scale(min.y, zoom_ratio) + attractor_y
                Line(points=[attractor_x, attractor_y, x, y])

    def draw_velocity(self, x, y, r, v, speed_indicator):
        if speed_indicator and v.norm() < altitude_speeding_help:
            reductor = 5
        else:
            reductor = 125

        x2 = x + v.x / reductor
        y2 = y + v.y / reductor
        with self.canvas.before:
            Color(0, 0.5, 0)
            Line(points=[x, y, x2, y2], width=4)
            if speed_indicator:
                if v.norm() > max_speed_before_crash:
                    Color(1, 0, 0, 1)
                mylabel = CoreLabel(
                    text=str("alt: " + str(int(r)) + "\nv: " + str(round(v.norm()))),
                    font_size=self.police_size,
                    color=(1, 1, 1, 1),
                )
                mylabel.refresh()
                # Get the texture and the texture size
                texture = mylabel.texture
                texture_size = list(texture.size)
                # Draw the texture on any widget canvas
                Rectangle(
                    pos=(x + 5, y + 5),
                    texture=texture,
                    size=texture_size,
                )

    def draw_ship(self, orbiter_x, orbiter_y, orientation, orbiter_name=""):

        with self.canvas.before:
            if orientation != None:
                Color(0, 0, 1)
                head_x = 8 * np.cos(orientation)
                head_y = 8 * np.sin(orientation)

                Ellipse(size=(15, 15)).pos = (orbiter_x - 7.5, orbiter_y - 7.5)
                Color(1, 0, 0)

                Ellipse(size=(8, 8)).pos = (
                    orbiter_x + head_x - 3,
                    orbiter_y + head_y - 3,
                )

            else:
                Color(1, 1, 0)
                Ellipse(size=(5, 5)).pos = (orbiter_x - 2.5, orbiter_y - 2.5)
                mylabel = CoreLabel(
                    text=orbiter_name, font_size=self.police_size, color=(1, 1, 1, 1)
                )
                mylabel.refresh()
                # Get the texture and the texture size
                texture = mylabel.texture
                texture_size = list(texture.size)
                # Draw the texture on any widget canvas
                Rectangle(
                    pos=(orbiter_x + 5, orbiter_y + 5),
                    texture=texture,
                    size=texture_size,
                )
