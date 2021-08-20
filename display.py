import pygame
import numpy as np

BLUE  =       (  0,   0, 255)
RED   =       (255,   0,   0)
GREEN =       (  0, 200,   0)
BLACK =       (  0,   0,   0)
class Display():
    def zoom_out(self):
        self.zoom_ratio +=0.05
        self.picture = pygame.transform.scale(self.earth_main_sprite, (int(111*self.zoom_ratio), int(111*self.zoom_ratio)))
        self.earth = self.picture.get_rect()
        self.earth.x = (self.width-self.picture.get_width())/2
        self.earth.y = (self.height-self.picture.get_height())/2
        self.earth_diameter = self.zoom_ratio*111/2
        refresh=True


    def zoom_in(self):
        self.zoom_ratio = self.zoom_ratio-0.1 if self.zoom_ratio>0.1 else self.zoom_ratio
        self.picture = pygame.transform.scale(self.earth_main_sprite, (int(111*self.zoom_ratio), int(111*self.zoom_ratio)))
        self.earth = self.picture.get_rect()
        self.earth.x = (self.width-self.picture.get_width())/2
        self.earth.y = (self.height-self.picture.get_height())/2
        self.earth_diameter = self.zoom_ratio*111/2
        refresh=True

    def __init__(self, event_listener, zoom_ratio=1):
        pygame.init()

        self.size = self.width, self.height = 800, 800
        self.black = 0, 0, 0
        self.zoom_ratio = zoom_ratio
        self.earth_diameter = zoom_ratio*111/2

        self.screen = pygame.display.set_mode(self.size,pygame.RESIZABLE)
        self.earth_main_sprite = pygame.image.load("images/earth.png")
        self.picture = pygame.transform.scale(self.earth_main_sprite, (111*self.zoom_ratio, 111*self.zoom_ratio))
        self.earth = self.picture.get_rect()

        self.width, self.height = pygame.display.Info().current_w, pygame.display.Info().current_h
        self.earth.x = (self.width-self.picture.get_width())/2
        self.earth.y = (self.height-self.picture.get_height())/2

        self.orbit_factor = 111/(2*6378140)
        event_listener.add_key_event(97, self.zoom_out)
        event_listener.add_key_event(113, self.zoom_in)

    def draw(self, orbiter, cartesien_orbit):
        self.screen.fill(BLACK)

        atmosphere = (self.earth.x+self.earth_diameter,self.earth.y+self.earth_diameter)
        pygame.draw.circle(self.screen, BLUE, atmosphere, (6378140+120000)*self.orbit_factor*self.zoom_ratio)


        (x2,y2,z2)=cartesien_orbit[-1]
        color=(100,100,100)
        for (x,y,z) in cartesien_orbit:
            # - y car dans ellipse, y vers le haut, dans plan y vers le bas
            pygame.draw.line(self.screen,color,(x*self.orbit_factor*self.zoom_ratio+self.earth.x+self.earth_diameter,-y*self.orbit_factor*self.zoom_ratio+self.earth.y+self.earth_diameter),(x2*self.orbit_factor*self.zoom_ratio+self.earth.x+self.earth_diameter,-y2*self.orbit_factor*self.zoom_ratio+self.earth.y+self.earth_diameter))
            color=(200,200,200)
            (x2,y2) = (x,y)
        
        self.screen.blit(self.picture, self.earth)

        orbiter_x = orbiter.r.x*self.orbit_factor*self.zoom_ratio+self.earth.x+self.earth_diameter
        orbiter_y = -orbiter.r.y*self.orbit_factor*self.zoom_ratio+self.earth.y+self.earth_diameter
        pygame.draw.circle(self.screen, BLUE, (orbiter_x,orbiter_y), 5)

        head_x = 5*np.cos(orbiter.orientation1)
        head_y = -5*np.sin(orbiter.orientation1)

        pygame.draw.circle(self.screen, RED, (orbiter_x+head_x,orbiter_y+head_y), 2)
        refresh = True
        pygame.draw.line(self.screen, GREEN, (orbiter_x,orbiter_y),(orbiter_x+orbiter.v.x/125,orbiter_y-orbiter.v.y/125), int(2))

        pygame.display.flip()

