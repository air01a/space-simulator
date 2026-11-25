import configparser
import glob
import unittest

from graphical.rocket_layout import layout_rocket
from orbiter import Load_Orbiters

W, H = 300, 450


def load(name):
    return Load_Orbiters.get_orbiter("rockets/%s.rocket" % name)[1]


def heights(layout):
    return {p.name: p.body[1] for p in layout.parts}


class TestRocketFiles(unittest.TestCase):
    def test_all_parts_have_shapes(self):
        files = sorted(glob.glob("rockets/*.rocket"))
        self.assertEqual(len(files), 5)
        for path in files:
            config = configparser.ConfigParser()
            config.read(path)
            for section in config.sections():
                if section.startswith("stage"):
                    for part in config[section]:
                        self.assertIn("shape." + part, config, "%s: %s" % (path, part))

    def test_saturn_v_silhouette(self):
        layout = layout_rocket(load("saturne5").stages.stages, W, H)
        y = heights(layout)
        order = ["s-ic", "s-ii", "s-ivb", "lem_descent", "lem_ascent", "sm", "cm"]
        for low, high in zip(order, order[1:]):
            self.assertLess(y[low], y[high], "%s < %s" % (low, high))
        self.assertEqual(len(layout.fairings), 1)

    def test_ariane5_boosters(self):
        layout = layout_rocket(load("ariane5").stages.stages, W, H)
        p = {part.name: part for part in layout.parts}
        self.assertEqual(p["booster1"].shape.position, "side")
        self.assertEqual(p["booster2"].shape.position, "side")
        epc_x, _, epc_w, _ = p["epc"].body
        left, right = sorted([p["booster1"].body, p["booster2"].body], key=lambda b: b[0])
        self.assertLessEqual(left[0] + left[2], epc_x + 1e-6)
        self.assertGreaterEqual(right[0], epc_x + epc_w - 1e-6)

    def test_ariane5_payload_becomes_satellite_when_dropped(self):
        rocket = load("ariane5")
        payload = rocket.stages.stages[-1]["payload"]
        self.assertIsNotNone(payload.shape.satellite)
        attached = {p.name: p for p in layout_rocket(rocket.stages.stages, W, H).parts}
        self.assertEqual(attached["payload"].kind, "stage")
        alone = layout_rocket([{"payload": payload}], W, H)
        self.assertEqual(alone.parts[0].kind, "satellite")

    def test_m51_public_figures(self):
        rocket = load("m51")
        self.assertEqual(rocket.name, "M51.3")
        self.assertEqual(len(rocket.stages.stages), 4)  # 3 solid stages + payload
        parts = [p for stage in rocket.stages.stages for p in stage.values()]
        launch_mass = sum(p.empty_mass + p.carburant_mass for p in parts)
        self.assertAlmostEqual(launch_mass, 52000, delta=500)  # ~52 t (public)
        length = sum(p.shape.length for p in parts)
        self.assertAlmostEqual(length, 12.0, delta=0.2)  # ~12 m (public)
        for p in parts:
            self.assertAlmostEqual(p.shape.diameter, 2.3, delta=0.01)  # 2.3 m (public)

    def test_m51_ideal_delta_v_is_ballistic_not_orbital(self):
        from math import log
        rocket = load("m51")
        stages = [list(stage.values()) for stage in rocket.stages.stages]
        mass = sum(p.empty_mass + p.carburant_mass for s in stages for p in s)
        dv = 0.0
        for stage in stages[:3]:
            fuel = sum(p.carburant_mass for p in stage)
            dv += stage[0].motor_speed * log(mass / (mass - fuel))
            mass -= sum(p.empty_mass + p.carburant_mass for p in stage)
        # Intercontinental ballistic range needs ~6-7.5 km/s; low orbit ~9.3 km/s with losses
        self.assertGreater(dv, 6500)
        self.assertLess(dv, 8500)

    def test_moon_lem_after_csm_drop(self):
        lem = load("saturne5_moon")
        lem.stages.sep_part("sm")
        lem.stages.sep_part("cm")
        layout = layout_rocket(lem.stages.stages, W, H)
        y = heights(layout)
        self.assertEqual(min(y, key=y.get), "lem_descent")
        self.assertEqual(layout.fairings, [])


if __name__ == "__main__":
    unittest.main()
