from archive.file_meta import FileMeta

class FileVideoMeta(FileMeta):
    def __init__(self, filename, info):
        super(FileVideoMeta, self).__init__(filename, info)
        self.filetype = 'video'
