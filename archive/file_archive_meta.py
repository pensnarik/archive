import os
import subprocess

from archive.file_meta import FileMeta, get_file_instance

class FileArchiveMeta(FileMeta):

    def __init__(self, filename, precompiled_hash=None):
        super(FileArchiveMeta, self).__init__(filename)
        self.filetype = 'archive'

    def unarchive(self):
        extension = self.filename.lower().split('.')[-1]

        if extension in ('tgz', 'gz'):
            subprocess.run('tar -zxf "%s" --directory ./tmp-unarchive/%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        elif extension == 'xz':
            subprocess.run('tar -Jxf "%s" --directory ./tmp-unarchive/%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        elif extension == 'zip':
            subprocess.run('unzip -qo "%s" -d ./tmp-unarchive/%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        elif extension == 'rar':
            subprocess.run('unrar -inul e "%s" ./tmp-unarchive/%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        else:
            return False

        return True

    def get_meta(self):
        meta = super(FileArchiveMeta, self).get_meta()
        # We need to unpack the archive and process all its files recursively
        os.system('rm -rf ./tmp-unarchive/%s' % self.hash)
        os.mkdir('./tmp-unarchive/%s' % self.hash)

        try:
            self.unarchive()
        except subprocess.CalledProcessError:
            os.system('rm -rf ./tmp-unarchive/%s' % self.hash)
            meta[self.hash]['corrupted'] = 'true'
            return meta

        meta[self.hash]['included_files'] = {}

        for root, dir, files in os.walk('./tmp-unarchive/%s' % self.hash):
            for file in files:
                filename = os.path.join(root, file)
                # We don't process symlinks
                if os.path.islink(filename): continue
                instance = get_file_instance(filename)
                meta[self.hash]['included_files'].update(instance.get_meta())
        # Clean up
        os.system('rm -rf tmp-unarchive/%s' % self.hash)
        return meta
