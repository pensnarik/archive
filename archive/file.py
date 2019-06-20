import os
import hashlib

class FilePath():

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path

class File():

    def __init__(self, file_path):
        self.file_path = file_path
        self.md5 = self.get_md5()

    def get_md5(self):
        return hashlib.md5(self.read()).hexdigest()

    def read(self):
        raise NotImplementedError

class LocalFile(File):

    def read(self):
        with open(str(self.file_path), 'rb') as f:
            return f.read()
