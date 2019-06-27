import os
import sys
import hashlib

def get_file_instance(filename, info):

    from archive.file_archive_meta import FileArchiveMeta
    from archive.file_image_meta import FileImageMeta
    from archive.file_video_meta import FileVideoMeta

    extension = filename.lower().split('.')[-1]
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
        return FileImageMeta(filename, info)
    elif extension in ['tgz', 'zip', 'rar', 'gz', 'xz']:
        return FileArchiveMeta(filename, info)
    elif extension in ['mp4', 'wmv', 'flv', 'avi', 'webm']:
        return FileVideoMeta(filename, info)
    else:
        return FileMeta(filename, info)

def get_file_hash(filename):
    with open(filename, 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    return md5

def get_file_size(filename):
    statinfo = os.stat(filename)
    return statinfo.st_size

class FileMeta():

    def __init__(self, filename, info):
        """
            `filename` is a local filename here, class methods should be able
            to access file located by its filename using only os module methods
            `read`, `open`, etc.
        """
        self.filename = filename
        self.filetype = 'text'
        self.info = info
        self.parent_file_hash = info.get('parent_file_hash')
        self.precompiled_hash = info.get('precompiled_hash')

        if self.precompiled_hash is not None:
            self.hash = precompiled_hash
        else:
            self.hash = get_file_hash(self.filename)

    def get_filename(self):
        if 'url' in self.info:
            return self.info['url']

        if self.parent_file_hash is None:
            return 'file://%s:%s' % (os.environ['ARCHIVE_HOSTNAME'], self.filename)
        else:
            return 'archived://%s:%s' % (self.parent_file_hash,
                                         self.filename.replace('./tmp-unarchive/%s' % self.parent_file_hash, ''))

    def get_meta(self):
        statinfo = os.stat(self.filename)

        file_meta = {'filename': self.get_filename(),
                     'size': statinfo.st_size,
                     'ctime': statinfo.st_ctime,
                     'mtime': statinfo.st_mtime,
                     'filetype': self.filetype}

        return {self.hash: file_meta}
