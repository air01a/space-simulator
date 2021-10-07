from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle


from display import Graphics
from spacetime import SpaceTime

class InfoLabel(Label):
    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 1, 0, 0.25)
            Rectangle(pos=self.pos, size=self.size)

class ControlInfoLabel(Label):
    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 1, 0.25)
            Rectangle(pos=self.pos, size=self.size)

class SpaceSimulatorApp(App):
    def build(self):
        self.control_label = ControlInfoLabel(text='',size_hint=(0.5,.1))

        layout = BoxLayout(orientation='vertical')
        self.space_time = SpaceTime(self.control_label)
        zoom_ratio = 50

        self.display = Graphics(self.space_time, zoom_ratio)

        #self.window_manager =  SpaceSimulator(self.space_time)
        self.display.size_hint=(1,.8)
        layout.add_widget(self.display)
        layout.add_widget(self.control_label)
        self.label = InfoLabel(text='Hello',size_hint=(1, .1))
        layout.add_widget(self.label)
        
        event = Clock.schedule_interval(self.space_time.update, 1 / 60.)
        display = Clock.schedule_interval(self.display.draw, 1 / 24.)
        info = Clock.schedule_interval(self.show_info, 1 / 10.)


        return layout

    def show_info(self,ft):
                self.label.text = self.space_time.controller.get_info()

    def on_request_close(self, *args):
        self.space_time.controller.stop()

    def __del__(self):
        self.space_time.controller.stop()


if __name__ == '__main__':
    SpaceSimulatorApp().run()
