import json
import os.path
import requests

from archive.backup import ArchiveBackup
from archive.file_meta import get_file_hash
from archive.api import backup

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']

class ArchiveBackupGoogle(ArchiveBackup):

    def __init__(self):
        pass

    def backup(self, filename):
        file_hash = get_file_hash(filename)
        headers = {'Authorization': 'Bearer %s' % os.environ['ARCHIVE_GDRIVE_TOKEN']}

        para = {
            'name': '%s.jpg' % file_hash,
            'hash': file_hash,
            # TODO: Should be configurable
            'parents': ['1YhyEfYlfYhsSlQ37zcA5o__CJ-NHYGyd']
        }
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': open(filename, "rb")
        }

        r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                          headers=headers,
                          files=files)

        backup(file_hash, 'google', r.json().get('id'))

    def list(self):
        # Call the Drive v3 API
        results = self.service.files().list(
            pageSize=1000, fields="nextPageToken, files(*)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                print(item)
                # print(u'{0} ({1})'.format(item['name'], item['id']))
