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

    def set_time_checkpoint(self,t):
        if t not in self.checkpoint and self.t<t:
            self.checkpoint.append(t)
            self.checkpoint.sort()

    def set_timespeed_limiter(self, t0,speed_limit,t1):
        self.time_speed_limiter.append((t0,speed_limit,t1))
        self.set_time_checkpoint(t0)


    def update_time(self):
        self.last_t = self.t
        current_time = time.time()

        # Check if there is a time speed limiter condition
        if len(self.time_speed_limiter)>0:
            for index, (t,speed_limit,t1) in enumerate(self.time_speed_limiter):
                if self.t>=t:
                    self.t_increment = speed_limit
                    if self.t>=t1:
                        self.time_speed_limiter.pop(index)
        
        self.t += (current_time - self.clock) * (1+self.t_increment)

        # Check if there is a checkpoint 
        if len(self.checkpoint)>0 and self.t>=self.checkpoint[0]:
            self.t = self.checkpoint[0]
            self.checkpoint.pop(0)

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
        self.checkpoint = []
        self.time_speed_limiter = []


