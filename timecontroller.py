import time
import logging, inspect


class TimeController():

    def time_accelerate(self):
        if self.t_increment==0:
            self.t_increment = 1
        else:
            self.t_increment *= 2

        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("TimeSeed %i" % self.t_increment)
        logging.debug("----------------------------")

    def time_normalize(self):

        self.t_increment = 0
        self.clock=time.time()-self.t

        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("TimeSeed Real time" )
        logging.debug("----------------------------")

    def time_decelarate(self):

        self.t_increment /= 2
        if self.t_increment < 1 :
            self.t_increment = 1
        
        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("TimeSeed %i" % self.t_increment)
        logging.debug("----------------------------")

    def delta_t(self):
        return self.t-self.last_t

    def update_time(self,accelerate = False):
        
        self.last_t = self.t

        if accelerate:
            self.t += 0.1
            return
        

        if self.t_increment!=0:
            self.t += self.t_increment
        else:
            self.t = time.time() - self.clock

    def __init__(self, t0, event_listener, t_increment =1):
        self.event_listener = event_listener
        self.t = t0
        self.t_increment = t_increment
        self.last_t = t0
        if t_increment==0:
            self.clock = time.time()
        self.event_listener.add_key_event(120,self.time_accelerate,"Accelerate time")
        self.event_listener.add_key_event(119,self.time_decelarate,"Deccelerate time")
        self.event_listener.add_key_event(99,self.time_normalize,"Real time")


