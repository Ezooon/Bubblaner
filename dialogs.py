from kivymd.uix.segmentedcontrol import MDSegmentedControlItem, MDSegmentedControl
from kivymd.color_definitions import colors as COLORS
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.card import MDCard
from kivymd.uix.chip import MDChip
from kivymd.toast import toast
from kivymd.app import MDApp

from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty, DictProperty
from kivy.effects.scroll import ScrollEffect
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex
from kivy.clock import Clock, mainthread
from kivy.lang.builder import Builder
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.utils import platform
from datetime import datetime
from kivy.metrics import dp, sp
import os

root_path = r'E:/Plans/simple planner'
if platform == 'android':
    from android.storage import primary_external_storage_path

    root_path = primary_external_storage_path()

Builder.load_file('dialogs.kv')


def last_or_next(value, step, steps):
    if int(value) == 0: return 0
    last_v = step
    next_v = step
    for i in range(steps):
        last_v = step * i
        next_v = step * (i + 1)
        if last_v < value <= next_v:
            break

    if (value - last_v) < (next_v - value):
        return last_v
    else:
        return next_v


def reasonable_step(goal, step):
    init_step = step
    add_factor = .0001
    round = 5
    while goal % step != 0 and add_factor < 10:
        step = (step + add_factor).__round__(round)
        if step > goal:
            step = init_step
            add_factor *= 10
            round -= 1

    bigger_step = step

    step = init_step
    add_factor = .0001
    round = 5
    while goal % step != 0 and add_factor < 10:
        step = (step - add_factor).__round__(round)
        if step > goal:
            step = init_step
            add_factor *= 10
            round -= 1

    smaller_step = step

    step = init_step
    if bigger_step - step < step - smaller_step:
        step = bigger_step
    else:
        step = smaller_step

    return step


class BubbleListItem(OneLineIconListItem):
    bubble = ObjectProperty(allownone=True)
    callback = ObjectProperty()

    def on_release(self):
        self.callback()


class ColorButton(MDIconButton):
    color = StringProperty('Blue')
    callback = ObjectProperty()

    def on_release(self):
        self.icon_color = self.theme_cls.text_color
        self.callback(self)


