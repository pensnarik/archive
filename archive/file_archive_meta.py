import os
import subprocess

from archive.file_meta import FileMeta, get_file_instance

class FileArchiveMeta(FileMeta):

    def __init__(self, filename, precompiled_hash=None, parent_file_hash=None):
        super(FileArchiveMeta, self).__init__(filename, precompiled_hash, parent_file_hash)
        self.filetype = 'archive'

    def unarchive(self):
        extension = self.filename.lower().split('.')[-1]

        if extension == 'tgz':
            subprocess.run('tar -zxf "%s" --directory ./tmp-unarchive/%s/' % (self.filename, self.hash),
                           shell=True, check=True)
        elif extension == 'gz':
            subprocess.run('gunzip -c "%s" > ./tmp-unarchive/%s/%s' % \
                            (self.filename, self.hash, os.path.basename('.'.join(self.filename.split('.')[:-1]))),
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

    def cleanup(self):
        os.system('rm -rf ./tmp-unarchive/%s' % self.hash)

    def get_meta(self):
        meta = super(FileArchiveMeta, self).get_meta()
        try:
            # We need to unpack the archive and process all its files recursively
            self.cleanup()
            os.mkdir('./tmp-unarchive/%s' % self.hash)

            try:
                self.unarchive()
            except subprocess.CalledProcessError:
                self.cleanup()
                meta[self.hash]['corrupted'] = 'true'
                return meta

            meta[self.hash]['included_files'] = {}

            for root, dir, files in os.walk('./tmp-unarchive/%s' % self.hash):
                for file in files:
                    filename = os.path.join(root, file)
                    # We don't process symlinks
                    if os.path.islink(filename): continue
                    instance = get_file_instance(filename, precompiled_hash=None, parent_file_hash=self.hash)
                    meta[self.hash]['included_files'].update(instance.get_meta())
        finally:
            self.cleanup()

        return meta
