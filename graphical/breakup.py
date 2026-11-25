########################################
# Breakup of a rocket burnt up in the atmosphere (no Kivy: pure geometry)
########################################

import random
from dataclasses import dataclass
from math import cos, sin

DURATION = 2.5  # s
MAX_FRAGMENTS = 90
GLOW = (1.0, 0.45, 0.1)
SPARK = (1.0, 0.85, 0.4)
HOT_TIME = 0.6  # Fragments turn orange during this time, then fade out


@dataclass
class Fragment:
    cx: float  # Center at t = 0, window coordinates
    cy: float
    w: float
    h: float
    vx: float  # px/s
    vy: float
    spin: float  # rad/s
    color: tuple  # (r, g, b) at t = 0
    spark: bool = False


def _pieces(rect, columns, rows):
    x, y, w, h = rect
    for i in range(columns):
        for j in range(rows):
            yield (x + w * i / columns, y + h * j / rows, w / columns, h / rows)


def make_fragments(layout, ox, oy, seed=0):
    """Fragments of the drawn parts (body and top) of a RocketLayout drawn at
    (ox, oy), flying away from the center of the drawing, plus sparks"""
    rng = random.Random(seed)
    rects = []
    for part in layout.parts:
        color = tuple(part.shape.color)
        for rect in [part.body] + ([part.top] if part.top else []) + list(part.panels):
            if rect[2] > 0 and rect[3] > 0:
                rows = max(1, min(6, round(1.5 * rect[3] / max(rect[2], 1))))
                rects += [(r, color) for r in _pieces(rect, 3, rows)]
    if not rects:
        return []
    rng.shuffle(rects)
    rects = rects[: MAX_FRAGMENTS * 2 // 3]
    cx0 = sum(r[0] + r[2] / 2 for r, _ in rects) / len(rects) + ox
    cy0 = sum(r[1] + r[3] / 2 for r, _ in rects) / len(rects) + oy
    size = max(max(r[0] + r[2] for r, _ in rects) - min(r[0] for r, _ in rects),
               max(r[1] + r[3] for r, _ in rects) - min(r[1] for r, _ in rects))
    fragments = []
    for (x, y, w, h), color in rects:
        cx, cy = x + w / 2 + ox, y + h / 2 + oy
        dx, dy = cx - cx0, cy - cy0
        norm = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        speed = size * rng.uniform(0.15, 0.45)
        fragments.append(Fragment(
            cx, cy, w, h,
            dx / norm * speed + rng.uniform(-0.1, 0.1) * size,
            dy / norm * speed + rng.uniform(-0.1, 0.1) * size,
            rng.uniform(-4.0, 4.0), color))
    for _ in range(MAX_FRAGMENTS - len(fragments)):
        a = rng.uniform(0, 6.283)
        speed = size * rng.uniform(0.4, 0.9)
        s = max(2.0, size * 0.012)
        fragments.append(Fragment(cx0, cy0, s, s, cos(a) * speed, sin(a) * speed, 0.0, SPARK, True))
    return fragments


def fragment_polygon(f, t):
    """Rotated, drifting (and slowing down) rectangle at time t: 4 points"""
    drift = t - 0.2 * t * t / DURATION  # Air drag: slows down
    cx, cy = f.cx + f.vx * drift, f.cy + f.vy * drift
    shrink = max(0.2, 1 - 0.5 * t / DURATION)
    hw, hh = f.w / 2 * shrink, f.h / 2 * shrink
    a = f.spin * t
    ca, sa = cos(a), sin(a)
    return [(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]


def fragment_color(f, t):
    """(r, g, b, a): the part color turning orange hot, then fading out"""
    if t >= DURATION:
        return (*f.color, 0.0)
    if f.spark:
        return (*SPARK, max(0.0, 1 - t / (DURATION * 0.6)))
    k = min(1.0, t / HOT_TIME)
    rgb = tuple(c + (g - c) * k for c, g in zip(f.color, GLOW))
    fade = 1.0 if t < HOT_TIME else max(0.0, 1 - (t - HOT_TIME) / (DURATION - HOT_TIME))
    return (*rgb, fade)
