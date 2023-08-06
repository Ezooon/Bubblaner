from utils.cropimage import crop_image
from kivy.uix.image import Image


def round_image(source="assets/images/user.jpg", image_instance=None):
    n_source = "assets/images/round_temp.png"
    if not source:
        return None
    if image_instance:
        s = image_instance.texture_size
        s = min(s), min(s)
        image_instance._coreimage.save(source)
        crop_image(s, source, n_source, int(s[0]/2))
        image_instance.source = n_source
        return
    else:
        s = Image(source=source).texture_size
        s = min(s), min(s)
        crop_image(s, source, n_source, int(max(s)/2))
    return Image(source=n_source).texture

