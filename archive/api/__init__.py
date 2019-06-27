import os
import requests



def backup(hash, service, uid):
    headers = {'Authorization': 'Bearer %s' % os.environ.get('ARCHIVE_SERVICE_TOKEN')}
    payload = {'hash': hash, 'service': service, 'uid': uid}
    result = requests.post('%s/api/backup' % (os.environ.get('ARCHIVE_SERVICE_URL')),
                           headers=headers, json=payload)

    return result.json()['id']
