########################################
# Reentry plasma around the rocket of the panel (no Kivy: pure geometry)
########################################

from math import log10, pi, sin

from graphical.flames import flicker
from reentry import PLASMA_MIN_FLUX

PLASMA_FULL_FLUX = 2e6  # W/m2: white hot
DARK_RED = (0.65, 0.08, 0.02)
ORANGE = (1.0, 0.45, 0.08)
WHITE = (1.0, 0.95, 0.85)
BOW_STEPS = 12


def intensity(flux):
    """0..1, logarithmic between the visible flux and the white hot one"""
    if flux < PLASMA_MIN_FLUX:
        return 0.0
    return min(1.0, log10(flux / PLASMA_MIN_FLUX) / log10(PLASMA_FULL_FLUX / PLASMA_MIN_FLUX))


def _mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def glow_color(flux):
    """(r, g, b, a): dark red -> orange -> white with the flux, a = 0 if invisible"""
    s = intensity(flux)
    if flux < PLASMA_MIN_FLUX:
        return (*DARK_RED, 0.0)
    rgb = _mix(DARK_RED, ORANGE, s / 0.5) if s < 0.5 else _mix(ORANGE, WHITE, (s - 0.5) / 0.5)
    return (*rgb, 0.35 + 0.5 * s)


def glow_polygons(bbox, flux, t, max_depth=float("inf")):
    """Shapes around the rocket bbox (x, y, w, h), the base facing the airflow:
    "bow" (shock under the base, convex) and "wakes" (2 trails along the sides,
    outside the body). Size grows with the flux, flickering with time t; the
    bow is at most max_depth deep"""
    x, y, w, h = bbox
    s = max(intensity(flux), 0.15)
    f = flicker(t)
    depth = min(w * (0.25 + 0.55 * s) * f, max(0.0, max_depth))
    half = w * (0.5 + 0.15 * s)
    cx = x + w / 2
    # Half ellipse under the base, ends at the base level
    bow = [(cx - half + 2 * half * k / BOW_STEPS, y - depth * sin(pi * k / BOW_STEPS)) for k in range(BOW_STEPS + 1)]
    bow = [(cx, y)] + bow
    length = h * (0.35 + 0.5 * s) * flicker(t, 1.1)
    width = w * (0.12 + 0.2 * s)
    wakes = [
        [(x, y), (x, y + length), (x - width, y + length * 0.15)],
        [(x + w, y), (x + w + width, y + length * 0.15), (x + w, y + length)],
    ]
    return {"bow": bow, "wakes": wakes}
