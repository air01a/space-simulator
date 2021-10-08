from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window




from display import Graphics, Compas
from spacetime import SpaceTime


class MainWindow(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

    def run(self):
        self.space_time = SpaceTime()

        self.space_time.controller.control_info_callback = self.show_info_control
        self.space_time.pilot.control_info_callback = self.show_info_control
        zoom_ratio = 50
        self.graphics = self.ids.graphics
        self.graphics.init(self.space_time, zoom_ratio)
        
        event = Clock.schedule_interval(self.space_time.update, 1 / 60.)
        display = Clock.schedule_interval(self.graphics.draw, 1 / 24.)
        info = Clock.schedule_interval(self.show_info, 1 / 10.)
        Window.bind(size=self.resize)

    def show_info(self,ft):
        self.ids.infoLabel.text = self.space_time.controller.get_info()

    def show_info_control(self,text):
        self.ids.controlInfoLabel.text = text

    def on_request_close(self, *args):
        self.space_time.controller.stop()



    def resize(self, pos, size):
        self.graphics.update()
    

class SpaceSimulatorApp(App):
    def build(self):
        main = MainWindow()
        main.run()
        return main




if __name__ == '__main__':
    SpaceSimulatorApp().run()
