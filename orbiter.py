########################################
# Define rockets (composition, )
########################################
from vector import Vector
from math import atan2, cos, pi, sin, log, acos, asin
import numpy as np
from orbit import Orbit
import logging, inspect
from constants import max_delta_t
import configparser
from orbitprojection import OrbitProjection
from constants import rcs_push_delta_v

########################################
# Define a composant of a stage
########################################


class Stage_Composant:
    def __init__(
        self,
        motor_flow,
        motor_speed,
        empty_mass,
        carburant_mass,
        drag_x_surf=0,
        payload=False,
    ):
        self.motor_flow = motor_flow
        self.motor_speed = motor_speed
        self.empty_mass = empty_mass
        self.carburant_mass = carburant_mass
        self.throttle = 1
        self.payload = payload
        self.drag_x_surf = drag_x_surf

    def thrust(self, dt):
        if self.carburant_mass > 0:
            t = dt * self.motor_flow * self.motor_speed * self.throttle
            self.carburant_mass -= dt * self.motor_flow * self.throttle
            return (t, self.carburant_mass)
        return (0, 0)


########################################
# Define rocket stages (multiple parts)
########################################


class Stages:
    def __init__(self):
        self.stages = []
        self.empty_part = []
        self.total_empty_mass = 0
        self.carburant_mass = 0
        self.drag_x_surf = 0

    def add_stage(self):
        self.stages.append({})

    def add_part(self, name, part):
        self.stages[-1][name] = part
        self.total_empty_mass += part.empty_mass
        if len(self.stages) > 1:
            self.total_empty_mass += part.carburant_mass
        else:
            self.carburant_mass += part.carburant_mass
        self.drag_x_surf += part.drag_x_surf

    def sep_part(self, name, stage=0):
        if len(self.stages) < 2:
            return
        if name in self.stages[stage].keys():
            part = self.stages[stage][name]
        else:
            return None
        self.total_empty_mass -= part.empty_mass
        self.carburant_mass -= part.carburant_mass
        self.drag_x_surf -= part.drag_x_surf
        del self.stages[stage][name]
        if len(self.stages[stage]) == 0:
            del self.stages[stage]
            if stage == 0:
                if len(self.stages[stage]) > 0:
                    for part2 in self.stages[stage].values():
                        self.total_empty_mass -= part2.carburant_mass
                        self.carburant_mass += part2.carburant_mass
        return part

    def sep_payload(self):
        for index, stages in enumerate(self.stages):
            for part in stages.keys():
                if stages[part].payload == True:
                    return self.sep_part(part, index)

    def set_thrust(self, name, throttle):
        if name == "ALL":
            for part in self.stages[0].keys():
                self.stages[0][part].throttle = throttle
        else:
            self.stages[0][name].throttle = throttle

    def get_thrust(self, dt):
        thrust = 0
        carburant_mass = 0
        for part in self.stages[0].keys():
            (thr, carb) = self.stages[0][part].thrust(dt)
            carburant_mass += carb
            thrust += thr
            if (
                thr + carb == 0
                and part not in self.empty_part
                and not self.stages[0][part].payload
            ):
                self.empty_part.append(part)
        self.carburant_mass = carburant_mass
        return thrust

    def get_total_mass(self):
        return self.total_empty_mass + self.carburant_mass

    def get_carburant_mass(self):
        return self.carburant_mass

    def drop_stage(self):
        for part in list(self.stages[0].keys()):
            self.sep_part(part)


########################################
# Define an orbiter from stages
# Manage acceleration and force
########################################


