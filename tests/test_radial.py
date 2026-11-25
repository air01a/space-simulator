"""Vertical launch = radial trajectory (angular momentum ~0, e ~ 1).
Regression: the trajectory was not drawn and the SOI search froze the game."""
import multiprocessing
import unittest
from math import pi

import numpy as np

EARTH_MU = 3.986004415e14
R = 6378140


def radial_orbit(vx=1e-10, alt=6100, vy=600):
    from orbit import Orbit
    from vector import Vector
    o = Orbit(EARTH_MU)
    o.set_from_state_vector(Vector(0, R + alt, 0), Vector(vx, vy, 0), 0)
    return o


def _project(queue):
    from attractor import Attractor
    from orbitprojection import OrbitProjection
    earth = Attractor("earth", R, EARTH_MU, soi=925000000)
    moon = Attractor("moon", 1737400, 4904042755112.52, soi=66100000)
    moon.parent = earth
    moon.set_orbit_parameters(earth.mu, 384000000, 0, pi, pi, 0, 3.80213448739820994)
    earth.child = [moon]
    results = []
    for vx in (0.0, 1e-12, 1e-10, -1e-10, 1e-6):
        op = OrbitProjection(earth, radial_orbit(vx=vx))
        op.calculate_time_series(0)
        pts = np.asarray(op.orbit_values.points)
        results.append((vx, len(pts), float(np.nanmax(np.linalg.norm(pts, axis=1))) if len(pts) else 0.0))
    queue.put(results)


def _project_fast(queue):
    """Vertical shot up to the moon distance: long SOI search window"""
    from attractor import Attractor
    from orbitprojection import OrbitProjection
    earth = Attractor("earth", R, EARTH_MU, soi=925000000)
    moon = Attractor("moon", 1737400, 4904042755112.52, soi=66100000)
    moon.parent = earth
    moon.set_orbit_parameters(earth.mu, 384000000, 0, pi, pi, 0, 3.80213448739820994)
    earth.child = [moon]
    op = OrbitProjection(earth, radial_orbit(vx=1e-10, alt=100000, vy=10900))
    op.calculate_time_series(0)
    pts = np.asarray(op.orbit_values.points)
    queue.put((len(pts), float(np.max(np.linalg.norm(pts, axis=1)))))


class TestRadialTrajectory(unittest.TestCase):
    def test_fast_vertical_shot_projection_is_fast(self):
        import time
        from attractor import Attractor
        from orbitprojection import OrbitProjection
        earth = Attractor("earth", R, EARTH_MU, soi=925000000)
        moon = Attractor("moon", 1737400, 4904042755112.52, soi=66100000)
        moon.parent = earth
        moon.set_orbit_parameters(earth.mu, 384000000, 0, pi, pi, 0, 3.80213448739820994)
        earth.child = [moon]
        op = OrbitProjection(earth, radial_orbit(vx=1e-10, alt=100000, vy=10900))
        start = time.perf_counter()
        op.calculate_time_series(0)
        self.assertLess(time.perf_counter() - start, 0.1)  # recomputed at each frame

    def test_fast_vertical_shot_does_not_freeze(self):
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_project_fast, args=(queue,))
        process.start()
        process.join(20)
        if process.is_alive():
            process.kill()
            self.fail("calculate_time_series froze on a fast radial trajectory (> 20 s)")
        n, r_max = queue.get(timeout=5)
        self.assertGreaterEqual(n, 2)
        self.assertGreater(r_max, 1e8)  # climbs beyond 100 000 km


    def test_bound_radial_orbit_is_elliptic(self):
        for vx in (0.0, 1e-12, 1e-10, -1e-10):
            o = radial_orbit(vx=vx)
            self.assertGreater(o.a, 0, vx)
            self.assertLess(o.e, 1, vx)  # energy < 0: ellipse, even when e rounds to 1 + eps

    def test_radial_positions_are_finite(self):
        o = radial_orbit()
        ts = np.linspace(0, 100, 11)
        self.assertTrue(np.all(np.isfinite(o.get_positions_at_times(ts))))
        self.assertTrue(all(np.isfinite(float(c)) for c in o.get_position_at_time(50)))

    def test_projection_of_vertical_climb_draws_and_does_not_freeze(self):
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_project, args=(queue,))
        process.start()
        process.join(20)
        if process.is_alive():
            process.kill()
            self.fail("calculate_time_series froze on a radial trajectory (> 20 s)")
        apogee = R + 6100 + 600 ** 2 / (2 * 9.8)  # ~ +18 km above the current point
        for vx, n, r_max in queue.get(timeout=5):
            self.assertGreaterEqual(n, 2, "vx=%r: no trajectory points" % vx)
            self.assertAlmostEqual(r_max, apogee, delta=2000, msg="vx=%r" % vx)


if __name__ == "__main__":
    unittest.main()
