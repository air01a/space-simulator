########################################
# Use keyboard to orient rocket
########################################
from numpy import pi

class PilotOrbiter:

    def engine_on(self,thrust = 1):
        self.orbiters.get_current_orbiter().stages.set_thrust("ALL",thrust)
        self.orbiters.get_current_orbiter().start_engine()
        self.orbiters.get_current_orbiter().display_info(self.orbiters.time.t)

        if self.control_info_callback:
            self.control_info_callback("+++ Engine started +++", None, None, True)
    
    def engine_off(self):
        self.orbiters.get_current_orbiter().stop_engine()
        self.orbiters.get_current_orbiter().display_info(self.orbiters.time.t)
    
        if self.control_info_callback:
            self.control_info_callback("+++ Engine stopped +++", None, None, False)

    def set_thrust(self, thrust):
        self.orbiters.get_current_orbiter().display_info(self.orbiters.time.t)
        self.orbiters.get_current_orbiter().lock = None
        self.orbiters.get_current_orbiter().stages.set_thrust("ALL", thrust/100)

    def turn_right(self):
        self.orbiters.get_current_orbiter().display_info(self.orbiters.time.t)
        self.orbiters.get_current_orbiter().lock = None
        self.orbiters.get_current_orbiter().orientation1 -= pi/20

    def turn_left(self):
        self.orbiters.get_current_orbiter().display_info(self.orbiters.time.t)

        self.orbiters.get_current_orbiter().orientation1 += pi/20

    def drop_payload(self):
        self.orbiters.separate_stage(self.orbiters.get_current_orbiter(),"payload")
        print("-------------------\nDropping Payload")
        if self.control_info_callback:
            self.control_info_callback("--------Dropping Payload", None, None)

    def display_param(self):
        orbiter = self.orbiters.get_current_orbiter()
        print(orbiter.orbit.a, orbiter.orbit.e, orbiter.orbit.i, orbiter.orbit.arg_pe, orbiter.orbit.raan, orbiter.orbit.f)
        print(orbiter.r, orbiter.v)

    def quit(self):
        #new_event = pygame.event.Event(pygame.QUIT, unicode='a', key=ord('a'))
        #pygame.event.post(new_event)
        print("quit")

    def __init__(self, orbiters, event_listener):
        self.event_listener = event_listener
        self.orbiters = orbiters
        self.thrust = False
        self.control_info_callback = None
        self.event_listener.add_key_event(273,self.engine_on,"Start Engine")
        self.event_listener.add_key_event(274,self.engine_off,"Stop Engine")
        self.event_listener.add_key_event(275,self.turn_right,"Change Ship orientation (to the right)")
        self.event_listener.add_key_event(276,self.turn_left,"Change Ship orientation (to the left)")
        self.event_listener.add_key_event(122,self.display_param,"Print Kepler parameters")
        self.event_listener.add_key_event(32,self.drop_payload,"Drop payload")

        #self.event_listener.add_key_event(pygame.K_ESCAPE,self.quit,"Quit simulation")


