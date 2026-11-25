"""Apollo CSM split in two parts: SM (engine, fuel) and CM (heat shield, parachute)"""
import unittest

from attractor import Attractor
from graphical.rocket_layout import layout_rocket
from orbiter import Load_Orbiters, Orbiters
from vector import Vector


class Clock:
    t = 0


def load(name):
    return Load_Orbiters.get_orbiter("rockets/%s.rocket" % name)[1]


def in_orbit(orbiters, name, rocket):
    rocket.set_attractor(Attractor("earth", 6378140, 3.986004415e14))
    rocket.set_state(Vector(7000000, 0, 0), Vector(0, 7500, 0), 0)
    orbiters.add_orbiter(name, rocket)
    return rocket


def mass(rocket):
    return sum(p.empty_mass + p.carburant_mass for s in rocket.stages.stages for p in s.values())


class TestCsmSplit(unittest.TestCase):
    def test_files_split_csm_and_keep_masses(self):
        for name, total in (("saturne5", 30000), ("saturne5_moon", 14800)):
            rocket = load(name)
            stage = next(s for s in rocket.stages.stages if "cm" in s)
            self.assertEqual(list(stage), ["sm", "cm"])
            self.assertEqual(stage["sm"].empty_mass + stage["sm"].carburant_mass
                             + stage["cm"].empty_mass + stage["cm"].carburant_mass, total)
            self.assertTrue(stage["cm"].heat_shield)
            self.assertEqual(stage["cm"].parachute.count, 3)
            self.assertFalse(stage["sm"].heat_shield)
            self.assertIsNone(stage["sm"].parachute)
            self.assertEqual(stage["cm"].motor_flow, 0)

    def test_saturn_v_drawing_order(self):
        layout = layout_rocket(load("saturne5").stages.stages, 300, 450)
        y = {p.name: p.body[1] for p in layout.parts}
        order = ["s-ic", "s-ii", "s-ivb", "lem_descent", "lem_ascent", "sm", "cm"]
        for low, high in zip(order, order[1:]):
            self.assertLess(y[low], y[high], "%s < %s" % (low, high))
        self.assertEqual(len(layout.fairings), 1)

    def test_drop_csm_stage_gives_one_stacked_orbiter(self):
        orbiters = Orbiters(Clock())
        lem = in_orbit(orbiters, "LEM", load("saturne5_moon"))
        before = mass(lem)
        orbiters.separate_full_stage(lem)
        orbiters.apply_remove()
        csm = orbiters.get_orbiter("sm+cm")
        self.assertIsNotNone(csm)
        self.assertEqual([list(s) for s in csm.stages.stages], [["sm"], ["cm"]])
        self.assertEqual([list(s) for s in lem.stages.stages], [["lem_descent"], ["lem_ascent"]])
        self.assertAlmostEqual(mass(csm) + mass(lem), before)
        self.assertAlmostEqual(csm.stages.get_total_mass(), mass(csm))
        # Second drop: the CM flies alone
        orbiters.separate_full_stage(csm)
        orbiters.apply_remove()
        self.assertEqual([list(s) for s in csm.stages.stages], [["cm"]])
        self.assertIsNotNone(orbiters.get_orbiter("sm"))
        self.assertAlmostEqual(csm.stages.get_total_mass(), 5500)

    def test_lem_drawn_alone_after_csm_drop(self):
        orbiters = Orbiters(Clock())
        lem = in_orbit(orbiters, "LEM", load("saturne5_moon"))
        orbiters.separate_full_stage(lem)
        layout = layout_rocket(lem.stages.stages, 300, 450)
        y = {p.name: p.body[1] for p in layout.parts}
        self.assertEqual(min(y, key=y.get), "lem_descent")
        self.assertEqual(layout.fairings, [])

    def test_escape_tower_only_on_the_launcher(self):
        rocket = load("saturne5")
        cm = rocket.stages.stages[3]["cm"]
        full = {p.name: p for p in layout_rocket(rocket.stages.stages, 300, 450).parts}
        alone = layout_rocket([{"cm": cm}], 300, 450).parts[0]
        self.assertTrue(full["cm"].tower)
        self.assertFalse(alone.tower)
        # Without the tower, the capsule fills the box: height/width = capsule ratio
        self.assertAlmostEqual(alone.top[3] / alone.top[2], 0.85, places=3)


if __name__ == "__main__":
    unittest.main()
