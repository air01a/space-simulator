########################################
# Layout of the 2D drawing of a rocket (no Kivy: pure geometry, testable)
#
# Input : the stages of an orbiter (stage 0 = first to burn) and the shapes of
# their parts. Output : rectangles in pixels of the drawing box, y up.
########################################

from dataclasses import dataclass, field

# Height of the top of a part, as a factor of its diameter
TOP_HEIGHT = {
    "none": 0.0,
    "ogive": 1.2,
    "cone": 1.0,
    "fairing": 0.9,
    "capsule": 0.85,
    "capsule_les": 0.85 + 2.5,  # capsule + launch escape tower
}
NOZZLE_HEIGHT = 0.15  # x diameter
NOZZLE_WIDTH = 0.3  # x diameter


@dataclass
class PartLayout:
    name: str
    shape: object  # PartShape
    body: tuple  # (x, y, w, h) px
    top: tuple  # (x, y, w, h) px, or None
    nozzles: list  # [(x, y, w, h)] px
    fuel: float  # 0..1, or None (no tank)
    state: str  # "active" | "empty" | "idle"
    kind: str = "stage"  # "stage" or "satellite" (payload flying alone)
    panels: list = field(default_factory=list)  # Solar panels [(x, y, w, h)] px
    tower: bool = False  # capsule_les drawn with its launch escape tower


@dataclass
class Fairing:
    cx: float  # px
    y0: float  # bottom
    w0: float  # width at the bottom
    y1: float  # top
    w1: float  # width at the top


@dataclass
class RocketLayout:
    parts: list = field(default_factory=list)  # Drawing order: back to front
    fairings: list = field(default_factory=list)
    scale: float = 0.0  # px / m


@dataclass
class _Item:
    stage: int
    name: str
    part: object  # Stage_Composant
    # Geometry in meters
    body: tuple = None
    top: tuple = None
    nozzles: list = field(default_factory=list)
    top_kind: str = None  # Top actually drawn (shape.top, or capsule without tower)

    @property
    def shape(self):
        return self.part.shape


# The launch escape tower is jettisoned early in the flight: drawn only on the
# launcher (3 stages or more), not on the spacecraft flying alone
TOWER_MIN_STAGES = 3


def _top_height(item):
    return TOP_HEIGHT.get(item.top_kind, 0.0) * item.shape.diameter


def _place(item, x_center, y):
    """Set the geometry of a part whose body bottom is at y. Return its top y."""
    d = item.shape.diameter
    top_h = _top_height(item)
    # Body length from the declared top: without its tower, the capsule is shorter
    body_h = max(0.0, item.shape.length - TOP_HEIGHT.get(item.shape.top, 0.0) * d)
    item.body = (x_center - d / 2, y, d, body_h)
    item.top = (x_center - d / 2, y + body_h, d, top_h) if top_h > 0 else None
    n = item.shape.nozzles
    item.nozzles = []
    if n > 0:
        nw = min(NOZZLE_WIDTH * d, d / n)
        nh = NOZZLE_HEIGHT * d
        if n == 1:
            centers = [x_center]
        else:
            first = x_center - d / 2 + nw / 2
            step = (d - nw) / (n - 1)
            centers = [first + k * step for k in range(n)]
        item.nozzles = [(c - nw / 2, y - nh, nw, nh) for c in centers]
    return y + body_h + top_h


def _stack_order(centers):
    """Central parts from bottom to top, with the draw_below relocations.
    Return (stack, relocated names)."""
    names = {it.name for it in centers}
    candidate = {
        it.name: it.shape.draw_below
        for it in centers
        if it.shape.draw_below in names and it.shape.draw_below != it.name
    }
    # A part whose target is itself relocated stays in place (no chain, no cycle)
    relocated = {n: t for n, t in candidate.items() if t not in candidate}
    stack = [it for it in centers if it.name not in relocated]
    for target in list(dict.fromkeys(relocated.values())):
        moved = [it for it in centers if relocated.get(it.name) == target]
        index = next(i for i, it in enumerate(stack) if it.name == target)
        stack[index:index] = moved
    return stack, set(relocated)


def fuel_and_state(stage_index, part, engine_on):
    """Fuel level (0..1, None without tank) and state of a part:
    "active" (burning), "empty" (tank empty) or "idle"."""
    initial = getattr(part, "initial_carburant_mass", 0) or 0
    fuel = None
    if initial > 0:
        fuel = min(1.0, max(0.0, part.carburant_mass / initial))
    if stage_index == 0 and engine_on and part.throttle > 0 and part.carburant_mass > 0:
        state = "active"
    elif initial > 0 and part.carburant_mass <= 0:
        state = "empty"
    else:
        state = "idle"
    return fuel, state


