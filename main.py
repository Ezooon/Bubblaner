from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.utils import iffloat
from kivymd.toast import toast
from kivymd.app import MDApp

from kivy.properties import ListProperty, StringProperty, DictProperty, ObjectProperty, NumericProperty
from kivy.clock import mainthread, Clock
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.utils import platform
from kivy.lang import Builder
from kivy.metrics import dp

import threading
import json
import sys
import os
from gestures4kivy import CommonGestures
from kivy.config import Config

_scroll_timeout = _scroll_distance = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = '{}sp'.format(Config.getint('widgets',
                                                   'scroll_distance'))
    Config.set('input', 'mouse', 'mouse, disable_multitouch')

root_path = r"E:/Plans/simple planner"

if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path

    root_path = os.path.join(primary_external_storage_path(), 'roadmaps')
    Window.softinput_mode = 'below_target'
Window.fullscreen = 0
    
Builder.load_file('main.kv')


class MenuItem(OneLineListItem):
    callback = ObjectProperty()

    def on_release(self):
        self.callback(self.text)


class MapScreen(MDScreen, CommonGestures):
    root_bubbles = ListProperty()
    middle_point = ListProperty([0, 0])
    filename = StringProperty('New Plan')
    path = StringProperty('New Plan')
    recent_files = DictProperty()
    recent_menu_caller = ObjectProperty()
    default_root = StringProperty(r"E:/Plans/simple planner")
    clipboard = DictProperty(None, allownone=True)
    background = StringProperty("C:/Users/hp/Pictures/A day/2022-12-01_21.04.02.png")
    direction_index = NumericProperty(0)

    def __init__(self, **kwargs):
        self.directions = ['down', 'bottom-left', 'left', 'top-left', 'up', 'top-right', 'right', "bottom-right"]
        super().__init__(**kwargs)
        self.mapview = self.ids.mapview
        self.color_picker = None
        self.center_bubbles()
        self.bubble_editor = self.ids.bubble_editor
        self.draw_links = True
        recent_items = [
                {
                    "viewclass": "MenuItem", 'text': name,
                    'callback': lambda x: self.load(self.recent_files[x])
                } for name in self.recent_files.keys()
            ]
        self.recent_files_menu = MDDropdownMenu(
            caller=self.ids.toolbar,
            items=[{"viewclass": "OneLineListItem", 'text': 'Choose a File', 'on_release': self.open_load_manager},
                   {"viewclass": "OneLineListItem", 'text': 'Empty File', 'on_release': lambda: self.load('')},
                   *recent_items],
            width_mult=4,
        )
        self.file_manager = MDFileManager(
            select_path=self.load,
            search='all',
            selector='file',
            ext=['.json']
        )
        # self.ids.quick_settings.get_button('google-circle')._bg_color = 0,0,0,0
        self.spinner = ModalView()
        self.spinner.canvas.clear()
        self.spinner.add_widget(MDSpinner(active=True, size=(dp(46), dp(46)), size_hint=(None, None)))

    def on_recent_files(self, instance, recent_files):
        recent_items = [
            {
                "viewclass": "MenuItem", 'text': name,
                'callback': lambda x: self.load(self.recent_files[x])
            } for name in self.recent_files.keys()
        ]
        items = [{"viewclass": "OneLineListItem", 'text': 'Choose a File', 'on_release': self.open_load_manager},
                 {"viewclass": "OneLineListItem", 'text': 'Empty File', 'on_release': lambda: self.load('')},
                 *recent_items]
        self.recent_files_menu = MDDropdownMenu(
            caller=self if not 'toolbar' in self.ids else self.ids.toolbar,
            items=items,
            width_mult=4,
        )

        value = str(recent_files).replace(r'\\\\', r'\\')
        value = value.replace('\\', r'\\')

        config = MDApp.get_running_app().config
        config.set('Files', 'recent_files', value)
        config.write()

    def append_root_bubbles(self, bubble):
        self.mapview.add_widget(bubble)
        self.root_bubbles.append(bubble)
        bubble.bind(center=self.update_middle_point)
        self.update_middle_point()

    def open_bubble_editor(self, height=Window.height/2.5, reset=True, **kwargs):
        if self.bubble_editor.bubble:
            if 'bubble' in kwargs:
                if kwargs['bubble'] == self.bubble_editor.bubble:
                    self.ids.backdrop.open(-height)
                # elif height == 0:
                #     self.ids.backdrop.close(False, dp(60))
                return
            self.bubble_editor.cancel()
        @mainthread
        def append_root_bubbles(bubble):
            # self.mapview.add_widget(bubble)
            self.root_bubbles.append(bubble)
            bubble.bind(center=self.update_middle_point)
            self.update_middle_point()

        def load_bubble(kwargs):
            if reset:
                self.bubble_editor.reset()
            for key in kwargs:
                exec(f'self.bubble_editor.{key} = kwargs["{key}"]')
            self.ids.backdrop.header_text = 'Edit: '+kwargs['bubble'].text

            # if height != 0:
            Clock.schedule_once(lambda x: self.ids.backdrop.open(-height), 0.1)
            # else:
            #     self.ids.backdrop.close(False, dp(60))

        if not kwargs:
            kwargs = {'callback': append_root_bubbles, 'sub_bubble_dependent': True}
        if 'bubble' not in kwargs.keys():
            from bubble import MBubble
            bubble = MBubble(pos=self.mapview.to_local(self.width/2 - dp(50), self.height - (self.height/4) - dp(50)))
            self.mapview.add_widget(bubble)
            bubble.color_platte = [MDApp.get_running_app().theme_cls.primary_palette, 'Black',
                                   MDApp.get_running_app().theme_cls.primary_palette]
            # self.root_bubbles.append(bubble)
            kwargs['bubble'] = bubble

        oet = threading.Thread(target=load_bubble, args=(kwargs,))
        Clock.schedule_once(lambda x: oet.start(), 0.5)

    def zoom_in(self):
        self.ids.mapview.scale += .2

    def zoom_out(self):
        if self.ids.mapview.scale_min <= self.ids.mapview.scale - .2:
            self.ids.mapview.scale -= .2

    def set_palette(self, button):
        app = MDApp.get_running_app()
        self.ids.color_picker.open([app.theme_cls.primary_palette], ['Primary Color'], app.change_palette)

    def open_save(self, path, filename=""):
        if not isinstance(path, str):
            path = "FileDoesNotExist"  # only to make path a string type
        if os.path.exists(path):
            self.save(path, filename)
            return
        if platform == 'win' and not os.path.exists(self.default_root):
            os.makedirs(self.default_root, exist_ok=True)

        from dialogs import open_save_dialog
        open_save_dialog(filename=self.filename,
                         location=self.path if self.path else self.default_root, callback=self.save)

    def save(self, path, filename):
        data = []
        from bubble import MBubble as Bubble
        for _id in Bubble.all_bubbles:
            bubble = Bubble.all_bubbles[_id]
            if not bubble.parent_bubble:
                data.append(bubble.save())
                if bubble not in self.root_bubbles:
                    self.root_bubbles.append(bubble)

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        self.filename = filename
        if filename+'.json' not in path:
            filename = os.path.join(path, filename+'.json')
        self.path = path

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        toast(f'"{filename}"\nhas been saved')

        if self.filename in self.recent_files:
            self.recent_files.pop(self.filename)
        self.recent_files[self.filename] = filename
        if len(self.recent_files) > 5:
            self.recent_files.pop(list(self.recent_files.keys())[0])

    def open_load_manager(self):
        self.recent_files_menu.dismiss()
        if os.path.exists(self.default_root):
            self.file_manager.show(self.default_root)
        self.file_manager.show(root_path)
        self.file_manager.exit_manager = lambda x: self.file_manager.close()

    def open_recent_files(self, button):
        self.recent_files_menu.open()

    def start_spinner(self):
        """add a spinner to the screen until somthing"""
        if self.spinner._is_open:
            self.spinner.dismiss()
            return
        self.spinner.open()

    def load(self, path):
        """load a file from memory"""
        self.draw_links = False
        if not os.path.exists(path) and path != '':
            toast(f"{path} DOES NOT EXIST!!")
            return

        self.recent_files_menu.dismiss()

        self.start_spinner()

        if self.file_manager._window_manager_open:
            self.file_manager.close()
        from bubble import MBubble as Bubble
        if path:
            with open(path, 'r') as f:
                data = json.load(f)
        else:
            data = {}

        self.mapview.clear_widgets()
        Bubble.all_bubbles.clear()
        Bubble.load_batch = []

        self.filename = os.path.split(path)[-1][:-5]
        if self.filename in self.recent_files:
            self.recent_files.pop(self.filename)
        self.recent_files[self.filename] = path
        if len(self.recent_files) > 5:
            self.recent_files.pop(list(self.recent_files.keys())[0])

        for bubble_data in data:
            bubble = Bubble.load(bubble_data)
            self.root_bubbles.append(bubble)
            bubble.bind(center=self.update_middle_point)
        self.start_spinner()
        self.mapview.add_widgets(Bubble.load_batch)
        self.update_middle_point()
        self.path = os.path.join(*os.path.split(path)[:-1])
        self.draw_links = True
        for _id in Bubble.all_bubbles:
            bubble = Bubble.all_bubbles[_id]
            if bubble.points_to:
                bubble.on_points_to()

    def paste(self):
        from bubble import MBubble
        bubble = MBubble.load(self.clipboard)
        self.mapview.add_widget(bubble)
        subbles = bubble.to_grandchildren()
        for sub in subbles:
            if not sub.onscreen:
                subbles.remove(sub)
        self.mapview.add_widgets(subbles)

        bubble.center_x += dp(50)
        bubble.center_y += dp(50)
        bubble.move_sub_bubbles(dp(20), dp(20), False)
        self.clipboard = None

    def on_clipboard(self, instance, value):
        if value:
            Animation(x=self.width - dp(24+100), d=.3).start(self.ids.clipboard)
            return
        Animation(x=self.width + dp(24+100), d=.3).start(self.ids.clipboard)

    def update_middle_point(self, *args):
        if not self.root_bubbles:
            self.middle_point = [0, 0]
            return
        centers = [bubble.center for bubble in self.root_bubbles]
        self.middle_point[0] = sum([center[0] for center in centers]) / len(centers)
        self.middle_point[1] = sum([center[1] for center in centers]) / len(centers)

    def center_bubbles(self):
        target = self.mapview.to_local(*self.center)
        start = self.middle_point
        displacement = [target[0] - start[0], target[1] - start[1]]
        self.mapview.displace(*displacement)

    def quick_settings(self, instance):
        from bubble import MBubble
        app = MDApp.get_running_app()
        primary_color = app.theme_cls.primary_color
        # Sub/Super-Bubble Size Ratio: blank
        if instance.icon == 'blank':
            i = MBubble.sub_ratio * 100
            if i >= 200:
                i = 0
            ratio = i + 12.5
            instance.label_text = str(iffloat(ratio)) + '%'
            MBubble.sub_ratio = ratio/100
            app.config.set('App', 'sub_ratio', MBubble.sub_ratio)

        # Add Super Bubble: google-circles
        elif instance.icon == 'google-circles':
            if MBubble.add_super:
                MBubble.add_super = False
                instance._bg_color = 0, 0, 0, 0.1
            else:
                MBubble.add_super = True
                instance._bg_color = primary_color
            app.config.set('App', 'add_super', MBubble.add_super if MBubble.add_super else '')

        # Sub-Bubbles Follow Parents: arrow-all
        elif instance.icon == 'arrow-all':
            if MBubble.follow_parent:
                instance._bg_color = 0, 0, 0, 0.1
                MBubble.follow_parent = False
            else:
                MBubble.follow_parent = True
                instance._bg_color = primary_color
            app.config.set('App', 'follow_parent', MBubble.follow_parent if MBubble.follow_parent else '')

        # New Bubble Direction: arrow--thin
        elif 'thin' in instance.icon:
            if self.direction_index >= 7:
                self.direction_index = -1
            self.direction_index += 1
            instance.icon = f'arrow-{self.directions[self.direction_index]}-thin'

        app.config.write()

    def help(self, *_):
        toast("We are terribly sorry! help is not ready yet.")

    def set_quick_settings(self, qs):
        from bubble import MBubble
        primary_color = MDApp.get_running_app().theme_cls.primary_color
        ratio = MBubble.sub_ratio * 100
        qs.get_button('blank').label_text = str(iffloat(ratio)) + '%'
        qs.get_button('google-circles')._bg_color = primary_color if MBubble.add_super else [0, 0, 0, 0.1]
        qs.get_button('arrow-all')._bg_color = primary_color if MBubble.follow_parent else [0, 0, 0, 0.1]

    def cgb_scroll(self, touch, focus_x, focus_y, delta_y, velocity):
        self.mapview.displace(0, -delta_y*abs(velocity))

    def cgb_pan(self, touch, focus_x, focus_y, delta_x, velocity):
        self.mapview.displace(delta_x*abs(velocity), 0)

    # def cgb_zoom(self, touch0, touch1, focus_x, focus_y, delta_scale):
    #     if platform not in 'android ios':
    #         delta_scale = 0.1 if delta_scale < 1 else - 0.1
    #         self.mapview.scale += delta_scale

    def on_background(self, instacne, value):
        app = MDApp.get_running_app()
        app.config.set('Theme', 'background', self.background)
        app.config.write()


