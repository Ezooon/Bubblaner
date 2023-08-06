"""
Components/GridLayout
=====================

:class:`~kivy.uix.gridlayout.GridLayout` class equivalent. Simplifies working
with some widget properties. For example:

GridLayout
----------

.. code-block::

    GridLayout:
        size_hint_y: None
        height: self.minimum_height

        canvas:
            Color:
                rgba: app.theme_cls.primary_color
            Rectangle:
                pos: self.pos
                size: self.size

MDGridLayout
------------

.. code-block::

    MDGridLayout:
        adaptive_height: True
        md_bg_color: app.theme_cls.primary_color

Available options are:
----------------------

- adaptive_height_
- adaptive_width_
- adaptive_size_

.. adaptive_height:
adaptive_height
---------------

.. code-block:: kv

    adaptive_height: True

Equivalent

.. code-block:: kv

    size_hint_y: None
    height: self.minimum_height

.. adaptive_width:
adaptive_width
--------------

.. code-block:: kv

    adaptive_width: True

Equivalent

.. code-block:: kv

    size_hint_x: None
    width: self.minimum_width

.. adaptive_size:
adaptive_size
-------------

.. code-block:: kv

    adaptive_size: True

Equivalent

.. code-block:: kv

    size_hint: None, None
    size: self.minimum_size
"""

from kivy.uix.gridlayout import GridLayout
from kivy.properties import BooleanProperty, StringProperty
from kivy.clock import Clock
from kivymd.uix import MDAdaptiveWidget


class MDGridLayout(GridLayout, MDAdaptiveWidget):
    float_children_y = BooleanProperty(False)
    float_children_x = BooleanProperty(False)
    order = StringProperty('left')

    def on_rows(self, instance, value):
        if self.order == 'left':
            return
        for i in range(value):
            row = self.children[self.cols*i:self.cols*(i+1)]
            row.reverse()
            self.children[self.cols * i:self.cols * (i + 1)] = row
        self.do_layout()

    def _iterate_layout(self, count):
        selfx = self.x
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        spacing_x, spacing_y = self.spacing

        i = count - 1
        y = self.top - padding_top
        cols = self._cols
        for row_height in self._rows:
            x = selfx + padding_left
            for col_width in cols:
                if i < 0:
                    break

                yield i, x, y - row_height, col_width, row_height
                i = i - 1
                x = x + col_width + spacing_x
            y -= row_height + spacing_y

    def do_layout(self, *largs):
        children = self.children
        if not children or not self._init_rows_cols_sizes(len(children)):
            l, t, r, b = self.padding
            self.minimum_size = l + r, t + b
            return
        self._fill_rows_cols_sizes()
        self._update_minimum_size()
        self._finalize_rows_cols_sizes()

        for i, x, y, w, h in self._iterate_layout(len(children)):
            c = children[i]
            x = x if not self.float_children_x else c.x
            y = y if not self.float_children_y else c.y
            c.pos = x, y
            shw, shh = c.size_hint
            shw_min, shh_min = c.size_hint_min
            shw_max, shh_max = c.size_hint_max

            if shw_min is not None:
                if shw_max is not None:
                    w = max(min(w, shw_max), shw_min)
                else:
                    w = max(w, shw_min)
            else:
                if shw_max is not None:
                    w = min(w, shw_max)

            if shh_min is not None:
                if shh_max is not None:
                    h = max(min(h, shh_max), shh_min)
                else:
                    h = max(h, shh_min)
            else:
                if shh_max is not None:
                    h = min(h, shh_max)

            if shw is None:
                if shh is not None:
                    c.height = h
            else:
                if shh is None:
                    c.width = w
                else:
                    c.size = (w, h)

    def add_widget(self, widget, index=0, canvas=None, on_added=None):
        super(MDGridLayout, self).add_widget(widget, index, canvas)
        if on_added is not None:
            Clock.schedule_once(on_added, 1/5)

    def add_widgets(self, widgets_list, dt=5):
        def add_widget(widgets, count):
            if len(widgets) <= count:
                return
            self.add_widget(widgets[count], on_added=lambda dt: add_widget(widgets, count+1))
        c = 0
        add_widget(widgets_list, c)
