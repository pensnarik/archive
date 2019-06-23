from archive.file_archive_meta import FileArchiveMeta
from archive.file_image_meta import FileImageMeta
from archive.file_video_meta import FileVideoMeta
from archive.file_meta import FileMeta

def get_file_instance(filename):
    extension = filename.lower().split('.')[-1]
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
        return FileImageMeta(filename)
    elif extension in ['tgz', 'zip', 'rar', 'gz', 'xz']:
        return FileArchiveMeta(filename)
    elif extension in ['mp4', 'wmv', 'flv', 'avi', 'webm']:
        return FileVideoMeta(filename)
    else:
        return FileMeta(filename)