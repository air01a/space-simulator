import pygame
from pygame.locals import VIDEORESIZE

import numpy as np
from vector import Vector
BLUE  =       (  0,   0, 255)
RED   =       (255,   0,   0)
GREEN =       (  0, 200,   0)
BLACK =       (  0,   0,   0)
ORANGE =      (255, 165,   0)
DEFAULT_EARTH_SIZE = 111
GRAY  =       (105, 105, 105, 0.1)

class Display():
    def add_object(self, object):
        self.objects.append(object)

    def resize(self):
        self.width, self.height = pygame.display.Info().current_w, pygame.display.Info().current_h
        self.x_center = (self.width-self.earth_picture.get_width())/2
        self.y_center = (self.height-self.earth_picture.get_height())/2


    def zoom_out(self):
        self.zoom_ratio = self.zoom_ratio+1.0 if self.zoom_ratio>1 else self.zoom_ratio*1.1

        size = max(20, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio)))
        self.earth_picture = pygame.transform.scale(self.earth_main_sprite, (size,size))
        self.moon_picture = pygame.transform.scale(self.moon_main_sprite, (round(size*0.27), round(size*0.27)))

        self.x_center = (self.width-self.earth_picture.get_width())/2
        self.y_center = (self.height-self.earth_picture.get_height())/2
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

    def zoom_in(self):
        self.zoom_ratio = self.zoom_ratio-1.0 if self.zoom_ratio>1 else self.zoom_ratio*0.9
        
        size = max(20, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio)))
        self.earth_picture = pygame.transform.scale(self.earth_main_sprite, (size,size))
        self.moon_picture = pygame.transform.scale(self.moon_main_sprite, (round(size*0.27), round(size*0.27)))

        self.x_center = (self.width-self.earth_picture.get_width())/2
        self.y_center = (self.height-self.earth_picture.get_height())/2
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

    def change_center(self):
        self.ship_centered = not self.ship_centered

    def __init__(self, attractor, event_listener, zoom_ratio=1):
        pygame.init()

        self.objects = []
        self.size = self.width, self.height = 800, 800
        self.black = 0, 0, 0
        self.zoom_ratio = zoom_ratio+0.0
        self.earth_diameter = zoom_ratio*DEFAULT_EARTH_SIZE/2

        self.screen = pygame.display.set_mode(self.size,pygame.RESIZABLE)



        self.earth_main_sprite = pygame.image.load("images/earth.png")
        self.earth_picture = pygame.transform.scale(self.earth_main_sprite, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio)+1, round(DEFAULT_EARTH_SIZE*self.zoom_ratio)+1))
        self.earth = Vector(0,0,0)
        self.moon_main_sprite = pygame.image.load("images/moon.png")
        self.moon_picture = pygame.transform.scale(self.moon_main_sprite, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio*0.27)+1, round(DEFAULT_EARTH_SIZE*self.zoom_ratio*0.27)+1))



        self.resize()
        self.ship_centered = True
        self.orbit_factor = DEFAULT_EARTH_SIZE/(2*6378140)
        event_listener.add_key_event(112, self.change_center,"Change screen center (earth vs ship)")
        
        event_listener.add_key_event(97, self.zoom_out, "Zoom out")
        event_listener.add_key_event(113, self.zoom_in, "Zoom in")

        event_listener.add_event(VIDEORESIZE,self.resize)

    def center_orbit(self, x, y, force_earth_center=False,xearth=0,yearth=0):
        if not force_earth_center:
            x = (x*self.orbit_factor*self.zoom_ratio+self.x_center+self.earth_diameter)
            y = (-y*self.orbit_factor*self.zoom_ratio+self.y_center+self.earth_diameter)
        else :
            x = (x*self.orbit_factor*self.zoom_ratio + xearth)
            y = (-y*self.orbit_factor*self.zoom_ratio + yearth)

        return (x,y)


    def draw_trajectory(self,orbit,cartesien_orbit,earth_x, earth_y):
        color_elipse = (200,200,200)
        color_lines  = (218,238,241)
        if len(cartesien_orbit)<2:
            return
        max = cartesien_orbit[-1]
        (min_x, min_y, min_z) =  cartesien_orbit[-2]
        if orbit.e<1 and len(cartesien_orbit)>3:
            (x2,y2,z2)=cartesien_orbit[-3]
        else:
            (x2,y2,z2)=cartesien_orbit[0]

        for (x,y,z) in cartesien_orbit[:-2]:
            # - y car dans ellipse, y vers le haut, dans plan y vers le bas
            (xc,yc) = self.center_orbit( x,y, True, earth_x,earth_y)
            (x2,y2) = self.center_orbit(x2,y2, True, earth_x,earth_y)
            pygame.draw.line(self.screen,color_elipse,(xc,yc),(x2,y2))
            
            #pygame.draw.line(self.screen,color_lines,(xc,yc),(earth_x,earth_y))
            (x2,y2) = (x,y)
        
        pygame.draw.line(self.screen,RED,self.center_orbit(min_x,min_y, True, earth_x,earth_y),(earth_x,earth_y))
        if max!=None:
            (max_x,max_y,max_z) = max
            pygame.draw.line(self.screen,RED,self.center_orbit(max_x,max_y, True, earth_x,earth_y),(earth_x,earth_y))

    def draw(self, orbiters):
        self.screen.fill(BLACK)

        orbiter = orbiters.get_current_orbiter()
        if orbiter == None:
            return
        (earth_x, earth_y) = (0,0)
        (orbiter_x,orbiter_y) = (orbiter.r.x, orbiter.r.y)

        if len(orbiter.attractor.child)==1:
            (moon_x,moon_y) = (orbiter.attractor.child[0].r.x,orbiter.attractor.child[0].r.y)
            soi = orbiter.attractor.child[0].soi
            moon = False
        else:
            (moon_x,moon_y) = (orbiter.attractor.r.x,orbiter.attractor.r.y)
            soi = orbiter.attractor.soi
            orbiter_x += moon_x
            orbiter_y += moon_y
            moon = True
        translate = (0,0)


        if self.ship_centered:
            translate = (orbiter_x,orbiter_y)

            (earth_x, earth_y) = (-orbiter_x,-orbiter_y)
            (orbiter_x,orbiter_y) = (0,0)

        (tx,ty) = translate

        (earth_x, earth_y) = self.center_orbit(earth_x,earth_y)
        (orbiter_x, orbiter_y) = self.center_orbit(orbiter_x,orbiter_y)
        (moon_x, moon_y) = self.center_orbit(moon_x-tx,moon_y-ty)

        pygame.draw.circle(self.screen, BLUE, (earth_x,earth_y), (6378140+120000)*self.orbit_factor*self.zoom_ratio)
        
        pygame.draw.circle(self.screen, BLUE, (earth_x,earth_y), (384000000-66100000)*self.orbit_factor*self.zoom_ratio,1)
        pygame.draw.circle(self.screen, BLUE, (earth_x,earth_y), (384000000+66100000)*self.orbit_factor*self.zoom_ratio,1)


        cartesien_orbit = orbiter.orbit.cartesien
        if not moon:
            self.draw_trajectory(orbiter.orbit,cartesien_orbit,earth_x,earth_y)
        else:
            self.draw_trajectory(orbiter.orbit,cartesien_orbit,moon_x,moon_y)

        pygame.draw.circle(self.screen, GRAY, (int(moon_x),int(moon_y)), (soi)*self.orbit_factor*self.zoom_ratio,1)
        self.screen.blit(self.moon_picture, (int(moon_x- self.earth_diameter*0.27),int(moon_y- self.earth_diameter*0.27)))

        self.earth.x = earth_x - self.earth_diameter
        self.earth.y = earth_y - self.earth_diameter


        self.screen.blit(self.earth_picture, (self.earth.x,self.earth.y))



        pygame.draw.circle(self.screen, GREEN, (orbiter_x,orbiter_y), 5)

        head_x = 5*np.cos(orbiter.orientation1)
        head_y = -5*np.sin(orbiter.orientation1)

        pygame.draw.circle(self.screen, RED, (orbiter_x+head_x,orbiter_y+head_y), 2)
        pygame.draw.line(self.screen, GREEN, (orbiter_x,orbiter_y),(orbiter_x+orbiter.v.x/125,orbiter_y-orbiter.v.y/125), int(2))


        for orbiter_name in (orbiters.get_orbiters().keys()):
            if orbiter_name!=orbiters.current_orbiter:
                orbiter = orbiters.get_orbiter(orbiter_name)
                (orbiter_x,orbiter_y) = (orbiter.r.x-tx, orbiter.r.y-ty)
                
                (orbiter_x, orbiter_y) = self.center_orbit(orbiter_x,orbiter_y)
                pygame.draw.circle(self.screen, ORANGE, (orbiter_x,orbiter_y), 3)
        pygame.display.flip()

