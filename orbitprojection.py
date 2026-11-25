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
import numpy as np
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
        # Position of the attractor (relative to its parent) to draw this
        # trajectory from. None = current attractor position
        self.origin = None
        # (time, attractor) of the next SOI entry
        self.soi_entry = None
        # Position of the attractor (relative to its parent) when the orbiter
        # leaves its SOI: drawn as a "ghost" SOI, where the next trajectory starts
        self.exit_ghost = None


# Use orbit object to calculate trajectories and intersection
class OrbitProjection:
    def __init__(self, attractor, orbit):
        self.attractor = attractor
        self.orbit = orbit
        self.cartesien = []
        self.orbit_values = None
        # Time of a requested (not yet done) projection update
        self.pending_t = None

    # Ask for a projection update, done later by refresh() (called by the display).
    # The orbit can change at each physics step (engine on), but the trajectory is
    # only displayed a few times per second: no need to compute it at each step.
    def request_update(self, t):
        self.pending_t = t

    def refresh(self):
        if self.pending_t != None:
            self.calculate_time_series(self.pending_t)

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

    # Vectorized _get_polar_ellipse (numpy array of angles)
    def _get_polar_ellipse_array(self, angles):
        e = self.orbit.e
        p = self.orbit.a if e == 1 else self.orbit.a * (1 - e ** 2)
        denom = 1 + e * np.cos(angles)
        if e > 1:
            bad = denom == 0
            if bad.any():
                denom[bad] = 1 + e * np.cos(angles[bad] + 0.0000001)
        return p / denom

    # Get angle from distance intersection
    def get_collision_angle(self, R):
        angle_collision1 = arccos(
            self.orbit.a * (1 - self.orbit.e ** 2) / (R * self.orbit.e)
            - 1 / self.orbit.e
        )
        return (angle_collision1, -angle_collision1)

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

    # Find the first time in [t_start, t_end] where the orbiter enters the SOI
    # of the child attractor att.
    #
    # There is no closed-form solution (Kepler equation + moving attractor), so we
    # look for the first root of
    #     d(t) = |r_orbiter(t) - r_att(t)| - soi
    #
    # d cannot change faster than v_max (sum of the maximum speeds), so on an
    # interval [t1, t2] it stays above (d1 + d2 - v_max * (t2 - t1)) / 2.
    # Only intervals where this lower bound is <= 0 can contain an entry: they are
    # subdivided again (all at once, with numpy), until they are shorter than tol.
    # No entry can be missed, even a grazing one.
    def find_soi_entry(self, att, t_start, t_end, tol=1.0, samples=512, sub=64):
        if t_end <= t_start:
            return None
        # The search window ends before any crash: the orbiter stays above the
        # surface, so its speed is bounded by the speed at max(perihelion, radius).
        # (A radial trajectory has a perihelion ~0: unbounded speed, every interval
        # would be a candidate -> millions of samples, seconds per frame)
        v_max = self.get_max_speed(self.orbit, self.attractor.radius) + self.get_max_speed(
            att.orbit, att.radius
        )

        def distance_to_soi(ts):
            r = self.orbit.get_positions_at_times(ts.ravel())
            r_att = att.orbit.get_positions_at_times(ts.ravel())
            return (np.linalg.norm(r - r_att, axis=1) - att.soi).reshape(ts.shape)

        # Rows = intervals (in time order), columns = sample times inside
        ts = np.linspace(t_start, t_end, samples + 1)[np.newaxis, :]
        d = distance_to_soi(ts)
        if d[0, 0] <= 0:
            return None  # Already inside: SOI change handled by check_boundaries

        while True:
            # Flatten into elementary intervals [t1, t2], still in time order
            t1, t2 = ts[:, :-1].ravel(), ts[:, 1:].ravel()
            d1, d2 = d[:, :-1].ravel(), d[:, 1:].ravel()
            entered = d2 <= 0
            candidate = entered | ((d1 + d2 - v_max * (t2 - t1)) / 2 <= 0)
            # Nothing after the first interval where we are surely inside matters
            first_entry = np.argmax(entered) if entered.any() else len(entered)
            candidate[first_entry + 1 :] = False
            index = np.nonzero(candidate)[0]
            if len(index) == 0:
                return None
            if t2[0] - t1[0] <= tol:
                return t2[first_entry] if entered.any() else None
            # Subdivide the candidate intervals
            ts = np.linspace(t1[index], t2[index], sub + 1, axis=1)
            d = distance_to_soi(ts)

    # Maximum speed on an orbit (at perihelion)
    def get_max_speed(self, orbit, min_radius=0.0):
        r_min = max(abs(orbit.a * (1 - orbit.e)), min_radius)
        return (orbit.mu * (2 / r_min - 1 / orbit.a)) ** 0.5

    # return ellipse points
    def calculate_time_series(self, current_t, recursive=False, points=200):
        self.pending_t = None
        series = []
        series_cartesien = []
        child = None
        soi_entry = None
        exit_ghost = None
        t_exit = None
        crash_t = None

        if self.orbit == None or self.orbit.a == 0:
            return (series, series_cartesien)
        angle = 0

        angle_max = 2 * pi
        # Time window where the trajectory is valid (None = one period)
        t_limits = []

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

            dt_exit = self.orbit.time_to_true_anomaly(angle_max, current_t)
            if dt_exit > 0:
                t_limits.append(current_t + dt_exit)

            # Depth of only one SOI exit (would be infinite)
            if not recursive and self.attractor.parent != None and dt_exit > 0:
                t_exit = current_t + dt_exit

        # If we cross the attractor
        # Do not calculate point that are inside
        if perihelion < self.attractor.radius:
            (angle1, angle2) = self.get_collision_angle(self.attractor.radius)
            if self.orbit.e < 1:
                angle = max(angle1, angle2)
                angle_max = 2 * pi - angle
            else:
                angle_max = max(angle1, angle2)
            # Impact happens on the way down (negative true anomaly)
            dt_crash = self.orbit.time_to_true_anomaly(
                -max(angle1, angle2), current_t
            )
            if dt_crash > 0:
                crash_t = current_t + dt_crash
                t_limits.append(crash_t)

        # SOI exit (ex: from the moon to the earth), unless we crash before
        if t_exit != None and (crash_t == None or crash_t > t_exit):
            parent = self.attractor.parent
            # Attractor state relative to its parent at SOI exit
            (r_att, v_att) = self.attractor.orbit.get_state_at_time(t_exit)
            # Orbiter state at exit
            (r, v) = self.orbit.get_state_at_time(t_exit)
            # Trajectory in the parent frame (intersect substracts r_att)
            child = self.intersect_child_attractor(
                parent, -r_att, -v_att, r, v, t_exit
            )
            # The trajectory inside the SOI is drawn around the attractor (current
            # position), the one after exit around the parent: the attractor will
            # have moved, it is shown at its exit time position
            exit_ghost = r_att

        # Look for an encounter with a child attractor (ex: the moon)
        if not recursive and self.attractor.child:
            if t_limits:
                t_end = min(t_limits)
            else:
                t_end = current_t + self.orbit.get_period()
            for att in self.attractor.child:
                if att.soi <= 0 or att.orbit == None:
                    continue
                t_entry = self.find_soi_entry(att, current_t, t_end)
                if t_entry != None and (soi_entry == None or t_entry < soi_entry[0]):
                    soi_entry = (t_entry, att)

        if soi_entry:
            # Draw only from the orbiter to the SOI entry point
            (t_entry, att) = soi_entry
            angle = self.orbit.get_true_anomaly_at_time(current_t)
            angle_max = self.orbit.get_true_anomaly_at_time(t_entry)
            if angle_max < angle:
                angle_max += 2 * pi
            # Exact state at SOI entry, relative to the child attractor
            (r_att, v_att) = att.orbit.get_state_at_time(t_entry)
            (r, v) = self.orbit.get_state_at_time(t_entry)
            child = self.intersect_child_attractor(att, r_att, v_att, r, v, t_entry)
            # The encounter happens before any SOI exit
            exit_ghost = None
            # Child trajectory is relative to the attractor position AT ENTRY TIME
            # (not its current position), so both trajectories connect on screen
            child.orbit_values.origin = r_att
        elif recursive:
            # Trajectory after a SOI change: start exactly at the orbiter position
            # at current_t (the SOI crossing point), until exit/crash or one period
            angle = self.orbit.get_true_anomaly_at_time(current_t)
            if t_limits:
                angle_max = self.orbit.get_true_anomaly_at_time(min(t_limits))
            elif self.orbit.e < 1:
                angle_max = angle + 2 * pi
            if self.orbit.e < 1:
                while angle_max <= angle:
                    angle_max += 2 * pi

        increment = min((angle_max - angle) / points, pi / 200)

        # Angles to draw (plain float loop: cheap)
        angles = []
        high_e = self.orbit.e > 0.9 and self.orbit.e < 1 and self.orbit.a > 100000000
        while True:
            if angle > angle_max:
                angle = angle_max
            angles.append(angle)
            if angle == angle_max:
                break
            # More point when near the aphelion
            if high_e:
                if angle % (2 * pi) > pi / 2 and angle % (2 * pi) < 3 * pi / 2:
                    angle += increment / 4
                else:
                    angle += increment * 4
            else:
                angle += increment
        angles = np.array(angles)

        # Distances and coordinates of all points at once (numpy)
        r = self._get_polar_ellipse_array(angles)
        # Stop at the first point inside the attractor (included)
        inside = np.nonzero(r < self.attractor.radius)[0]
        if len(inside):
            angles = angles[: inside[0] + 1]
            r = r[: inside[0] + 1]
        series = list(zip(angles.tolist(), r.tolist()))
        # Only keep points inside the attractor SOI
        if self.attractor.soi != 0:
            keep = r <= self.attractor.soi * (1 + 1e-9)
            angles = angles[keep]
            r = r[keep]
        series_cartesien = self.orbit.get_eci_array(r * np.cos(angles), r * np.sin(angles))

        # Transform coordonnates to ECI
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
            if soi_entry:
                self.orbit_values.soi_entry = soi_entry
        self.orbit_values.exit_ghost = exit_ghost
