from kivy.uix.scatterlayout import ScatterPlaneLayout
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock


class MapView(ScatterPlaneLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_bring_to_front = True
        self.do_rotation = True

    def displace(self, x, y):
        self.apply_transform(Matrix().translate(x, y, 0), post_multiply=True)

    def add_widget(self, widget, index=0, canvas=None, on_added=None):
        super(MapView, self).add_widget(widget, index, canvas)
        if on_added is not None:
            Clock.schedule_once(on_added, 1/5)

    def add_widgets(self, widgets_list, dt=5):
        def add_widget(widgets, count):
            if len(widgets) <= count:
                return
            self.add_widget(widgets[count], on_added=lambda dt: add_widget(widgets, count+1))
        c = 0
        add_widget(widgets_list, c)
