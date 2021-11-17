from kivy.uix.widget import Widget
from kivy.graphics import *
from constants import altitude_speeding_help, max_speed_before_crash
from kivy.core.text import Label as CoreLabel
from constants import default_earth_size
from kivy.core.window import Window


class DrawAttractor(Widget):
    def setAttractor(self, attractor, rec=False):
        if not rec:
            self.attractor = []
            self.attractor_name = {}
        with self.canvas.before:
            Color(1, 1, 1, 1)
            ptr = Rectangle(source=attractor.picture)
            if attractor.atmosphere_limit != 0:
                (r, g, b, a) = attractor.atmosphere_color
                Color(r, g, b, a)
                atm_ptr = Ellipse()
            else:
                atm_ptr = None

        self.attractor.append(
            {
                "name": attractor.name,
                "size": attractor.radius,
                "atmosphere": attractor.atmosphere_limit,
                "atmosphere_color": attractor.atmosphere_color,
                "image": attractor.picture,
                "ptr": ptr,
                "atm_ptr": atm_ptr,
                "soi": attractor.soi,
                "obj": attractor,
            }
        )
        self.attractor_name[attractor.name] = self.attractor[-1]
        for att in attractor.child:
            self.setAttractor(att, True)

    def init(self, attractor, ratio):
        # 0 : center on ship, 1: center on current orbiter's attractor
        self.view_center = 0
        self.ratio = ratio
        self.setAttractor(attractor)
        self.size_x, self.size_y = Window.size
        self.size_x = self.size_x / 2
        self.size_y = self.size_y / 2
        self.attractor_display_coordinates = {}

    def scale(self, x, zoom_ratio):
        return x * self.ratio * zoom_ratio

    def get_ship_coordinates(self, orbiter, zoom_ratio):
        (x, y) = self.attractor_display_coordinates[orbiter.attractor.name]
        x += self.scale(orbiter.r.x, zoom_ratio)
        y += self.scale(orbiter.r.y, zoom_ratio)
        return (x, y)

    def draw_orbit(self, attractor, zoom_ratio):
        if not attractor.parent:
            return
        (center_x, center_y) = self.attractor_display_coordinates[attractor.parent.name]
        orbit_values = attractor.orbit_projection.orbit_values

        (x2, y2, z2) = orbit_values.points[0]
        x2 = self.scale(x2, zoom_ratio) + center_x
        y2 = self.scale(y2, zoom_ratio) + center_y
        for (x, y, z) in orbit_values.points[1:-1]:
            x = self.ratio * zoom_ratio * x + center_x
            y = self.ratio * zoom_ratio * y + center_y
            with self.canvas.after:
                Color(0.32, 0.54, 0.71, 1)
                Line(points=[x, y, x2, y2], width=0.5)
                (x2, y2) = (x, y)

    def draw_attractor(self, zoom_ratio, current_orbiter):
        self.canvas.after.clear()
        self.attractor_display_coordinates = {}
        if self.view_center == 0:
            center_x = current_orbiter.r.x + current_orbiter.attractor.r.x
            center_y = current_orbiter.r.y + current_orbiter.attractor.r.y
        else:
            center_x = current_orbiter.attractor.r.x
            center_y = current_orbiter.attractor.r.y
        for att in self.attractor:
            self.draw_orbit(att["obj"], zoom_ratio)
            r = att["size"] * zoom_ratio * self.ratio
            x = (att["obj"].r.x - center_x) * zoom_ratio * self.ratio + self.size_x
            y = (att["obj"].r.y - center_y) * zoom_ratio * self.ratio + self.size_y

            self.attractor_display_coordinates[att["name"]] = (x, y)
            x -= r
            y -= r

            if att["atm_ptr"] != None:
                r2 = (att["size"] + att["atmosphere"]) * zoom_ratio * self.ratio
                att["atm_ptr"].size = (2 * r2, 2 * r2)
                att["atm_ptr"].pos = (x + r - r2, y + r - r2)

            if att["soi"] != 0:
                r2 = (att["soi"]) * zoom_ratio * self.ratio
                with self.canvas.after:
                    Color(0.80, 0.36, 0.36, 1)
                    Line(circle=(x + r, y + r, r2), width=1)

            att["ptr"].pos = (x, y)
            att["ptr"].size = (2 * r, 2 * r)
        return self.attractor_display_coordinates

    def set_window_size(self, width, height):
        self.size_x = width / 2
        self.size_y = height / 2

    def change_center(self):
        self.view_center = 1 - self.view_center
