#!/usr/bin/env python3

from __future__ import with_statement

import os
import re
import sys
import errno
import time

import requests
from fusepy import FUSE, FuseOSError, Operations


class Passthrough(Operations):
    def __init__(self, root):
        self.root = root

    # Helpers
    # =======

    def local_path(self, md5):
        headers = {'Authorization': 'Bearer %s' % os.environ.get('ARCHIVE_SERVICE_TOKEN')}
        result = requests.get('%s/api/image/local_filename/%s' % (os.environ.get('ARCHIVE_SERVICE_URL'), md5),
                              headers=headers)
        return result.json()['filename']

    def api_get_attr(self, md5):
        headers = {'Authorization': 'Bearer %s' % os.environ.get('ARCHIVE_SERVICE_TOKEN')}
        result = requests.get('%s/api/image/getattr/%s' % (os.environ.get('ARCHIVE_SERVICE_URL'), md5),
                              headers=headers)
        print(result.json())
        return result.json()['attrs']

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def api_request(self, filter, value):
        headers = {'Authorization': 'Bearer %s' % os.environ.get('ARCHIVE_SERVICE_TOKEN')}
        payload = {'filter': filter, 'value': value}
        url = '%s/api/image/list' % os.environ.get('ARCHIVE_SERVICE_URL')
        result = requests.post(url, headers=headers, json=payload)
        #print(result.text)
        return result.json()['files']

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print('access("%s", "%s")' % (path, mode,))

    def chmod(self, path, mode):
        print('chmod(%s, %s)' % (path, mode,))
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        print('chown(%s, %s)' % (path, mode,))
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        print('getattr(%s, %s)' % (path, fh,))

        if re.match('/\d{4}/\d{4}-\d{2}/\d{4}-\d{2}-\d{2}/[0-9a-f]{32}\..+$', path):
            st_mode = 33204
            attrs = self.api_get_attr((path.split('/')[-1]).split('.')[0])
        else:
            st_mode = 16877
            attrs = {'ctime': 1561368290, 'mtime': 1561368290, 'atime': 1561368290, 'size': 4096}

        return {'st_atime': attrs['ctime'],
                'st_ctime': attrs['ctime'],
                'st_gid': 1003,
                'st_mode': st_mode,
                'st_mtime': attrs['mtime'],
                'st_nlink': 1,
                'st_size': attrs['size'],
                'st_uid': 1001}

    def readdir(self, path, fh):
        print('readdir("%s", "%s")' % (path, fh,))

        dirents = ['.', '..']

        if path == '/':
            dirents.extend([i['file_name'] for i in self.api_request('/', '')])
        elif re.match('/\d{4}$', path):
            dirents.extend([i['file_name'] for i in self.api_request('year', path[1:])])
        elif re.match('/\d{4}/\d{4}-\d{2}$', path):
            dirents.extend([i['file_name'] for i in self.api_request('month', path.split('/')[-1])])
        elif re.match('/\d{4}/\d{4}-\d{2}/\d{4}-\d{2}-\d{2}$', path):
            dirents.extend([i['file_name'] for i in self.api_request('day', path.split('/')[-1])])
        else:
            pass

        for r in dirents:
            yield r

    def readlink(self, path):
        print('readlink("%s")' % path)
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        raise FuseOSError(errno.EACCES)

    def rmdir(self, path):
        raise FuseOSError(errno.EACCES)

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EACCES)

    def statfs(self, path):
        print('statfs("%s")' % path)
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        raise FuseOSError(errno.EACCES)

    def symlink(self, name, target):
        raise FuseOSError(errno.EACCES)

    def rename(self, old, new):
        raise FuseOSError(errno.EACCES)

    def link(self, target, name):
        raise FuseOSError(errno.EACCES)

    def utimens(self, path, times=None):
        print('utimens("%s")' % path)
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        print('open("%s", "%s")' % (path, flags,))
        full_path = self.local_path((path.split('/')[-1]).split('.')[0])
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        print('create("%s", "%s")' % (path, mode,))
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        print('read("%s", "%s")' % (path, length,))
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        raise FuseOSError(errno.EACCES)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EACCES)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(mountpoint, root):
    FUSE(Passthrough(root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1], '/')
