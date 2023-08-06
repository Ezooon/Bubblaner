from kivymd.app import MDApp
from Arabic_for_Kivy import to_ar

app = MDApp.get_running_app()
language = app.language


def plural_reform(value, plural, singular, two_form=""):
    if language == 'Arabic':
        if value == 1:
            return singular
        elif value == 2 and two_form != "":
            return two_form
        elif value == 0 or value > 10:
            return to_ar(str(value) +" "+ to_ar(singular))
        return to_ar(str(value) +" "+ to_ar(plural))
    else:  # language == 'English' or True:
        if value == 1:
            return str(value) +" "+ singular
        return str(value) +" "+ plural
