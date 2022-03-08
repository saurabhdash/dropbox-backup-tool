from re import L
import dropbox
from os import listdir
from os.path import isfile, join, isdir
import os
from tqdm import tqdm
from dropbox.files import WriteMode
import os
import psutil
import multiprocessing
from utils_mp import MyPool
from functools import partialmethod, partial
import time

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

  

# class DropboxBackupTool:
#     def __init__(self, access_token, source_dir, threads=2):
#         self.setup_db(access_token, source_dir)
#         self.setup_mp(threads)
#         upload(source_dir, '/', )
        

#     def setup_mp(self, threads):
#         self.process_id = os.getpid()
#         self.threads = threads
#         self.parallel = None

#     def setup_db(self, access_token, source_dir):
#         self.access_token = access_token
#         self.source = source_dir
#         self.target = '/'
#         self.dbx = dropbox.Dropbox(self.access_token)

class DropBoxConfig:
    def __init__(self, access_token, threads):
        self.access_token = access_token
        # self.source = source_dir
        # self.target = target_dir
        self.threads = threads
        self.parallel = None
        self.dbx = dropbox.Dropbox(self.access_token)

        self.main_process_id = os.getpid()
        self.children = 0
        self.active_processes = 0
        self.pool = MyPool(self.threads)

def upload(current_dir, target_dir, dbconfig):

    all_contents = listdir(current_dir)

    # Base case: if the directory is empty, dont do anything
    if len(all_contents) == 0:
        return

    main_process = psutil.Process(dbconfig.main_process_id)
    children = main_process.children(recursive=True)
    active_processes = len(children) + 1 #plus parent
    new_processes = len(all_contents)

    print('Current active processes: ', active_processes)
    print('New processes: ', new_processes)
    pool = dbconfig.pool
    if dbconfig.threads > active_processes: # if there are more processes than threads, start new processes
        pool.map_async(partial(dispatch_upload, current_dir=current_dir, target_dir=target_dir, dbconfig=dbconfig), all_contents)
    else:
        for content in all_contents:
            # pool.apply_async(partial(dispatch_upload, current_dir=current_dir, target_dir=target_dir, dbconfig=dbconfig), (content,))
            dispatch_upload(content=content, current_dir=current_dir, target_dir=target_dir, dbconfig=dbconfig)

def dispatch_upload(content, current_dir, target_dir, dbconfig): 
    if isfile(join(current_dir, content)):
        print(f'filepath: {join(current_dir, content)} target: {join(target_dir, content)}')
        upload_file(join(current_dir, content), target_dir, dbconfig)
    
    elif isdir(join(current_dir, content)):
        # If the content is a file, upload it; if it is a directory, recursively call the function
        print(f'moving into directory: {join(current_dir, content)}')
        upload(join(current_dir, content), join(target_dir, content), dbconfig)


def upload_file(source, dest, dbconfig):
    file = source.split('/')[-1] # get the file name
    # dbx = dropbox.Dropbox(self.access_token)
    _upload(source, join(dest, file), dbconfig)


def _upload(
        file_path,
        target_path,
        dbconfig,
        timeout=900,
        chunk_size=50 * 1024 * 1024,
):
    # dbx = dropbox.Dropbox(dbconfig.access_token, timeout=timeout)
    dbx = dbconfig.dbx
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

def main3():
    with open("/hdd2/extra_home/sdash38/dropbox_keys/backup.txt", "r") as f:
        access_token = f.read().strip()
    dbconfig = DropBoxConfig(access_token=access_token, threads=16)
    start = time.time()
    upload('./', '/', dbconfig)
    print(f'Time taken: {(time.time() - start)/3600} hours')
    dbconfig.pool.close()
    dbconfig.pool.join()

if __name__ == '__main__':
    # g = partial(add,a=1, c=2)
    # g(5)

    main3()
    