class ColorContent(MDBoxLayout):
    chosen = ListProperty(['Blue', 'Blue', 'Blue'])
    chosen_button = ObjectProperty()
    primary_colors = dict()
    utility_button1 = ObjectProperty()
    callback = ObjectProperty()
    color_wheel = None
    options = ListProperty(['Pick Color'])
    selected_option = StringProperty('')
    segments = ObjectProperty()
    file_manager_path = StringProperty("C:/Users/hp/Pictures")  # Fixme You Know What You did

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        color_wheel = ColorContent.color_wheel
        if not color_wheel:
            color_line = MDGridLayout()
            color_line.rows = 1
            color_line.spacing = [dp(10), dp(10)]
            color_line.padding = [dp(10)] * 4
            color_line.adaptive_size = True
            ColorContent.color_wheel = ScrollView(size=(Window.width, dp(65)), size_hint=(1, None),
                                                  bar_inactive_color=[0] * 4, bar_color=[0] * 4,
                                                  effect_cls=ScrollEffect, do_scroll_y=False)
            color_wheel = ColorContent.color_wheel
            color_wheel.add_widget(color_line)
        elif color_wheel.parent and color_wheel.parent != self:
            # remove color_wheel from it's last parent so it shows in this one ToDo not needed
            color_wheel.parent.remove_widget(color_wheel)
        color_line = color_wheel.children[0]

        self.orientation = 'vertical'
        # self.padding = [dp(10), 0, dp(10), 0]
        self.adaptive_size = True

        # Loading Color Buttons
        if not color_line.children or not ColorContent.primary_colors:
            color_line.clear_widgets()
            self.utility_button1 = ColorButton(icon="image-outline", callback=self.utility)
            self.utility_button2 = ColorButton(icon="format-font-size-decrease", callback=self.utility)
            self.utility_button1.theme_icon_color = "Custom"
            color_line.add_widget(self.utility_button1)
            for color in COLORS:
                if color in ['Light', 'Dark']:
                    continue
                button = ColorButton(icon='circle-outline', color=color)
                color_line.add_widget(button)
                button.md_bg_color = get_color_from_hex(COLORS[color]['500'])
                button.theme_icon_color = "Custom"
                button.icon_color = [1, 1, 1, 0]
                ColorContent.primary_colors[color] = get_color_from_hex(COLORS[color]['500'])

                if color == self.chosen[0]:
                    self.chosen_button = button
                    self.chosen_button.icon_color = button.theme_cls.text_color

                button.callback = self.pre_callback

        else:
            for button in color_line.children:
                button.callback = self.pre_callback
        self.max_width = dp(48) * len(COLORS)
        if color_wheel.parent or (color_wheel.parent != self and color_wheel.parent):
            color_wheel.parent.remove_widget(color_wheel)
            self.add_widget(color_wheel, 1)
        else:
            self.add_widget(color_wheel, 1)
        color_line.adaptive_size = True

        if self.options:
            if not self.segments:
                self.segments = MDSegmentedControl()
            if not self.segments.parent:
                self.add_widget(self.segments)

            self.segments.ids.segment_panel.bind(width=self.resize)

    def resize(self, instance, width):
        if self.segments.ids.segment_panel.width != ColorContent.color_wheel.width:
            self.segments.ids.segment_panel.width = ColorContent.color_wheel.width

    def on_chosen(self, instance, value):
        if not ColorContent.color_wheel:
            return
        for button in ColorContent.color_wheel.children[0].children:
            if button.color == value[0]:
                if self.chosen_button:
                    self.chosen_button.icon_color = [1, 1, 1, 0]
                self.chosen_button = button
                self.chosen_button.icon_color = button.theme_cls.text_color
            else:
                button.icon_color = [0] * 4

    @mainthread
    def on_options(self, instance, options):
        self.selected_option = options[0]
        if not self.segments:
            self.segments = MDSegmentedControl()

        self.segments.ids.segment_panel.clear_widgets()

        for option in options:
            opw = MDSegmentedControlItem(text=option)
            self.segments.add_widget(opw)
            self.segments.update_segment_panel_width(opw)

        def fix(dt):
            cn = len(self.segments.ids.segment_panel.children)
            if (cn / 2) == len(options):
                self.segments._remove_last_separator()
                Clock.schedule_once(self.segments._set_width_segment_switch, 1.0)

        Clock.schedule_once(fix, 1)

    def on_selected_option(self, instance, option):
        """To change the utility button accordingly"""
        if not self.utility_button1:
            return
        color_line = ColorContent.color_wheel.children[0]
        app = MDApp.get_running_app()

        # if option == "Link":
        #     if self.utility_button2 in color_line.children:
        #         color_line.remove_widget(self.utility_button2)
        #     if self.utility_button1 in color_line.children:
        #         color_line.remove_widget(self.utility_button1)
        # else:
        #     if self.utility_button1 not in color_line.children:
        #         color_line.add_widget(self.utility_button1, len(color_line.children))

        if option in ["Bubble", "Primary Color"]:
            self.utility_button1.disabled = False
            self.utility_button1.icon = "image-outline"
            if self.utility_button2 in color_line.children:
                color_line.remove_widget(self.utility_button2)

            if option == "Primary Color":
                if app.root.background:
                    self.utility_button1.icon_color = app.theme_cls.primary_color
                else:
                    self.utility_button1.icon_color = app.theme_cls.text_color
            else:
                bubble = app.root.ids.bubble_editor.bubble
                if bubble:
                    if bubble.background:
                        self.utility_button1.icon_color = app.theme_cls.primary_color
                    else:
                        self.utility_button1.icon_color = app.theme_cls.text_color

        elif option == "Text":
            self.utility_button1.disabled = False
            self.utility_button1.icon_color = app.theme_cls.text_color
            self.utility_button1.icon = "format-font-size-increase"  # ToDo or "decrease" or ratio
            color_line.add_widget(self.utility_button2, -1)

        elif option == "Link":
            if self.utility_button2 in color_line.children:
                color_line.remove_widget(self.utility_button2)
            self.utility_button1.icon_color = app.theme_cls.text_color
            self.utility_button1.icon = "middleware-outline"
            bubble = app.root.ids.bubble_editor.bubble
            if bubble.parent_bubble:
                self.utility_button1.disabled = False
            else:
                self.utility_button1.disabled = True

    def on_segments(self, instance, value):
        def change_option(sc, widget):
            self.selected_option = widget.text
            color = self.chosen[self.options.index(self.selected_option)]
            for button in ColorContent.color_wheel.children[0].children:
                if color == button.color:
                    if self.chosen_button:
                        self.chosen_button.icon_color = [1, 1, 1, 0]
                    self.chosen_button = button
                    self.chosen_button.icon_color = button.theme_cls.text_color

        value.bind(on_active=change_option)

    def pre_callback(self, button):
        self.chosen[self.options.index(self.selected_option)] = button.color
        self.chosen_button.icon_color = [1, 1, 1, 0]
        self.chosen_button = button
        self.chosen_button.icon_color = button.theme_cls.text_color

        self.callback(button.color, self.selected_option)
        self.on_selected_option(None, self.selected_option)

    def utility(self, button):
        app = MDApp.get_running_app()
        bubble = "Primary Color" not in self.options
        if bubble:
            bubble = app.root.ids.bubble_editor.bubble

        if button.icon == 'image-outline':

            if bubble:
                if bubble.background:
                    self.file_manager_path = os.path.join(*(os.path.split(bubble.background)[:-1]))
                    bubble.background = ""
                    self.utility_button1.icon_color = app.theme_cls.text_color
                    return
            elif app.root.background:
                self.file_manager_path = os.path.join(*(os.path.split(app.root.background)[:-1]))
                app.root.background = ""
                self.utility_button1.icon_color = app.theme_cls.text_color
                return

            def file(path):
                if bubble:
                    bubble.background = path
                else:
                    app.root.background = path

                self.file_manager_path = os.path.join(*(os.path.split(path)[:-1]))
                self.file_manager.close()

            self.file_manager = MDFileManager(
                select_path=file,
                search='all',
                preview=True
            )
            self.file_manager.show(self.file_manager_path)
            self.file_manager.exit_manager = lambda x: self.file_manager.close()

        elif button.icon in ["format-font-size-increase", "format-font-size-decrease"]:
            if "increase" in button.icon:
                bubble.font_size += sp(1)
            else:
                bubble.font_size -= sp(1)
            return

        elif button.icon == "middleware-outline":
            if bubble.parent_bubble:
                bubble.add_in_between()

        app.root.ids.color_picker.close()


