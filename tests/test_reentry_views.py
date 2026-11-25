"""Geometry of the rocket panel animations: plasma, parachutes, breakup"""
import unittest

from graphical import breakup, parachute, plasma
from graphical.rocket_layout import layout_rocket
from orbiter import Load_Orbiters

BBOX = (100.0, 200.0, 40.0, 120.0)  # x, y, w, h


def xs(points):
    return [p[0] for p in points]


def ys(points):
    return [p[1] for p in points]


class TestPlasma(unittest.TestCase):
    def test_invisible_below_50_kw(self):
        self.assertEqual(plasma.glow_color(49e3)[3], 0.0)
        self.assertEqual(plasma.glow_color(0.0)[3], 0.0)
        self.assertGreater(plasma.glow_color(60e3)[3], 0.0)

    def test_whiter_and_stronger_with_the_flux(self):
        low, high = plasma.glow_color(80e3), plasma.glow_color(2e6)
        self.assertGreater(high[2], low[2])  # Blue component: red -> white
        self.assertGreater(high[3], low[3])
        self.assertLessEqual(max(high), 1.0)

    def test_bow_under_the_base_and_wake_outside_the_body(self):
        shapes = plasma.glow_polygons(BBOX, 1e6, 0.3)
        x, y, w, h = BBOX
        self.assertLess(min(ys(shapes["bow"])), y)  # Bow shock under the base
        for wake in shapes["wakes"]:
            self.assertTrue(max(xs(wake)) <= x + 1e-6 or min(xs(wake)) >= x + w - 1e-6)
        self.assertEqual(len(shapes["wakes"]), 2)

    def test_bow_limited_to_the_room_under_the_base(self):
        shapes = plasma.glow_polygons(BBOX, 2e6, 0.0, max_depth=10)
        self.assertGreaterEqual(min(ys(shapes["bow"])), BBOX[1] - 10 - 1e-6)

    def test_bow_grows_with_the_flux(self):
        small = plasma.glow_polygons(BBOX, 1e5, 0.0)["bow"]
        big = plasma.glow_polygons(BBOX, 2e6, 0.0)["bow"]
        self.assertLess(min(ys(big)), min(ys(small)))


class TestParachute(unittest.TestCase):
    def test_count_and_place(self):
        domes, lines = parachute.canopies(200, 100, 20, 3, 1.0, 0.0, 150)
        self.assertEqual(len(domes), 3)
        self.assertEqual(len(lines), 6)  # Two suspension lines per canopy
        for dome in domes:
            self.assertGreater(min(ys(dome)), 100)  # Above the capsule
            self.assertLessEqual(max(ys(dome)), 100 + 150 + 1e-6)  # In the room

    def test_stay_within_the_given_width(self):
        # Panel 300 px wide, capsule centered at x = 200: canopies and lines in [50, 350]
        for t in (0.0, 1.0, 2.0, 3.0):
            domes, lines = parachute.canopies(200, 100, 20, 3, 1.0, t, 300, half_width=150)
            points = [p for d in domes for p in d] + [(l[2], l[3]) for l in lines]
            self.assertGreaterEqual(min(xs(points)), 50)
            self.assertLessEqual(max(xs(points)), 350)

    def test_opens(self):
        def span(progress):
            domes, _ = parachute.canopies(200, 100, 20, 3, progress, 0.0, 150)
            return max(max(xs(d)) for d in domes) - min(min(xs(d)) for d in domes)

        self.assertLess(span(0.1), span(0.5))
        self.assertLess(span(0.5), span(1.0))

    def test_sways_a_little(self):
        a = parachute.canopies(200, 100, 20, 1, 1.0, 0.0, 150)[0][0]
        b = parachute.canopies(200, 100, 20, 1, 1.0, 1.0, 150)[0][0]
        shift = abs(sum(xs(a)) / len(a) - sum(xs(b)) / len(b))
        self.assertGreater(shift, 0.0)
        self.assertLess(shift, 20)


class TestBreakup(unittest.TestCase):
    def setUp(self):
        rocket = Load_Orbiters.get_orbiter("rockets/saturne5.rocket")[1]
        self.layout = layout_rocket(rocket.stages.stages[2:4], 200, 300)

    def test_fragments_start_on_the_drawing(self):
        frags = breakup.make_fragments(self.layout, 10, 20, seed=1)
        self.assertGreater(len(frags), 4)
        self.assertLessEqual(len(frags), breakup.MAX_FRAGMENTS)
        for f in frags:
            self.assertTrue(10 - 1 <= f.cx <= 10 + 200 + 1)
            self.assertTrue(20 - 1 <= f.cy <= 20 + 300 + 1)

    def test_fly_apart_and_fade_out(self):
        frags = breakup.make_fragments(self.layout, 0, 0, seed=1)
        cx = sum(f.cx for f in frags) / len(frags)
        cy = sum(f.cy for f in frags) / len(frags)

        def spread(t):
            total = 0.0
            for f in frags:
                pts = breakup.fragment_polygon(f, t)
                mx, my = sum(xs(pts)) / 4, sum(ys(pts)) / 4
                total += ((mx - cx) ** 2 + (my - cy) ** 2) ** 0.5
            return total

        self.assertLess(spread(0.0), spread(1.0))
        self.assertGreater(breakup.fragment_color(frags[0], 0.2)[3], 0.5)
        self.assertEqual(breakup.fragment_color(frags[0], breakup.DURATION)[3], 0.0)

    def test_deterministic(self):
        a = breakup.make_fragments(self.layout, 0, 0, seed=3)
        b = breakup.make_fragments(self.layout, 0, 0, seed=3)
        self.assertEqual([(f.cx, f.vx) for f in a], [(f.cx, f.vx) for f in b])


if __name__ == "__main__":
    unittest.main()
