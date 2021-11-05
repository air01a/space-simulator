from numpy import (
    cos,
    sin,
    pi,
    tan,
    arccos,
    arctan,
    arcsin,
    cross,
    sinh,
    tanh,
    cosh,
    arctanh,
    arccos,
)
from vector import Vector
from orbit import Orbit


# Store all orbit cartesian values
class OrbitValues:
    def __init__(self, points, polar_points, perihelion, aphelion):
        self.points = points
        self.perihelion = perihelion
        self.aphelion = aphelion
        self.polar_points = polar_points
        self.child = None


# Use orbit object to calculate trajectories and intersection
class OrbitProjection:
    def __init__(self, attractor, orbit):
        self.attractor = attractor
        self.orbit = orbit
        self.cartesien = []
        self.orbit_values = None

    # Get r from angle
    def _get_polar_ellipse(self, angle):
        if self.orbit.e < 1:
            r = self.orbit.a * (1 - self.orbit.e ** 2) / (1 + self.orbit.e * cos(angle))
        elif self.orbit.e == 1:
            r = self.orbit.a / (1 + self.orbit.e * cos(angle))
        else:
            if 1 + self.orbit.e * cos(angle) != 0:
                r = (
                    self.orbit.a
                    * (1 - self.orbit.e ** 2)
                    / (1 + self.orbit.e * cos(angle))
                )
            else:
                r = (
                    self.orbit.a
                    * (1 - self.orbit.e ** 2)
                    / (1 + self.orbit.e * cos(angle + 0.0000001))
                )
        return r

    # Get angle from distance intersection
    def get_collision_angle(self, R):
        angle_collision1 = arccos(
            self.orbit.a * (1 - self.orbit.e ** 2) / (R * self.orbit.e)
            - 1 / self.orbit.e
        )
        return (angle_collision1, -angle_collision1)

    # Get time for an angle
    def get_collision_time(self, angle_collision, n):
        if angle_collision < 0:
            angle_collision = 2 * pi + angle_collision
        E = self.orbit.get_eccentric_from_true_anomaly(angle_collision)

        if self.orbit.e < 1:
            M = E - self.orbit.e * sin(E)
        else:
            M = self.orbit.e * sinh(E) - E
        t = abs((M - self.orbit.M0) / n)
        return t

    # Get cartesian coordonates for angle
    def get_position(self, angle):
        r = self._get_polar_ellipse(angle)
        return Vector(r * cos(angle), r * sin(angle), 0)

    # Manage child attractor intersection
    def intersect_child_attractor(self, attractor, r_att, v_att, r, v, t):
        orbit = Orbit()
        orbit.set_attractor(attractor)
        orbit.set_from_state_vector((r - r_att), (v - v_att), t)
        op = OrbitProjection(attractor, orbit)
        op.calculate_time_series(t, True, 50)
        return op

    # return ellipse points
    def calculate_time_series(self, current_t, recursive=False, points=200):
        series = []
        series_cartesien = []
        escape_soi = False
        child = None
        in_child_soi = False

        if self.orbit == None or self.orbit.a == 0:
            return (series, series_cartesien)
        angle = 0

        angle_max = 2 * pi
        n = (self.orbit.mu / (abs(self.orbit.a) ** 3)) ** 0.5
        # period = 2*pi*((abs(self.orbit.a)**3/self.orbit.mu)**0.5)

        # Calculate max and min
        perihelion, aphelion = self.orbit.get_limit()

        # Define min and max angle to draw
        if self.orbit.e == 1:
            angle = 0
            angle_max = pi / 3
        elif self.orbit.e > 1:
            angle = -arccos(-1 / self.orbit.e)
            angle_max = -angle - 0.00001

        # If we go outside the current attractor SOI
        # Calculate angle of exit and only draw points inside SOI
        if self.attractor.soi > 0 and (
            aphelion > self.attractor.soi or self.orbit.e >= 1
        ):
            (angle1, angle2) = self.get_collision_angle(self.attractor.soi)

            angle = min(angle1, angle2)
            angle_max = max(angle1, angle2)

            # Depth of only one SOI exit (would be infinite)
            if not recursive:
                parent = self.attractor.parent
                # If parent exists
                if parent != None:
                    # Get time of SOI exit
                    t = self.get_collision_time(angle_max, n)
                    # Calculate child attractor postion at SOI
                    (r_att, v_att) = self.attractor.orbit.update_position(t + current_t)
                    (r_att, v_att) = (-r_att, -v_att)
                    # Calculate ship position  at exit
                    (r, v) = self.orbit.update_position(t + current_t)
                    # Calculate trajectory
                    child = self.intersect_child_attractor(
                        parent, r_att, v_att, r, v, t + current_t
                    )

        # If we cross the attractor
        # Do not calculate point that are inside
        if perihelion < self.attractor.radius:
            (angle1, angle2) = self.get_collision_angle(self.attractor.radius)
            if self.orbit.e < 1:
                angle = max(angle1, angle2)
                angle_max = 2 * pi - angle
            else:
                angle_max = max(angle1, angle2)
            # angle_max = 2 * pi - angle

        increment = min((angle_max - angle) / points, pi / 200)
        # increment = (angle_max-angle) / points
        # Calculate points
        local_increment = increment

        while angle < (angle_max + local_increment) and not escape_soi:
            if angle > angle_max:
                angle = angle_max

            # Get distance for the angle
            r = self._get_polar_ellipse(angle)
            series.append((angle, r))

            # Populate cartesien coordonnates
            rv = self.orbit.get_eci(Vector(r * cos(angle), r * sin(angle), 0))

            # If we are inside the attractor SOI, calculate
            if (
                self.attractor == None
                or self.attractor.soi == 0
                or r <= self.attractor.soi
            ):
                if self.attractor.child == None or recursive:
                    if r < self.attractor.soi:
                        series_cartesien.append(rv)
                    if r < self.attractor.radius:
                        escape_soi = True
                else:
                    # Check if we cross a child attractor
                    in_child_soi = False
                    for att in self.attractor.child:
                        # by comparing distance
                        if (
                            rv.norm() > att.r.norm() - att.soi
                            and rv.norm() < att.r.norm() + att.soi
                        ):
                            in_child_soi = True
                            # Get time
                            t = self.get_collision_time(angle, n)
                            # Calculate child attractor position
                            (r_att, v_att) = att.orbit.update_position(t, False)
                            # Calculate distance
                            d = (r_att - rv).norm()
                            # Check for collision
                            if abs(d) < att.soi:
                                # Create child trajectory
                                escape_soi = True
                                (r, v) = self.orbit.update_position(t)
                                child = self.intersect_child_attractor(
                                    att, r_att, v_att, r, v, t
                                )

                    series_cartesien.append(rv)
            # else:
            #    escape_soi = True
            # More point when near the aphelion
            if in_child_soi:
                local_increment = increment / 20
            else:
                if self.orbit.e > 0.9 and self.orbit.e < 1 and self.orbit.a > 100000000:
                    if angle > pi / 2 and angle < 3 * pi / 2:
                        local_increment = increment / 4
                    else:
                        local_increment = increment * 4
                else:
                    local_increment = increment
            angle += local_increment

        # Transform coordonnates to ECI
        # series_cartesien = self.orbit.get_eci(series_cartesien)
        perihelion = self.orbit.get_eci(Vector(perihelion, 0, 0))

        if self.orbit.e < 1:
            if aphelion < self.attractor.soi:
                aphelion = Vector(-aphelion, 0, 0)
                aphelion = self.orbit.get_eci(aphelion)
            else:
                aphelion = None

        else:
            aphelion = None

        self.orbit_values = OrbitValues(series_cartesien, series, perihelion, aphelion)
        if child:
            self.orbit_values.child = child
