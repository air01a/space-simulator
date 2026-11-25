"""Information bar (speed, altitude, fuel...): shown with or without a mission"""
import os
import unittest

os.environ.setdefault("KIVY_NO_ARGS", "1")

from spacetime import SpaceTime


class TestInfoBar(unittest.TestCase):
    def test_info_without_mission(self):
        st = SpaceTime("scenario/m51.scn")
        self.assertIsNone(st.controller)
        info = st.get_info()
        for word in ("altitude", "velocity", "carburant"):
            self.assertIn(word, info)
        self.assertIn("kg", info)

    def test_info_with_mission_unchanged(self):
        st = SpaceTime("scenario/ariane5.scn")
        self.assertEqual(st.get_info(), st.controller.get_info())

    def test_no_orbiter(self):
        st = SpaceTime("scenario/m51.scn")
        st.orbiters.remove(st.orbiters.get_current_orbiter_name())
        st.orbiters.apply_remove()
        self.assertEqual(st.get_info(), "No Orbiter found")


if __name__ == "__main__":
    unittest.main()


class TestDistanceRangeHeat(unittest.TestCase):
    def setUp(self):
        from math import sqrt
        from attractor import Attractor
        from orbiter import Load_Orbiters, Orbiters
        from vector import Vector
        from tests.test_reentry import TC, earth
        self.Vector = Vector
        self.att = earth()
        self.rocket = Load_Orbiters.get_orbiter("rockets/m51.rocket")[1]
        self.rocket.set_attractor(self.att)
        r = 6378140 + 300e3
        self.v0 = sqrt(self.att.mu / r)
        self.rocket.set_state(Vector(r, 0.0, 0.0), Vector(0.0, self.v0, 0.0), 0)
        self.tc = TC()

    def fly(self, seconds, frame=1.0):
        while self.tc.t < seconds:
            self.tc.t += frame
            self.rocket.update_position(self.tc, frame)

    def test_distance_is_the_path_length(self):
        self.fly(100)
        self.assertAlmostEqual(self.rocket.distance, self.v0 * 100, delta=self.v0 * 100 * 0.01)

    def test_ground_range_from_the_start_point(self):
        self.fly(100)
        # Circular orbit at 300 km: ground track = path x R / r
        expected = self.v0 * 100 * 6378140 / (6378140 + 300e3)
        self.assertAlmostEqual(self.rocket.ground_range(), expected, delta=expected * 0.01)

    def test_separated_stage_keeps_the_counters(self):
        from orbiter import Orbiters

        class Clock:
            t = 100.0

        self.fly(100)
        orbiters = Orbiters(Clock())
        orbiters.add_orbiter("M51.3", self.rocket)
        orbiters.separate_full_stage(self.rocket)
        orbiters.apply_remove()
        stage = orbiters.get_orbiter("stage1")
        self.assertAlmostEqual(stage.distance, self.rocket.distance)
        self.assertAlmostEqual(stage.ground_range(), self.rocket.ground_range())

    def test_info_columns(self):
        st = SpaceTime("scenario/m51.scn")
        o = st.orbiters.get_current_orbiter()
        o.distance, o.heat_flux, o.heat_load = 1234e3, 350e3, 2.5e6
        info = st.get_info()
        header, values = info.split("\n")
        for word in ("distance", "range", "heat"):
            self.assertIn(word, header)
        self.assertIn("1234km", values)
        self.assertIn("350kW/m2", values)
        self.assertIn("25%", values)
        self.assertIn("shield", values)  # The M51 head has a heat shield
        # Columns aligned: each value starts under its title
        for title in ("altitude", "distance", "heat"):
            col = header.index(title)
            self.assertNotEqual(values[col], " ")
            self.assertEqual(values[col - 1], " ")


class TestAccelerationMachMass(unittest.TestCase):
    def test_speed_of_sound_standard_atmosphere(self):
        import flightinfo
        self.assertAlmostEqual(flightinfo.speed_of_sound(0), 340.3, delta=0.2)
        self.assertAlmostEqual(flightinfo.speed_of_sound(11000), 295.1, delta=0.2)
        self.assertAlmostEqual(flightinfo.speed_of_sound(15000), 295.1, delta=0.2)
        self.assertAlmostEqual(flightinfo.speed_of_sound(50000), 329.8, delta=0.3)

    def test_felt_acceleration_on_the_pad_at_full_thrust(self):
        from tests.test_reentry import TC, earth
        from orbiter import Load_Orbiters
        from vector import Vector
        rocket = Load_Orbiters.get_orbiter("rockets/m51.rocket")[1]
        rocket.set_attractor(earth())
        rocket.set_state(Vector(6378140.0, 0.0, 0.0), Vector(0.0, 0.0, 0.0), 0)
        rocket.orientation1 = 0.0  # Vertical (the launch site is on the x axis)
        rocket.rcs = 0
        rocket.start_engine()
        rocket.stages.set_thrust("ALL", 1)
        tc = TC()
        tc.t = 0.1
        rocket.update_position(tc, 0.1)
        # 460 kg/s x 2750 m/s / ~52 t = 24.3 m/s2 = 2.48 g (minus 0.1 s of fuel)
        self.assertAlmostEqual(rocket.felt_acceleration / 9.80665, 2.48, delta=0.02)

    def test_no_felt_acceleration_in_orbit(self):
        from math import sqrt
        from tests.test_reentry import TC, earth
        from orbiter import Load_Orbiters
        from vector import Vector
        rocket = Load_Orbiters.get_orbiter("rockets/m51.rocket")[1]
        att = earth()
        rocket.set_attractor(att)
        r = 6378140 + 300e3
        rocket.set_state(Vector(r, 0.0, 0.0), Vector(0.0, sqrt(att.mu / r), 0.0), 0)
        rocket.rcs = 0
        tc = TC()
        tc.t = 1.0
        rocket.update_position(tc, 1.0)
        self.assertEqual(rocket.felt_acceleration, 0.0)

    def test_columns(self):
        st = SpaceTime("scenario/m51.scn")
        o = st.orbiters.get_current_orbiter()
        from vector import Vector
        o.v = Vector(0.0, 680.6, 0.0)  # Mach 2 at sea level
        o.felt_acceleration = 2 * 9.80665
        header, values = st.get_info().split("\n")
        for word in ("acceleration", "mach", "mass", "periapsis apoapsis"):
            self.assertIn(word, header)
        self.assertNotIn("aphelion", header)
        self.assertIn("2.00g", values)
        self.assertIn("2.00 ", values)  # Mach
        self.assertIn("52.0t", values)
