from math import e
from kivy.graphics import *
from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window

import numpy as np
from vector import Vector

DEFAULT_EARTH_SIZE = 111
BLUE  =       (  0,   0, 1, 1)
RED   =       (255,   0,   0)
GREEN =       (  0, 200,   0)
BLACK =       (  0,   0,   0)
ORANGE =      (255, 165,   0)
DEFAULT_EARTH_SIZE = 111
GRAY  =       (105, 105, 105, 0.1)

class WindowsViewer:
    def __init__(self):
        self.center = (0,0)
        self.size = 100000


class DrawTrajectory(Widget):

    def draw_soi(self,x,y,radius,color):
        (r,g,b,a)=color
        with self.canvas:
            Color(r,b,b,a)
            Line(circle=(x,y,radius),width=1)
    
    def draw_trajectory(self,dis,orbit,cartesien_orbit,earth_x, earth_y):
        self.canvas.clear()
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
            (xc,yc) = dis.center_orbit( x,y, True, earth_x,earth_y)
            (x2,y2) = dis.center_orbit(x2,y2, True, earth_x,earth_y)
            with self.canvas:
                Color(color_elipse)
                Line(points=[xc,yc,x2,y2])
            

            (x2,y2) = (x,y)
        with self.canvas:
            Color(255,0,0)
            (x,y) = dis.center_orbit(min_x,min_y, True, earth_x,earth_y)
            Line(points=[x,y,earth_x,earth_y])
            if max!=None:
                (max_x,max_y,max_z) = max
                (max_x,max_y) = dis.center_orbit(max_x,max_y, True, earth_x,earth_y)
                Line(points=[max_x,max_y, earth_x,earth_y])
    

    def draw_ship(self, orbiter_x,orbiter_y,orientation):

        with self.canvas:
            if orientation!=None:
                Color(0,0,1)
                head_x = 5*np.cos(orientation)
                head_y = 5*np.sin(orientation)

                Ellipse(size=(15,15)).pos = (orbiter_x-7.5,orbiter_y-7.5)
                Color(1,0,0)

                Ellipse(size=(5,5)).pos = (orbiter_x+head_x,orbiter_y+head_y)

            else:
                Color(1,1,0)
                Ellipse(size=(5,5)).pos = (orbiter_x-2.5,orbiter_y-2.5)

 
class Graphics(Widget):

    def __init__(self, orbiters,event_listener, zoom_ratio=1):
        super(Graphics, self).__init__()
        self.orbiters = orbiters

        with self.canvas:
            
            
            Color(0,   0, 255)
            self.earth_atmosphere  = Ellipse()
            Color(1,1, 1, 1)

            self.earth_main_sprite = Rectangle(source = "images/earth.png")
            self.moon_main_sprite  = Rectangle(source = "images/moon.png")

        self.size = self.width, self.height = Window.size
        self.zoom_ratio = zoom_ratio+0.0
        self.earth_diameter = zoom_ratio*DEFAULT_EARTH_SIZE/2

        self.earth = Vector(0,0,0)
        self.ship_centered = True
        self.orbit_factor = DEFAULT_EARTH_SIZE/(2*6378140)
        self.x_center  = self.width/2-self.earth_diameter 
        self.y_center  = self.height/2-self.earth_diameter 

        self.draw_trajectory = DrawTrajectory()
        self.add_widget(self.draw_trajectory)


        self.bind(pos=self.update)
        self.bind(size=self.update)
        event_listener.add_key_event(112, self.change_center,"Change screen center (earth vs ship)")
        
        event_listener.add_key_event(97, self.zoom_out, "Zoom out")
        event_listener.add_key_event(113, self.zoom_in, "Zoom in")    
    
    def zoom_out(self):
        self.zoom_ratio = self.zoom_ratio+1.0 if self.zoom_ratio>1 else self.zoom_ratio*1.1

        size = max(20, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio)))
        
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

        self.x_center = (self.width-self.earth_diameter)/2
        self.y_center = (self.height-self.earth_diameter)/2

    def zoom_in(self):
        self.zoom_ratio = self.zoom_ratio-1.0 if self.zoom_ratio>1 else self.zoom_ratio*0.9
        
        size = max(20, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio)))
        
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2
        self.x_center = (self.width-self.earth_diameter)/2
        self.y_center = (self.height-self.earth_diameter)/2
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

    def change_center(self):
        self.ship_centered = not self.ship_centered


    def update(self, *args):
        self.size = self.width, self.height = Window.size
        self.x_center  = self.width/2-self.earth_diameter 
        self.y_center  = self.height/2-self.earth_diameter 


    def center_orbit(self, x, y, force_earth_center=False,xearth=0,yearth=0):
        if not force_earth_center:
            x = (x*self.orbit_factor*self.zoom_ratio+self.x_center+self.earth_diameter)
            y = (y*self.orbit_factor*self.zoom_ratio+self.y_center+self.earth_diameter)
        else :
            x = (x*self.orbit_factor*self.zoom_ratio + xearth)
            y = (y*self.orbit_factor*self.zoom_ratio + yearth)

        return (x,y)

    


    def draw(self):
        orbiters = self.orbiters
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



        with self.canvas:
            self.earth_atmosphere.pos= (earth_x- self.earth_diameter/2,earth_y- self.earth_diameter/2)
            display_size = (6378140+120000)*self.orbit_factor*self.zoom_ratio
            self.earth_atmosphere.size=(display_size,display_size)


            cartesien_orbit = orbiter.orbit.cartesien
            if not moon:
                self.draw_trajectory.draw_trajectory(self,orbiter.orbit,cartesien_orbit,earth_x,earth_y)
            else:
                self.draw_trajectory.draw_trajectory(self,orbiter.orbit,cartesien_orbit,moon_x,moon_y)

            display_size = (soi)*self.orbit_factor*self.zoom_ratio

            self.draw_trajectory.draw_soi(int(moon_x),int(moon_y),display_size,BLUE)
            self.draw_trajectory.draw_soi(earth_x,earth_y, (384000000-66100000)*self.orbit_factor*self.zoom_ratio,BLUE)
            self.draw_trajectory.draw_soi(earth_x,earth_y, (384000000+66100000)*self.orbit_factor*self.zoom_ratio,BLUE)
          
            display_size = (round(DEFAULT_EARTH_SIZE*self.zoom_ratio*0.27))
            self.moon_main_sprite.pos = int(moon_x)-display_size/2,int(moon_y)-display_size/2
            self.moon_main_sprite.size = (display_size,display_size)

            self.earth.x = earth_x - self.earth_diameter/2
            self.earth.y = earth_y - self.earth_diameter/2

            self.earth_main_sprite.pos   = (self.earth.x,self.earth.y)
            self.earth_main_sprite.size  = (self.earth_diameter,self.earth_diameter)

            self.draw_trajectory.draw_ship(orbiter_x,orbiter_y,orbiter.orientation1)



            for orbiter_name in (orbiters.get_orbiters().keys()):
                if orbiter_name!=orbiters.current_orbiter:
                    orbiter = orbiters.get_orbiter(orbiter_name)
                    (orbiter_x,orbiter_y) = (orbiter.r.x-tx, orbiter.r.y-ty)
                    
                    (orbiter_x, orbiter_y) = self.center_orbit(orbiter_x,orbiter_y)
                    self.draw_trajectory.draw_ship(orbiter_x,orbiter_y,None)
