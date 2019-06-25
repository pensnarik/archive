import os
import hashlib

def get_file_instance(filename, precompiled_hash=None):
    from archive.file_archive_meta import FileArchiveMeta
    from archive.file_image_meta import FileImageMeta
    from archive.file_video_meta import FileVideoMeta

    extension = filename.lower().split('.')[-1]
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
        return FileImageMeta(filename, precompiled_hash)
    elif extension in ['tgz', 'zip', 'rar', 'gz', 'xz']:
        return FileArchiveMeta(filename, precompiled_hash)
    elif extension in ['mp4', 'wmv', 'flv', 'avi', 'webm']:
        return FileVideoMeta(filename, precompiled_hash)
    else:
        return FileMeta(filename, precompiled_hash)

def get_file_hash(filename):
    with open(filename, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    return md5

def get_file_size(filename):
    statinfo = os.stat(filename)
    return statinfo.st_size

class FileMeta():

    def __init__(self, filename, precompiled_hash=None):
        self.filename = filename
        self.filetype = 'text'
        if precompiled_hash is not None:
            self.hash = precompiled_hash
        else:
            self.hash = get_file_hash(self.filename)

    def get_meta(self):
        statinfo = os.stat(self.filename)

        file_meta = {'filename': self.filename,
                     'size': statinfo.st_size,
                     'ctime': statinfo.st_ctime,
                     'mtime': statinfo.st_mtime,
                     'filetype': self.filetype}

        return {self.hash: file_meta}
