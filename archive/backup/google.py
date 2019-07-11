import json
import os.path
import requests
import subprocess

from archive.backup import ArchiveBackup
from archive.file_meta import get_file_hash
from archive.api import backup

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']

class ArchiveBackupGoogle(ArchiveBackup):

    credentials = {}

    def __init__(self):
        with open('credentials.json') as cf:
            self.credentials = json.load(cf)

    def encrypt(self, filename, hash):
        output_filename = "./tmp-unarchive/%s.gpg" % hash
        subprocess.run('gpg --encrypt --recipient "Andrei Zhidenkov" --output "%s" "%s"' % \
                       (output_filename, filename,), shell=True, check=True)
        return output_filename

    def get_headers(self):
        return {'Authorization': 'Bearer %s' % self.credentials['access_token']}

    def refresh_token(self):
        payload = {'client_id': self.credentials['client_id'],
                   'client_secret': self.credentials['client_secret'],
                   'refresh_token': os.environ['ARCHIVE_GDRIVE_REFRESH_TOKEN'],
                   'grant_type': 'refresh_token'}

        r = requests.post("https://www.googleapis.com/oauth2/v4/token", data=payload)

        if 'access_token' in r.json():
            self.credentials['access_token'] = r.json()['access_token']
            with open('credentials.json', 'wt') as f:
                f.write(json.dumps(self.credentials))
        else:
            raise Exception('Could not refresh access token')

        return True

    def backup(self, filename):
        file_hash = get_file_hash(filename)
        encrypted_filename = self.encrypt(filename, file_hash)

        para = {
            'name': '%s.gpg' % file_hash,
            'hash': file_hash,
            # TODO: Should be configurable
            'parents': ['1YhyEfYlfYhsSlQ37zcA5o__CJ-NHYGyd']
        }
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': open(encrypted_filename, "rb")
        }

        try_googleapi_request = True

        while try_googleapi_request:
            r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                              headers=self.get_headers(),
                              files=files)

            if r.status_code == 401:
                if self.refresh_token():
                    try_googleapi_request = True
                else:
                    raise Exception('Could not update API token')
            elif r.status_code == 403:
                os.remove(encrypted_filename)
                raise Exception(r.json()['error']['message'])
            else:
                try_googleapi_request = False

        os.remove(encrypted_filename)
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
