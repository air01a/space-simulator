import os
import tempfile
import unittest

from equipment import Parachute, parse_equipment
from orbiter import Load_Orbiters, Stage_Composant, Stages


class TestParseEquipment(unittest.TestCase):
    def test_defaults(self):
        eq = parse_equipment(None)
        self.assertFalse(eq.heat_shield)
        self.assertIsNone(eq.parachute)

    def test_values(self):
        eq = parse_equipment({"heat_shield": "yes", "parachute": "25.4, 3, 3000, 200 ; Apollo"})
        self.assertTrue(eq.heat_shield)
        self.assertEqual(eq.parachute, Parachute(25.4, 3, 3000.0, 200.0))

    def test_invalid_keeps_default(self):
        eq = parse_equipment({"heat_shield": "maybe", "parachute": "25, -3, 3000, 200"})
        self.assertFalse(eq.heat_shield)
        self.assertIsNone(eq.parachute)
        self.assertIsNone(parse_equipment({"parachute": "25, 3, 3000"}).parachute)


class TestLoadEquipment(unittest.TestCase):
    def test_section_case_insensitive(self):
        text = (
            "[param]\nname = Test\n[stage1]\nBooster = 10,2000,100,100,1\n"
            "[stage2]\nCM = 0,0,500,0,1\n[Equipment.CM]\nheat_shield = yes\n"
            "parachute = 10, 1, 2000, 150\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".rocket", delete=False) as f:
            f.write(text)
        try:
            rocket = Load_Orbiters.get_orbiter(f.name)[1]
        finally:
            os.unlink(f.name)
        cm = rocket.stages.stages[1]["cm"]
        self.assertTrue(cm.heat_shield)
        self.assertEqual(cm.parachute.count, 1)
        self.assertFalse(rocket.stages.stages[0]["booster"].heat_shield)


class TestTanklessPart(unittest.TestCase):
    def test_part_without_tank_is_never_empty(self):
        # A capsule (no tank) in the burning stage must not be dropped by the
        # mission controller as an "empty" part
        stages = Stages()
        stages.add_stage()
        stages.add_part("sm", Stage_Composant(10, 3000, 100, 50))
        stages.add_part("cm", Stage_Composant(0, 0, 500, 0))
        stages.add_stage()
        stages.add_part("lem", Stage_Composant(10, 3000, 100, 50))
        stages.get_thrust(0.1)
        self.assertNotIn("cm", stages.empty_part)
        stages.get_thrust(10)  # sm tank emptied
        stages.get_thrust(0.1)  # seen empty on the next step
        self.assertIn("sm", stages.empty_part)
        self.assertNotIn("cm", stages.empty_part)


if __name__ == "__main__":
    unittest.main()
