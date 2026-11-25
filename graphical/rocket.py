########################################
# Rocket panel: 2D drawing of the controlled orbiter (stages, fuel, state)
########################################

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Mesh, Rectangle
from kivy.graphics.scissor_instructions import ScissorPop, ScissorPush
from kivy.uix.widget import Widget

from graphical import breakup, parachute, plasma
from graphical.flames import flame_polygons
from graphical.rocket_layout import fuel_and_state, layout_rocket

ACTIVE_COLOR = (1, 0.75, 0.2)
NOZZLE_COLOR = (0.25, 0.25, 0.27)
FAIRING_COLOR = (0.9, 0.9, 0.9)
FOIL_COLOR = (0.85, 0.68, 0.2)  # Satellite body (gold thermal blanket)
PANEL_COLOR = (0.1, 0.16, 0.38)  # Solar panels
PANEL_GRID = (0.45, 0.55, 0.8)
FLAME_OUTER = (1.0, 0.45, 0.1, 0.85)
FLAME_INNER = (1.0, 0.92, 0.6, 0.95)
FLAME_ROOM = 0.1  # Part of the panel height kept under the rocket for the flames
CHUTE_ROOM = 0.55  # Part of the drawing height kept above the capsule for the parachutes
CANOPY_COLORS = ((1.0, 0.55, 0.15), (0.95, 0.95, 0.95))
LINE_COLOR = (0.85, 0.85, 0.85, 0.8)
DESTROYED_COLOR = (1.0, 0.35, 0.2)


def state_key(orbiter, size=(0, 0), pos=(0, 0)):
    """Everything the drawing depends on: redraw only when it changes.
    The canvas is drawn in window coordinates, so the position matters too."""
    size = (int(size[0]), int(size[1]), int(pos[0]), int(pos[1]))
    if orbiter is None:
        return (None, size)
    parts = []
    for index, stage in enumerate(orbiter.stages.stages):
        for name, part in stage.items():
            fuel, state = fuel_and_state(index, part, orbiter.engine_on)
            parts.append((index, name, None if fuel is None else round(fuel * 100), state))
    chute = bool(getattr(orbiter, "parachute_deployed", False))
    return (orbiter.name, size, bool(orbiter.engine_on), chute, tuple(parts))


def stack_labels(centers, label_height):
    """Vertical centers of labels, moved up when needed so that they do not
    overlap (same order as the input)"""
    order = sorted(range(len(centers)), key=lambda i: centers[i])
    result = list(centers)
    previous = None
    for i in order:
        y = centers[i]
        if previous is not None and y < previous + label_height:
            y = previous + label_height
        result[i] = y
        previous = y
    return result


def burning_nozzles(layout, orbiter, ox, oy):
    """Nozzles of the burning parts, in window coordinates, with their throttle:
    [((x, y, w, h), throttle), ...]"""
    stage0 = orbiter.stages.stages[0] if orbiter.stages.stages else {}
    result = []
    for part in layout.parts:
        if part.state != "active" or part.name not in stage0:
            continue
        throttle = stage0[part.name].throttle
        for (x, y, w, h) in part.nozzles:
            result.append(((x + ox, y + oy, w, h), throttle))
    return result


def _shade(color, factor):
    return tuple(min(1.0, max(0.0, c * factor)) for c in color)


def _desaturate(color):
    return tuple((c + 0.5) / 2 for c in color)


def _set_vertices(mesh, points):
    vertices = []
    for x, y in points:
        vertices += [x, y, 0, 0]
    mesh.vertices = vertices


def _new_mesh(group, count):
    mesh = Mesh(vertices=[0, 0, 0, 0] * count, indices=list(range(count)), mode="triangle_fan")
    group.add(mesh)
    return mesh


def _bbox(layout, ox, oy):
    """Window bbox (x, y, w, h) of the bodies and tops of a layout, or None"""
    rects = []
    for part in layout.parts:
        rects += [part.body] + ([part.top] if part.top else [])
    rects = [r for r in rects if r[2] > 0]
    if not rects:
        return None
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    return (x0 + ox, y0 + oy, x1 - x0, y1 - y0)


def _polygon(points):
    """Convex polygon [(x, y), ...] as a Kivy Mesh"""
    vertices = []
    for x, y in points:
        vertices += [x, y, 0, 0]
    Mesh(vertices=vertices, indices=list(range(len(points))), mode="triangle_fan")


