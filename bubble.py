from math import sqrt, pow
from datetime import datetime
from random import randint

from kivymd.color_definitions import colors as COLORS
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.theming import ThemableBehavior
from kivymd.utils import iffloat
from kivymd.toast import toast
from kivymd.app import MDApp

from kivy.uix.behaviors import DragBehavior
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, ListProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.metrics import dp, sp, MetricsBase
from kivy.utils import get_color_from_hex, get_hex_from_color
from kivy.clock import Clock
from kivy.lang import Builder

from dialogs import MDDialog

Builder.load_file('bubble.kv')


def distance(a, b):
    return sqrt(pow((a[0] - b[0]), 2) + pow((a[1] - b[1]), 2))


def datetimestr(s):
    # "2022-08-20 23:51:00"
    args = s[:4], s[5:7], s[8:10], s[11:13], s[14:16], s[17:19]
    args = [int(sd) for sd in args]
    return datetime(*args)


class Link(Widget):
    bubble = ObjectProperty()
    points_to = ObjectProperty()
    to_edge = ListProperty([0, 0])
    from_edge = ListProperty()
    parent_link = BooleanProperty(False)
    bubbles = []
    points_tos = {}
    links = {}

    def __init__(self, **kwargs):
        super(Link, self).__init__(**kwargs)
        if not self.parent_link:
            self.links[f'{self.bubble.id}-{self.points_to.id}'] = self
        else:
            self.links[f'{self.bubble.id}-parent'] = self

    def __delete__(self, instance):
        print(instance, 'Just Checking')
        self.points_to.unbind(center=self.update_to_edge)
        self.bubble.unbind(center=self.update_to_edge)
        super(Link, self).__delete__(instance)

    def on_bubble(self, instance, bubble):
        if bubble not in Link.bubbles:
            Link.bubbles.append(bubble)
            Link.points_tos[bubble.id] = []

    def on_points_to(self, instance, points_to):
        points_to.bind(center=self.update_to_edge)
        self.bubble.bind(center=self.update_to_edge)
        if not self.parent_link:
            points_to.points_to_self.append(self.bubble.id)
        if self.bubble in Link.bubbles and not self.parent_link:
            if points_to not in Link.points_tos[self.bubble.id]:
                 Link.points_tos[self.bubble.id].append(points_to)
        self.update_to_edge()

    def update_to_edge(self, *args):
        if not self.points_to:
            self.to_edge = self.bubble.center
            return
        points_to = self.points_to.first_onscreen()
        bubble = self.bubble.first_onscreen()
        if not bubble:
            del self
            return
        if not points_to:
            bubble.on_points_to()
            return
        a = ax, ay = points_to.center
        b = bx, by = bubble.center
        n1 = ac = points_to.width / 2 + dp(24)
        ab = distance(a, b)
        n2 = cb = ab - ac
        n1n2 = (n1 + n2) if (n1 + n2) > 0 else 1
        cx = ((n1 * bx) + (n2 * ax)) / n1n2
        cy = ((n1 * by) + (n2 * ay)) / n1n2
        c = (cx, cy)
        self.to_edge = c
        self.update_from_edge(bubble, points_to)

    def update_from_edge(self, points_to, bubble):
        if not self.points_to:
            self.to_edge = self.bubble.center
            return
        a = ax, ay = points_to.center
        b = bx, by = bubble.center
        n1 = ac = points_to.width / 2
        if not self.parent_link:
            n1 = ac = points_to.width / 2 + dp(24)
        ab = distance(a, b)
        n2 = cb = ab - ac
        n1n2 = (n1 + n2) if (n1 + n2) > 0 else 1
        cx = ((n1 * bx) + (n2 * ax)) / n1n2
        cy = ((n1 * by) + (n2 * ay)) / n1n2
        c = (cx, cy)
        self.from_edge = c


class BubbleButton(MDIconButton):
    bubble = ObjectProperty()
    bubbles = []

    def on_bubble(self, instance, bubble):
        self.theme_icon_color = "Custom"
        self.icon_color = bubble.color
        BubbleButton.bubbles.append(bubble.id)

    def on_release(self):
        app = MDApp.get_running_app()
        app.root.mapview.add_widget(self.bubble)


