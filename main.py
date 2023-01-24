from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
import sys
from kivy.config import Config
from display import Graphics
from spacetime import SpaceTime

LOGLEVEL = 'critical'
# Main Window, display graphics & co
class MainWindow(BoxLayout, Screen):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

    def run(self, filename):
        self.space_time = SpaceTime(filename)

        self.graphics = self.ids.graphics
        self.graphics.init(self.space_time)

        event = Clock.schedule_interval(self.space_time.update, 1 / 60.0)
        display = Clock.schedule_interval(self.graphics.draw, 1 / 24.0)
        if self.space_time.controller:
            info = Clock.schedule_interval(self.show_info, 1 / 10.0)
        Window.bind(size=self.resize)

    def show_info(self, ft):
        self.ids.infoLabel.text = self.space_time.controller.get_info()

    def show_info_control(self, text):
        self.ids.controlInfoLabel.text = text

    def on_request_close(self, *args):
        self.space_time.controller.stop()

    def resize(self, pos, size):
        self.graphics.update()


# File picker for scenario
class Filechooser(BoxLayout, Screen):
    def __init__(self, **kwargs):
        self.callback = kwargs["callback"]
        del kwargs["callback"]
        super(Filechooser, self).__init__(**kwargs)

    def select(self, *args):
        try:
            self.callback(args[1][0])
        except:
            pass


# Main App
class SpaceSimulatorApp(App):
    def build(self):
        # If  file in sysarg
        if len(sys.argv) > 1:
            file_name = sys.argv[1]
            self.main = MainWindow(name="main")
            self.main.run(file_name)
            return self.main

        # else pick one
        self.sm = ScreenManager()
        self.sm.add_widget(Filechooser(name="filechooser", callback=self.callback))
        self.main = MainWindow(name="main")
        self.sm.add_widget(self.main)
        return self.sm

    # When a file has been chosen
    def callback(self, file):
        self.sm.current = "main"
        self.main.run(file)


# Application entry
if __name__ == "__main__":
    Config.set("graphics", "fullscreen", "auto")
    Config.set("graphics", "window_state", "maximized")
    Config.set("graphics", "resizable", 1)
    Config.set("kivy", "log_level", LOGLEVEL)
    Config.write()
    SpaceSimulatorApp().run()
