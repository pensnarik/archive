import os
import hashlib

def get_file_instance(filename):
    from archive.file_archive_meta import FileArchiveMeta
    from archive.file_image_meta import FileImageMeta
    from archive.file_video_meta import FileVideoMeta

    extension = filename.lower().split('.')[-1]
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
        return FileImageMeta(filename)
    elif extension in ['tgz', 'zip', 'rar', 'gz', 'xz']:
        return FileArchiveMeta(filename)
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