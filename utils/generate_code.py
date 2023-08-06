from qrcode import make
from datetime import datetime
from barcode import __BARCODE_MAP as MAP
from barcode.writer import ImageWriter, Image, ImageDraw
from kivy.uix.image import Image as KImage


class PNGWriter(ImageWriter):
    def _init(self, code):
        self.text = ''
        size = self.calculate_size(len(code[0]), len(code), self.dpi)
        self._image = Image.new(self.mode, size, self.background)
        self._draw = ImageDraw.Draw(self._image)


def generate_qr(data, name='qr'):
    qr = make(data)
    # path = 'cache/'+str(datetime.now()).replace(':', "-")+"_qr.png"
    path = 'cache/' + name + ".png"
    qr.save(path)
    return KImage(source=path).texture


def generate_barcode(data, type='ean13', name='barcode'):
    # path = 'cache/'+str(datetime.now()).replace(':', "-")+"_barcode"
    path = 'cache/' + name
    try:
        bc = MAP[type](data, writer=PNGWriter())
    except:
        bc = MAP["code128"](data, writer=PNGWriter())
    bc.save(path)

    return KImage(source=path+'.png').texture

