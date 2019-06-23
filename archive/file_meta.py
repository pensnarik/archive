import os
import hashlib

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