class RoadMapApp(MDApp):
    recent_files = DictProperty()
    file = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._install_settings_keys = lambda x: None
        self.keyboard = Window.request_keyboard(None, self, 'text')
        self.keyboard.bind(on_key_down=self.key_down)

    def key_down(self, keyboard, key_code, txt, modifiers):
        # print(key_code, modifiers)
        if key_code[0] == 27:  # escape
            self.root.ids.backdrop.close(True)
            return True
        elif key_code[0] == 13:  # enter
            return False
        elif key_code[0] == 292:  # f11
            self.fullscreen()
            return True
        elif key_code[0] == 110 and 'ctrl' in modifiers and 'shift' in modifiers:  # ctrl + shift + n
            if self.root.bubble_editor.bubble:
                self.root.bubble_editor.bubble.add_bubble()
            return True

        elif key_code[0] == 115 and 'ctrl' in modifiers and 'shift' in modifiers:  # ctrl + shift + s
            self.root.open_save(1)
            return True

        elif key_code[0] == 110 and 'ctrl' in modifiers:  # ctrl + n
            self.root.open_bubble_editor(height=0)
            return True

        elif key_code[0] == 115 and 'ctrl' in modifiers:  # ctrl + c
            self.root.open_save(self.root.path, self.root.filename)
            return True
        return False

    def build_config(self, config):
        config.setdefaults('Theme', {'style': 'Dark', 'primary_palette': 'Blue', 'fullscreen': '0',
                                     'background': ''})
        config.setdefaults('App', {'add_super': '', 'sub_ratio': '0.90', 'follow_parent': True})
        config.setdefaults('Files', {'default_root': root_path, 'recent_files': '{}'})
        if not os.path.exists(root_path):
            os.makedirs(root_path, exist_ok=True)

    def change_style(self, *args):
        style = 'Light' if self.theme_cls.theme_style == 'Dark' else 'Dark'
        self.theme_cls.theme_style = style
        self.config.set('Theme', 'style', style)
        self.config.write()
        self.root.ids.color_picker.update_color()

    def change_palette(self, color, _):
        self.theme_cls.primary_palette = color
        self.config.set('Theme', 'primary_palette', color)
        self.config.write()

    def build(self):
        self.icon = 'icon.ico'
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            
        config = self.config
        self.theme_cls.primary_palette = config.get('Theme', 'primary_palette')
        fullscreen = config.get('Theme', 'fullscreen')
        Window.fullscreen = fullscreen if fullscreen == 'auto' else 0
        self.theme_cls.theme_style = config.get('Theme', 'style')

        recent_files = config.get('Files', 'recent_files').replace('\\', r"\\")
        recent_files = recent_files.replace(r'\\\\', r'\\')
        exec(f'self.recent_files = '+recent_files)
        default_root = config.get('Files', 'default_root')

        return MapScreen(recent_files=self.recent_files, default_root=default_root)

    def fullscreen(self, *args):
        if Window.fullscreen == 0:
            Window.fullscreen = 'auto'
            self.config.set('Theme', 'fullscreen', 'auto')
            self.config.write()
            return
        Window.fullscreen = 0
        self.config.set('Theme', 'fullscreen', '0')
        self.config.write()

    def on_start(self):
        from bubble import BubbleButtons, MBubble as Bubble
        from dialogs import BubbleEditor
        if not Bubble.new_bubble_dialog:
            # Bubble.new_bubble_dialog = BubbleEditor()
            Bubble._buttons = BubbleButtons(bubble=Bubble())
        self.root.ids.backdrop.ids._front_layer.y = -Window.height*2
        if self.file:
            self.root.load(self.file)

        self.root.background = self.config.get('Theme', 'background')
        Bubble.sub_ratio = float(self.config.get('App', 'sub_ratio'))
        Bubble.add_super = self.config.get('App', 'add_super')
        Bubble.follow_parent = self.config.get('App', 'follow_parent')


one = "" if len(sys.argv) <= 1 else sys.argv[1]
print(sys.argv)
RoadMapApp(file=one).run()
