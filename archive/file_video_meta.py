from archive.file_meta import FileMeta

class FileVideoMeta(FileMeta):
    def __init__(self, filename, precompiled_hash=None, parent_file_hash=None):
        super(FileVideoMeta, self).__init__(filename, precompiled_hash, parent_file_hash)
        self.filetype = 'video'
