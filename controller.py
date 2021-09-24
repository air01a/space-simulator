import threading
import time

attitude_control=[(1000,1.48353),(2000,1.39626),(3000,1.309),(4000,1.13446),(10000,0.785398),
                  (16000,0.785398),(40000,0.610865),(60000,0.36),(80000,0.35),(160000,0.5),(208000,-0.1),(220000,-0.436332),(258770,-0.890118)]

class Controller:
    def showControl(self):
        alt = None
        print("time;thrust;altitude;velocity;carburant;(apogée,périgée)")
        if len(attitude_control)>0:
            (alt,control) = attitude_control.pop(0)
        

        while not self.finish:
            altitude = self.orbiter.r.norm() - self.orbiter.attractor.radius

            if alt != None  and altitude>alt:
                print("+++++++++++++++++++++++++")
                print("+++ Attitude Control +++")
                print("Angle %i" % int(control*180/3.141592))
                print("+++++++++++++++++++++++++")

                self.orbiter.orientation1 = control
                if len(attitude_control)>0:
                    (alt,control) = attitude_control.pop(0)

                else:
                    alt = None


            (perigee,apogee) = self.orbiter.orbit.get_limit()
            perigee = int((perigee-self.orbiter.attractor.radius)/1000)
            apogee = int((apogee - self.orbiter.attractor.radius)/1000)
            perigee = max(0,perigee)
            apogee = max(0,apogee)
            print("%is %.2fN %.2fkm %.2fkm/s %ikg %ideg [%ikm, %ikm]"%(int(self.time.t),self.orbiter.thrust,(altitude)/1000,self.orbiter.v.norm()/1000,int(self.orbiter.stages.get_carburant_mass()),int(self.orbiter.orientation1*180/3.141592),perigee,apogee))
            if len(self.orbiter.stages.empty_part)>0:
                while len(self.orbiter.stages.empty_part)>0:
                    part = self.orbiter.stages.empty_part.pop(0)
                    self.orbiter.stages.sep_part(part)
                    print("############# Stage Separation ##############")
                    print(part)
                    print("#############################################")
            time.sleep(1)

    def __init__(self, orbiter, timecontroller):
        self.orbiter = orbiter
        self.time = timecontroller
        self.finish = False
        self.thread = threading.Thread(target=self.showControl)
        self.thread.start()

    def stop(self):
        self.finish = True