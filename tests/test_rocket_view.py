import os
import unittest

os.environ.setdefault("KIVY_NO_ARGS", "1")

from graphical.rocket import burning_nozzles, stack_labels, state_key
from graphical.rocket_layout import layout_rocket
from orbiter import Load_Orbiters


def ariane():
    return Load_Orbiters.get_orbiter("rockets/ariane5.rocket")[1]


class TestStateKey(unittest.TestCase):
    def test_key_stable_when_nothing_changes(self):
        rocket = ariane()
        self.assertEqual(state_key(rocket, (200, 300)), state_key(rocket, (200, 300)))

    def test_key_changes_on_fuel_percent_sep_and_engine(self):
        rocket = ariane()
        key = state_key(rocket, (200, 300))
        epc = rocket.stages.stages[0]["epc"]
        epc.carburant_mass = epc.initial_carburant_mass * 0.99
        fuel_key = state_key(rocket, (200, 300))
        self.assertNotEqual(key, fuel_key)
        rocket.stages.sep_part("booster1")
        sep_key = state_key(rocket, (200, 300))
        self.assertNotEqual(fuel_key, sep_key)
        rocket.engine_on = True
        self.assertNotEqual(sep_key, state_key(rocket, (200, 300)))
        self.assertNotEqual(state_key(rocket, (200, 300)), state_key(rocket, (201, 300)))

    def test_key_changes_when_the_parachute_opens(self):
        # The rocket is drawn smaller to leave room for the canopies
        rocket = ariane()
        key = state_key(rocket, (200, 300))
        rocket.parachute_deployed = True
        self.assertNotEqual(key, state_key(rocket, (200, 300)))

    def test_key_changes_on_position(self):
        rocket = ariane()
        self.assertNotEqual(state_key(rocket, (200, 300), (0, 0)), state_key(rocket, (200, 300), (500, 0)))

    def test_active_labels_do_not_overlap(self):
        rocket = ariane()
        layout = layout_rocket(rocket.stages.stages, 300, 450, engine_on=True)
        centers = [p.body[1] + p.body[3] / 2 for p in layout.parts if p.state == "active"]
        self.assertEqual(len(centers), 3)
        ys = stack_labels(centers, 19)
        self.assertEqual(len(ys), 3)
        ys = sorted(ys)
        for low, high in zip(ys, ys[1:]):
            self.assertGreaterEqual(high - low, 19 - 1e-9)

    def test_burning_nozzles_follow_engine_and_throttle(self):
        rocket = ariane()
        layout = layout_rocket(rocket.stages.stages, 300, 450, engine_on=False)
        self.assertEqual(burning_nozzles(layout, rocket, 0, 0), [])
        rocket.engine_on = True
        rocket.stages.set_thrust("ALL", 0.5)
        layout = layout_rocket(rocket.stages.stages, 300, 450, engine_on=True)
        nozzles = burning_nozzles(layout, rocket, 10, 20)
        self.assertEqual(len(nozzles), 3)  # booster1, booster2, epc: 1 nozzle each
        for (x, y, w, h), throttle in nozzles:
            self.assertEqual(throttle, 0.5)
        epc = [p for p in layout.parts if p.name == "epc"][0]
        ex, ey, ew, eh = epc.nozzles[0]
        self.assertIn(((ex + 10, ey + 20, ew, eh), 0.5), nozzles)

    def test_key_none_orbiter(self):
        self.assertEqual(state_key(None, (200, 300)), state_key(None, (200, 300)))


if __name__ == "__main__":
    unittest.main()
