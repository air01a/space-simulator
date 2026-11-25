########################################
# Parachutes above the capsule of the panel (no Kivy: pure geometry)
########################################

from math import cos, pi, sin

DOME_STEPS = 10
SWAY = 0.06  # radians
SWAY_FREQUENCY = 0.25  # Hz


def _ease(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def canopies(anchor_x, anchor_y, width, count, progress, t, room, half_width=float("inf")):
    """Canopies tied to the anchor (top of the capsule, width = capsule width),
    opening with progress (0..1), in a room of this height above the anchor and
    of half_width on each side of it.
    Return (domes, lines): domes = convex polygons [(x, y)], lines = suspension
    lines (x0, y0, x1, y1), two per canopy"""
    p = _ease(progress)
    count = max(1, count)
    lines_length = room * (0.25 + 0.4 * p)
    # Horizontal room left once the sway is taken into account
    sway_room = room * 0.65 * sin(SWAY) + 4
    # Full size: the canopies side by side fill most of the room
    radius_full = max(1.0, min(room * 0.3, 0.9 * (half_width - sway_room) / count))
    radius = radius_full * (0.12 + 0.88 * p)
    # Flat ellipse when packed, dome when open
    dome_h = radius * (0.25 + 0.4 * p)
    spread = radius_full * 2.05 * p
    sway = sin(SWAY * sin(2 * pi * SWAY_FREQUENCY * t))
    domes, lines = [], []
    for k in range(count):
        offset = (k - (count - 1) / 2) * spread
        cx = anchor_x + offset + lines_length * sway
        cy = anchor_y + (lines_length ** 2 - offset ** 2) ** 0.5 if lines_length > abs(offset) else anchor_y + lines_length
        dome = [(cx, cy)]
        for i in range(DOME_STEPS + 1):
            a = pi * i / DOME_STEPS
            dome.append((cx + radius * cos(a), cy + dome_h * sin(a)))
        domes.append(dome)
        lines.append((anchor_x - width * 0.15, anchor_y, cx - radius, cy))
        lines.append((anchor_x + width * 0.15, anchor_y, cx + radius, cy))
    return domes, lines