class Orbiter:
    def __init__(self, name, stages):
        self.orbit = None
        self.empty_mass = 0
        self.r = Vector(0.0, 0.0, 0.0)
        self.v = Vector(0.0, 0.0, 0.0)
        self.attractor = None
        self.orientation1 = np.pi / 2
        self.orientation2 = 0
        self.dv = Vector(0.0, 0.0, 0.0)
        self.stages = stages
        self.thrust = False
        self.last_a = Vector(0, 0, 0)
        self.orbit_projection = OrbitProjection(self.attractor, self.orbit)
        self.controller = None
        self.name = name
        self.lock = None
        self.control_info_callback = None
        self.rcs = True

    def start_engine(self):
        self.thrust = 1

    def stop_engine(self):
        self.thrust = 0

    def drop_stage(self):
        self.stages.drop_stage()

    def set_state(self, r, v, t):
        self.r = r
        self.v = v
        if self.attractor != None and self.r.norm() - self.attractor.radius > 1000:
            self.orbit.set_from_state_vector(r, v, t)

    def set_controller(self, controller):
        self.controller = controller

    def set_orbit_parameters(self, a, e, i, raan, arg_pe, f):
        self.orbit.set_elements(a, e, i, raan, arg_pe, f)
        (self.r, self.v) = self.orbit.update_position(0)

    def set_attractor(self, attractor):
        self.attractor = attractor
        self.orbit = Orbit(attractor.mu)
        self.orbit.set_attractor(attractor)
        self.orbit_projection.attractor = attractor
        self.orbit_projection.orbit = self.orbit

    def change_orientation(self, o1, o2):
        self.orientation1 = o1
        self.orientation2 = o2
        self.lock = None

    def get_force(self):
        ra = self.r.norm()
        angle = atan2(self.r.y, self.r.x)
        return Vector(ra * cos(angle), ra * sin(angle), 0)

    def check_boundaries(self, time_controller):
        new_attractor = self.attractor.check_boundaries(self.r)
        if new_attractor != None:
            (r, v) = self.attractor.change_attractor(
                self.r, self.v, new_attractor, self.attractor
            )
            self.set_attractor(new_attractor)
            self.set_state(r, v, time_controller.t)
            self.orbit_projection.calculate_time_series(time_controller.t)
            time_controller.time_normalize()

    def lock_orientation_prograde(self):
        self.lock = "P"

    def lock_orientation_retrograde(self):
        self.lock = "R"

    def rcs_push(self):
        self.rcs = True

    def set_attitude(self):

        if self.lock == "R":
            self.orientation1 = pi + self.v.angle2D()
        elif self.lock == "P":
            self.orientation1 = self.v.angle2D()

    # Apply forces and update vector v and r
    def update_position(self, time_controller, dt):
        trajectory_update = False
        t = time_controller.t
        # if delta t > max_delta_t (from constants), divide delta_t to avoid too big time increment
        # Otherwise, with delta t too high, force will be inconsistant
        delta_t_array = []
        if dt < max_delta_t:
            delta_t_array.append(dt)
        else:
            t_increment = 0
            while t_increment < dt:
                increment = min(max_delta_t, dt - t_increment)
                delta_t_array.append(increment)
                t_increment += increment

        # Iterate delta_t
        for dt in delta_t_array:
            # If motors are on, calculate dv
            if self.thrust or self.rcs:
                dv = self.delta_v(t, dt)
            else:
                dv = None

            # If rocket is in flight
            if self.r.norm() > self.attractor.radius:
                # Calculate gravitationnal force
                a = self.attractor.get_gravitationnal_field(self.r)
            else:
                a = Vector(0, 0, 0)

            # If motors are on, update velocity vector
            if dv != None:
                self.v += dv
                trajectory_update = True

            # If the rocket is in atmosphere, calculate the drag force
            friction = self.attractor.get_drag_force(
                self.r.norm() - self.attractor.radius, self.v, self.stages.drag_x_surf
            )
            if friction != 0:
                dv = Vector(0, 0, 0)
                a += friction / (self.stages.get_total_mass())
                trajectory_update = True

            # Integrate to calculate Velocity vector and position
            self.v += (a + self.last_a) / 2 * dt
            self.last_a = a
            self.r = self.r + self.v * dt

            if self.controller:
                self.controller.control_flight_path(self)

        self.set_attitude()

        logging.debug(
            "+++++ %s - %s"
            % (
                inspect.getfile(inspect.currentframe()),
                inspect.currentframe().f_code.co_name,
            )
        )
        logging.debug("Position " + str(self.r))
        logging.debug("Distance " + str(self.r.norm()))
        logging.debug("Velocity " + str(self.v))
        logging.debug("Velocity " + str(self.v.norm()))
        logging.debug("----------------------------")

        # If the trajectory has changed, update the kepler projection
        if (
            trajectory_update
            and self.r.norm() > self.attractor.radius
            and self.v.norm() > 0
        ):
            self.set_state(self.r, self.v, t)
            self.orbit_projection.calculate_time_series(t)

        self.check_boundaries(time_controller)

        # Detect rocket crash
        if self.r.norm() < self.attractor.radius:
            return True
        return False

    # Propagate kepler equation to calculate Velocity and position
    # Use for time acceleration
    def update_position_delta_t(self, time_controller):

        if self.controller:
            self.controller.control_flight_path(self)
        if self.v.norm() == 0:
            return True
        (r, v) = self.orbit.update_position(time_controller.t)
        if r != None:
            (self.r, self.v) = (r, v)
        self.check_boundaries(time_controller)

        self.set_attitude()

        if self.r.norm() < self.attractor.radius:
            return True
        return False

    # Calculate delta v when rocket motors are on
    def delta_v(self, t, dt):

        v_direction = Vector(cos(self.orientation1), sin(self.orientation1), 0)
        self.dv = Vector(0, 0, 0)
        if self.rcs:
            self.dv = rcs_push_delta_v * v_direction
            self.rcs = 0
        if self.thrust:
            mass = self.stages.get_total_mass()
            thrust = self.stages.get_thrust(dt)
            self.thrust = thrust / (1000 * dt)
            self.dv += v_direction * thrust / mass
        return self.dv

    def display_info(self, t):

        altitude = (self.r.norm() - self.attractor.radius) / 1000
        (perigee, apogee) = self.orbit.get_limit()
        perigee = int((perigee - self.attractor.radius) / 1000)
        apogee = int((apogee - self.attractor.radius) / 1000)
        perigee = max(0, perigee)
        apogee = max(0, apogee)
        velocity = self.v.norm() / 1000
        print(
            "%is %.2fkN %.2fkm %.2fkm/s %ikg %ideg [%ikm, %ikm]"
            % (
                int(t),
                self.thrust,
                altitude,
                velocity,
                int(self.stages.get_carburant_mass()),
                int(self.orientation1 * 180 / 3.141592),
                perigee,
                apogee,
            )
        )


