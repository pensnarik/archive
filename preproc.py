#!/usr/bin/env python3

import os
import sys
import hashlib
import json
import requests
import subprocess

from archive.file_meta import get_file_instance, get_file_size, get_file_hash

FILE_SIZE_LIMIT = 2*1024*1024*1024

class App():

    def check(self, hash):
        headers = {'Authorization': 'Bearer %s' % os.environ.get('ARCHIVE_SERVICE_TOKEN')}
        result = requests.get('%s/api/check/%s' % (os.environ.get('ARCHIVE_SERVICE_URL'), hash),
                              headers=headers)
        return result.json()['result']

    def check_environment(self):
        for env in ['ARCHIVE_SERVICE_URL', 'ARCHIVE_SERVICE_TOKEN', 'ARCHIVE_HOSTNAME']:
            if not (env in os.environ):
                raise Exception('%s environmemt variable is not set, please refer the ' \
                                'documentation' % env)

    def download_remote_file(self, url):
        """
        Downloads remote file into local directory
        """
        filename = './tmp-unarchive/%s.%s' % (hashlib.md5(url.encode('utf-8')).hexdigest(), url.split('.')[-1])
        subprocess.run('curl -o "%s" "%s"' % (filename, url), shell=True, check=True)
        if os.path.exists(filename):
            return filename
        else:
            raise Exception('Could not download file "%s"' % url)

    def process_file(self, filename):
        info = {}
        if filename.startswith('http://') or filename.startswith('https://'):
            full_path = self.download_remote_file(filename)
            # Save original file URL
            info['url'] = filename
        else:
            full_path = os.path.abspath(filename)

        if get_file_size(full_path) > FILE_SIZE_LIMIT:
            hash = get_file_hash(full_path)
            if self.check(hash) == True:
                sys.stderr.write('File is already in archive, skipping\n')
                return {hash: {'exists': True}}

        instance = get_file_instance(full_path, info)
        return instance.get_meta()

    def run(self):
        self.check_environment()

        result = {}

        if not sys.stdin.isatty():
            for filename in sys.stdin.readlines():
                result.update(self.process_file(filename.strip()))
        else:
            result.update(self.process_file(sys.argv[1]))

        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)

if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
