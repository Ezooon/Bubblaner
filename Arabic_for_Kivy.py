import re
from kivy.clock import mainthread
from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput, Cache_append, Cache_get
from arabic_reshaper import reshape  # يلصق الأحرف
from bidi.algorithm import get_display  # يرتب الأحرف
from kivy.graphics import Rectangle
from kivy.metrics import sp, dp
from kivy.properties import ObjectProperty
from kivy.utils import get_hex_from_color

app = App.get_running_app()
FL_IS_LINEBREAK = 0x01


def text_size(text, font_size=sp(20)):
    return CoreLabel(font_size=font_size).get_extents(text)


def to_ar(txt):
    txt = str(txt)
    return get_display(reshape(txt))


arabic_letters = to_ar('ضصثقفغعهخحجدطكمنتالبيسشئءؤرلاىةوزظ')+'ضصثقفغعهخحجدطكمنتالبيسشئءؤرلاىةوزظ'


def word(text, index=1):
    r_word = ''
    for i in range(index-1):
        r_word = text[:text.index(" ")]
    return r_word


def reform(text, width):
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        if not indexes(line) or not any(list(filter(lambda x: x in arabic_letters, line))):
            new_lines.append(line)
            continue
        lsi = indexes(line)[-1]
        if text_size(line)[0] > width:
            # line = to_ar(line)[:lsi]+"\n"+to_ar(line)[lsi+1:]
            new_lines.append(line[lsi:])
            new_lines.append(line[:lsi])
        else:
            new_lines.append(line)

    if new_lines:
        return '\n'.join(new_lines)
    else:
        return text


def indexes(text, ci=0, sub=" ", indexes=True):
    spaces = []
    if not text:
        return text
    for c in range(len(text)):
        if text[c] == sub:
            spaces.append(c)
    if indexes:
        return spaces
    if not spaces:
        return text
    more_ci = list(filter(lambda x: x < ci, spaces))
    b_ci = max(more_ci or [-1]) + 1
    try:
        if text[ci] == sub:
            b_ci = ci
    except: pass
    less_ci = list(filter(lambda x: x > ci, spaces))
    a_ci = min(less_ci or [len(text)])
    return (a_ci, b_ci), spaces


def revers_text(text):
    new_text = ""
    for c in text:
        new_text = c + new_text
    return new_text


def add_nums(*args, index=1):
    if len(args) == 2:
        args.revers()
        return sum(args)


def from_ar(txt):
    txt = str(txt)
    return get_display(txt)


class ToAr:
    def __init__(self, ori):
        self.ori = ori

    def to_ar(self):
        return get_display(reshape(self.ori))


class ArButton(Button):
    def __init__(self, **kwargs):
        super(ArButton, self).__init__(**kwargs)
        self.text = to_ar(self.text)
        self.font_name = "assets/languages/micross.ttf"


class ArLabel(Label):
    def __init__(self, **kwargs):
        super(ArLabel, self).__init__(**kwargs)
        self.text = get_display(reshape(self.text))
        self.font_name = "assets/languages/micross.ttf"
        self.halign = 'left'  # App.get_running_app().lang_direction

    # def on_text(self, instance, value):
    #     lines = value.split('\n')
    #     if not value or len(value) < 5:
    #         return
    #     new_lines = []
    #     for line in lines:
    #         if not indexes(line):
    #             continue
    #         lsi = indexes(line)[-1]
    #         if text_size(line)[0] > self.width:
    #             # line = to_ar(line)[:lsi]+"\n"+to_ar(line)[lsi+1:]
    #             new_lines.append(line[lsi:])
    #             new_lines.append(line[:lsi])
    #         else:
    #             new_lines.append(line)
    #     self.text = '\n'.join(new_lines)
    #
    # def get_text_width(self, text, tab_width=4, _label_cached=None):
    #     # Return the width of a text, according to the current line options
    #     kw = {'font_size': self.font_size, 'font_name': self.font_name, 'font_context': None, 'font_family': None,
    #           'text_language': None, 'base_direction': App.get_running_app().lang_direction, 'anchor_x': 'left',
    #           'anchor_y': 'top', 'padding_x': self.padding_x, 'padding_y': self.padding_y, 'padding': (0, 0)}
    #
    #     try:
    #         cid = u'{}\0{}\0{}'.format(text, False, kw)
    #     except UnicodeDecodeError:
    #         cid = '{}\0{}\0{}'.format(text, False, kw)
    #
    #     width = Cache_get('textinput.width', cid)
    #     if width:
    #         return width
    #     if not _label_cached:
    #         _label_cached = CoreLabel()
    #     text = text.replace('\t', ' ' * tab_width)
    #     width = _label_cached.get_extents(text)[0]
    #     Cache_append('textinput.width', cid, width)
    #     return width