########################################
# Handle multiple orbiters
########################################


class Orbiters:
    def __init__(self, time):
        self.orbiters = {}
        self.current_orbiter = None
        self.deleted_orbiters = []
        self.time = time

    def add_orbiter(self, name, orbiter):
        self.orbiters[name] = orbiter
        if len(self.orbiters) == 1:
            self.current_orbiter = name

    def set_active_orbiter(self, name):
        self.current_orbiter = name

    def get_current_orbiter(self):
        if self.current_orbiter == None:
            return None
        return self.orbiters[self.current_orbiter]

    def get_current_orbiter_name(self):
        return self.current_orbiter

    def get_current_orbiter_names(self):
        return list(self.orbiters.keys())

    def get_orbiter(self, name):
        if name in self.orbiters.keys():
            return self.orbiters[name]
        return None

    def get_orbiters(self):
        return self.orbiters

    def remove(self, name):
        self.deleted_orbiters.append(name)

    def apply_remove(self):
        for orb in self.deleted_orbiters:
            if orb in self.orbiters.keys():
                if orb == self.current_orbiter:
                    self.current_orbiter = None
                del self.orbiters[orb]

                if self.current_orbiter == None and len(self.orbiters) > 0:
                    self.current_orbiter = list(self.orbiters.keys())[0]

    def separate_stage(self, orbiter, part_name, thrust=0):
        if part_name in orbiter.stages.empty_part:
            orbiter.stages.empty_part.pop(orbiter.stage.empty_part.index(part_name))
        if part_name == "payload":
            part = orbiter.stages.sep_payload()
        else:
            part = orbiter.stages.sep_part(part_name)
        if part == None:
            return
        stages = Stages()
        stages.add_stage()
        stages.add_part(part_name, part)

        new_orbiter = Orbiter(part_name, stages)
        new_orbiter.set_attractor(orbiter.attractor)
        self.add_orbiter(part_name, new_orbiter)
        new_orbiter.set_state(orbiter.r, orbiter.v, self.time.t)
        new_orbiter.orbit_projection.calculate_time_series(self.time.t)
        orbiter.thrust = thrust
        print("############# Stage Separation ##############")
        print(part)
        print("#############################################")

    def separate_full_stage(self, orbiter):
        for part in list(orbiter.stages.stages[0].keys()):
            self.separate_stage(orbiter, part)


########################################
# Load an orbiter from an INI file
########################################


class Load_Orbiters:
    @staticmethod
    def get_orbiter(file_name):
        config = configparser.ConfigParser()
        config.read(file_name)
        finish = False
        stage = 0
        name = config["param"]["name"]
        stages = Stages()

        while not finish:
            stage += 1
            stage_str = "stage" + str(stage)
            if stage_str in config.keys():
                print("Add stage %s" % stage_str)
                stages.add_stage()
                for part in config[stage_str].keys():
                    payload = True if part == "payload" else False
                    data = config[stage_str][part]
                    (
                        ejected_mass,
                        velocity,
                        dry_mass,
                        carburant_mass,
                        drag_x_surf,
                    ) = data.split(",")
                    print(
                        "Add composant : ",
                        part,
                        (ejected_mass, velocity, dry_mass, carburant_mass, drag_x_surf),
                    )
                    stages.add_part(
                        part,
                        Stage_Composant(
                            int(ejected_mass),
                            int(velocity),
                            int(dry_mass),
                            int(carburant_mass),
                            float(drag_x_surf),
                            payload,
                        ),
                    )
            else:
                finish = True
        orbiter = Orbiter(name, stages)
        return (name, orbiter)