class NumbersSelector(MDBoxLayout):
    number = NumericProperty(1)
    min_max = ListProperty([0, 60])
    name = StringProperty('year')
    holding = BooleanProperty(False)

    def increase(self, dt):
        if not self.holding:
            return False
        if self.number < self.min_max[1]:
            self.number += 1

    def decrease(self, dt):
        if not self.holding:
            return False
        if self.number > self.min_max[0]:
            self.number -= 1

    def on_touch_up(self, touch):
        self.holding = False
        return super(NumbersSelector, self).on_touch_up(touch)

    def on_touch_down(self, touch):
        self.holding = True
        if self.ids.increase.collide_point(*touch.pos):
            Clock.schedule_interval(self.increase, 0.2)
        elif self.ids.decrease.collide_point(*touch.pos):
            Clock.schedule_interval(self.decrease, 0.2)
        return super(NumbersSelector, self).on_touch_down(touch)

    def get_current_number(self):
        return self.number


class DatePicker(MDBoxLayout):
    name = StringProperty('Date')
    datetime = ObjectProperty()
    time_only = BooleanProperty(False)

    def on_time_only(self, instance, value):
        if value:
            self.ids.number_box.remove_widget(self.ids.year)
            self.ids.number_box.remove_widget(self.ids.month)
            self.ids.number_box.remove_widget(self.ids.day)
        elif not (self.ids.year in self.ids.number_box.children):
            self.ids.number_box.add_widget(self.ids.day, 5)
            self.ids.number_box.add_widget(self.ids.month, 7)
            self.ids.number_box.add_widget(self.ids.year, 9)

    def get_time(self):
        v = dict()
        for child in self.ids.number_box.children:
            if isinstance(child, NumbersSelector):
                v[child.name] = child.number

        hour = v['hour'] if self.ids.am_pm.text == 'AM' else v['hour'] + 12
        date = datetime(v['year'], v['month'], v['day'], hour, v["minute"])
        return date

    def reset(self, value=None, mminutes=0):
        if not value:
            value = datetime.now()
        ids = self.ids
        ids.year.default = value.year
        ids.month.default = value.month
        ids.day.default = value.day
        ids.hour.default = value.hour if value.hour <= 12 else value.hour - 12
        minute = value.minute + mminutes
        ids.minute.default = minute if minute <= 60 else minute - 60