class ArInput(TextInput):
    next = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super(ArInput, self).__init__(**kwargs)
        self.text = get_display(reshape(self.text))
        # self.font_name = "assets/languages/micross.ttf"
        self.hint_text = get_display(reshape(self.hint_text))
        self.halign = 'left'  # App.get_running_app().lang_direction
        self.anchor = 'left'  # App.get_running_app().lang_direction

    def _set_line_text(self, line_num, text):
        # Set current line with other text than the default one.
        self._lines_labels[line_num] = self._create_line_label(to_ar(text))
        self._lines[line_num] = text

    def insert_text(self, substring, from_undo=False):
        if self.readonly or not substring or not self._lines:
            return

        if isinstance(substring, bytes):
            substring = substring.decode('utf8')

        if self.replace_crlf:
            substring = substring.replace(u'\r\n', u'\n')

        # self._hide_handles(EventLoop.window)

        if not from_undo and self.multiline and self.auto_indent \
                and substring == u'\n':
            substring = self._auto_indent(substring)

        mode = self.input_filter
        if mode not in (None, 'int', 'float'):
            substring = mode(substring, from_undo)
            if not substring:
                return

        cc, cr = self.cursor
        sci = self.cursor_index
        ci = sci()
        text = self._lines[cr]
        if any(list(filter(lambda x: x in 'ضصثقفغعهخحجدطكمنتالبيسشئءؤرلاىةوزظ', text))):
            cc = self.cursor_col
            indexes = list(range(len(text)))
            indexes.reverse()
            cc = indexes[cc-1] if cc != len(text) else cc

        len_str = len(substring)
        new_text = text[:cc] + substring + text[cc:]
        if mode is not None:
            if mode == 'int':
                if not re.match(self._insert_int_pat, new_text):
                    return
            elif mode == 'float':
                if not re.match(self._insert_float_pat, new_text):
                    return
        self._set_line_text(cr, new_text)

        wrap = (self._get_text_width(  # the width of the current line of text
            new_text,
            self.tab_width,
            self._label_cached) > (self.width - self.padding[0] -  # the width of the widget
                                   self.padding[2]))

        if len_str > 1 or substring == u'\n' or wrap:
            # Avoid refreshing text on every keystroke.
            # Allows for faster typing of text when the amount of text in
            # TextInput gets large.

            start, finish, lines, \
            lineflags, len_lines = self._get_line_from_cursor(cr, new_text)
            # calling trigger here could lead to wrong cursor positioning
            # and repeating of text when keys are added rapidly in a automated
            # fashion. From Android Keyboard for example.
            self._refresh_text_from_property('insert', start, finish, lines,
                                             lineflags, len_lines)

        self.cursor = self.get_cursor_from_index(ci + len_str)
        # handle undo and redo
        self._set_unredo_insert(ci, ci + len_str, substring, from_undo)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if 'shift' in modifiers:
            return False
        if keycode[0] in (9,) and self.next:
            self.focus = False
            if callable(self.next):
                self.next(self)
            else:
                self.next.focus = True
            return True
        return super(ArInput, self).keyboard_on_key_down(window, keycode, text, modifiers)

    def do_backspace(self, from_undo=False, mode='bkspc'):
        '''Do backspace operation from the current cursor position.
        This action might do several things:

            - removing the current selection if available.
            - removing the previous char and move the cursor back.
            - do nothing, if we are at the start.

        '''
        if self.readonly:
            return
        col, row = self.cursor
        _lines = self._lines
        text = _lines[row]
        if any(list(filter(lambda x: x in 'ضصثقفغعهخحجدطكمنتالبيسشئءؤرلاىةوزظ', text))):
            col = self.cursor_col
            indexes = list(range(len(text)))
            indexes.reverse()
            col = indexes[col - 1] if col != len(text) else col

        cursor_index = self.cursor_index()
        text_last_line = _lines[row - 1]

        if col == 0 and row == 0:
            return
        _lines_flags = self._lines_flags
        start = row
        if col == 0:
            substring = u'\n' if _lines_flags[row] else u' '
            new_text = text_last_line + text
            self._set_line_text(row - 1, new_text)
            self._delete_line(row)
            start = row - 1
        else:
            # ch = text[col-1]
            substring = text[col - 1]
            new_text = text[:col - 1] + text[col:]
            self._set_line_text(row, new_text)

        # refresh just the current line instead of the whole text
        start, finish, lines, lineflags, len_lines = (
            self._get_line_from_cursor(start, new_text)
        )
        # avoid trigger refresh, leads to issue with
        # keys/text send rapidly through code.
        self._refresh_text_from_property(
            'insert' if col == 0 else 'del', start, finish,
            lines, lineflags, len_lines
        )

        self.cursor = self.get_cursor_from_index(cursor_index - 1)
        # handle undo and redo
        self._set_unredo_bkspc(
            cursor_index,
            cursor_index - 1,
            substring, from_undo, mode)

    @mainthread
    def _refresh_text(self, text, *largs):
        # Refresh all the lines from a new text.
        # By using cache in internal functions, this method should be fast.
        mode = 'all'
        if len(largs) > 1:
            mode, start, finish, _lines, _lines_flags, len_lines = largs
            # start = max(0, start)
            cursor = None
        else:
            cursor = self.cursor_index()
            _lines, self._lines_flags = self._split_smart(text)
        _lines_labels = []
        _line_rects = []
        _create_label = self._create_line_label

        for x in _lines:
            lbl = _create_label(to_ar(x))
            _lines_labels.append(lbl)
            _line_rects.append(Rectangle(size=lbl.size))

        if mode == 'all':
            self._lines_labels = _lines_labels
            self._lines_rects = _line_rects
            self._lines = _lines
        elif mode == 'del':
            if finish > start:
                self._insert_lines(start,
                                   finish if start == finish else (finish + 1),
                                   len_lines, _lines_flags,
                                   _lines, _lines_labels, _line_rects)
        elif mode == 'insert':
            self._insert_lines(
                start,
                finish if (start == finish and not len_lines)
                else (finish + 1),
                len_lines, _lines_flags, _lines, _lines_labels,
                _line_rects)

        min_line_ht = self._label_cached.get_extents('_')[1]
        # with markup texture can be of height `1`
        self.line_height = max(_lines_labels[0].height, min_line_ht)
        # self.line_spacing = 2
        # now, if the text change, maybe the cursor is not at the same place as
        # before. so, try to set the cursor on the good place
        row = self.cursor_row
        self.cursor = self.get_cursor_from_index(self.cursor_index()
                                                 if cursor is None else cursor)
        # if we back to a new line, reset the scroll, otherwise, the effect is
        # ugly
        if self.cursor_row != row:
            self.scroll_x = 0
        # with the new text don't forget to update graphics again
        self._trigger_update_graphics()

    def _get_text_width(self, text, tab_width, _label_cached):
        # Return the width of a text, according to the current line options
        text = to_ar(text)

        kw = self._get_line_options()

        try:
            cid = u'{}\0{}\0{}'.format(text, self.password, kw)
        except UnicodeDecodeError:
            cid = '{}\0{}\0{}'.format(text, self.password, kw)

        width = Cache_get('textinput.width', cid)
        if width:
            return width
        if not _label_cached:
            _label_cached = self._label_cached

        text = text.replace('\t', ' ' * tab_width)
        if not self.password:
            width = _label_cached.get_extents(text)[0]
        else:
            width = _label_cached.get_extents(
                self.password_mask * len(text))[0]
        Cache_append('textinput.width', cid, width)
        return width

