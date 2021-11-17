import configparser
from attractor import Attractor
from orbiter import Orbiter, Stages, Stage_Composant, Orbiters, Load_Orbiters
from vector import Vector
from controller import Controller

##############################################
# Manage scenery file
# (file containing attractor config, orbiters and mission controller)
#
##############################################


class Scenery:
    # Read attractor config
    def read_attractor(self, name, parent=None):
        print("Reading %s" % name)

        attractor_name = self.config[name]["Name"]
        mu = float(self.config[name]["MU"])
        radius = float(self.config[name]["Radius"])

        attractor = Attractor(attractor_name, radius, mu)

        if "Soi" in self.config[name].keys():
            soi = float(self.config[name]["Soi"])
            attractor.set_soir(soi)

        if "Atmosphere" in self.config[name].keys():
            atmosphere = self.config[name]["Atmosphere"].split(",")
            (p0, h0, atmosphere_limit) = tuple(atmosphere)
            attractor.set_atmosphere_condition(
                float(p0), float(h0), float(atmosphere_limit)
            )

        if "Picture" in self.config[name].keys():
            attractor.set_picture(self.config[name]["Picture"])

        if "Orbit" in self.config[name].keys() and parent != None:
            orbit = self.config[name]["Orbit"].split(",")
            (a, e, i, raan, arg_pe, f) = tuple(orbit)
            attractor.parent = parent
            attractor.set_orbit_parameters(
                parent.mu,
                float(a),
                float(e),
                float(i),
                float(raan),
                float(arg_pe),
                float(f),
            )

            attractor.update_position(0)

        if "Child" in self.config[name].keys():
            for child in self.config[name]["Child"].split(","):
                attractor.add_child(self.read_attractor(child, attractor))

        self.attractors[attractor_name] = attractor
        return attractor

    # Read orbiters config
    def read_orbiters(self, time_controller):
        orbiters = Orbiters(time_controller)

        for orbiters_name in self.config["ORBITERS"]["Name"].split(","):
            orbiter_param = self.config[orbiters_name]
            file = orbiter_param["File"]
            attractor = orbiter_param["Attractor"]
            (orbiter_name, orbiter) = Load_Orbiters.get_orbiter(file)
            orbiter.set_attractor(self.attractors[attractor])

            if "Position" in orbiter_param.keys():
                position = orbiter_param["Position"]
                velocity = orbiter_param["Velocity"]
                (x, y, z) = tuple(position.split(","))
                (vx, vy, vz) = tuple(velocity.split(","))
                r = Vector(float(x), float(y), float(z))
                v = Vector(float(vx), float(vy), float(vz))
                orbiter.set_state(r, v, 0)
            else:
                orbit = orbiter_param["Orbit"].split(",")
                (a, e, i, raan, arg_pe, f) = tuple(orbit)
                orbiter.set_orbit_parameters(
                    float(a),
                    float(e),
                    float(i),
                    float(raan),
                    float(arg_pe),
                    float(f),
                )
            orbiter.orbit_projection.calculate_time_series(0)

            orbiters.add_orbiter(orbiter_name, orbiter)
        self.orbiters = orbiters
        return orbiters

    # Read controller config
    def read_mission(self, time_controller):
        if "MISSION" in self.config.keys():
            mission = self.config["MISSION"]["File"]
            return Controller(mission, self.orbiters, time_controller)

    def __init__(self, file_name):
        self.config = configparser.ConfigParser()
        self.config.read(file_name)
        self.attractors = {}
