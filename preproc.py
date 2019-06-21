#!/usr/bin/env python3

import os
import sys
import hashlib
import json
import subprocess
import math

from PIL import Image, ExifTags
from PIL.JpegImagePlugin import JpegImageFile

EXCLUDE_EXIF = ['MakerNote', 'UserComment']

def get_file_instance(filename):
    extension = filename.lower().split('.')[-1]
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
        return FileImageMeta(filename)
    elif extension in ['tgz', 'zip', 'rar', 'gz', 'xz']:
        return FileMetaArchive(filename)
    elif extension in ['mp4', 'wmv', 'flv', 'avi', 'webm']:
        return FileVideoMeta(filename)
    else:
        return FileMeta(filename)

class FileMeta():

    def __init__(self, filename):
        self.filename = filename
        self.filetype = 'text'
        self.hash = self.get_hash()

    def get_hash(self):
        with open(self.filename, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        return md5

    def get_meta(self):
        statinfo = os.stat(self.filename)

        file_meta = {'filename': self.filename,
                     'size': statinfo.st_size,
                     'ctime': statinfo.st_ctime,
                     'mtime': statinfo.st_mtime,
                     'filetype': self.filetype}

        return {self.hash: file_meta}

class FileImageMeta(FileMeta):

    def __init__(self, filename):
        super(FileImageMeta, self).__init__(filename)
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

        for y in range(0, width):
            for x in range(0, height):
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
        return hash_as_str

    def exit2text(self, value):
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

    def get_image_info(self):
        try:
            image = Image.open(self.filename)
        except Exception:
            return {}

        if isinstance(image, JpegImageFile) and image._getexif() is not None:
            exif = {
                ExifTags.TAGS[k]: self.exit2text(v)
                for k, v in image._getexif().items()
                if k in ExifTags.TAGS and ExifTags.TAGS[k] not in EXCLUDE_EXIF
            }
        else:
            exif = {}

        meta = {}
        meta['width'] = image.width
        meta['height'] = image.height
        meta['format'] = image.format
        meta['exif'] = exif
        meta['pcp_hash'] = self.get_pcp_hash()

        return meta

class FileMetaArchive(FileMeta):

    def __init__(self, filename):
        super(FileMetaArchive, self).__init__(filename)
        self.filetype = 'archive'

    def unarchive(self):
        extension = self.filename.lower().split('.')[-1]

        if extension in ('tgz', 'gz'):
            subprocess.run('tar -zxf "%s" --directory ./%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        elif extension == 'xz':
            subprocess.run('tar -Jxf "%s" --directory ./%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        elif extension == 'zip':
            subprocess.run('unzip -qo "%s" -d ./%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        elif extension == 'rar':
            subprocess.run('unrar -inul e "%s" ./%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        else:
            return False

        return True

    def get_meta(self):
        meta = super(FileMetaArchive, self).get_meta()
        # We need to unpack the archive and process all its files recursively
        os.system('rm -rf %s' % self.hash)
        os.mkdir('./%s' % self.hash)

        try:
            self.unarchive()
        except subprocess.CalledProcessError:
            os.system('rm -rf %s' % self.hash)
            meta[self.hash]['corrupted'] = 'true'
            return meta

        meta[self.hash]['included_files'] = {}

        for root, dir, files in os.walk('./%s' % self.hash):
            for file in files:
                filename = os.path.join(root, file)
                # We don't process symlinks
                if os.path.islink(filename): continue
                instance = get_file_instance(filename)
                meta[self.hash]['included_files'].update(instance.get_meta())
        # Clean up
        os.system('rm -rf %s' % self.hash)
        return meta

class FileVideoMeta(FileMeta):
    def __init__(self, filename):
        super(FileMetaArchive, self).__init__(filename)
        self.filetype = 'video'

class App():

    def run(self):
        filename = sys.argv[1]

        instance = get_file_instance(filename)

        print(json.dumps(instance.get_meta(), ensure_ascii=False))

if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
