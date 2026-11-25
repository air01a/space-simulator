"""Atmospheric reentry: heating, destruction without heat shield"""
import os
import unittest
from math import exp, sqrt

os.environ.setdefault("KIVY_NO_ARGS", "1")

import reentry
from attractor import Attractor
from orbiter import Load_Orbiters, Stages
from vector import Vector

MU = 3.986004415e14
R = 6378140


class TC:
    """Minimal time controller for orbiter.update_position"""

    def __init__(self):
        self.t = 0.0

    def time_normalize(self):
        pass


def earth():
    att = Attractor("earth", R, MU)
    att.set_atmosphere_condition(1.39, 7900, 120000)  # Same as the scenarios
    return att


def part_alone(file, name):
    """Orbiter made of one part of a .rocket file"""
    rocket = Load_Orbiters.get_orbiter("rockets/%s.rocket" % file)[1]
    stage = next(s for s in rocket.stages.stages if name in s)
    stages = Stages()
    stages.add_stage()
    stages.add_part(name, stage[name])
    rocket.stages = stages
    return rocket


def reentry_state(alt, apogee=200e3, perigee=40e3):
    """Position, velocity at altitude alt, descending, on an apogee x perigee orbit"""
    ra, rp, r = R + apogee, R + perigee, R + alt
    a = (ra + rp) / 2
    e = (ra - rp) / (ra + rp)
    v = sqrt(MU * (2 / r - 1 / a))
    vt = sqrt(MU * a * (1 - e * e)) / r
    vr = -sqrt(max(0.0, v * v - vt * vt))
    return Vector(r, 0.0, 0.0), Vector(vr, vt, 0.0)


def fly(orbiter, r, v, frame=1.0, max_time=3000):
    """Integrate until destroyed or on the ground. Return (outcome, altitude of the
    end, max heat load, last speed)"""
    orbiter.set_attractor(earth())
    orbiter.set_state(r, v, 0)
    tc = TC()
    max_load = 0.0
    while tc.t < max_time:
        tc.t += frame
        speed = orbiter.v.norm()
        crashed = orbiter.update_position(tc, frame)
        max_load = max(max_load, orbiter.heat_load)
        alt = orbiter.r.norm() - R
        if orbiter.destroyed:
            return "destroyed", alt, max_load, speed
        if crashed:
            return "crashed", alt, max_load, speed
        if orbiter.v.norm() == 0:
            return "landed", alt, max_load, speed
    return "flying", orbiter.r.norm() - R, max_load, orbiter.v.norm()


class TestHeatFormulas(unittest.TestCase):
    def test_sutton_graves(self):
        # q = 1.7415e-4 * sqrt(rho / rn) * v^3, x (1 - vw^2 / v^2): hot wall correction
        expected = 1.7415e-4 * sqrt(5e-5) * 7800 ** 3 * (1 - 1500 ** 2 / 7800 ** 2)
        self.assertAlmostEqual(reentry.heat_flux(1e-4, 7800, 2.0), expected)
        self.assertEqual(reentry.heat_flux(0.0, 7800, 2.0), 0.0)

    def test_no_heating_below_the_wall_speed(self):
        # Supersonic but slow (falling booster): the air is not hotter than the wall
        self.assertEqual(reentry.heat_flux(1.0, 1500, 2.0), 0.0)
        self.assertEqual(reentry.heat_flux(1.0, 900, 2.0), 0.0)
        self.assertEqual(reentry.heat_flux(1.0, 0, 2.0), 0.0)

    def test_heat_load_cools_down(self):
        q = reentry.update_heat_load(0.0, 1000.0, 2.0)
        self.assertAlmostEqual(q, 2000.0)
        cooled = reentry.update_heat_load(q, 0.0, reentry.HEAT_TAU)
        self.assertAlmostEqual(cooled, 2000.0 * exp(-1))


class TestReentry(unittest.TestCase):
    def test_bare_stage_destroyed_between_70_and_85_km(self):
        r, v = reentry_state(125e3)
        outcome, alt, _, speed = fly(part_alone("saturne5", "s-ivb"), r, v)
        self.assertEqual(outcome, "destroyed")
        self.assertGreater(alt, 70e3)
        self.assertLess(alt, 85e3)
        self.assertGreater(speed, 6000)

    def test_service_module_destroyed(self):
        r, v = reentry_state(125e3)
        outcome, alt, _, _ = fly(part_alone("saturne5", "sm"), r, v)
        self.assertEqual(outcome, "destroyed")

    def test_command_module_is_not_destroyed(self):
        r, v = reentry_state(125e3)
        cm = part_alone("saturne5", "cm")
        cm.stages.stages[0]["cm"].parachute = None  # Heating only here
        outcome, _, max_load, _ = fly(cm, r, v)
        self.assertNotEqual(outcome, "destroyed")
        self.assertGreater(max_load, reentry.HEAT_LOAD_MAX)  # It would have burnt

    def test_m51_head_survives_the_reentry(self):
        head = part_alone("m51", "payload")
        self.assertTrue(head.has_heat_shield())
        r, v = reentry_state(125e3)
        outcome, _, max_load, _ = fly(head, r, v)
        self.assertNotEqual(outcome, "destroyed")
        self.assertGreater(max_load, reentry.HEAT_LOAD_MAX)  # Unshielded, it would burn

    def test_no_heating_out_of_the_atmosphere(self):
        rocket = part_alone("saturne5", "s-ivb")
        r = Vector(R + 300e3, 0.0, 0.0)
        outcome, _, max_load, _ = fly(rocket, r, Vector(0.0, sqrt(MU / r.norm()), 0.0), max_time=200)
        self.assertEqual(outcome, "flying")
        self.assertEqual(max_load, 0.0)
        self.assertFalse(rocket.in_atmosphere())


