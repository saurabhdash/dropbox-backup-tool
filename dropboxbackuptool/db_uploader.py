from re import L
import dropbox
from os import listdir
from os.path import isfile, join, isdir
import os
from tqdm import tqdm
from dropbox.files import WriteMode

class UploadData:
    def __init__(self, access_token, source_dir, target_dir):
        self.access_token = access_token
        self.source = source_dir
        self.target = target_dir

    def upload_folder(self):
        """Updates folder in dropbox
        """
        dbx = dropbox.Dropbox(self.access_token)
        orgpath = self.source
        destpath = self.target
        fileslist = [f for f in listdir(orgpath) if isfile(join(orgpath, f))]
        # print(onlyfiles)
        for file in fileslist:
            file_from = join(orgpath, file)
            print(file_from)
            self.upload(dbx, file_from, join(destpath, file))

    def upload_file(self, source, dest):
        file = source.split('/')[-1] # get the file name
        dbx = dropbox.Dropbox(self.access_token)
        self.upload(dbx, source, join(dest, file))

    @staticmethod
    def upload(
            dbx,
            file_path,
            target_path,
            timeout=900,
            chunk_size=50 * 1024 * 1024,
    ):
        # dbx = dropbox.Dropbox(access_token, timeout=timeout)
        with open(file_path, "rb") as f:
            file_size = os.path.getsize(file_path)
            if file_size <= chunk_size:
                # print(
                    dbx.files_upload(f.read(), target_path, mode=dropbox.files.WriteMode.overwrite)
                    # )
            else:
                with tqdm(total=file_size, desc="Uploaded") as pbar:
                    upload_session_start_result = dbx.files_upload_session_start(
                        f.read(chunk_size)
                    )
                    pbar.update(chunk_size)
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=upload_session_start_result.session_id,
                        offset=f.tell(),
                    )
                    commit = dropbox.files.CommitInfo(path=target_path, mode=dropbox.files.WriteMode.overwrite) # mode is required to enable overwrite
                    while f.tell() < file_size:
                        if (file_size - f.tell()) <= chunk_size:
                            # print(
                                dbx.files_upload_session_finish(
                                    f.read(chunk_size), cursor, commit
                                )
                            # )
                        else:
                            dbx.files_upload_session_append(
                                f.read(chunk_size),
                                cursor.session_id,
                                cursor.offset,
                            )
                            cursor.offset = f.tell()
                        pbar.update(chunk_size)

    def upload_folder_recursive(self):
        pass
  


class DropboxBackupTool:
    def __init__(self, access_token, source_dir):
        self.setup_db(access_token, source_dir)
        self.upload(source_dir, '/')

    def setup_db(self, access_token, source_dir):
        self.access_token = access_token
        self.source = source_dir
        self.target = '/'
        self.dbx = dropbox.Dropbox(self.access_token)

    def upload(self, current_dir, target_dir):

        all_contents = listdir(current_dir)

        # Base case: if the directory is empty, dont do anything
        if len(all_contents) == 0:
            return

        # If the content is a file, upload it; if it is a directory, recursively call the function
        for content in all_contents:
            # print(f'content: {content} isfile:{isfile(content)} isdir:{isdir(content)}')
            if isfile(join(current_dir, content)):
                print(f'filepath: {join(current_dir, content)} target: {join(target_dir, content)}')
                self.upload_file(join(current_dir, content), target_dir)
            if isdir(join(current_dir, content)):
                print(f'moving into directory: {join(current_dir, content)}')
                self.upload(join(current_dir, content), join(target_dir, content))


    def upload_file(self, source, dest):
        file = source.split('/')[-1] # get the file name
        # dbx = dropbox.Dropbox(self.access_token)
        self._upload(self.dbx, source, join(dest, file))

    @staticmethod
    def _upload(
            dbx,
            file_path,
            target_path,
            timeout=900,
            chunk_size=50 * 1024 * 1024,
    ):
        # dbx = dropbox.Dropbox(access_token, timeout=timeout)
        with open(file_path, "rb") as f:
            file_size = os.path.getsize(file_path)
            if file_size <= chunk_size:
                # print(
                    dbx.files_upload(f.read(), target_path, mode=dropbox.files.WriteMode.overwrite)
                    # )
            else:
                with tqdm(total=file_size, desc="Uploaded") as pbar:
                    upload_session_start_result = dbx.files_upload_session_start(
                        f.read(chunk_size)
                    )
                    pbar.update(chunk_size)
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=upload_session_start_result.session_id,
                        offset=f.tell(),
                    )
                    commit = dropbox.files.CommitInfo(path=target_path, mode=dropbox.files.WriteMode.overwrite) # mode is required to enable overwrite
                    while f.tell() < file_size:
                        if (file_size - f.tell()) <= chunk_size:
                            # print(
                                dbx.files_upload_session_finish(
                                    f.read(chunk_size), cursor, commit
                                )
                            # )
                        else:
                            dbx.files_upload_session_append(
                                f.read(chunk_size),
                                cursor.session_id,
                                cursor.offset,
                            )
                            cursor.offset = f.tell()
                        pbar.update(chunk_size)
                        
def main():
    with open("/hdd2/extra_home/sdash38/dropbox_keys/backup.txt", "r") as f:
        access_token = f.read().strip()
    orgpath = './'
    destpath = '/'
    uploaddata = UploadData(access_token, orgpath)
    # uploaddata.upload_file(os.path.join(orgpath,"test_file.txt"), destpath)
    uploaddata.upload_folder()
    # uploaddata.upload_folder()

def main2():
    with open("/hdd2/extra_home/sdash38/dropbox_keys/backup.txt", "r") as f:
        access_token = f.read().strip()
    orgpath = './'
    dbtool = DropboxBackupTool(access_token, orgpath)
    # dbtool.upload(os.getcwd(), '/')


if __name__ == '__main__':
    main2()
    