def _ogive(x, y, w, h, bluntness=0.0, steps=8):
    """Curved nose cone on the rectangle (x, y, w, h). bluntness 0..1 (fairing)"""
    cx = x + w / 2
    left, right = [], []
    for k in range(steps + 1):
        t = k / steps
        # Half width: 1 at the bottom, 0 (or bluntness) at the top, curved
        half = (w / 2) * max(bluntness * (1 - t), (1 - t * t))
        left.append((cx - half, y + t * h))
        right.append((cx + half, y + t * h))
    _polygon([(cx, y)] + right + left[::-1])


class RocketView(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self._key = None
        self._layout = None  # Last layout and its offset, for the flames
        self._offset = (0, 0)
        # Flames: their own layer, redrawn at each frame (animation)
        self._flames = InstructionGroup()
        self.canvas.after.add(self._flames)
        self._flame_meshes = []  # [(outer Mesh, inner Mesh)] per burning nozzle
        # Reentry plasma (behind the flames), parachutes, breakup: own layers
        self._plasma = InstructionGroup()
        self._plasma_items = None  # (bow Color, bow Mesh, wake Color, wake Meshes)
        self._chutes = InstructionGroup()
        self._chute_items = None  # (count, [(Color, Mesh)], [Line])
        self._fx = InstructionGroup()
        self._fragments = None  # [(Fragment, Color, Mesh)] while breaking up
        self._breakup_t0 = 0.0
        self.canvas.after.insert(0, self._plasma)
        self.canvas.after.add(self._chutes)
        self.canvas.after.add(self._fx)
        self._shown = None  # Orbiter drawn: to see it burn up
        self._bbox = None  # Window bbox of the drawn rocket

    # Redraw the rocket if its state (or the panel geometry) has changed,
    # and animate the flames. Return True if the rocket was redrawn
    def update(self, orbiter):
        now = Clock.get_boottime()
        if self._fragments is not None:
            if now - self._breakup_t0 < breakup.DURATION + 0.5:
                self._animate_breakup(now - self._breakup_t0)
                return False
            self._end_breakup()
        # The drawn orbiter burnt up: it flies apart, before showing the next one
        if self._shown is not None and self._shown.destroyed and self._layout is not None:
            self._start_breakup(now)
            return True
        if orbiter is not None and getattr(orbiter, "destroyed", False):
            orbiter = None
        self._shown = orbiter
        key = state_key(orbiter, self.size, self.pos)
        redrawn = key != self._key
        if redrawn:
            self._key = key
            self._draw(orbiter)
        self._draw_flames(orbiter)
        self._draw_plasma(orbiter, now)
        self._draw_chutes(orbiter, now)
        return redrawn

    # Reentry plasma: bow shock under the base and wakes along the sides
    def _draw_plasma(self, orbiter, t):
        flux = getattr(orbiter, "heat_flux", 0.0) if orbiter is not None else 0.0
        color = plasma.glow_color(flux)
        if color[3] <= 0 or self._bbox is None:
            if self._plasma_items is not None:
                self._plasma.clear()
                self._plasma_items = None
            return
        if self._plasma_items is None:
            self._plasma.add(self._scissor())
            bow_color = Color(*color)
            self._plasma.add(bow_color)
            bow = _new_mesh(self._plasma, plasma.BOW_STEPS + 2)
            wake_color = Color(*color)
            self._plasma.add(wake_color)
            wakes = [_new_mesh(self._plasma, 3), _new_mesh(self._plasma, 3)]
            self._plasma.add(ScissorPop())
            self._plasma_items = (bow_color, bow, wake_color, wakes)
        bow_color, bow, wake_color, wakes = self._plasma_items
        shapes = plasma.glow_polygons(self._bbox, flux, t, max_depth=self._bbox[1] - self.y - 2)
        bow_color.rgba = color
        wake_color.rgba = (*color[:3], color[3] * 0.6)
        _set_vertices(bow, shapes["bow"])
        for mesh, points in zip(wakes, shapes["wakes"]):
            _set_vertices(mesh, points)

    # Parachutes above the capsule, opening then swaying
    def _draw_chutes(self, orbiter, t):
        chute = orbiter.parachute() if orbiter is not None and orbiter.parachute_deployed else None
        if chute is None or self._bbox is None:
            if self._chute_items is not None:
                self._chutes.clear()
                self._chute_items = None
            return
        if self._chute_items is None or self._chute_items[0] != chute.count:
            self._chutes.clear()
            self._chutes.add(self._scissor())
            line_color = Color(*LINE_COLOR)
            self._chutes.add(line_color)
            lines = []
            for _ in range(2 * chute.count):
                line = Line(points=[0, 0, 0, 0], width=1)
                self._chutes.add(line)
                lines.append(line)
            domes = []
            for k in range(chute.count):
                color = Color(*CANOPY_COLORS[k % 2])
                self._chutes.add(color)
                domes.append(_new_mesh(self._chutes, parachute.DOME_STEPS + 2))
            self._chutes.add(ScissorPop())
            self._chute_items = (chute.count, domes, lines)
        _, domes, lines = self._chute_items
        x, y, w, h = self._bbox
        room = self.y + self.height - (y + h) - 4
        cx = x + w / 2
        dome_points, line_points = parachute.canopies(
            cx, y + h, w, chute.count, orbiter.parachute_progress, t, room,
            half_width=min(cx - self.x, self.right - cx) - 4,
        )
        for mesh, points in zip(domes, dome_points):
            _set_vertices(mesh, points)
        for line, points in zip(lines, line_points):
            line.points = list(points)

    # Clip to the panel (window coordinates): the animations stay inside
    def _scissor(self):
        return ScissorPush(x=int(self.x), y=int(self.y), width=int(self.width), height=int(self.height))

    def _start_breakup(self, now):
        fragments = breakup.make_fragments(self._layout, *self._offset, seed=id(self._shown) % 1000)
        name = self._shown.name
        self._shown = None
        self._layout = None
        self._bbox = None
        for group in (self._flames, self._plasma, self._chutes):
            group.clear()
        self._flame_meshes = []
        self._plasma_items = None
        self._chute_items = None
        self._draw_frame("%s : détruit" % name, DESTROYED_COLOR)
        self._fragments = []
        self._fx.add(self._scissor())
        for fragment in fragments:
            color = Color(*breakup.fragment_color(fragment, 0.0))
            self._fx.add(color)
            self._fragments.append((fragment, color, _new_mesh(self._fx, 4)))
        self._fx.add(ScissorPop())
        self._breakup_t0 = now
        self._animate_breakup(0.0)

    def _animate_breakup(self, t):
        for fragment, color, mesh in self._fragments:
            color.rgba = breakup.fragment_color(fragment, t)
            _set_vertices(mesh, breakup.fragment_polygon(fragment, t))

    def _end_breakup(self):
        self._fx.clear()
        self._fragments = None
        self._key = None  # Redraw the next orbiter

    def _draw_flames(self, orbiter):
        nozzles = []
        if orbiter is not None and self._layout is not None:
            nozzles = burning_nozzles(self._layout, orbiter, *self._offset)
        # Kivy objects created only when the number of burning nozzles changes;
        # at each frame, only their vertices are updated (cheap)
        if len(nozzles) != len(self._flame_meshes):
            self._flames.clear()
            self._flame_meshes = []
            for _ in nozzles:
                meshes = []
                for color in (FLAME_OUTER, FLAME_INNER):
                    self._flames.add(Color(*color))
                    mesh = Mesh(vertices=[0, 0, 0, 0] * 5, indices=list(range(5)), mode="triangle_fan")
                    self._flames.add(mesh)
                    meshes.append(mesh)
                self._flame_meshes.append(meshes)
        if not nozzles:
            return
        t = Clock.get_boottime()
        for index, ((nozzle, throttle), meshes) in enumerate(zip(nozzles, self._flame_meshes)):
            # Room under the nozzle exit, inside the panel
            max_length = nozzle[1] - (self.y + 2)
            polygons = flame_polygons(nozzle, throttle, t, max_length, phase=index * 1.3)
            for mesh, points in zip(meshes, polygons):
                vertices = []
                for x, y in points or [(nozzle[0], nozzle[1])] * 5:
                    vertices += [x, y, 0, 0]
                mesh.vertices = vertices

    def _label(self, text, size):
        label = CoreLabel(text=text, font_size=size)
        label.refresh()
        return label.texture

    # Background, frame and title. Return the title height
    def _draw_frame(self, text, color=(1, 1, 1)):
        font = max(8, int(Window.height / 800 * 14))
        x0, y0 = self.pos
        w, h = self.size
        self.canvas.clear()
        with self.canvas:
            Color(0, 0, 0, 0.55)
            Rectangle(pos=self.pos, size=self.size)
            Color(1, 1, 1, 0.35)
            Line(rectangle=(x0, y0, w, h), width=1)
            title = self._label(text, font)
            Color(*color, 1)
            Rectangle(
                texture=title,
                pos=(x0 + (w - title.width) / 2, y0 + h - title.height - 4),
                size=title.size,
            )
        return title.height + 8

    def _draw(self, orbiter):
        font = max(8, int(Window.height / 800 * 14))
        x0, y0 = self.pos
        w, h = self.size
        title_h = self._draw_frame(orbiter.name if orbiter else "None")
        with self.canvas:
            self._layout = None
            self._bbox = None
            # Parachutes and plasma rebuilt with the new geometry (clipping rectangle)
            self._chutes.clear()
            self._chute_items = None
            self._plasma.clear()
            self._plasma_items = None
            if orbiter is None:
                return
            room = h * FLAME_ROOM
            box_w = w * 0.78  # room on the right for the fuel percentages
            box_h = h - title_h - room
            if orbiter.parachute_deployed:
                box_h *= 1 - CHUTE_ROOM  # The parachutes above the capsule
            layout = layout_rocket(orbiter.stages.stages, box_w, box_h, orbiter.engine_on)
            ox, oy = x0, y0 + room
            self._layout = layout
            self._offset = (ox, oy)
            self._bbox = _bbox(layout, ox, oy)
            for part in layout.parts:
                self._draw_part(part, ox, oy, font)
            for fairing in layout.fairings:
                self._draw_fairing(fairing, ox, oy)
            self._draw_fuel_labels(layout, oy, font)

    # Payload flying alone: body, booms, deployed solar panels, antenna dish
    def _draw_satellite(self, part, ox, oy):
        bx, by, bw, bh = part.body
        bx += ox
        by += oy
        cy = by + bh / 2
        for (px, py, pw, ph) in part.panels:
            px += ox
            py += oy
            # Boom between the body and the panel
            Color(0.6, 0.6, 0.6)
            start, end = (bx, px + pw) if px < bx else (bx + bw, px)
            Line(points=[start, cy, end, cy], width=1)
            # Panel and its cells
            Color(*PANEL_COLOR)
            Rectangle(pos=(px, py), size=(pw, ph))
            Color(*PANEL_GRID, 0.7)
            cells = max(1, int(pw / max(ph * 0.6, 1)))
            for k in range(1, cells):
                x = px + pw * k / cells
                Line(points=[x, py, x, py + ph], width=1)
            Line(points=[px, py + ph / 2, px + pw, py + ph / 2], width=1)
            Line(rectangle=(px, py, pw, ph), width=1)
        # Body, with volume
        Color(*FOIL_COLOR)
        Rectangle(pos=(bx, by), size=(bw, bh))
        Color(*_shade(FOIL_COLOR, 1.2))
        Rectangle(pos=(bx + bw * 0.12, by), size=(bw * 0.15, bh))
        Color(*_shade(FOIL_COLOR, 0.7))
        Rectangle(pos=(bx + bw * 0.78, by), size=(bw * 0.22, bh))
        # Antenna dish on the top
        Color(0.92, 0.92, 0.92)
        dish_w = bw * 0.8
        Ellipse(pos=(bx + (bw - dish_w) / 2, by + bh - dish_w * 0.15), size=(dish_w, dish_w * 0.35))
        if part.state == "active":
            Color(*ACTIVE_COLOR)
            Line(rectangle=(bx, by, bw, bh), width=1.5)

    def _draw_part(self, part, ox, oy, font):
        if part.kind == "satellite":
            self._draw_satellite(part, ox, oy)
            return
        shape = part.shape
        color = shape.color
        band = shape.band
        if part.state == "empty":
            color = _desaturate(color)
            band = _desaturate(band) if band else None
        bx, by, bw, bh = part.body
        bx += ox
        by += oy

        # Nozzles (bell shape, wider at the bottom)
        Color(*NOZZLE_COLOR)
        for (nx, ny, nw, nh) in part.nozzles:
            nx += ox
            ny += oy
            _polygon([(nx, ny), (nx + nw, ny), (nx + nw * 0.75, ny + nh), (nx + nw * 0.25, ny + nh)])

        # Body, with a light band on the left and a dark one on the right (volume)
        if bh > 0:
            Color(*color)
            Rectangle(pos=(bx, by), size=(bw, bh))
            Color(*_shade(color, 1.15))
            Rectangle(pos=(bx + bw * 0.12, by), size=(bw * 0.12, bh))
            Color(*_shade(color, 0.7))
            Rectangle(pos=(bx + bw * 0.8, by), size=(bw * 0.2, bh))
            if band:
                Color(*band)
                for level in (0.15, 0.7):
                    Rectangle(pos=(bx, by + bh * level), size=(bw, bh * 0.06))
            # Fuel: darker from the bottom up to the fuel level
            if part.fuel is not None and part.fuel > 0:
                Color(0, 0, 0, 0.15)
                Rectangle(pos=(bx, by), size=(bw, bh * part.fuel))

        # Top
        if part.top:
            tx, ty, tw, th = part.top
            tx += ox
            ty += oy
            Color(*color)
            if shape.top == "ogive":
                _ogive(tx, ty, tw, th)
            elif shape.top == "fairing":
                _ogive(tx, ty, tw, th, bluntness=0.35)
            elif shape.top == "cone":
                _polygon([(tx, ty), (tx + tw, ty), (tx + tw / 2, ty + th)])
            else:  # capsule, capsule_les
                capsule_h = th * 0.85 / 3.35 if part.tower else th
                _polygon(
                    [(tx, ty), (tx + tw, ty), (tx + tw * 0.62, ty + capsule_h), (tx + tw * 0.38, ty + capsule_h)]
                )
                if part.tower:
                    # Launch escape tower: thin truss and its motor
                    tower_y = ty + capsule_h
                    tower_h = th - capsule_h
                    Color(0.75, 0.2, 0.15)
                    Rectangle(pos=(tx + tw * 0.46, tower_y), size=(tw * 0.08, tower_h * 0.55))
                    Rectangle(pos=(tx + tw * 0.4, tower_y + tower_h * 0.55), size=(tw * 0.2, tower_h * 0.3))
                    _polygon(
                        [
                            (tx + tw * 0.4, tower_y + tower_h * 0.85),
                            (tx + tw * 0.6, tower_y + tower_h * 0.85),
                            (tx + tw * 0.5, tower_y + tower_h),
                        ]
                    )

        # Burning stage: outline (fuel percentages drawn by _draw_fuel_labels)
        if part.state == "active":
            Color(*ACTIVE_COLOR)
            Line(rectangle=(bx, by, bw, max(bh, 1)), width=1.5)

    # Fuel percentage of the burning parts, on the right, without overlap
    def _draw_fuel_labels(self, layout, oy, font):
        active = [p for p in layout.parts if p.state == "active" and p.fuel is not None]
        if not active:
            return
        labels = [self._label("%d%%" % round(p.fuel * 100), max(8, font - 2)) for p in active]
        centers = [oy + p.body[1] + p.body[3] / 2 for p in active]
        Color(*ACTIVE_COLOR)
        for label, y in zip(labels, stack_labels(centers, max(l.height for l in labels))):
            Rectangle(
                texture=label,
                pos=(self.x + self.width * 0.8, y - label.height / 2),
                size=label.size,
            )

    def _draw_fairing(self, fairing, ox, oy):
        cx = fairing.cx + ox
        y0, y1 = fairing.y0 + oy, fairing.y1 + oy
        points = [
            (cx - fairing.w0 / 2, y0),
            (cx + fairing.w0 / 2, y0),
            (cx + fairing.w1 / 2, y1),
            (cx - fairing.w1 / 2, y1),
        ]
        Color(*FAIRING_COLOR, 0.25)
        _polygon(points)
        Color(*FAIRING_COLOR, 0.6)
        Line(points=[c for p in points + points[:1] for c in p], width=1)
