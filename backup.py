#!/usr/bin/env python3

import sys

from archive.backup.google import ArchiveBackupGoogle

class App():

    def get_backup_service_instance(self, service):
        if service == 'google':
            return ArchiveBackupGoogle()
        else:
            raise NotImplementedError('Backup method for %s is not implemented' % service)

    def run(self):
        # TODO:
        # 1. Check that there is no backups for this file
        service = sys.argv[1]
        file = sys.argv[2]

        backup = self.get_backup_service_instance(service)
        backup.backup(file)

if __name__ == '__main__':
    app = App()
    sys.exit(app.run())
