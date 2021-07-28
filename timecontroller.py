class TimeController():

    def time_accelerate(self):
        self.t_increment *= 2
    
    def time_normalize(self):
        self.t_increment = 1

    def time_decelarate(self):
        self.t_increment /= 2
        if self.t_increment < 1 :
            self.t_increment = 1
        
    def delta_t(self):
        return self.t_increment

    def update_time(self):
        self.t += self.t_increment

    def __init__(self, t0, event_listener, t_increment =1):
        self.event_listener = event_listener
        self.t = t0
        self.t_increment = t_increment
        self.event_listener.add_key_event(120,self.time_accelerate)
        self.event_listener.add_key_event(119,self.time_decelarate)
        self.event_listener.add_key_event(20,self.time_normalize)


