import pygame
from numpy import pi

class PilotOrbiter:

    def engine_on(self):
        self.thrust = True
    
    def engine_off(self):
        self.thrust = False
    
    def turn_right(self):
        self.orbiter.orientation1 -= pi/20

    def turn_left(self):
        self.orbiter.orientation1 += pi/20
         
    def display_param(self):
        print(self.orbiter.orbit.a, self.orbiter.orbit.e, self.orbiter.orbit.i, self.orbiter.orbit.arg_pe, self.orbiter.orbit.raan, self.orbiter.orbit.f)

    def quit(self):
        new_event = pygame.event.Event(pygame.QUIT, unicode='a', key=ord('a'))
        pygame.event.post(new_event)

    def __init__(self, orbiter, event_listener):
        self.event_listener = event_listener
        self.orbiter = orbiter
        self.thrust = False
        self.event_listener.add_key_event(pygame.K_UP,self.engine_on)
        self.event_listener.add_key_event(pygame.K_DOWN,self.engine_off)
        self.event_listener.add_key_event(pygame.K_RIGHT,self.turn_right)
        self.event_listener.add_key_event(pygame.K_LEFT,self.turn_left)
        self.event_listener.add_key_event(pygame.K_ESCAPE,self.quit)
        self.event_listener.add_key_event(pygame.K_ESCAPE,self.quit)
        self.event_listener.add_key_event(pygame.K_z,self.display_param)


