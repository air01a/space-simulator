import os
import tempfile
import unittest

from attractor import Attractor
from orbiter import Load_Orbiters, Orbiters
from rocketshape import PartShape, parse_color, parse_shape
from vector import Vector


ROCKET = """[param]
name = T

[stage1]
epc=270,4200,12300,220000,18
"""

TWO_STAGES = """[param]
name = T2

[stage1]
booster1=1800,2800,38000,237000,15
epc=270,4200,12300,220000,18

[stage2]
eps=17,6000,2100,13000,0

[shape.booster1]
length = 31
position = side
"""


class Clock:
    t = 0.0


def load(text):
    with tempfile.NamedTemporaryFile("w", suffix=".rocket", delete=False) as f:
        f.write(text)
    try:
        return Load_Orbiters.get_orbiter(f.name)[1]
    finally:
        os.unlink(f.name)


class TestParseShape(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(
            parse_shape(None, False),
            PartShape(10, 3, "none", 1, parse_color("#d0d0d0"), None, "center", None, False),
        )

    def test_payload_defaults(self):
        shape = parse_shape(None, True)
        self.assertEqual(shape.top, "fairing")
        self.assertEqual(shape.nozzles, 0)

    def test_parse_values(self):
        shape = parse_shape(
            {
                "length": "30.5",
                "diameter": "5.4",
                "top": "ogive",
                "nozzles": "5",
                "color": "#ffffff",
                "band": "#000000",
                "position": "side",
                "draw_below": "csm",
                "enclosed": "true",
            },
            False,
        )
        self.assertEqual(shape.length, 30.5)
        self.assertEqual(shape.diameter, 5.4)
        self.assertEqual(shape.top, "ogive")
        self.assertEqual(shape.nozzles, 5)
        self.assertEqual(shape.color, (1.0, 1.0, 1.0))
        self.assertEqual(shape.band, (0.0, 0.0, 0.0))
        self.assertEqual(shape.position, "side")
        self.assertEqual(shape.draw_below, "csm")
        self.assertIs(shape.enclosed, True)

    def test_invalid_values_fall_back(self):
        shape = parse_shape(
            {"top": "banane", "length": "abc", "color": "blanc", "position": "dessus", "nozzles": "-2"},
            False,
        )
        default = parse_shape(None, False)
        self.assertEqual(shape.top, "none")
        self.assertEqual(shape.length, 10)
        self.assertEqual(shape.color, default.color)
        self.assertEqual(shape.position, "center")
        self.assertEqual(shape.nozzles, 1)


class TestSatelliteShape(unittest.TestCase):
    def test_satellite_parsed(self):
        self.assertEqual(parse_shape({"satellite": "4.5, 2.5, 30"}, True).satellite, (4.5, 2.5, 30.0))

    def test_no_satellite_by_default(self):
        self.assertIsNone(parse_shape(None, True).satellite)

    def test_invalid_satellite_falls_back(self):
        for value in ("4.5, 2.5", "a, b, c", "4.5, -2, 30", "4.5, 2.5, 1"):
            self.assertIsNone(parse_shape({"satellite": value}, True).satellite, value)


class TestParseComments(unittest.TestCase):
    def test_inline_comments_are_ignored(self):
        shape = parse_shape(
            {"length": "30.5        ; longueur (m)", "color": "#f0f0f0      ; couleur", "draw_below": "csm     ; cible"},
            False,
        )
        self.assertEqual(shape.length, 30.5)
        self.assertEqual(shape.color, parse_color("#f0f0f0"))
        self.assertEqual(shape.draw_below, "csm")


class TestLoadShapes(unittest.TestCase):
    def test_shape_section_name_is_case_insensitive(self):
        orbiter = load(ROCKET.replace("epc=", "EPC=") + "\n[shape.EPC]\nlength = 30.5\n")
        self.assertEqual(orbiter.stages.stages[0]["epc"].shape.length, 30.5)

    def test_separate_empty_part(self):
        earth = Attractor("earth", 6378140, 3.986004415e14)
        orbiters = Orbiters(Clock())
        rocket = load(TWO_STAGES)
        rocket.set_attractor(earth)
        rocket.set_state(Vector(7000000, 0, 0), Vector(0, 7500, 0), 0)
        orbiters.add_orbiter("T2", rocket)
        rocket.stages.stages[0]["booster1"].carburant_mass = 0
        rocket.stages.get_thrust(0.1)
        self.assertIn("booster1", rocket.stages.empty_part)
        orbiters.separate_full_stage(rocket)
        self.assertEqual(list(rocket.stages.stages[0]), ["eps"])

    def test_loaded_rocket_has_shapes(self):
        orbiter = load(ROCKET + "\n[shape.epc]\nlength = 30.5\n")
        part = orbiter.stages.stages[0]["epc"]
        self.assertEqual(part.shape.length, 30.5)
        self.assertEqual(part.initial_carburant_mass, 220000)

    def test_rocket_without_shapes_still_loads(self):
        orbiter = load(ROCKET)
        self.assertEqual(orbiter.stages.stages[0]["epc"].shape, parse_shape(None, False))

    def test_shape_follows_part(self):
        earth = Attractor("earth", 6378140, 3.986004415e14)
        orbiters = Orbiters(Clock())
        rocket = load(TWO_STAGES)
        rocket.set_attractor(earth)
        rocket.set_state(Vector(7000000, 0, 0), Vector(0, 7500, 0), 0)
        orbiters.add_orbiter("T2", rocket)
        shape = rocket.stages.stages[0]["booster1"].shape
        orbiters.separate_stage(rocket, "booster1")
        self.assertIs(orbiters.get_orbiter("booster1").stages.stages[0]["booster1"].shape, shape)
        self.assertEqual(shape.position, "side")

        other = load(ROCKET)
        other.set_attractor(earth)
        other.set_state(Vector(7000000, 0, 0), Vector(0, 7500, 0), 0)
        orbiters.add_orbiter("T", other)
        epc_shape = other.stages.stages[0]["epc"].shape
        orbiters.dock("T2", "T")
        self.assertIs(rocket.stages.stages[-1]["epc"].shape, epc_shape)


if __name__ == "__main__":
    unittest.main()
