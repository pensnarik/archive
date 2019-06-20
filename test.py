#!/usr/bin/env python3

from archive.file import FilePath, LocalFile

f = LocalFile(FilePath('test.py'))

print(f.get_md5())
