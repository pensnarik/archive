#!/usr/bin/env python3

import os
import sys
import hashlib
import json

from archive.file_meta import get_file_instance

class App():

    def run(self):
        filename = sys.argv[1]

        instance = get_file_instance(filename)
        print(json.dumps(instance.get_meta(), ensure_ascii=False))

if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