class BubbleButtons(MDFloatLayout):
    bubble = ObjectProperty()
    b_color = ListProperty(get_color_from_hex(COLORS['Blue']['600']))
    b_t_color = ListProperty(get_color_from_hex(COLORS['Blue']['600']))
    dismissed = BooleanProperty(True)

    bpos1 = ListProperty((0, 0))
    bpos2 = ListProperty((0, 0))
    bpos3 = ListProperty((0, 0))
    bpos4 = ListProperty((0, 0))
    bpos5 = ListProperty((0, 0))
    bpos6 = ListProperty((0, 0))
    bpos7 = ListProperty((0, 0))
    bpos8 = ListProperty((0, 0))
    bpos9 = ListProperty((0, 0))

    def on_touch_up(self, touch):
        super(BubbleButtons, self).on_touch_up(touch)
        bubble = self.bubble
        if not bubble:
            return
        dist = (distance(bubble.pos, (bubble.right, bubble.top)) - bubble.width) / 2
        bpos1 = [bubble.center_x, bubble.y - dist]
        bpos5 = [bubble.center_x, bubble.top + dist]
        bpos3 = [bubble.x - dist, bubble.center_y]
        bpos7 = [bubble.right + dist, bubble.center_y]
        x, y = touch.pos

        collided = bpos3[0]-24 <= x <= bpos7[0]+24 and bpos1[1]-24 <= y <= bpos5[1]+24
        if not collided:
            print('this should not show up if im clicing non ta bubbble')
            self.dismiss()

    def on_bubble_center(self, instance, center):
        self.center = center
        self.dismiss()
        if self.dismissed:
            self.bpos1 = self.bpos2 = self.bpos3 = self.bpos4 \
                = self.bpos5 = self.bpos6 = self.bpos7 = self.bpos8 = self.bpos9 = center

    def summon(self, bubble):
        self.dismissed = False
        mapview = MDApp.get_running_app().root.mapview
        if self.bubble != bubble:
            if self.bubble:
                self.bubble.unbind(center=self.on_bubble_center)
            self.bubble = bubble
            bubble.bind(center=self.on_bubble_center)
            self.dismiss(False)
            # self.center = bubble.center
            self.on_bubble_center(self, bubble.center)
        # self.b_color = bubble.b_color
        self.size = bubble.size
        mapview.remove_widget(bubble)
        if self not in mapview.children:
            mapview.add_widget(self)
        mapview.add_widget(bubble)

        dist = (distance(bubble.pos, (bubble.right, bubble.top)) - bubble.width) / 2

        if not (bubble.goal == 0 or bubble.sub_bubble_dependent):
            Animation(
                bpos1=[bubble.center_x, bubble.y - dist],
                bpos5=[bubble.center_x, bubble.top + dist],
                d=.3, t='out_elastic'
            ).start(self)

        if bubble.parent_bubble:
            Animation(
                bpos8=[bubble.right, bubble.y],
                # bpos0=[(bubble.right - dp(48)) - (dist / 2), bubble.y + (dist / 2)],
                d=.3, t='out_elastic'
            ).start(self)

        if bubble.children_bubbles:
            Animation(
                bpos4=[bubble.x, bubble.top],
                d=.3, t='out_elastic'
            ).start(self)

        Animation(
            bpos2=bubble.pos,
            bpos3=[bubble.x - dist, bubble.center_y],
            bpos6=[bubble.right, bubble.top],
            bpos7=[bubble.right + dist, bubble.center_y],
            bpos9=[bubble.right + dist, bubble.top + dist],
            b_color=bubble.b_color,
            b_t_color=bubble.text_color,
            d=.3, t='out_elastic'
        ).start(self)
        Animation(
            bb_rows_pos=bubble.center,
            d=.3, t='out_elastic'
        ).start(bubble)

    def dismiss(self, dismissed=True):
        self.dismissed = dismissed
        Animation(
            bpos1=self.center,
            bpos2=self.center,
            bpos3=self.center,
            bpos4=self.center,
            bpos5=self.center,
            bpos6=self.center,
            bpos7=self.center,
            bpos8=self.center,
            bpos9=self.center,
            d=.3
        ).start(self)
        Animation(
            bb_rows_pos=[self.bubble.center_x, self.bubble.y - dp(40)],
            d=.3, t='out_elastic'
        ).start(self.bubble)
        mapview = MDApp.get_running_app().root.mapview
        mapview.remove_widget(self)


