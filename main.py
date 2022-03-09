from dropboxbackuptool.db_uploader import DropboxBackupTool

if __name__ == '__main__':
    with open("/hdd2/extra_home/sdash38/dropbox_keys/backup.txt", "r") as f:
        access_token = f.read().strip()

    dbtool = DropboxBackupTool(access_token, '/hdd2/extra_home/sdash38/test_folder', num_processes=2)
    dbtool.backup_all()