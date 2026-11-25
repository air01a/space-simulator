########################################
# Engine flames of the rocket panel (no Kivy: pure geometry, testable)
########################################

from math import pi, sin

LENGTH = 7.0  # Flame length at full throttle, x nozzle width
PLUME = 0.3  # The plume widens by this much on each side, x nozzle width
CORE_LENGTH = 0.55  # Core (bright part) length, x flame length
CORE_WIDTH = 0.5  # Core width, x nozzle width


def flicker(t, phase=0.0):
    """Length factor in [0.8, 1.2], changing quickly with time t (seconds).
    Two sines of unrelated frequencies: irregular but smooth."""
    return 1 + 0.12 * sin(2 * pi * 7.0 * t + phase) + 0.08 * sin(2 * pi * 13.3 * t + 1.7 + 2 * phase)


def flame_polygons(nozzle, throttle, t, max_length, phase=0.0):
    """Flame under a nozzle (x, y, w, h), y = bottom of the nozzle (exit).
    Return (outer, inner) convex polygons [(x, y), ...], ([], []) if no thrust.
    Length proportional to the throttle, flickering, clamped to max_length."""
    if throttle <= 0 or max_length <= 0:
        return [], []
    x, y, w, _ = nozzle
    # Clamp before the flicker, so that a flame limited by the room still flickers
    base = min(max_length / 1.2, LENGTH * w * throttle)
    length = base * flicker(t, phase)
    # Same width as the nozzle at its exit, then the plume widens
    outer = [
        (x, y),
        (x + w, y),
        (x + w * (1 + PLUME), y - length * 0.3),
        (x + w / 2, y - length),
        (x - w * PLUME, y - length * 0.3),
    ]
    core = length * CORE_LENGTH
    cx0 = x + w * (1 - CORE_WIDTH) / 2
    cw = w * CORE_WIDTH
    inner = [
        (cx0, y),
        (cx0 + cw, y),
        (cx0 + cw * 0.85, y - core * 0.4),
        (cx0 + cw / 2, y - core),
        (cx0 + cw * 0.15, y - core * 0.4),
    ]
    return outer, inner
