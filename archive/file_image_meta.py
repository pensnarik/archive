import os
import re
import math
import subprocess

from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
from PIL.JpegImagePlugin import JpegImageFile

from archive.file_meta import FileMeta
from archive.gps_tools import get_lat_lon, get_googlemaps_link

EXCLUDE_EXIF = ['MakerNote', 'UserComment']

class FileImageMeta(FileMeta):

    def __init__(self, filename, precompiled_hash=None, parent_file_hash=None):
        super(FileImageMeta, self).__init__(filename, precompiled_hash, parent_file_hash)
        self.filetype = 'image'

    def get_meta(self):
        meta = super(FileImageMeta, self).get_meta()
        meta[self.hash].update(self.get_image_info())
        return meta

    def get_pcp_hash(self):
        command = 'convert -depth 8 -strip -type Grayscale -geometry 8x8! "%s" "%s/%s.png"' % \
                  (self.filename, 'pcp_hash', self.hash)

        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError:
            return '0000000000000000'

        im = Image.open('pcp_hash/%s.png' % self.hash)
        width, height = im.size

        if width != height:
            raise Exception('Width != height')

        sum = 0

        for y in range(0, height):
            for x in range(0, width):
                pixel = im.getpixel((x, y))
                sum += pixel

        average = sum / (width*height)

        hash = list()

        for y in range(0, width):
            bits = 0
            for x in range(0, height):
                bit = int(im.getpixel((x, y)) > average)
                bits += bit * math.pow(2, 7 - x)
            hash.append(int(bits))

        hash_as_str = ''.join(['%.2x' % i for i in hash])

        os.system('rm pcp_hash/%s.png' % self.hash)

        return hash_as_str

    def exif2text(self, value):
        """ Helper function """
        if isinstance(value, str):
            result = str(value)
        elif isinstance(value, int):
            result = str(value)
        elif isinstance(value, bytes):
            result = value.hex()
        else:
            result = str(value)

        return result.replace('\u0000', '')

    def exif_datetime(self, exif):
        if 'DateTime' in exif:
            value = exif['DateTime']
        else:
            return None

        if re.match('^\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}', value):
            return '-'.join(value.split(' ')[0].split(':')) + ' ' + value.split(' ')[1]
        else:
            return None
            # raise Exception('Invalid date time format in EXIF: "%s"' % value)

    def get_image_info(self):
        try:
            image = Image.open(self.filename)
        except Exception:
            return {}

        if isinstance(image, JpegImageFile) and image._getexif() is not None:
            info = image._getexif()
            exif = {}
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == 'GPSInfo':
                    gps_data = {}
                    # print(value)
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        if isinstance(value[t], bytes):
                            gps_data[sub_decoded] = str(value[t])
                        else:
                            if isinstance(value[t], str):
                                gps_data[sub_decoded] = value[t].replace('\u0000', '')
                            else:
                                gps_data[sub_decoded] = value[t]
                    exif[decoded] = gps_data
                elif decoded in EXCLUDE_EXIF:
                    continue
                else:
                    exif[decoded] = self.exif2text(value)
        else:
            exif = {}

        meta = {}
        meta['width'] = image.width
        meta['height'] = image.height
        meta['format'] = image.format.lower()
        meta['mode'] = image.mode
        meta['exif'] = exif
        meta['pcp_hash'] = self.get_pcp_hash()

        if 'GPSInfo' in exif and get_lat_lon(exif) != (None, None):
            meta['latlon'] = get_lat_lon(exif)
            meta['googlemaps'] = get_googlemaps_link(meta['latlon'])

        if self.exif_datetime(exif) is not None:
            meta['exif_datetime'] = self.exif_datetime(exif)

        return meta