class BubbleEditor(ScrollView):
    bubble = ObjectProperty(allownone=True)
    parent_bubble = ObjectProperty(allownone=True)
    value = NumericProperty(0)
    sub_bubble_dependent = BooleanProperty(False)
    sub_sum = BooleanProperty(True)
    backup_bubble = DictProperty()
    color_platte = ListProperty(['Blue', 'Gray', 'Blue'])
    callback = ObjectProperty(allownone=True)
    p_scroll_y = NumericProperty(1)
    select_to = 'add_link'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        color_palette = MDApp.get_running_app().theme_cls.primary_palette
        self.color_platte = [color_palette, 'Gray', color_palette]
        self.changed_parent = False
        self.bubbles_menu_items = []
        self.bubbles_menu_dialog = None
        self.keyboard = Window.request_keyboard(None, self, 'text')
        self.keyboard.bind(on_key_down=self.key_down)

    def key_down(self, keyboard, key_code, txt, modifiers):
        if key_code[0] == 13:  # enter
            self.edit(True)
            return True
        return False

    def on_bubble(self, instance, bubble):
        if not bubble:
            return
        self.backup_bubble['text'] = self.ids.text.text = bubble.text
        self.backup_bubble['parent_bubble'] = self.parent_bubble = bubble.parent_bubble

        self.backup_bubble['sub_bubble_dependent'] = bubble.sub_bubble_dependent
        self.backup_bubble['sub_sum'] = bubble.sub_sum
        self.backup_bubble['goal'] = bubble.goal
        self.ids.goal.text = str(bubble.goal)
        self.backup_bubble['step'] = bubble.step
        self.ids.step.text = str(bubble.step)
        self.backup_bubble['value'] = self.value = bubble.value
        # self.steps()

        self.backup_bubble['color_platte'] = bubble.color_platte
        self.color_platte = bubble.color_platte
        self.ids.limit.active = True if bubble.datetime_start else False
        if bubble.datetime_start:
            self.ids.datetime_start.reset(bubble.datetime_start)
            self.ids.datetime_end.reset(bubble.datetime_end)
        BubbleEditor.select_to = 'add_children'
        self.change_add(True)
        BubbleEditor.select_to = 'add_link'
        self.change_add(True)

    def cancel(self):
        bubble = self.bubble
        if not bubble:
            return
        from bubble import MBubble
        MBubble.select_mode = False
        if bubble.id not in MBubble.all_bubbles.keys():
            bubble.remove(None, 'Remove')
            del bubble
            return
        bubble.text = self.backup_bubble['text']
        bubble.change_parent(self.backup_bubble['parent_bubble'])

        bubble.sub_bubble_dependent = self.backup_bubble['sub_bubble_dependent']
        bubble.sub_sum = self.backup_bubble['sub_sum']
        bubble.goal = self.backup_bubble['goal']
        bubble.step = self.backup_bubble['step']
        self.steps()
        # bubble.value = self.backup_bubble['value']

        bubble.color_platte = self.backup_bubble['color_platte']

        self.bubble = None
        if self.dialog:
            self.dialog.close(True)

    @mainthread
    def change_add(self, bubble):
        """add, remove or change the parent, children or points tos"""
        if not (self.bubble and bubble):
            return
        from bubble import MBubble
        if BubbleEditor.select_to == 'add_link':
            if bubble == self.bubble:
                self.bubble.text = self.ids.text.text
                self.bubble.on_color_platte(self, self.color_platte)
                BubbleEditor.select_to = 'add_link'
                MDApp.get_running_app().root.ids.backdrop.open(-Window.height / 2.5)
                toast("can't link a bubble to itself")
                return
            if isinstance(bubble, MBubble):
                self.bubble.points_to.append(bubble.id)

            MBubble.select_mode = False
            self.ids.points_to.clear_widgets()

            def remove(instance):
                self.ids.points_to.remove_widget(instance)
                self.bubble.points_to.remove(instance.bubble_id)

            for bb in self.bubble.points_to:
                if bb not in MBubble.all_bubbles:
                    continue
                bub = MBubble.all_bubbles[bb]
                chip = MDChip(text=bub.text)
                chip.md_bg_color = bub.color
                chip.icon_right = "close-circle-outline"
                chip.bubble_id = bub.id
                chip.bind(on_release=remove)
                self.ids.points_to.add_widget(chip, 1)
            self.ids.points_to.add_widget(self.ids.adc)
            self.ids.points_to.add_widget(self.ids.vse, len(self.ids.points_to.children))
            self.ids.points_to.add_widget(self.ids.parent_bb_chip, len(self.ids.points_to.children))

        elif BubbleEditor.select_to == 'add_children':
            if bubble == self.bubble:
                self.bubble.text = self.ids.text.text
                self.bubble.on_color_platte(self, self.color_platte)
                MDApp.get_running_app().root.ids.backdrop.open(-Window.height / 2.5)
                MBubble.select_mode = False
                print('False '*100)
                return
            elif isinstance(bubble, MBubble):
                if bubble in self.bubble.children_bubbles:
                    bubble.change_parent(None)
                else:
                    bubble.change_parent(self.bubble)

            def add_child(_):
                BubbleEditor.select_to = "add_children"
                self.choose_bubble()

            def remove_child(instance):
                self.ids.children_bubbles.remove_widget(instance)

            self.ids.children_bubbles.clear_widgets()
            for bub in self.bubble.children_bubbles:
                chip = MDChip(text=bub.text)
                chip.md_bg_color = bub.color
                chip.icon_right = "close-circle-outline"
                chip.bubble_id = bub.id
                chip.bind(on_release=remove_child)
                self.ids.children_bubbles.add_widget(chip, 1)
            self.ids.children_bubbles.add_widget(MDChip(text="Add", on_release=add_child,
                                                        icon_right='plus-circle-outline'))

            return

        elif not BubbleEditor.select_to:
            MBubble.select_mode = False
            if bubble == self.bubble:
                self.parent_bubble = None
                self.changed_parent = True
                self.bubble.change_parent(None)
                self.bubble.text = self.ids.text.text
                self.bubble.on_color_platte(self, self.color_platte)
                BubbleEditor.select_to = 'add_link'
                return

            if self.bubble:
                if self.bubble.is_child(bubble):
                    toast("can't assign to a sub bubble")
                    self.bubble.text = self.ids.text.text
                    self.bubble.on_color_platte(self, self.color_platte)
                    BubbleEditor.select_to = 'add_link'
                    return

            self.changed_parent = True
            self.parent_bubble = bubble
            self.bubble.change_parent(bubble)

        self.bubble.text = self.ids.text.text
        self.bubble.on_color_platte(self, self.color_platte)
        BubbleEditor.select_to = 'nothing'

    def choose_bubble(self):
        from bubble import MBubble
        MBubble.select_mode = True
        self.bubble.text = 'DONE' if BubbleEditor.select_to else "NONE"
        self.bubble.color = 0, 0, 0, 1
        self.bubble.text_color = 1, 1, 1, 1
        MDApp.get_running_app().root.ids.backdrop.close()

    def reset(self):
        self.bubble = None
        # self.ids.text.text = ''
        self.sub_bubble_dependent = False
        self.ids.sub_bubble_dependent.active = False
        self.sub_sum = True
        self.ids.sub_sum.active = True
        self.ids.goal.text = '10'
        self.ids.step.text = '1'
        self.ids.steps.text = '10'
        self.ids.limit.active = False
        self.ids.datetime_start.reset()
        self.ids.datetime_end.reset(mminutes=10)
        self.parent_bubble = None
        self.value = 0

        color_palette = MDApp.get_running_app().theme_cls.primary_palette
        self.color_platte = [color_palette, 'Gray', color_palette]

        self.callback = None
        self.scroll_y = 1

    def color_picking(self, color, option):
        if option == 'Bubble':
            self.color_platte[0] = color
        elif option == 'Text':
            self.color_platte[1] = color
        elif option == 'Link':
            self.color_platte[2] = color
        self.bubble.on_color_platte(self, self.color_platte)

    def edit(self, key_13=False):
        bubble = self.bubble
        if not bubble:
            return
        bubble.datetime_start = self.ids.datetime_start.get_time() if self.ids.limit.active else None
        bubble.datetime_end = self.ids.datetime_end.get_time() if self.ids.limit.active else None
        bubble.color_platte = self.backup_bubble['color_platte']
        if self.dialog:
            self.dialog.close(True)

        from bubble import MBubble
        MBubble.select_mode = False
        if bubble.id not in MBubble.all_bubbles.keys():
            bubble.id = max(MBubble.all_bubbles.keys() or [0]) + 1
            MBubble.all_bubbles[bubble.id] = bubble

        if self.callback:
            self.callback(bubble)

        self.bubble = None

    def reasonable_step(self):
        goal = float(self.ids.goal.text)
        step = float(self.ids.step.text)
        steps = int(goal / (step or 1))
        self.ids.steps.text = str(steps)

        self.value = last_or_next(self.value, step, steps)

        if step > goal:
            self.ids.step.text = str(goal)
            return
        if (goal / (step or 1)).__round__(4) % 1 == 0:
            return

        step = reasonable_step(goal, step)
        self.ids.step.text = str(step)
        self.ids.steps.text = str(int(goal / step))
        self.value = last_or_next(self.value, step, steps)

    def on_value(self, instance, value):
        if self.bubble:
            self.bubble.value = value

    def steps(self):
        steps = int(self.ids.steps.text or 1)
        goal = float(self.ids.goal.text or 1)
        step = float(goal / (steps or 1))
        self.ids.step.text = str(step)
        self.value = last_or_next(self.value, step, steps)

    # def on_scroll_y(self, instance, value):
    #     vp_height = self._viewport.height
    #     if self.height < 30:
    #         return
    #     delta_sy = self.p_scroll_y - value
    #     sh = vp_height - self.height
    #     dy = delta_sy * float(sh)
    #     dialog_height = self.parent.parent.parent.y
    #
    #     dy = dy if dialog_height + dy < -10 else abs(dialog_height)
    #
    #     if dy < 0:
    #         self.parent.parent.parent.y += dy
    #         self.p_scroll_y = 1
    #         return
    #     elif dialog_height < -10 or self.height < vp_height:
    #         self.parent.parent.parent.y += dy
    #         self.p_scroll_y = 1
    #         # self.scroll_y = 1
    #         return
    #     self.p_scroll_y = value
    #
    # def on_scroll_y(self, instance, scroll):
    #     vp_height = self._viewport.height
    #     delta_scroll = self.p_scroll_y - scroll
    #     height_difference = vp_height - self.height
    #     delta_scroll_distance = delta_scroll * float(height_difference)
    #     print(delta_scroll_distance)


