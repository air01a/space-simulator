import unittest

from graphical.flames import flame_polygons

NOZZLE = (100.0, 50.0, 10.0, 4.0)  # x, y, w, h (px), y = bottom of the nozzle


def ys(points):
    return [p[1] for p in points]


def xs(points):
    return [p[0] for p in points]


class TestFlames(unittest.TestCase):
    def test_flame_starts_at_nozzle_exit_and_goes_down(self):
        outer, inner = flame_polygons(NOZZLE, throttle=1.0, t=0.0, max_length=100)
        self.assertAlmostEqual(max(ys(outer)), 50.0)
        self.assertLess(min(ys(outer)), 50.0)
        self.assertAlmostEqual(max(ys(inner)), 50.0)
        self.assertGreater(min(ys(inner)), min(ys(outer)))  # core shorter than the flame

    def test_plume_leaves_the_nozzle_and_widens(self):
        outer, inner = flame_polygons(NOZZLE, 1.0, 0.0, 100)
        exit_xs = sorted(x for x, y in outer if y == 50.0)
        self.assertEqual(exit_xs, [100.0, 110.0])  # same width as the nozzle at its exit
        self.assertLess(min(xs(outer)), 100.0)  # then wider (plume)
        self.assertGreater(max(xs(outer)), 110.0)
        self.assertLessEqual(max(xs(outer)) - min(xs(outer)), 1.6 * 10 + 1e-9)
        self.assertGreater(min(xs(inner)), min(xs(outer)))
        self.assertLess(max(xs(inner)), max(xs(outer)))

    def length(self, throttle, t, max_length=1000):
        outer, _ = flame_polygons(NOZZLE, throttle, t, max_length)
        return 50.0 - min(ys(outer)) if outer else 0.0

    def test_length_follows_throttle(self):
        for t in (0.0, 0.37, 1.9):
            self.assertAlmostEqual(self.length(0.5, t), self.length(1.0, t) / 2)

    def test_flicker_changes_with_time_within_20_percent(self):
        lengths = [self.length(1.0, k / 60) for k in range(120)]
        self.assertGreater(max(lengths) - min(lengths), 0)
        base = 7.0 * NOZZLE[2]
        for value in lengths:
            self.assertGreaterEqual(value, base * 0.8 - 1e-9)
            self.assertLessEqual(value, base * 1.2 + 1e-9)

    def test_no_flame_without_throttle(self):
        self.assertEqual(flame_polygons(NOZZLE, 0.0, 0.0, 100), ([], []))

    def test_length_clamped_to_available_room(self):
        self.assertLessEqual(self.length(1.0, 0.0, max_length=7), 7 + 1e-9)

    def test_clamped_flame_still_flickers(self):
        lengths = [self.length(1.0, k / 60, max_length=20) for k in range(120)]
        self.assertTrue(all(v <= 20 + 1e-9 for v in lengths))
        self.assertGreater(max(lengths) - min(lengths), 1.0)


if __name__ == "__main__":
    unittest.main()
