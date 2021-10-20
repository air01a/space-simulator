# THE UGLY part 

from math import e,pi, degrees, atan2,atan, log
from kivy.graphics import *
from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
import numpy as np
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import time
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
        self.tmp = 180


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
        self.canvas.before.clear()
        self.canvas.clear()

    


    # Draw trajectory of orbiter
    def draw_trajectory(self,dis,orbit,orbit_values,earth_x, earth_y,secondary=False):

        color_elipse = (200,200,200)
        color_lines  = (218,238,241)

        if not orbit_values or len(orbit_values.points)<1:
            return

        max = orbit_values.aphelion
        min =  orbit_values.perihelion
        (x2,y2,z2)=orbit_values.points[0]

        with self.canvas.before:
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

                
    
    def draw_velocity(self, x,y,x2,y2):
        with self.canvas.before:
            Color(0,0.5,0)
            Line(points=[x,y,x2,y2],width=4)

    def draw_ship(self, orbiter_x,orbiter_y,orientation):

        with self.canvas.before:
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

    def drop_payload(self):
        self.world.pilot.drop_payload()

    def init(self, world, zoom_ratio=1):
        self.lock = False
        self.orbiter_index=0
        self.goto = None
        self.orbiters = world.orbiters
        self.ids.orbiter_control.text = self.orbiters.get_current_orbiter_name()
        with self.canvas.before:
            Color(0.44,   0.64, 0.94,0.20)
            self.earth_atmosphere  = Ellipse()
            Color(1,1, 1, 1)
            self.draw_trajectory = DrawTrajectory()
            self.add_widget(self.draw_trajectory)
            Color(1,1, 1, 1)
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
        self.world.controller.add_control_callback(self.control_info)
        self.world.pilot.control_info_callback = self.control_info
        self.world.time_controller.on_change_callback = self.set_time_slider
        self.set_zoom_display()
        
    def control_info(self,message,thrust, orientation, engine=None):
        if message:
            self.parent.parent.ids.controlInfoLabel.text = message
        elif thrust!=None and orientation!= None :
            self.parent.parent.ids.controlInfoLabel.text = "+++ Attitude Control Angle %s +++" % str(orientation)
        elif message!=None:
            print(message, thrust, orientation)

        if engine!=None:
            self.ids.switch.active=engine

    def engine_on(self,active):
        if active:
            self.world.pilot.engine_on()
        else:
            self.world.pilot.engine_off()

    def drop_stage(self):
        self.orbiters.separate_full_stage(self.orbiters.get_current_orbiter())
        self.engine_on(False)

    def adapt_zoom(self):
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2
        self.x_center = (self.width/2-self.earth_diameter)
        self.y_center = (self.height/2-self.earth_diameter)
        

    def change_zoom(self, value):
        while self.lock:
            time.sleep(0.01)
        value = 10 - value
        if value<0:
            self.zoom_ratio = 1 / 1.1**abs(value)
        else:
            self.zoom_ratio = 1 + 2**abs(value)
        self.adapt_zoom()

    def set_zoom_display(self):
        if self.zoom_ratio<1:
            value = 10 + log(1/self.zoom_ratio)/log(1.1)
        else:
            value = 10 + log(self.zoom_ratio-1)/log(2)
        self.ids.zoom.value = value
        

    def zoom_out(self):
        while self.lock:
            time.sleep(0.01)
        self.zoom_ratio = self.zoom_ratio+1.0 if self.zoom_ratio>1 else self.zoom_ratio*1.1        
        self.adapt_zoom()
        self.set_zoom_display() 

    def zoom_in(self):
        while self.lock:
            time.sleep(0.01)
        self.zoom_ratio = self.zoom_ratio-1.0 if self.zoom_ratio>1 else self.zoom_ratio*0.9        
        self.adapt_zoom()
        self.set_zoom_display() 

    def change_center(self):
        self.ship_centered = not self.ship_centered


    def update(self, *args):
        self.width, self.height = Window.size
        self.earth_diameter = self.zoom_ratio*DEFAULT_EARTH_SIZE/2

        self.x_center  = self.width/2-self.earth_diameter 
        self.y_center  = self.height/2-self.earth_diameter 

    def change_thrust(self, value):
        self.world.pilot.set_thrust(value)


    def change_time(self, value):
        if value<10:
            self.world.time_controller.t_increment = value
        else:
            self.world.time_controller.t_increment = 5*(1.2**value)


    def set_time_slider(self, value):
        if value>10:
            value = int(log(value/5)/log(1.2))
        self.ids.time.value = value

    def center_orbit(self, x, y, force_earth_center=False,xearth=0,yearth=0):
        if not force_earth_center:
            x = (x*self.orbit_factor*self.zoom_ratio+self.x_center+self.earth_diameter)
            y = (y*self.orbit_factor*self.zoom_ratio+self.y_center+self.earth_diameter)
        else :
            x = (x*self.orbit_factor*self.zoom_ratio + xearth)
            y = (y*self.orbit_factor*self.zoom_ratio + yearth)

        return (x,y)

    def draw(self,dt):
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


        self.lock = True
        self.draw_trajectory.clear()

        with self.canvas.before:
            display_size = (6378140+120000)*self.orbit_factor*self.zoom_ratio
            self.earth_atmosphere.pos= (earth_x - display_size, earth_y - display_size)
            self.earth_atmosphere.size=(2*display_size,2*display_size)

            

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
                           

                    (orbiter2_x, orbiter2_y) = self.center_orbit(orbiter2_x,orbiter2_y)
                    self.draw_trajectory.draw_ship(orbiter2_x,orbiter2_y,None)
            self.lock = False

            