if __name__ == "__main__":
    unittest.main()


class TestParachute(unittest.TestCase):
    CHUTE = None

    def setUp(self):
        from equipment import Parachute
        self.chute = Parachute(25.4, 3, 3000.0, 200.0)

    def test_deploy_conditions(self):
        deploy = reentry.should_deploy
        self.assertTrue(deploy(self.chute, 2900, 150, descending=True))
        self.assertFalse(deploy(self.chute, 3100, 150, descending=True))  # Too high
        self.assertFalse(deploy(self.chute, 2900, 250, descending=True))  # Too fast
        self.assertFalse(deploy(self.chute, 2900, 150, descending=False))  # Going up
        self.assertFalse(deploy(None, 2900, 150, descending=True))

    def test_area_opens_in_3_seconds(self):
        full = 0.8 * 3 * 3.141592653589793 * 12.7 ** 2
        self.assertAlmostEqual(reentry.parachute_area(self.chute, 1.0), full)
        self.assertAlmostEqual(reentry.parachute_area(self.chute, 0.5), full / 2)
        self.assertEqual(reentry.parachute_area(None, 1.0), 0.0)
        self.assertAlmostEqual(reentry.opening_progress(0.0, 1.5), 0.5)
        self.assertEqual(reentry.opening_progress(0.9, 1.0), 1.0)

    def test_command_module_lands_under_its_parachute(self):
        r, v = reentry_state(125e3)
        cm = part_alone("saturne5", "cm")
        outcome, alt, _, speed = fly(cm, r, v, frame=0.5)
        self.assertEqual(outcome, "landed")
        self.assertTrue(cm.parachute_deployed)
        self.assertEqual(cm.parachute_progress, 1.0)
        self.assertLess(speed, 10)  # max_speed_before_crash

    def test_descent_under_parachute_without_numerical_warning(self):
        # Almost vertical fall: cos(true anomaly) rounded above 1 gave NaN
        import warnings
        r, v = reentry_state(125e3)
        cm = part_alone("saturne5", "cm")
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            outcome = fly(cm, r, v, frame=0.5)[0]
        self.assertEqual(outcome, "landed")

    def test_parachute_never_retracts(self):
        r, v = reentry_state(125e3)
        cm = part_alone("saturne5", "cm")
        fly(cm, r, v, frame=0.5)
        cm.v = Vector(0.0, 300.0, 0.0)  # Too fast now: stays deployed
        self.assertTrue(cm.parachute_deployed)

    def test_no_parachute_crashes(self):
        r, v = reentry_state(125e3)
        cm = part_alone("saturne5", "cm")
        cm.stages.stages[0]["cm"].parachute = None
        outcome, _, _, speed = fly(cm, r, v, frame=0.5)
        self.assertEqual(outcome, "crashed")
        self.assertGreater(speed, 10)


class FakeClock:
    now = 1000.0

    @classmethod
    def time(cls):
        return cls.now


class TestReentryWithTimeWarp(unittest.TestCase):
    """Above x10, the orbits are propagated with Kepler (no atmosphere): a
    reentry must switch back to the numerical integration"""

    def setUp(self):
        import timecontroller
        self.tc_module = timecontroller
        self._time = timecontroller.time
        timecontroller.time = FakeClock
        from spacetime import SpaceTime
        self.st = SpaceTime("scenario/m51.scn")
        self.rocket = self.st.orbiters.get_current_orbiter()
        self.rocket.rcs = 0

    def tearDown(self):
        self.tc_module.time = self._time

    def test_reentry_at_x77_is_capped_and_burns(self):
        FakeClock.now += 1 / 60
        self.st.update(1 / 60)
        # A bare first stage (the M51 head has a heat shield)
        stages = Stages()
        stages.add_stage()
        stages.add_part("stage1", self.rocket.stages.stages[0]["stage1"])
        self.rocket.stages = stages
        r, v = reentry_state(130e3)  # Above the atmosphere (120 km)
        self.rocket.set_state(r, v, self.st.time_controller.t)
        self.rocket.orbit_projection.calculate_time_series(self.st.time_controller.t)
        self.st.time_controller.set_time_increment(77)
        increments = []
        for _ in range(60 * 120):
            # Frames that start in the atmosphere (the one entering it was
            # computed before, with Kepler)
            inside = self.rocket.in_atmosphere()
            FakeClock.now += 1 / 60
            self.st.update(1 / 60)
            if inside:
                increments.append(self.st.time_controller.t_increment)
            if self.rocket.destroyed:
                break
        self.assertTrue(self.rocket.destroyed)
        self.assertTrue(increments)
        self.assertLessEqual(max(increments), 10)