class DateTimeFields(MDBoxLayout):
    def invalid_time(self, field, next_f):
        hint = field.hint_text
        text = field.text
        now = datetime.now()
        if "Y" in hint:
            year = int(text)
            next_f.focus = True
            valid = 2100 > year >= now.year
            field.error = not valid
            if not valid:
                field.text = str(now.year)
            return valid
        elif "M" in hint:
            month = int(text)
            next_f.focus = True
            valid = 13 > month >= 1
            valid = False if int(self.ids.year.text) <= now.year and month < now.month else valid
            field.error = not valid
            if not valid:
                field.text = str(now.month)
            return valid
        elif "D" in hint:
            day = int(text)
            next_f.focus = True
            valid = 31 >= day >= 1
            valid = False if int(self.ids.year.text) <= now.year and int(
                self.ids.month.text) <= now.month and day < now.day else valid
            field.error = not valid
            if not valid:
                field.text = str(now.day)
            return valid

        elif "h" in hint:
            hour = int(text)
            next_f.focus = True
            valid = 12 > hour >= 0
            hour24 = hour if self.ids.am_pm.text == 'AM' else hour + 12
            valid = False if hour24 < now.hour else valid
            field.error = not valid
            if not valid:
                field.text = str(now.hour if now.hour <= 12 else now.hour - 12)
            return valid
        elif "m" in hint:
            minute = int(text)
            valid = 60 > minute >= 1
            hour24 = int(self.ids.hour.text) if self.ids.am_pm.text == 'AM' else int(self.ids.hour.text) + 12
            valid = False if hour24 <= now.hour and minute < now.minute else valid
            field.error = not valid
            if not valid:
                field.text = str(now.minute)
            return valid

    def get_time(self):
        Y = int(self.ids.year.text)
        M = int(self.ids.month.text)
        D = int(self.ids.day.text)
        h = int(self.ids.hour.text) if self.ids.am_pm.text == 'AM' else int(self.ids.hour.text) + 12
        m = int(self.ids.minute.text)
        return datetime(Y, M, D, h, m, 0)


