########################################
# Shape of a rocket part, for the 2D drawing of the rocket
# Read from the optional [shape.<part name>] sections of the .rocket files
########################################

from dataclasses import dataclass

TOPS = ("none", "ogive", "cone", "fairing", "capsule", "capsule_les")
POSITIONS = ("center", "side")
DEFAULT_COLOR = "#d0d0d0"


def parse_color(text):
    """'#rrggbb' -> (r, g, b) in 0..1. Raise ValueError if malformed."""
    text = text.strip()
    if len(text) != 7 or text[0] != "#":
        raise ValueError("Color must be #rrggbb: %r" % text)
    return tuple(int(text[i : i + 2], 16) / 255 for i in (1, 3, 5))


@dataclass
class PartShape:
    length: float  # Total length (top included), meters
    diameter: float  # Meters
    top: str  # One of TOPS
    nozzles: int  # Number of nozzles drawn under the part
    color: tuple  # (r, g, b), 0..1
    band: tuple  # (r, g, b) of the decorative bands, or None
    position: str  # "center" (stacked) or "side" (booster)
    draw_below: str  # Draw this part just under this other part, or None
    enclosed: bool  # Part inside a fairing (adapter)
    # (body height, body width, solar panels span) in meters: drawn as a
    # satellite when it flies alone (separated), else with its normal shape
    satellite: tuple = None


def _positive(value, cast):
    value = cast(value)
    if value <= 0:
        raise ValueError(value)
    return value


def _non_negative_int(value):
    value = int(value)
    if value < 0:
        raise ValueError(value)
    return value


def _choice(choices):
    def parse(value):
        value = value.strip().lower()
        if value not in choices:
            raise ValueError(value)
        return value

    return parse


def _bool(value):
    value = value.strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ValueError(value)


def _satellite(value):
    values = tuple(float(v) for v in value.split(","))
    if len(values) != 3 or min(values) <= 0 or values[2] <= values[1]:
        raise ValueError(value)
    return values


def _name(value):
    value = value.strip().lower()
    if not value:
        raise ValueError(value)
    return value


# key -> parser. A missing or invalid value keeps the default of the key
PARSERS = {
    "length": lambda v: _positive(v, float),
    "diameter": lambda v: _positive(v, float),
    "top": _choice(TOPS),
    "nozzles": _non_negative_int,
    "color": parse_color,
    "band": parse_color,
    "position": _choice(POSITIONS),
    "draw_below": _name,
    "enclosed": _bool,
    "satellite": _satellite,
}


def parse_shape(section, is_payload):
    """Shape from a [shape.<part>] section (mapping of strings), or None.
    A payload defaults to a fairing without nozzle."""
    values = {
        "length": 10.0,
        "diameter": 3.0,
        "top": "fairing" if is_payload else "none",
        "nozzles": 0 if is_payload else 1,
        "color": parse_color(DEFAULT_COLOR),
        "band": None,
        "position": "center",
        "draw_below": None,
        "enclosed": False,
        "satellite": None,
    }
    if section is not None:
        for key, parse in PARSERS.items():
            if key in section:
                # Inline comment ("length = 30.5 ; meters"). Not '#': used by colors
                text = section[key].split(";")[0].strip()
                try:
                    values[key] = parse(text)
                except (ValueError, TypeError):
                    print("Invalid shape value %s = %r, default used" % (key, section[key]))
    return PartShape(**values)
