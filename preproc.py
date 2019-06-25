#!/usr/bin/env python3

import os
import sys
import hashlib
import json
import requests

from archive.file_meta import get_file_instance, get_file_size, get_file_hash

FILE_SIZE_LIMIT = 2*1024*1024

class App():

    def check(self, hash):
        headers = {'Authorization': 'Bearer %s' % os.environ.get('ARCHIVE_SERVICE_TOKEN')}
        result = requests.get('%s/api/check/%s' % (os.environ.get('ARCHIVE_SERVICE_URL'), hash),
                              headers=headers)
        return result.json()['result']

    def run(self):
        filename = sys.argv[1]

        if get_file_size(filename) > FILE_SIZE_LIMIT:
            hash = get_file_hash(filename)
            if self.check(hash) == True:
                sys.stderr.write('File is already in archive, skipping\n')
                print(json.dumps({}))
                sys.exit(2)

        instance = get_file_instance(filename)
        print(json.dumps(instance.get_meta(), ensure_ascii=False))
        sys.exit(0)

if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
