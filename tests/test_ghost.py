import unittest

from graphical.ghost import format_eta, ghost_label


class TestEta(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(format_eta(12 * 60 + 30), "+12 min")

    def test_hours(self):
        self.assertEqual(format_eta(97 * 3600 + 3 * 60 + 59), "+97 h 03")

    def test_days(self):
        self.assertEqual(format_eta(6 * 86400 + 1 * 3600 + 20 * 60), "+6 d 01 h")

    def test_past_or_now(self):
        self.assertEqual(format_eta(-5), "+0 min")

    def test_label(self):
        self.assertEqual(ghost_label("moon", 3 * 3600), "moon +3 h 00")


if __name__ == "__main__":
    unittest.main()
