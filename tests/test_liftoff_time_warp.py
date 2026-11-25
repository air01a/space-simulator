"""Engine started on the launch pad while time is accelerated (> x10).
Regression: the rocket never took off (Kepler propagation ignores the thrust
when the speed is 0) and the game looked frozen."""
import os
import unittest

os.environ.setdefault("KIVY_NO_ARGS", "1")

import timecontroller


class FakeClock:
    now = 1000.0

    @classmethod
    def time(cls):
        return cls.now


class TestLiftoffWithTimeWarp(unittest.TestCase):
    def setUp(self):
        self._time = timecontroller.time
        timecontroller.time = FakeClock
        from spacetime import SpaceTime
        self.st = SpaceTime("scenario/m51.scn")
        self.rocket = self.st.orbiters.get_current_orbiter()
        self.rocket.rcs = 0

    def tearDown(self):
        timecontroller.time = self._time

    def run_frames(self, n):
        for _ in range(n):
            FakeClock.now += 1 / 60
            self.st.update(1 / 60)

    def altitude(self):
        return self.rocket.r.norm() - self.rocket.attractor.radius

    def test_rocket_takes_off_with_time_accelerated(self):
        self.run_frames(1)
        self.st.time_controller.set_time_increment(77)  # time slider pushed before liftoff
        self.rocket.start_engine()
        self.rocket.stages.set_thrust("ALL", 1)
        self.run_frames(120)  # 2 s of wall clock
        self.assertGreater(self.altitude(), 100)  # it left the pad
        self.assertLessEqual(self.st.time_controller.t_increment, 10)  # capped while burning

    def test_engine_on_at_zero_throttle_does_not_cap_time_warp(self):
        # Mission coasting phases: engine "on" but throttle 0
        self.run_frames(1)
        self.rocket.start_engine()
        self.rocket.stages.set_thrust("ALL", 0)
        self.st.time_controller.set_time_increment(77)
        self.run_frames(60)
        self.assertEqual(self.st.time_controller.t_increment, 77)

    def test_time_warp_unchanged_without_engine(self):
        self.run_frames(1)
        self.st.time_controller.set_time_increment(77)
        self.run_frames(60)
        self.assertEqual(self.st.time_controller.t_increment, 77)
        self.assertAlmostEqual(self.altitude(), 0, delta=1)


if __name__ == "__main__":
    unittest.main()
