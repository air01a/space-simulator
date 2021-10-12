# THE UGLY part 

from math import e,pi, degrees, atan2,atan
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
    def init(self,spacetime):

        self.orbiters = spacetime.orbiters
        self.angle = 180


    def on_touch_down(self, touch):
        #self.size=(200,200)
        if self.collide_point(*touch.pos):
            y = (touch.y - self.center[1])
            x = (touch.x - self.center[0])
            calc = 0.5*degrees(atan2(y, x))
            self.prev_angle = calc if calc > 0 else 360+calc
            self.tmp = self.angle

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            y = (touch.y - self.center[1])
            x = (touch.x - self.center[0])
            calc = 0.5*degrees(atan2(y, x))
            new_angle = calc if calc > 0 else 360+calc

            self.angle = (self.tmp + (new_angle-self.prev_angle))%360
            print(self.angle)
            self.orbiters.get_current_orbiter().orientation1=(self.angle*2*pi/180+pi/2)%(2*pi)
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
            Color(r,g,b,a)
            Line(circle=(x,y,radius),width=1)
    
    def clear(self):
        self.canvas.clear()
    


    # Test of ellipse instruction for elliptic orbit
    # But not as fast as believed, and many problems due to orbit focus on focci
    # and ellipse is based on center, so too many angle convertion to be efficient
    def draw_trajectory_ellipse(self,dis, orbit,att_x,att_y,cartesien):
        perihelion, aphelion = orbit.get_limit()
        zoom_factor=dis.orbit_factor    

        a = orbit.a
        b = a * (1 - orbit.e**2)**0.5
        center = ( a**2 - b**2 )**0.5

        ellipse_x,ellipse_y = att_x + (center-a)*zoom_factor*dis.zoom_ratio, att_y-b*zoom_factor*dis.zoom_ratio
        
        with self.canvas:
            self.canvas.clear()
            PushMatrix()
            Color(200,200,200)
            angle = (orbit.arg_pe*180/pi % 360)
            if orbit.i>pi/2:
                angle = 180 - angle
            else:
                angle+=180
            
            #print(cartesien[0],cartesien[1]*180/pi)
            if cartesien[0].y!=0:
                vec = cartesien[0]
                angle = atan(abs(vec.y)/(abs(vec.x)-center))
                #anglemin = 90+(180+angle*180/pi)
                #anglemax = 360+90-(180+angle*180/pi)
                anglemin = 90 - abs(angle)*180/pi
                anglemax =  90 + abs(angle)*180/pi
            else:
                anglemin = 0
                anglemax = 359

            points = 300
            if (e>0.995):
                points *= 5
            Rotate(origin=(att_x,att_y),angle=angle)
            Line(ellipse=( ellipse_x, ellipse_y, 2*a*dis.zoom_ratio*zoom_factor, 2*b*dis.zoom_ratio*zoom_factor, anglemin,anglemax,points))
            Color(255,0,0)

            Line(points=[att_x, att_y, att_x+aphelion*dis.zoom_ratio*zoom_factor,att_y])
            Line(points=[att_x, att_y, att_x-perihelion*dis.zoom_ratio*zoom_factor,att_y])


            PopMatrix()
            Line(ellipse=(100,100,80,20,0, 240))

    # Draw trajectory of orbiter
    def draw_trajectory(self,dis,orbit,orbit_values,earth_x, earth_y,secondary=False):

        color_elipse = (200,200,200)
        color_lines  = (218,238,241)

        if len(orbit_values.points)<1:
            return

        max = orbit_values.aphelion
        min =  orbit_values.perihelion
        (x2,y2,z2)=orbit_values.points[0]

        with self.canvas:
            if not secondary:
                Color(color_elipse)
            else:
                Color(0,1,1)
            for (x,y,z) in orbit_values.points[1:-1]:
                (xc,yc) = dis.center_orbit( x,y, True, earth_x,earth_y)
                (x2,y2) = dis.center_orbit(x2,y2, True, earth_x,earth_y)
                Line(points=[xc,yc,x2,y2])

                (x2,y2) = (x,y)
            if secondary:
                Color(1,0,0)
            else:
                Color(1,0,0,0.3)
            if max!=None:
                (x,y) = dis.center_orbit(max.x,max.y, True, earth_x,earth_y)
                Line(points=[earth_x,earth_y,x,y])
            
            (x,y) = dis.center_orbit(min.x,min.y, True, earth_x,earth_y)
            Line(points=[earth_x,earth_y,x,y])
        #with self.canvas:
        #    Color(255,0,0)
        #    (x,y) = dis.center_orbit(min_x,min_y, True, earth_x,earth_y)
        #    Line(points=[x,y,earth_x,earth_y])
                
    
    def draw_velocity(self, x,y,x2,y2):
        with self.canvas:
            Color(0,0.5,0)
            Line(points=[x,y,x2,y2],width=4)

    def draw_ship(self, orbiter_x,orbiter_y,orientation):

        with self.canvas:
            if orientation!=None:
                Color(0,0,1)
                head_x = 8*np.cos(orientation)
                head_y = 8*np.sin(orientation)

                Ellipse(size=(15,15)).pos = (orbiter_x-7.5,orbiter_y-7.5)
                Color(1,0,0)

                Ellipse(size=(8,8)).pos = (orbiter_x+head_x-3,orbiter_y+head_y-3)

            else:
                Color(1,1,0)
                Ellipse(size=(5,5)).pos = (orbiter_x-2.5,orbiter_y-2.5)

 
