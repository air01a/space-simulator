from kivy.core.window import Window
from kivy.uix.widget import Widget


class EventListener(Widget):
    def __init__(self):
        super(EventListener, self).__init__()
        self.key_event    = {}
        self.event = {}
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def add_key_event(self,key,func,msg):
        car = (self._keyboard.keycode_to_string(key))
 
        print("%s : %s"%(car,msg) )
        self.key_event[key] = func


    def add_event(self, key, func):
        self.event[key] = func
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        #for event in pygame.event.get():
         #   if event.type == pygame.QUIT: 
         #       return Trues
            
         #   if event.type == pygame.KEYDOWN:
       
        #print('The key', keycode, 'have been pressed')
        #print(' - text is %r' % text)
        #print(' - modifiers are %r' % modifiers)
        key = keycode[0]
        #print(key)
        if key in self.key_event.keys():
            self.key_event[key]()
        
        #if event.type in self.event.keys():
         #   self.event[event.type]()
        
        return False

    