def _layout_satellite(item, width, height, engine_on, margin):
    """A payload flying alone: satellite body with its solar panels deployed
    on each side, centered in the box"""
    body_h, body_w, span = item.shape.satellite
    gap = 0.04 * span  # Boom between the body and a panel
    panel_w = max(0.0, (span - body_w) / 2 - gap)
    panel_h = 0.45 * body_h
    scale = min((width - 2 * margin) / span, (height - 2 * margin) / body_h)
    cx, cy = width / 2, height / 2
    body = (cx - body_w * scale / 2, cy - body_h * scale / 2, body_w * scale, body_h * scale)
    panel_y = cy - panel_h * scale / 2
    panels = [
        (cx - span * scale / 2, panel_y, panel_w * scale, panel_h * scale),
        (cx + span * scale / 2 - panel_w * scale, panel_y, panel_w * scale, panel_h * scale),
    ]
    fuel, state = fuel_and_state(item.stage, item.part, engine_on)
    part = PartLayout(item.name, item.shape, body, None, [], fuel, state, "satellite", panels)
    return RocketLayout(parts=[part], fairings=[], scale=scale)


def layout_rocket(stages, width, height, engine_on=False, margin=8):
    items = [
        _Item(index, name, part)
        for index, stage in enumerate(stages)
        for name, part in stage.items()
    ]
    if not items:
        return RocketLayout()
    for it in items:
        it.top_kind = it.shape.top
        if it.top_kind == "capsule_les" and len(stages) < TOWER_MIN_STAGES:
            it.top_kind = "capsule"
    if len(items) == 1 and items[0].shape.satellite:
        return _layout_satellite(items[0], width, height, engine_on, margin)

    centers = [it for it in items if it.shape.position != "side"]
    sides = [it for it in items if it.shape.position == "side"]
    stack, relocated = _stack_order(centers)

    # Central stack, bottom to top, centered on x = 0
    y = 0.0
    tops = {}
    for it in stack:
        tops[it.name] = _place(it, 0.0, y)
        y = tops[it.name]

    # Fairings around the relocated enclosed parts (meters for now)
    fairings_m = []
    i = 0
    while i < len(stack):
        if stack[i].name in relocated and stack[i].shape.enclosed:
            j = i
            while j + 1 < len(stack) and stack[j + 1].name in relocated and stack[j + 1].shape.enclosed:
                j += 1
            below = stack[i - 1] if i > 0 else stack[i]
            above = stack[j + 1] if j + 1 < len(stack) else stack[j]
            fairings_m.append(
                (stack[i].body[1], below.shape.diameter, tops[stack[j].name], above.shape.diameter)
            )
            i = j + 1
        else:
            i += 1

    # Side boosters of each stage, alternately left and right of the reference part
    for stage in sorted({it.stage for it in sides}):
        ref = next((it for it in stack if it.stage == stage), stack[0] if stack else None)
        d_ref = ref.shape.diameter if ref else 0.0
        base = ref.body[1] if ref else 0.0
        for k, it in enumerate([s for s in sides if s.stage == stage]):
            d = it.shape.diameter
            offset = d_ref / 2 + d / 2 + (k // 2) * d
            _place(it, offset if k % 2 else -offset, base)

    # Bounding box (meters) and scale to fit the box
    rects = []
    for it in sides + stack:
        rects += [it.body] + it.nozzles + ([it.top] if it.top else [])
    min_x = min(r[0] for r in rects)
    max_x = max(r[0] + r[2] for r in rects)
    min_y = min(r[1] for r in rects)
    max_y = max(r[1] + r[3] for r in rects)
    bw, bh = max_x - min_x, max_y - min_y
    scale = min((width - 2 * margin) / bw if bw > 0 else float("inf"),
                (height - 2 * margin) / bh if bh > 0 else float("inf"))
    if scale == float("inf"):
        scale = 1.0
    ox = (width - bw * scale) / 2 - min_x * scale
    oy = margin - min_y * scale

    def px(r):
        return (r[0] * scale + ox, r[1] * scale + oy, r[2] * scale, r[3] * scale)

    layout = RocketLayout(scale=scale)
    # Drawing order: boosters, then the stack from top to bottom (the nozzles of a
    # part are drawn before - behind - the part under it)
    for it in sides + stack[::-1]:
        fuel, state = fuel_and_state(it.stage, it.part, engine_on)
        layout.parts.append(
            PartLayout(
                it.name,
                it.shape,
                px(it.body),
                px(it.top) if it.top else None,
                [px(n) for n in it.nozzles],
                fuel,
                state,
                tower=it.top_kind == "capsule_les",
            )
        )
    for (y0, d0, y1, d1) in fairings_m:
        layout.fairings.append(Fairing(ox, y0 * scale + oy, d0 * scale, y1 * scale + oy, d1 * scale))
    return layout
