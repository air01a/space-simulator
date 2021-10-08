# THE UGLY part 

from math import e,pi, degrees, atan2
from kivy.graphics import *
from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
import numpy as np
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from vector import Vector

DEFAULT_EARTH_SIZE = 111
BLUE  =       (  0,   0, 1, 1)
RED   =       (255,   0,   0)
GREEN =       (  0, 200,   0)
BLACK =       (  0,   0,   0)
ORANGE =      (255, 165,   0)
DEFAULT_EARTH_SIZE = 111
GRAY  =       (105, 105, 105, 0.1)



class Compas(Button):
    def __init__(self,**kwargs):
        super(Compas, self).__init__(**kwargs)

        #self.orbiters = spacetime.orbiters
        self.angle = 180
        
    def set_param(self,spacetime):
        self.orbiters = spacetime.orbiters
        self.angle = 180



    def on_touch_down(self, touch):
        #self.size=(200,200)
        if self.collide_point(*touch.pos):
            y = (touch.y - self.center[1])
            x = (touch.x - self.center[0])
            calc = degrees(atan2(y, x))
            self.prev_angle = calc if calc > 0 else 360+calc
            self.tmp = self.angle

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            y = (touch.y - self.center[1])
            x = (touch.x - self.center[0])
            calc = 10*degrees(atan2(y, x))
            new_angle = calc if calc > 0 else 360+calc

            self.angle = (self.tmp - (new_angle-self.prev_angle))%360
            print(self.angle)
            #self.orbiters.get_current_orbiter().orientation1=(self.angle*2*pi/180+pi/2)%(2*pi)
            self.draw()

    def on_touch_up(self, touch):
        #Animation(angle=0).start(self)
        self.draw()

    def draw(self):
        with self.canvas.before:
            PushMatrix()
            Rotate(origin=(120,Window.height-60), angle=-self.angle-90)
            PopMatrix()

    def repos(self):
        self.canvas.clear()
        self.draw()    


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
    
    def draw_velocity(self, x,y,x2,y2):
        with self.canvas:
            Color(0,0.5,0)
            Line(points=[x,y,x2,y2],width=4)

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

 
class Graphics(BoxLayout):

    def init(self, world, zoom_ratio=1):
        self.orbiters = world.orbiters
        with self.canvas:
            #self.background = Rectangle(source = "images/galaxy.jpeg", size=Window.size,pos=self.pos)
            Color(0,   0, 255)
            self.earth_atmosphere  = Ellipse()
            Color(1,1, 1, 1)

            self.draw_trajectory = DrawTrajectory()
            self.add_widget(self.draw_trajectory)
            Color(1,1, 1, 1)

            #self.compas = Compas(world)
            #self.compas.draw()

            #self.add_widget(self.compas)
            self.earth_main_sprite = Rectangle(source = "images/earth.png")
            self.moon_main_sprite  = Rectangle(source = "images/moon.png")

        self.width, self.height = Window.size
        self.zoom_ratio = zoom_ratio+0.0
        self.earth_diameter = zoom_ratio*DEFAULT_EARTH_SIZE/2

        self.earth = Vector(0,0,0)
        self.ship_centered = True
        self.orbit_factor = DEFAULT_EARTH_SIZE/(2*6378140)
        self.x_center  = self.width/2-self.earth_diameter 
        self.y_center  = self.height/2-self.earth_diameter 
        world.event_listener.add_key_event(112, self.change_center,"Change screen center (earth vs ship)")
        
        world.event_listener.add_key_event(97, self.zoom_out, "Zoom out")
        world.event_listener.add_key_event(113, self.zoom_in, "Zoom in")
        self.world=world
    
    def zoom_out(self):
        self.zoom_ratio = self.zoom_ratio+1.0 if self.zoom_ratio>1 else self.zoom_ratio*1.1

        size = max(20, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio)))
        
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

        self.x_center = (self.width/2-self.earth_diameter)
        self.y_center = (self.height/2-self.earth_diameter)

    def zoom_in(self):
        self.zoom_ratio = self.zoom_ratio-1.0 if self.zoom_ratio>1 else self.zoom_ratio*0.9
        
        size = max(20, (round(DEFAULT_EARTH_SIZE*self.zoom_ratio)))
        
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2
        self.x_center = (self.width/2-self.earth_diameter)
        self.y_center = (self.height/2-self.earth_diameter)
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

    def change_center(self):
        self.ship_centered = not self.ship_centered


    def update(self, *args):
        self.width, self.height = Window.size
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

        self.x_center  = self.width/2-self.earth_diameter 
        self.y_center  = self.height/2-self.earth_diameter 
        self.background.size = Window.size
        self.compas.repos()


    def center_orbit(self, x, y, force_earth_center=False,xearth=0,yearth=0):
        if not force_earth_center:
            x = (x*self.orbit_factor*self.zoom_ratio+self.x_center+self.earth_diameter)
            y = (y*self.orbit_factor*self.zoom_ratio+self.y_center+self.earth_diameter)
        else :
            x = (x*self.orbit_factor*self.zoom_ratio + xearth)
            y = (y*self.orbit_factor*self.zoom_ratio + yearth)

        return (x,y)

    def draw(self,dt):
        #self.update()
        orbiters = self.world.orbiters
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

            self.earth.x = earth_x - self.earth_diameter
            self.earth.y = earth_y - self.earth_diameter

            self.earth_main_sprite.pos   = (self.earth.x,self.earth.y)
            self.earth_main_sprite.size  = (self.earth_diameter*2,self.earth_diameter*2)
            self.draw_trajectory.draw_velocity(orbiter_x,orbiter_y,orbiter_x+orbiter.v.x/125,orbiter_y+orbiter.v.y/125)

            self.draw_trajectory.draw_ship(orbiter_x,orbiter_y,orbiter.orientation1)



            for orbiter_name in (orbiters.get_orbiters().keys()):
                if orbiter_name!=orbiters.current_orbiter:
                    orbiter = orbiters.get_orbiter(orbiter_name)
                    (orbiter_x,orbiter_y) = (orbiter.r.x-tx, orbiter.r.y-ty)
                    
                    (orbiter_x, orbiter_y) = self.center_orbit(orbiter_x,orbiter_y)
                    self.draw_trajectory.draw_ship(orbiter_x,orbiter_y,None)
