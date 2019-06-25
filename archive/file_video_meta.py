from archive.file_meta import FileMeta

class FileVideoMeta(FileMeta):
    def __init__(self, filename, precompiled_hash=None):
        super(FileVideoMeta, self).__init__(filename)
        self.filetype = 'video'
