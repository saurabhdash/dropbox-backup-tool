from re import L
from tracemalloc import start
import dropbox
from os import listdir
from os.path import isfile, join, isdir, isabs
import os
from tqdm import tqdm
from dropbox.files import WriteMode
import os
import psutil
import multiprocessing
from utils_mp import MyPool
from functools import partialmethod, partial
import time
import subprocess

class DropboxBackupTool:
    def __init__(self, access_token, source_dir, num_processes=1):
        self.contents = self.get_content_list(source_dir)
        self.source_dir = source_dir
        self.__access_token = access_token
        self.num_processes = num_processes
        assert num_processes < 24, "Number of processes should be less than 24"

    @staticmethod
    def get_content_list(current_dir):
        all_contents = listdir(current_dir)
        return all_contents

    @staticmethod
    def compress_dir(name):
        if isabs(name):
            dir_name = name.split('/')[-1]
        else:
            dir_name = name

        command = f"tar -I pigz -cf {dir_name}.tgz {name}"
        start = time.time()
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        print(f'time taken for compression of {name}: {time.time() - start}')

    @staticmethod
    def uncompress(name):
        command = f"tar -I pigz -xf {name}"
        start = time.time()
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        print(f'time taken for decompression of {name}: {time.time() - start}')
    
    @staticmethod
    def delete_tgz(name):
        tarfile =  f"{name}.tgz"
        os.remove(tarfile)
        print(f"deleted {tarfile}")

    def _upload(
            self,
            file_path,
            target_path,
            timeout=900,
            chunk_size=50 * 1024 * 1024,
    ):
        dbx = dropbox.Dropbox(self.__access_token, timeout=timeout)
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
                                dbx.files_upload_session_finish_batch(
                                    f.read(chunk_size), cursor, commit
                                )
                            # )
                        else:
                            dbx.files_upload_session_append_v2(
                                f.read(chunk_size),
                                cursor.session_id,
                                cursor.offset,
                            )
                            cursor.offset = f.tell()
                        pbar.update(chunk_size)

    def _create_backup_content(self, content):
        if(isfile(join(self.source_dir, content))):
            print(f'file: {join(self.source_dir, content)}')
            self._upload(join(self.source_dir, content), join('/', content))

        elif(isdir(join(self.source_dir, content))):
            print(f'dir: {join(self.source_dir, content)}')
            self.compress_dir(content)
            print(f"uploading: {join(self.source_dir, content)+'.tgz'}...")
            self._upload(join(self.source_dir, content)+'.tgz', join('/', content+'.tgz'))
            print('finished uploading')
            self.delete_tgz(content)

    def _create_backup(self):
        for content in self.contents:
            self._create_backup_content(content)

    def _create_backup_mp(self):
        with MyPool(self.num_processes) as pool:
            pool.map(self._create_backup_content, self.contents)

    # def backup_single_dir(self, dirpath):
    #     if not isdir(dirpath):
    #         raise NotADirectoryError("Can't find directory")
    #     if isabs(dirpath):
    #         dir_name = dirpath.split('/')[-1]
    #     else:
    #         dir_name = dirpath

    #     start = time.time()
    #     print(f'dir: {dirpath}')
    #     self.compress_dir(dirpath)
    #     print(f"uploading: {join(self.source_dir, dir_name)+'.tgz'}...")
    #     self._upload(join(dirpath, f'{dir}.tgz'), join('/', dir_name+'.tgz'))
    #     print('finished uploading')
    #     self.delete_tgz(dirpath)
    #     print(f"Total time taken for backup of {dirpath}: {time.time() - start}")

    def backup_all(self):
        start = time.time()
        if self.num_processes == 1:
            self._create_backup()
        else:
            self._create_backup_mp()
        print(f"Total time taken for backup: {time.time() - start}")

if __name__ == '__main__':
    with open("/hdd2/extra_home/sdash38/dropbox_keys/backup.txt", "r") as f:
        access_token = f.read().strip()

    dbtool = DropboxBackupTool(access_token, './', num_processes=4)
    dbtool.backup_all()
    # dbtool.backup_single_dir('/hdd2/extra_home/sdash38/matchbox')
    # dbtool.compress_dir('./.git')
    # dbtool.uncompress('test_folder.tgz')