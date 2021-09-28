import threading
import time
from orbiter import Orbiter, Stages, Stage_Composant, Orbiters
from math import pi

attitude_control=[(1000,1.48353),(2000,1.39626),(3000,1.309),(8000,1.13446),(16000,0.785398),
                  (24000,0.785398),(80000,0.610865),(60000,0.36),(80000,0.35),(160000,0.5),(208000,-0.1),(220000,-0.436332),(258770,-0.890118)]

attitude_control = [('alt',1.21,81,100),('alt',56.54,72,1),('alt',60.53,63,100),('alt',84.21,54,100),('alt',143.14,45,100),('alt',200,35,100),('aphelion',250,-28,100),('aphelion',474,-37,100)]


class Controller:
    def showControl(self):
        orbiter = self.orbiters.get_current_orbiter()
        alt = None
        print("time;thrust;altitude;velocity;carburant;(apogée,périgée)")
        if len(attitude_control)>0:
            (param,alt,control,throttle) = attitude_control.pop(0)
        

        while not self.finish:
            altitude = (orbiter.r.norm() - orbiter.attractor.radius)/1000
            (perigee,apogee) = orbiter.orbit.get_limit()
            perigee = int((perigee-orbiter.attractor.radius)/1000)
            apogee = int((apogee - orbiter.attractor.radius)/1000)
            perigee = max(0,perigee)
            apogee = max(0,apogee)

            if alt != None  and altitude>alt:
                if  ((param == 'alt'         and altitude > alt) or
                    (param == 'perihelion'  and perigee  > alt) or
                    (param == 'aphelion'    and apogee   > alt) or
                    (param == 'time'        and self.time.t > alt)):

                    print("+++++++++++++++++++++++++")
                    print("+++ Attitude Control +++")
                    print("Angle %i" % int(control))
                    print("+++++++++++++++++++++++++")

                    orbiter.orientation1 = control * pi / 180
                    if len(attitude_control)>0:
                        (param,alt,control,throttle) = attitude_control.pop(0)

                    else:
                        alt = None

            
            print("%is %.2fkN %.2fkm %.2fkm/s %ikg %ideg [%ikm, %ikm]"%(int(self.time.t),orbiter.thrust,altitude,orbiter.v.norm()/1000,int(orbiter.stages.get_carburant_mass()),int(orbiter.orientation1*180/3.141592),perigee,apogee))
            if len(orbiter.stages.empty_part)>0:
                while len(orbiter.stages.empty_part)>0:
                    part_name = orbiter.stages.empty_part.pop(0)
                    part = orbiter.stages.sep_part(part_name)
                    stages = Stages()
                    stages.add_stage()
                    stages.add_part(part_name,part)
                    
                    new_orbiter = Orbiter(stages)
                    new_orbiter.set_attractor(orbiter.attractor)
                    self.orbiters.add_orbiter(part_name,new_orbiter)
                    new_orbiter.set_state(orbiter.r,orbiter.v,self.time.t)
                    print("############# Stage Separation ##############")
                    print(part)
                    print("#############################################")
            time.sleep(1)

    def __init__(self, orbiters, timecontroller):
        self.orbiters = orbiters
        self.time = timecontroller
        self.finish = False
        self.thread = threading.Thread(target=self.showControl)
        self.thread.start()

    def stop(self):
        self.finish = True