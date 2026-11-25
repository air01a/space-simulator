import unittest

from graphical.rocket_layout import Fairing, layout_rocket
from orbiter import Stage_Composant
from rocketshape import parse_shape

W, H, MARGIN = 300, 450, 8


def shape(**kw):
    section = {k: str(v) for k, v in kw.items()}
    return parse_shape(section, False)


def part(shp, fuel=1.0, initial=100.0, payload=False):
    p = Stage_Composant(10, 3000, 1000, initial, 0, payload, shp)
    p.carburant_mass = initial * fuel
    return p


def make_stages(stages):
    """[[(name, shape, fuel, initial), ...], ...] -> Stages.stages-like list"""
    out = []
    for stage in stages:
        d = {}
        for name, shp, fuel, initial in stage:
            d[name] = part(shp, fuel, initial)
        out.append(d)
    return out


def by_name(layout):
    return {p.name: p for p in layout.parts}


class TestLayout(unittest.TestCase):
    def test_stack_order_bottom_to_top(self):
        stages = make_stages([[("a", shape(), 1, 100)], [("b", shape(), 1, 100)], [("c", shape(), 1, 100)]])
        p = by_name(layout_rocket(stages, W, H))
        self.assertLess(p["a"].body[1], p["b"].body[1])
        self.assertLess(p["b"].body[1], p["c"].body[1])

    def test_fits_in_box_and_keeps_ratio(self):
        stages = make_stages(
            [
                [("s1", shape(length=42, diameter=10, nozzles=5), 1, 100)],
                [("cap", shape(length=11, diameter=3.9, top="capsule_les"), 1, 100)],
            ]
        )
        layout = layout_rocket(stages, W, H, margin=MARGIN)
        for p in layout.parts:
            for (x, y, w, h) in [p.body] + p.nozzles + ([p.top] if p.top else []):
                self.assertGreaterEqual(x, MARGIN - 1e-6)
                self.assertLessEqual(x + w, W - MARGIN + 1e-6)
                self.assertGreaterEqual(y, MARGIN - 1e-6)
                self.assertLessEqual(y + h, H - MARGIN + 1e-6)
        s1 = by_name(layout)["s1"]
        self.assertAlmostEqual(s1.body[3] / s1.body[2], 42 / 10, places=6)

    def test_side_boosters_left_and_right(self):
        stages = make_stages(
            [
                [
                    ("booster1", shape(length=31, diameter=3, top="ogive", position="side"), 1, 100),
                    ("booster2", shape(length=31, diameter=3, top="ogive", position="side"), 1, 100),
                    ("epc", shape(length=30.5, diameter=5.4), 1, 100),
                ]
            ]
        )
        p = by_name(layout_rocket(stages, W, H))
        epc_x, epc_y, epc_w, _ = p["epc"].body
        xs = sorted([p["booster1"].body, p["booster2"].body], key=lambda b: b[0])
        self.assertLessEqual(xs[0][0] + xs[0][2], epc_x + 1e-6)
        self.assertGreaterEqual(xs[1][0], epc_x + epc_w - 1e-6)
        self.assertAlmostEqual(p["booster1"].body[1], epc_y, places=6)
        self.assertAlmostEqual(p["booster2"].body[1], epc_y, places=6)

    def test_only_side_parts(self):
        stages = make_stages([[("b1", shape(position="side"), 1, 100), ("b2", shape(position="side"), 1, 100)]])
        layout = layout_rocket(stages, W, H, margin=MARGIN)
        for p in layout.parts:
            x, y, w, h = p.body
            self.assertTrue(MARGIN - 1e-6 <= x and x + w <= W - MARGIN + 1e-6)
            self.assertTrue(MARGIN - 1e-6 <= y and y + h <= H - MARGIN + 1e-6)

    def test_fuel_and_states(self):
        stages = make_stages([[("low", shape(), 0.25, 100)], [("up", shape(), 1, 100)]])
        p = by_name(layout_rocket(stages, W, H, engine_on=True))
        self.assertAlmostEqual(p["low"].fuel, 0.25)
        self.assertEqual(p["low"].state, "active")
        self.assertEqual(p["up"].state, "idle")
        empty = by_name(layout_rocket(make_stages([[("e", shape(), 0, 100)]]), W, H, engine_on=True))
        self.assertEqual(empty["e"].state, "empty")
        self.assertEqual(empty["e"].fuel, 0)

    def test_payload_without_fuel(self):
        stages = [{"payload": part(parse_shape(None, True), 0, 0, payload=True)}]
        p = by_name(layout_rocket(stages, W, H, engine_on=True))["payload"]
        self.assertIsNone(p.fuel)
        self.assertEqual(p.state, "idle")

    def apollo_top(self, with_csm=True):
        lem = dict(draw_below="csm", enclosed="true")
        stages = [[("s-ivb", shape(length=17.8, diameter=6.6), 1, 100)]]
        if with_csm:
            stages.append([("csm", shape(length=11, diameter=3.9, top="capsule_les"), 1, 100)])
        stages.append([("lem_descent", shape(length=3.2, diameter=4.2, **lem), 1, 100)])
        stages.append([("lem_ascent", shape(length=2.8, diameter=4.0, **lem), 1, 100)])
        return make_stages(stages)

    def test_draw_below_puts_lem_under_csm(self):
        layout = layout_rocket(self.apollo_top(), W, H)
        p = by_name(layout)
        y = {n: p[n].body[1] for n in p}
        self.assertLess(y["s-ivb"], y["lem_descent"])
        self.assertLess(y["lem_descent"], y["lem_ascent"])
        self.assertLess(y["lem_ascent"], y["csm"])
        self.assertEqual(len(layout.fairings), 1)
        f = layout.fairings[0]
        self.assertIsInstance(f, Fairing)
        self.assertAlmostEqual(f.w0, p["s-ivb"].body[2], places=6)
        self.assertAlmostEqual(f.w1, p["csm"].body[2], places=6)

    def test_draw_below_missing_target(self):
        layout = layout_rocket(self.apollo_top(with_csm=False), W, H)
        p = by_name(layout)
        self.assertLess(p["s-ivb"].body[1], p["lem_descent"].body[1])
        self.assertLess(p["lem_descent"].body[1], p["lem_ascent"].body[1])
        self.assertEqual(layout.fairings, [])

    def test_draw_below_cycle(self):
        stages = make_stages([[("a", shape(draw_below="b"), 1, 100)], [("b", shape(draw_below="a"), 1, 100)]])
        p = by_name(layout_rocket(stages, W, H))
        self.assertLess(p["a"].body[1], p["b"].body[1])

    def satellite_payload(self):
        shp = parse_shape({"length": "17", "diameter": "5.4", "satellite": "4.5, 2.5, 30"}, True)
        return part(shp, 0, 0, payload=True)

    def test_satellite_alone_has_deployed_panels(self):
        layout = layout_rocket([{"payload": self.satellite_payload()}], W, H)
        (sat,) = layout.parts
        self.assertEqual(sat.kind, "satellite")
        x, y, w, h = sat.body
        self.assertAlmostEqual(h / w, 4.5 / 2.5, places=6)
        self.assertEqual(len(sat.panels), 2)
        left, right = sorted(sat.panels, key=lambda r: r[0])
        self.assertLessEqual(left[0] + left[2], x + 1e-6)
        self.assertGreaterEqual(right[0], x + w - 1e-6)
        span = right[0] + right[2] - left[0]
        self.assertAlmostEqual(span / w, 30 / 2.5, places=6)
        self.assertIsNone(sat.top)
        self.assertEqual(sat.nozzles, [])
        for (px, py, pw, ph) in sat.panels + [sat.body]:
            self.assertTrue(-1e-6 <= px and px + pw <= W + 1e-6)

    def test_satellite_attached_is_drawn_as_fairing(self):
        stages = make_stages([[("eps", shape(length=3.4, diameter=5.4), 1, 100)]])
        stages.append({"payload": self.satellite_payload()})
        p = by_name(layout_rocket(stages, W, H))["payload"]
        self.assertEqual(p.kind, "stage")
        self.assertEqual(p.panels, [])
        self.assertIsNotNone(p.top)  # fairing

    def test_empty_stages(self):
        layout = layout_rocket([], W, H)
        self.assertEqual(layout.parts, [])
        self.assertEqual(layout.fairings, [])


if __name__ == "__main__":
    unittest.main()
