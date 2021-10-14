########################################
# Flight path management
########################################


import threading
import time
from orbiter import Orbiter, Stages, Stage_Composant, Orbiters
from math import pi
import json
from vector import Vector


class Controller:

    def control_flight_path(self, orbiter):
        if len(self.attitude_control)>0:
            (param,alt,control,throttle) = self.attitude_control[0]
        else:
            return
        
        altitude = (orbiter.r.norm() - orbiter.attractor.radius)/1000
        (perigee,apogee) = orbiter.orbit.get_limit()
        perigee = int((perigee-orbiter.attractor.radius)/1000)
        apogee = int((apogee - orbiter.attractor.radius)/1000)
        perigee = max(0,perigee)
        apogee = max(0,apogee)
        velocity = orbiter.v.norm()/1000
        if  ((param == 'alt'         and altitude > alt) or
            (param == 'perihelion'  and perigee  > alt) or
            (param == 'aphelion'    and apogee   > alt) or
            (param == 'velocity'    and velocity   > alt) or
            (param == 'time'        and self.time.t > alt)):

            if self.control_info_callback:
                self.control_info_callback("+++ Attitude Control Angle %i +++" % int(control))
            self.attitude_control.pop(0)
            orbiter.orientation1 = control * pi / 180
            orbiter.stages.set_thrust("ALL",throttle/100)
                
        if len(orbiter.stages.empty_part)>0 and (len(orbiter.stages.stages)>1):
            while len(orbiter.stages.empty_part)>0:
                part_name = orbiter.stages.empty_part.pop(0)
                self.orbiters.separate_stage(orbiter,part_name)
                print("--------------------------------\n----  Separating %s"%part_name)
                if self.control_info_callback:
                    self.control_info_callback( "----  Separating %s"%part_name)

    def showControl(self):
        alt = None
        last_t = -1
        print("time;thrust;altitude;velocity;carburant;(perihelion,aphelion)")
        if len(self.attitude_control)>0:
            (param,alt,control,throttle) = self.attitude_control.pop(0)
        

        while not self.finish:
            orbiter = self.orbiters.get_current_orbiter()
            if orbiter==None:
                return
            altitude = (orbiter.r.norm() - orbiter.attractor.radius)/1000
            (perigee,apogee) = orbiter.orbit.get_limit()
            perigee = int((perigee-orbiter.attractor.radius)/1000)
            apogee = int((apogee - orbiter.attractor.radius)/1000)
            perigee = max(0,perigee)
            apogee = max(0,apogee)
            velocity = orbiter.v.norm()/1000
            if alt != None:
                if  ((param == 'alt'         and altitude > alt) or
                    (param == 'perihelion'  and perigee  > alt) or
                    (param == 'aphelion'    and apogee   > alt) or
                    (param == 'velocity'    and velocity   > alt) or
                    (param == 'time'        and self.time.t > alt)):
                    if self.control_info_callback:
                        self.control_info_callback("+++ Attitude Control Angle %i +++" % int(control))
                    print("+++++++++++++++++++++++++")
                    print("+++ Attitude Control +++")
                    print("Angle %i" % int(control))
                    print("+++++++++++++++++++++++++")

                    orbiter.orientation1 = control * pi / 180
                    orbiter.stages.set_thrust("ALL",throttle/100)
                    if len(self.attitude_control)>0:
                        (param,alt,control,throttle) = self.attitude_control.pop(0)

                    else:
                        alt = None

            
            #print("%is %.2fkN %.2fkm %.2fkm/s %ikg %ideg [%ikm, %ikm]"%(int(self.time.t),orbiter.thrust,altitude, velocity,int(orbiter.stages.get_carburant_mass()),int(orbiter.orientation1*180/3.141592),perigee,apogee))
            if len(orbiter.stages.empty_part)>0 and (len(orbiter.stages.stages)>1):
                while len(orbiter.stages.empty_part)>0:
                    part_name = orbiter.stages.empty_part.pop(0)
                    self.orbiters.separate_stage(orbiter,part_name)
                    print("--------------------------------\n----  Separating %s"%part_name)
                    if self.control_info_callback:
                        self.control_info_callback( "----  Separating %s"%part_name)
            last_t = self.time.t
            if self.time.t_increment==0:
                time.sleep(1)
            else:
                time.sleep(0.1)
            if self.time.t == last_t:
                self.finish = True

    def get_info(self):
        orbiter = self.orbiters.get_current_orbiter()
        altitude = (orbiter.r.norm() - orbiter.attractor.radius)/1000
        (perigee,apogee) = orbiter.orbit.get_limit()
        perigee = int((perigee-orbiter.attractor.radius)/1000)
        apogee = int((apogee - orbiter.attractor.radius)/1000)
        perigee = max(0,perigee)
        apogee = max(0,apogee)
        velocity = orbiter.v.norm()/1000
        info =  "%is %.2fkN %.2fkm %.2fkm/s %ikg %ideg [%ikm, %ikm]"%(int(self.time.t),orbiter.thrust,altitude, velocity,int(orbiter.stages.get_carburant_mass()),int(orbiter.orientation1*180/3.141592),perigee,apogee)
        return info

    

    def __init__(self, flight_path, orbiters, timecontroller,control_info = None):
        self.orbiters = orbiters
        self.time = timecontroller
        self.finish = False
        self.control_info_callback = control_info
        with open(flight_path) as json_file:
            data = json.load(json_file)
            self.attitude_control = data['flight_path']

            #self.attitude_control = []


            orbiter = self.orbiters.get_current_orbiter()
            r = v = Vector(0,0,0)
            if ('r' in data.keys()):
                r = Vector(data['r'])
            if ('v' in data.keys()):
                v = Vector(data['v'])
            orbiter.set_state(r,v,0)


        #self.thread = threading.Thread(target=self.showControl)
        #self.thread.start()

    def stop(self):
        self.finish = True


    def __del__(self):
        print("desturcteur")
        self.stop()