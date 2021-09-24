import pygame

class EventListener:
    def __init__(self):
        self.key_event    = {}
        self.event = {}

    def add_key_event(self,key,func,msg):
        car = (pygame.key.name(key))
 
        print("%s : %s"%(car,msg) )
        self.key_event[key] = func


    def add_event(self, key, func):
        self.event[key] = func
    
    def pop_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                return True
            
            if event.type == pygame.KEYDOWN:
                key = event.key

                if key in self.key_event.keys():

                    self.key_event[key]()
            
            if event.type in self.event.keys():
                self.event[event.type]()
        
        return False

    