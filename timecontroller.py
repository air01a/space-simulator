########################################
# Control time operations
########################################


import time
import logging, inspect


class TimeController():

    def time_accelerate(self):
        if self.t_increment<5:
            self.t_increment += 1
        else:
            self.t_increment *= 2

        if self.on_change_callback!=None:
            self.on_change_callback(self.t_increment)


        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("TimeSeed %i" % self.t_increment)
        logging.debug("----------------------------")

    def time_normalize(self):

        self.t_increment = 0
        if self.on_change_callback!=None:
            self.on_change_callback(self.t_increment)

        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("TimeSeed Real time" )
        logging.debug("----------------------------")

    def time_decelarate(self):
        if self.t_increment < 6:
            self.t_increment -= 1
        else:
            self.t_increment = int(self.t_increment/2)
        if self.t_increment < 0 :
            self.t_increment = 0
        
        if self.on_change_callback!=None:
            self.on_change_callback(self.t_increment)
        logging.debug("+++++ %s - %s" % (inspect.getfile(inspect.currentframe()), inspect.currentframe().f_code.co_name))
        logging.debug("TimeSeed %i" % self.t_increment)
        logging.debug("----------------------------")

    def delta_t(self):
        return self.t-self.last_t

    def set_limiter(self,t):
        if t not in self.limiter and self.t<t:
            self.limiter.append(t)
            self.limiter.sort()

    def update_time(self):
        self.last_t = self.t
        current_time = time.time()
        self.t += (current_time - self.clock) * (1+self.t_increment)
        if len(self.limiter)>0 and self.t>=self.limiter[0]:
            self.t = self.limiter[0]+0.00001
            self.limiter.pop(0)

        self.clock = current_time

    def set_time_increment(self, increment):
        self.t_increment = increment
        if self.on_change_callback!=None:
            self.on_change_callback(self.t_increment)

    def __init__(self, t0, event_listener, t_increment = 0):
        self.event_listener = event_listener
        self.t = t0
        self.t_increment = t_increment
        self.last_t = t0
        self.clock = time.time()
        self.on_change_callback = None
        self.event_listener.add_key_event(120,self.time_accelerate,"Accelerate time")
        self.event_listener.add_key_event(119,self.time_decelarate,"Deccelerate time")
        self.event_listener.add_key_event(99,self.time_normalize,"Real time")
        self.time_slow = []
        self.limiter = []


