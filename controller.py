import threading
import time



class Controller:
    def showControl(self):
        print("time;thrust;delta v;altitude, velocity, carburant")
        while not self.finish:
            print(int(self.time.t),int(self.orbiter.thrust),self.orbiter.dv.norm(), self.orbiter.r.norm() - int(self.orbiter.attractor.radius), int(self.orbiter.v.norm()),int(self.orbiter.stages.get_carburant_mass()))
            if len(self.orbiter.stages.empty_part)>0:
                while len(self.orbiter.stages.empty_part)>0:
                    part = self.orbiter.stages.empty_part.pop(0)
                    self.orbiter.stages.sep_part(part)
                    print("############# Stage Separation ##############")
                    print(part)
    
                    print("#############################################")
                    
            
            time.sleep(0.2)

    def __init__(self, orbiter, timecontroller):
        self.orbiter = orbiter
        self.time = timecontroller
        self.finish = False
        self.thread = threading.Thread(target=self.showControl)
        self.thread.start()

    def stop(self):
        self.finish = True