class Graphics(BoxLayout):
    def on_orbiter_touch(self,direction):
        orbiters = self.orbiters.get_current_orbiter_names()
        self.orbiter_index+=direction
        if self.orbiter_index<0:
            self.orbiter_index = len(orbiters)-1
        
        if self.orbiter_index>=len(orbiters):
            self.orbiter_index = 0

        if self.orbiter_index >=0 :
            self.ids.orbiter_control.text = orbiters[self.orbiter_index]
        else:
            self.ids.orbiter_control.text = "None"
         
    def change_orbiter(self):
        self.orbiters.current_orbiter = self.ids.orbiter_control.text

    def init(self, world, zoom_ratio=1):
        self.orbiter_index=0
        self.goto = 'payload'
        self.orbiters = world.orbiters
        self.ids.orbiter_control.text = self.orbiters.get_current_orbiter_name()
        with self.canvas:
            #self.background = Rectangle(source = "images/galaxy.jpeg", size=Window.size,pos=self.pos)
            Color(0.44,   0.64, 0.94,0.20)
            self.earth_atmosphere  = Ellipse()
            Color(1,1, 1, 1)
            self.draw_trajectory = DrawTrajectory()
            self.add_widget(self.draw_trajectory)

            Color(1,1, 1, 1)

            #self.compas = Compas(world)
            #self.compas.draw()

            #self.add_widget(self.compas)
            self.ids.compas.init(world)
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
    
    def engine_on(self):
        self.world.pilot.engine_on()

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
            display_size = (6378140+120000)*self.orbit_factor*self.zoom_ratio
            self.earth_atmosphere.pos= (earth_x - display_size, earth_y - display_size)
            self.earth_atmosphere.size=(2*display_size,2*display_size)

            

            display_size = (soi)*self.orbit_factor*self.zoom_ratio
            self.draw_trajectory.clear()

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
            
            orbit_values = orbiter.orbit_projection.orbit_values
            if not moon:
                self.draw_trajectory.draw_trajectory(self,orbiter.orbit,orbit_values,earth_x,earth_y)
                #self.draw_trajectory.draw_trajectory(self,orbiter.orbit,earth_x,earth_y)
            else:
                self.draw_trajectory.draw_trajectory(self,orbiter.orbit,orbit_values,moon_x,moon_y)
                #self.draw_trajectory.draw_trajectory2(self,orbiter.orbit,moon_x,moon_y)

            self.draw_trajectory.draw_velocity(orbiter_x,orbiter_y,orbiter_x+orbiter.v.x/125,orbiter_y+orbiter.v.y/125)
            self.draw_trajectory.draw_ship(orbiter_x,orbiter_y,orbiter.orientation1)
            
            for orbiter_name in (orbiters.get_orbiters().keys()):
                if orbiter_name!=orbiters.current_orbiter:

                    orbiter2 = orbiters.get_orbiter(orbiter_name)
                    (orbiter2_x,orbiter2_y) = (orbiter2.r.x-tx, orbiter2.r.y-ty)
                    
                    if orbiter_name == self.goto:
                        orbit_values = orbiter2.orbit_projection.orbit_values

                        if orbiter2.attractor.name=='moon':
                            self.draw_trajectory.draw_trajectory(self,orbiter2.orbit,orbit_values,moon_x,moon_y,True)
                        else:
                            self.draw_trajectory.draw_trajectory(self,orbiter2.orbit,orbit_values,earth_x,earth_y, True)
                           

                    (orbiter_x, orbiter_y) = self.center_orbit(orbiter_x,orbiter_y)
                    self.draw_trajectory.draw_ship(orbiter_x,orbiter_y,None)
            
            