class MBubble(ThemableBehavior, DragBehavior, ButtonBehavior, MDFloatLayout):
    id = NumericProperty(None)
    text = StringProperty('')
    to_goal = StringProperty('0/1')
    goal = NumericProperty(1)
    step = NumericProperty(1)
    value = NumericProperty(0)
    sub_bubble_dependent = BooleanProperty(False)
    sub_sum = BooleanProperty(True)
    datetime_end = ObjectProperty(None, allownone=True)
    datetime_start = ObjectProperty(None, allownone=True)
    created_datetime = ObjectProperty(allownone=True)
    color_platte = ListProperty(['Blue', 'Gray', 'Blue'])
    color = ListProperty(get_color_from_hex(COLORS['Blue']['500']))
    line_color = ListProperty(get_color_from_hex(COLORS['Blue']['700']))
    b_color = ListProperty(get_color_from_hex(COLORS['Blue']['600']))
    text_color = ListProperty([0, 0, 0, 1])
    progress_color = ListProperty([0, 1, 0, 1])
    background = StringProperty("")
    font_size = NumericProperty(sp(25))
    expanded = BooleanProperty(True)
    onscreen = BooleanProperty(True)
    parent_bubble = ObjectProperty(None, allownone=True)
    children_bubbles = ListProperty()
    children_bubbles_buttons = ListProperty()
    parent_edge = ListProperty((0, 0))
    points_to = ListProperty([])
    points_to_self = ListProperty([])

    _angle_start = NumericProperty(123)
    _angle_end = NumericProperty(123)
    _full_angle = NumericProperty(-213)
    _progress_full = NumericProperty(123 + 213)
    _progress_step = NumericProperty((123 + 213) / 10)
    _progress_value = NumericProperty(0)

    _last_center_pos = ListProperty((0, 0))

    time_angle_start = NumericProperty(126)
    time_angle_end = NumericProperty(126)
    time_full_angle = NumericProperty(-216)
    time_progress_full = NumericProperty(126 + 216)
    time_progress_step = NumericProperty(None)
    time_progress_value = StringProperty('')

    all_bubbles = dict()
    _buttons = None

    select_mode = False
    new_bubble_dialog = None
    sub_ratio = 0.875
    add_super = False
    follow_parent = True
    load_batch = []

    bpos0 = ListProperty((0, 0))
    bb_rows_pos = ListProperty((0, 0))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.parent_edge = self.center
        self.size = [dp(200), dp(200)]
        if 'size' in kwargs.keys():
            def pff(d):
                self.size = kwargs['size']
            Clock.schedule_once(pff, 0)

        self.bpos0 = self.right - dp(48), self.y
        self.bb_rows_pos = [self.center_x, self.y - dp(40)]
        # self.update_parent_edge()

        if not self.created_datetime:
            self.created_datetime = datetime.now()
        self.update_time_progress_step()
        self._last_center_pos = self._last_center_pos

    def first_onscreen(self):
        if self.onscreen:
            return self
        if self.parent_bubble:
            return self.parent_bubble.first_onscreen()

    def enlarge(self, enlarge=True):
        if enlarge:
            self.height += dp(10)
            self.y -= dp(5)
            self.width += dp(10)
            self.x -= dp(5)
        else:
            self.height -= dp(10)
            self.y += dp(5)
            self.width -= dp(10)
            self.x += dp(5)

    def add_bubble(self):
        if self.id not in MBubble.all_bubbles.keys():
            toast('save this bubble first!')
            return

        def add(new_bubble):
            if self.parent_bubble or not MBubble.add_super:
                self.children_bubbles.append(new_bubble)
            else:
                root = MDApp.get_running_app().root
                if self in root.root_bubbles:
                    root.root_bubbles.remove(self)
                    root.root_bubbles.append(new_bubble)
                self.change_parent(new_bubble)

        root = MDApp.get_running_app().root
        poses = ([self.x, self.y - dp(250)], [self.x - dp(250), self.y - dp(250)],
                 [self.x - dp(250), self.y], [self.x - dp(250), self.y + dp(250)],
                 [self.x, self.y + dp(250)], [self.x + dp(250), self.y + dp(250)],
                 [self.x + dp(250), self.y], [self.x + dp(250), self.y - dp(250)])
        parent = None
        if self.parent_bubble or not MBubble.add_super:
            parent = self
        bubble = MBubble(parent_bubble=parent, color_platte=self.color_platte,
                         pos=poses[root.direction_index], size=[sqrt((self.width**2)*MBubble.sub_ratio)]*2)
        root.ids.bubble_editor.cancel()
        root.mapview.add_widget(bubble)
        root.open_bubble_editor(height=0, callback=add, bubble=bubble)
        # MDApp.get_running_app().root.ids.backdrop.close(dp(60))

    def add_in_between(self):
        if self.id not in MBubble.all_bubbles.keys():
            toast('save this bubble first!')
            return

        def add(new_bubble):
            root = MDApp.get_running_app().root
            if self in root.root_bubbles:
                root.root_bubbles.remove(self)
                root.root_bubbles.append(new_bubble)
            # self.change_parent(new_bubble)

        root = MDApp.get_running_app().root
        poses = ([self.x - dp(250), self.y], [self.x, self.y + dp(250)],
                 [self.x + dp(250), self.y], [self.x, self.y - dp(250)],)

        bubble = MBubble(parent_bubble=self.parent_bubble, color_platte=self.color_platte,
                         pos=poses[randint(0, 3)], size=[sqrt((self.width**2)*MBubble.sub_ratio)]*2)
        root.ids.bubble_editor.cancel()
        root.mapview.add_widget(bubble)
        root.open_bubble_editor(height=0, callback=add, bubble=bubble)
        # MDApp.get_running_app().root.ids.backdrop.close(dp(60))
        self.change_parent(bubble)

    def on_center(self, instance, center):  # try to make sure things stay in place.
        # self.update_parent_edge()
        self.bpos0 = self.right - dp(48), self.y
        self.bb_rows_pos = [center[0], self.y - dp(40)]
        if self not in MDApp.get_running_app().root.mapview.children:
            self._last_center_pos = self.center

    def on_touch_up(self, touch):
        super(MBubble, self).on_touch_up(touch)

        if self.center == self._last_center_pos:
            return
        x, y = self.center[0] - self._last_center_pos[0], self.center[1] - self._last_center_pos[1]
        self.move_sub_bubbles(x, y)

    def move_sub_bubbles(self, x, y, force=False):
        if force or not MBubble.follow_parent:
            self._last_center_pos = self.center
            return

        def center_center(anim, bubble):
            bubble._last_center_pos = bubble.center

        for bubble in self.children_bubbles:
            anim = Animation(center=(bubble.center_x + x, bubble.center_y + y), d=0.2)
            anim.start(bubble)
            anim.bind(on_complete=center_center)
            if bubble.children_bubbles:
                bubble.move_sub_bubbles(x, y)
        self._last_center_pos = self.center

    def on_parent_bubble(self, instance, value):
        MDApp.get_running_app().root.mapview.add_widget(Link(parent_link=True, bubble=self, points_to=value))

    def update_parent_edge(self, *args):
        print('IF THIS MESAAGE NEVER POPS UP JUST DELEATE THE WHOLE FUNCTION!')
        if not self.parent_bubble:
            self.parent_edge = self.center
            return
        a = ax, ay = self.parent_bubble.center
        b = bx, by = self.center
        n1 = ac = self.parent_bubble.width / 2 + dp(21)
        ab = distance(a, b)
        n2 = cb = ab - ac
        n1n2 = (n1 + n2) if (n1 + n2) > 0 else 1
        cx = ((n1 * bx) + (n2 * ax)) / n1n2
        cy = ((n1 * by) + (n2 * ay)) / n1n2
        c = (cx, cy)
        self.parent_edge = c

    def on_parent(self, *args):
        self.onscreen = args[1] is not None

    def on_sub_bubble_dependent(self, instance, value):
        self.update_value()

    def expand_collapse(self, collapse=None):
        app = MDApp.get_running_app()
        if collapse is None:
            collapse = self.expanded
        else:
            self.expanded = collapse

        # collapse
        if self.expanded and collapse:
            bubble_buttons = []
            for child in self.children_bubbles:
                if child.children_bubbles:
                    child.expand_collapse(collapse)
                if child.onscreen:
                    app.root.mapview.remove_widget(child)
                bubble_buttons.append(BubbleButton(bubble=child))
            self.children_bubbles_buttons = bubble_buttons
            self.expanded = False

        # expand
        else:
            for child in self.children_bubbles:
                if not child.onscreen:
                    app.root.mapview.add_widget(child)
                if child.children_bubbles and child.expanded:
                    child.expand_collapse(False)
            self.children_bubbles_buttons = []
            self.expanded = True

    def off_screen(self, link_to_parent=False):
        if not self.parent_bubble:  #    or MBubble._buttons.dismissed) and not link_to_parent:
            return
        app = MDApp.get_running_app()
        app.root.mapview.remove_widget(self)
        if self.id not in BubbleButton.bubbles:
            self.parent_bubble.children_bubbles_buttons.append(BubbleButton(bubble=self))
        if self.children_bubbles:
            self.expand_collapse(True)

    def on_children_bubbles_buttons(self, instance, bubble_buttons):  # FixMe Bubble Buttons duplicate when pressing
        if not bubble_buttons:
            self.expanded = True
        else:
            self.expanded = False

        row1 = self.ids.row1
        row2 = self.ids.row2
        row2.clear_widgets()

        def pop(bb):
            if bb in self.children_bubbles_buttons:
                self.children_bubbles_buttons.remove(bb)

        if len(bubble_buttons) >= 5:
            row1.clear_widgets()
            for bubble_button in bubble_buttons[:5]:
                bubble_button.size_hint = 1, 1
                row1.add_widget(bubble_button)
                bubble_button.bind(on_release=lambda x: pop(x))
        else:
            row1.clear_widgets()
            for bubble_button in bubble_buttons:
                bubble_button.size_hint = 1, 1
                row1.add_widget(bubble_button)
                bubble_button.bind(on_release=lambda x: pop(x))

        if 5 < len(bubble_buttons) >= 9:
            row2.clear_widgets()
            for bubble_button in bubble_buttons[5:9]:
                bubble_button.size_hint = 1, 1
                row2.add_widget(bubble_button)
                bubble_button.bind(on_release=lambda x: pop(x))
        else:
            row2.clear_widgets()
            for bubble_button in bubble_buttons[5:]:
                bubble_button.size_hint = 1, 1
                row2.add_widget(bubble_button)
                bubble_button.bind(on_release=lambda x: pop(x))

        if len(bubble_buttons) >= 10 and row2.children:
            row2.remove_widget(row2.children[-1])
            more_button = MDIconButton(icon='dots-horizontal-circle-outline', icon_color=self.color,
                                       theme_icon_color='Custom')
            more_button.size_hint = 1, 1
            row2.add_widget(more_button)

    def on_release(self):
        root = MDApp.get_running_app().root
        if MBubble.select_mode:
            root.bubble_editor.change_add(self)
            if not root.bubble_editor.select_to == 'add_children':
                MBubble.select_mode = False
            return

        if MBubble._buttons.bubble == self:
            if MBubble._buttons.dismissed:
                MBubble._buttons.summon(self)
            root.ids.backdrop.close(True)
            root.open_bubble_editor(bubble=self)
            return
        elif MBubble._buttons.dismissed or MBubble._buttons.bubble != self:
            MBubble._buttons.dismiss()
            MBubble._buttons.summon(self)
            if root.ids.bubble_editor.bubble != self:
                root.ids.bubble_editor.cancel()
            root.ids.backdrop.close(True)
            root.open_bubble_editor(height=0, bubble=self)
            return

        root.ids.backdrop.close()
        MBubble._buttons.dismiss()

    def color_dialog(self):

        def change_color(color, option):
            if option == 'Bubble':
                self.color_platte[0] = color
            elif option == 'Text':
                self.color_platte[1] = color
            elif option == 'Link':
                self.color_platte[2] = color

        options = ['Bubble', 'Text', 'Link']
        app = MDApp.get_running_app()
        app.root.ids.color_picker.open(self.color_platte, options, change_color)

    def on_color_platte(self, instance, colors):
        self.color = get_color_from_hex(COLORS[colors[0]]['500'])
        self.b_color = get_color_from_hex(COLORS[colors[0]]['500'])  # 600 ToDo if bad Chage back
        if sum(self.color[:3]) > 1.5:
            self.text_color = get_color_from_hex(COLORS[colors[1]]['500'])  # 900
        else:
            self.text_color = get_color_from_hex(COLORS[colors[1]]['500'])  # 200
        self.line_color = get_color_from_hex(COLORS[colors[2]]['500'])  # 700

    def edit(self):
        MDApp.get_running_app().root.open_bubble_editor(height=0, bubble=self)

    def on_goal(self, instance, value):
        if value == 0:
            value = 10
        self._progress_step = (self._progress_full / value) * self.step
        self.to_goal = str(iffloat(self.value.__round__(4))) + '/' + str(iffloat(self.goal.__round__(4)))

    def on_step(self, instance, value):
        # if self.goal == 0:
        #     self.goal = 10
        self._progress_step = (self._progress_full / (self.goal or 1)) * value

    def on__progress_value(self, instance, progress_value):
        self.value = self.step * progress_value
        self._angle_end = self._angle_start - (self._progress_step * progress_value)

    def on_value(self, instance, value):
        if not self.sub_bubble_dependent and self.step != 0:
            self._angle_end = self._angle_start - (self._progress_step * (value / self.step))
        if self.parent_bubble:
            if self.parent_bubble.sub_bubble_dependent:
                self.parent_bubble.update_value()
        self.to_goal = str(iffloat(self.value.__round__(4))) + '/' + str(iffloat(self.goal.__round__(4)))
        if value < 0:  # value > self.start
            self.progress_color = [1, 0, 0, 1]
        elif value > self.goal:
            self.progress_color = [1, 1, 0, 1]
        else:
            self.progress_color = [0, 1, 0, 1]

    def on_children_bubbles(self, instance, value):
        if value:
            if self.sub_bubble_dependent:
                self.update_value()

    def update_value(self):
        if (not self.children_bubbles) or not self.sub_bubble_dependent:
            return
        self.goal = sum([bubble.goal for bubble in self.children_bubbles])
        self._angle_end = sum([bubble._angle_end for bubble in self.children_bubbles]) / len(self.children_bubbles)
        self.value = sum([bubble.value for bubble in self.children_bubbles])
        if not self.sub_sum:
            self.goal /= len(self.children_bubbles)
            self.value /= len(self.children_bubbles)

    def __repr__(self):
        return f'<bubble: {self.text}, id: {self.id}, value: {self.value}/{self.goal}>'

    def save(self, *execlode):
        children_bubbles = []
        for bubble in self.children_bubbles:
            children_bubbles.append(bubble.save(*execlode))

        d = MetricsBase().density
        data = {
            'id': self.id,
            'text': self.text,
            'goal': self.goal,
            'step': self.step,
            'value': self.value,
            'sub_bubble_dependent': self.sub_bubble_dependent,
            'sub_sum': self.sub_sum,
            'color_platte': self.color_platte,
            'onscreen': self.onscreen,
            'datetime_start': str(self.datetime_start) if self.datetime_start is not None else self.datetime_start,
            'datetime_end': str(self.datetime_end) if self.datetime_end is not None else self.datetime_end,
            'created_datetime': str(self.created_datetime),
            'pos': (self.x/d, self.y/d),
            'size': (self.width/d, self.height/d),
            'children_bubbles': children_bubbles,
            'points_to': self.points_to,
            'font_size': self.font_size,
            'background': self.background
            }
        for to_execlode in execlode:
            data.pop(to_execlode)

        return data

    @classmethod
    def load(cls, data, **more_data):
        children_bubbles = data.pop('children_bubbles') if 'children_bubbles' in data else []
        try:
            data['created_datetime'] = datetimestr(data['created_datetime'])
        except: pass
        try:
            data['datetime_start'] = datetimestr(data['datetime_start'])
        except: pass
        try:
            if 'datetime_end' not in data.keys():  # ToDo remove this
                data['datetime_end'] = data.pop('datetime_limit')
            if data['datetime_end'] == 'None':
                data['datetime_end'] = None
            data['datetime_end'] = datetimestr(data['datetime_end'])
        except: pass
        x, y = data['pos']
        data['pos'] = (dp(x), dp(y))

        data = {**data, **more_data}
        bubble = MBubble(**data)
        bubble.update_time_progress_step()
        # load children
        for child_data in children_bubbles:
            child = cls.load(child_data, parent_bubble=bubble)
            bubble.children_bubbles.append(child)
            if not child.onscreen:
                bubble.children_bubbles_buttons.append(BubbleButton(bubble=child))

        if bubble.onscreen:
            # MDApp.get_running_app().root.mapview.add_widget(bubble)
            cls.load_batch.append(bubble)

        if bubble.sub_bubble_dependent and bubble.children_bubbles:
            bubble.update_value()

        elif not bubble.sub_bubble_dependent:
            bubble._progress_value = bubble.value / bubble.step

        if bubble.id in MBubble.all_bubbles or not bubble.id:
            id_ = max(MBubble.all_bubbles or [39]) + 1
            if id_ in MBubble.all_bubbles.keys():
                id_ = randint(max(MBubble.all_bubbles.keys()) + 1, id_ + 300)
            bubble.id = id_

        MBubble.all_bubbles[bubble.id] = bubble
        return bubble

    def remove_dialog(self):
        dialog = MDDialog(title='Remove Bubble?')
        dialog.buttons = [
            MDFlatButton(
                text="Remove",
                theme_text_color="Custom",
                text_color=self.theme_cls.primary_color,
                on_release=lambda x: self.remove(dialog, x.text)
            ),
            MDFlatButton(
                text="Cancel",
                theme_text_color="Custom",
                text_color=[0, 1, 0, 1],
                on_release=lambda x: self.remove(dialog, x.text)
            ),
        ]

        if self.children_bubbles:
            color = get_hex_from_color(self.theme_cls.primary_color)
            dialog.text = f'[color={color}]Remove[/color]: children will have no parent.\n' \
                          f'[color={color}]With Children[/color]: children will be removed as well.\n' \
                          f'[color={color}]Inherit[/color]: parent will inherit children.\n'
            buttons = [
                MDFlatButton(
                    text="With Children",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: self.remove(dialog, x.text)
                )]
            if self.parent_bubble:
                buttons.append(
                    MDFlatButton(
                        text="Inherit",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: self.remove(dialog, x.text)
                    ))

            dialog.buttons = [dialog.buttons[0], *buttons, dialog.buttons[1]]

        dialog.__init__()
        dialog.open()

    def remove(self, dialog, option):
        root = MDApp.get_running_app().root
        mapview = root.mapview
        root.ids.backdrop.close(True)

        if option == 'Remove':
            for i in range(len(self.children_bubbles)):
                child = self.children_bubbles[0]
                if not child.onscreen:
                    mapview.add_widget(child)
                child.change_parent(None)

            if self.parent_bubble:
                if self in self.parent_bubble.children_bubbles:
                    self.change_parent(None)
            mapview.remove_widget(self)
            if self.id in MBubble.all_bubbles:
                MBubble.all_bubbles.pop(self.id)
            self.points_to = []
            for pts in self.points_to_self:
                if f'{pts}-{self.id}' in Link.links:
                    link = Link.links.pop(f'{pts}-{self.id}')
                    mapview.remove_widget(link)
                    del link

        elif option == 'With Children':
            children = self.children_bubbles.copy()
            for child in children:
                child.remove(None, option)

            if self.parent_bubble:
                self.change_parent(None)
            mapview.remove_widget(self)
            MBubble.all_bubbles.pop(self.id)

        elif option == 'Inherit':
            children = self.children_bubbles.copy()
            for child in children:
                child.change_parent(self.parent_bubble)
                if not child.onscreen:
                    mapview.add_widget(child)

            if self.parent_bubble:
                self.change_parent(None)
            mapview.remove_widget(self)
            MBubble.all_bubbles.pop(self.id)
            for pts in self.points_to_self:
                if f'{pts}-{self.id}' in Link.links:
                    link = Link.links.pop(f'{pts}-{self.id}')
                    mapview.remove_widget(link)
                    del link

        del self
        if dialog:
            dialog.dismiss()

    def copy(self, dialog, option):
        if option == 'Cancel':
            if dialog:
                dialog.dismiss()
            return

        root = MDApp.get_running_app().root
        mapview = root.mapview
        root.ids.backdrop.close(True)
        parent = self.parent_bubble
        self.change_parent(None)
        copy = self.save("points_to")
        self.change_parent(parent)

        # if option == 'Copy':
        #     copy.pop('children_bubbles')
        #     bubble = MBubble.load(copy)
        #     mapview.add_widget(bubble)
        # else:  # option == "With Children":
        root.clipboard = copy

        if dialog:
            dialog.dismiss()

    def to_grandchildren(self):
        subbles = list(self.children_bubbles)
        for child in self.children_bubbles:
            subbles += list(child.to_grandchildren())
        return subbles

    def change_parent(self, parent_bubble):
        if parent_bubble == self.parent_bubble:
            return

        mapview = MDApp.get_running_app().root.mapview
        if f'{self.id}-parent' in Link.links:
            link = Link.links.pop(f'{self.id}-parent')
            mapview.remove_widget(link)
            del link
 
        if not parent_bubble:
            if self.parent_bubble:
                self.parent_bubble.children_bubbles.remove(self)
            if not self.onscreen:
                mapview.add_widget(self)
            self.parent_bubble = None
            self.update_parent_edge()
        else:
            if self.parent_bubble:
                if self in self.parent_bubble.children_bubbles:
                    self.parent_bubble.children_bubbles.remove(self)
            self.parent_bubble = parent_bubble
            self.parent_bubble.children_bubbles.append(self)
            if not self.onscreen:
                self.off_screen(True)
            self.update_parent_edge()
            self.parent_bubble.update_value()

    def on_datetime_end(self, *args):
        if not (self.datetime_end and self.datetime_start):
            return
        self.time_angle_end = -216
        self.update_time_progress_step()

    def update_time_progress_step(self):
        if self.datetime_end is None or self.datetime_start is None:
            return
        td = self.datetime_end - self.datetime_start
        self.time_progress_step = self.time_progress_full / td.total_seconds()

        current_td = self.datetime_end - datetime.now()
        diff = (self.time_progress_step * (td.total_seconds() - current_td.total_seconds())) - 216
        if not self.time_progress_value == '00:00:00':
            self.time_angle_end = diff - 216
        else:
            self.time_angle_end = 126

        Clock.schedule_interval(self.update_time, 1)
        # MBubble.time_limit_bubbles.append(self.) ToDo make a function to cycle a list instead of one at a time

    def update_time(self, dt):
        whole_td = self.datetime_end - self.datetime_start
        if (self.datetime_start - datetime.now()).total_seconds() > 0:
            td = self.datetime_start - datetime.now()
        else:
            td = self.datetime_end - datetime.now()
            if not self.time_progress_value == '00:00:00':
                self.time_angle_end = (self.time_progress_step *
                                       (whole_td.total_seconds() - td.total_seconds())) - 216
            else:
                self.time_angle_end = 126

        self.time_progress_value = (str(td)[:-7]).replace(',', '\n')
        if (self.datetime_start - datetime.now()).total_seconds() > 0:
            self.time_progress_value += ' to start'

        if td.total_seconds() <= 0:
            self.time_progress_value = '00:00:00'
            return False

    def is_child(self, bubble):
        if bubble in self.children_bubbles:
            return True
        for child in self.children_bubbles:
            return child.is_child(bubble)

    def collide_point(self, x, y):
        sq_collided = super().collide_point(x, y)
        lt_c = self.x <= x <= self.x + 24 and self.top - 24 <= y <= self.top
        rt_c = self.right - 24 <= x <= self.right and self.top - 24 <= y <= self.top
        lb_c = self.x <= x <= self.x + 24 and self.y <= y <= self.y + 24
        # rb_c = self.right - 24 <= x <= self.right and self.y <= y <= self.y + 24

        return sq_collided if not (lt_c or rt_c or lb_c) else False

    def on_points_to(self, *_):
        b_list = self.points_to
        if not MDApp.get_running_app().root.draw_links:
            return
        if self in Link.bubbles:
            # add
            for b in b_list:
                if b not in MBubble.all_bubbles:
                    b_list.remove(b)
                    continue
                bub = MBubble.all_bubbles[b]
                if bub not in Link.points_tos[self.id]:
                    MDApp.get_running_app().root.mapview.add_widget(Link(bubble=self, points_to=bub))

            # remove
            for b in Link.points_tos[self.id]:
                if b.id not in b_list:
                    if f'{self.id}-{b.id}' in Link.links:
                        link = Link.links.pop(f'{self.id}-{b.id}')
                        MDApp.get_running_app().root.mapview.remove_widget(link)
                        del link
                    if b in Link.points_tos[self.id]:
                        Link.points_tos[self.id].remove(b)
        else:
            for b in b_list:
                if b in MBubble.all_bubbles:
                    bub = MBubble.all_bubbles[b]
                    MDApp.get_running_app().root.mapview.add_widget(Link(bubble=self, points_to=bub))
