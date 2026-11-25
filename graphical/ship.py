from kivy.uix.widget import Widget
from kivy.graphics import *
from constants import altitude_speeding_help, max_speed_before_crash
from kivy.core.text import Label as CoreLabel
import numpy as np


GHOST_COLOR = (0, 1, 1)


class DrawTrajectory(Widget):
    def set_ratio(self, ratio):
        self.ratio = ratio

    def clear(self):
        self.canvas.before.clear()
        self.canvas.clear()

    def scale(self, x, zoom_ratio):
        return x * self.ratio * zoom_ratio

    # "Ghost" of an attractor at a predicted position (ex: moon at encounter):
    # its SOI (light veil + dashed circle), the attractor picture (with a minimum
    # size to stay visible when zoomed out) and a label (name + delay)
    def draw_ghost(self, x, y, attractor, zoom_ratio, label=None):
        soi_r = self.scale(attractor.soi, zoom_ratio)
        body_r = max(self.scale(attractor.radius, zoom_ratio), attractor.min_size, 5)
        with self.canvas.before:
            Color(*GHOST_COLOR, 0.10)
            Ellipse(pos=(x - soi_r, y - soi_r), size=(2 * soi_r, 2 * soi_r))
            Color(*GHOST_COLOR, 0.9)
            Line(circle=(x, y, soi_r), width=1, dash_length=6, dash_offset=4)
            Color(1, 1, 1, 0.6)
            Ellipse(
                pos=(x - body_r, y - body_r),
                size=(2 * body_r, 2 * body_r),
                source=attractor.picture,
            )
            if label:
                texture = self.ghost_label_texture(label)
                Color(*GHOST_COLOR, 1)
                Rectangle(
                    texture=texture,
                    pos=(x + max(soi_r, body_r) + 4, y - texture.height / 2),
                    size=texture.size,
                )

    def ghost_label_texture(self, text):
        size = int(getattr(self, "police_size", 18) * 0.8)
        cache = self.__dict__.setdefault("_ghost_labels", {})
        if (text, size) not in cache:
            if len(cache) > 50:
                cache.clear()
            label = CoreLabel(text=text, font_size=size)
            label.refresh()
            cache[(text, size)] = label.texture
        return cache[(text, size)]

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
        k = self.ratio * zoom_ratio

        with self.canvas.before:
            if not secondary:
                Color(color_elipse)
                dashed = 0
            else:
                Color(0, 1, 1)
                dashed = 4

            # A single Line for the whole trajectory (one instruction instead of
            # one per segment: much cheaper to build and to render)
            pts = orbit_values.points[:, :2] * k + (attractor_x, attractor_y)
            Line(points=pts.ravel().tolist(), dash_offset=dashed)

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