class SaveContent(MDBoxLayout):
    filename = StringProperty()
    location = StringProperty()
    callback = ObjectProperty(print)

    def on_location(self, instance, value):
        if not os.path.exists(value):
            self.location = root_path

    def set_location(self, path):
        self.location = str(path)
        self.file_manager.close()

    def file_manager_open(self):
        self.file_manager = MDFileManager(
            select_path=self.set_location,
            search='dirs',
        )
        self.file_manager.show(self.location)
        self.file_manager.exit_manager = lambda x: self.file_manager.close()


class MColorPicker(MDCard):
    colors = ObjectProperty()
    chosen = ListProperty(['Blue', 'Blue', 'Blue'])
    options = ListProperty(['Pick Color'])

    def __init__(self, **kwargs):
        super(MColorPicker, self).__init__(**kwargs)
        self.height = dp(115)
        self.radius = [dp(15)] * 2
        self.color_picking = print

        self.style = 'filled'
        options = ['Bubble', 'Line', 'Text']
        self.orientation = 'vertical'
        self.padding = [0] * 4
        self.colors = ColorContent(selected_option='Bubble',
                                   options=options,
                                   callback=self.color_picking,
                                   pos_hint={'center_x': 0.5})
        self.colors.size_hint_x = 1
        Clock.schedule_once(lambda c: self.add_widget(self.colors), 0)

    def open(self, chosen, options, callback):
        if len(self.colors.children) <= 1:
            self.colors.__init__()
        self.colors.chosen = chosen
        self.colors.options = options
        self.colors.callback = callback

        child = self.colors.segments.ids.segment_panel.children[-1]
        if isinstance(child, MDSegmentedControlItem):
            self.colors.segments.on_press_segment(child, 1)
            self.colors.on_selected_option(None, child.text)

        Animation(y=dp(5), d=.2).start(self)

    def close(self):
        Animation(y=-self.height - 10, d=.2).start(self)
        MDApp.get_running_app().root.ids.backdrop.close(True)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) and self.y >= 0:
            self.close()
        return super(MColorPicker, self).on_touch_down(touch)

    def update_color(self):
        theme = MDApp.get_running_app().theme_cls
        self.md_bg_color = theme.bg_darkest
        if self.colors:
            self.colors.segments.md_bg_color = theme.bg_dark
            self.colors.segments.segment_color = theme.bg_darkest


