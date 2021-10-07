########################################
# Use keyboard to orient rocket
########################################
from numpy import pi

class PilotOrbiter:

    def engine_on(self):
        self.orbiters.get_current_orbiter().stages.set_thrust("ALL",1)
        self.orbiters.get_current_orbiter().thrust = True
    
    def engine_off(self):
        self.orbiters.get_current_orbiter().thrust = False
    
    def turn_right(self):

        self.orbiters.get_current_orbiter().orientation1 -= pi/20

    def turn_left(self):
        self.orbiters.get_current_orbiter().orientation1 += pi/20

    def drop_payload(self):
        self.orbiters.separate_stage(self.orbiters.get_current_orbiter(),"payload")
        print("-------------------\nDropping Payload")

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
        self.event_listener.add_key_event(273,self.engine_on,"Start Engine")
        self.event_listener.add_key_event(274,self.engine_off,"Stop Engine")
        self.event_listener.add_key_event(275,self.turn_right,"Change Ship orientation (to the right)")
        self.event_listener.add_key_event(276,self.turn_left,"Change Ship orientation (to the left)")
        self.event_listener.add_key_event(122,self.display_param,"Print Kepler parameters")
        self.event_listener.add_key_event(32,self.drop_payload,"Drop payload")

        #self.event_listener.add_key_event(pygame.K_ESCAPE,self.quit,"Quit simulation")


