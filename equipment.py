########################################
# Equipment of a rocket part: heat shield, parachute
# Read from the optional [equipment.<part name>] sections of the .rocket files
########################################

from dataclasses import dataclass


@dataclass(frozen=True)
class Parachute:
    diameter: float  # Diameter of one canopy, meters
    count: int  # Number of canopies
    deploy_altitude: float  # Deployed below this altitude, meters
    max_speed: float  # ... and below this speed, m/s


@dataclass(frozen=True)
class Equipment:
    heat_shield: bool = False
    parachute: Parachute = None


def _bool(value):
    value = value.strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ValueError(value)


def _parachute(value):
    values = [v.strip() for v in value.split(",")]
    if len(values) != 4:
        raise ValueError(value)
    chute = Parachute(float(values[0]), int(values[1]), float(values[2]), float(values[3]))
    if chute.diameter <= 0 or chute.count <= 0 or chute.deploy_altitude <= 0 or chute.max_speed <= 0:
        raise ValueError(value)
    return chute


PARSERS = {"heat_shield": _bool, "parachute": _parachute}


def parse_equipment(section):
    """Equipment from an [equipment.<part>] section (mapping of strings).
    A missing or invalid value keeps the default (none)"""
    values = {}
    if section is not None:
        for key, parse in PARSERS.items():
            if key in section:
                text = section[key].split(";")[0].strip()
                try:
                    values[key] = parse(text)
                except (ValueError, TypeError):
                    print("Invalid equipment value %s = %r, default used" % (key, section[key]))
    return Equipment(**values)