# def open_new_bubble_dialog(content=None, **kwargs):
#     if not content:
#         content = BubbleEditor(**kwargs)
#     else:
#         for key in kwargs:
#             exec(f'content.{key} = kwargs["{key}"]')
#
#     if content.parent:
#         content.dialog.open()
#         content.ids.text.focus = True
#         print('opened')
#         return
#     dialog = MDDialog(type='custom', content_cls=content)
#     dialog.auto_dismiss = False
#     content.dialog = dialog
#     dialog.radius = [dp(20)]
#
#     def resize(instance, value):
#         dialog.size = content.size
#         content.parent.size = content.size
#
#     dialog.size = content.width, content.height
#     content.bind(size=resize)
#     dialog.bind(size=resize)
#     dialog.ids.container.padding = (0, 0, 0, 0)
#     dialog.ids.spacer_top_box.padding = (0, 0, 0, 0)
#     dialog.open()
#     print('opened')
#     content.ids.text.focus = True
#     return content


def open_save_dialog(content=None, **kwargs):
    if not content:
        content = SaveContent(**kwargs)
    else:
        for key in kwargs:
            exec(f'content.{key} = kwargs["{key}"]')

    if content.parent:
        content.dialog.open()
        return
    dialog = MDDialog(type='custom', content_cls=content)
    dialog.auto_dismiss = False
    content.dialog = dialog
    dialog.radius = [dp(20)]

    def resize(instance, value):
        dialog.size[1] = content.size[1]
        content.parent.size[1] = content.size[1]

    # dialog.size = content.width, content.height
    content.bind(size=resize)
    dialog.bind(size=resize)
    dialog.ids.container.padding = (0, 0, 0, 0)
    dialog.ids.spacer_top_box.padding = (0, 0, 0, 0)
    dialog.open()
    return content


def open_choose_color_dialog(content=None, **kwargs):
    return
