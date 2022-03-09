import dropbox
from os import listdir, mkdir
from os.path import isfile, join, isdir, isabs
import os
from tqdm import tqdm
from dropbox.files import WriteMode
import os
import multiprocessing
import time
import subprocess
from pathlib import Path

class DropboxBackupTool:
    '''
    DropBox Backup Tool
    '''
    def __init__(self, args):
        self.mode = args.mode
        self.source_dir = args.source_dir # source directory
        self.contents = self.get_content_list(args.source_dir) # list of all files and folders in source_dir
        self.__access_token = self.read_token(args.token_file) # access token
        self.num_processes = args.num_processes # number of processes to use for multiprocessing
        assert args.num_processes < 24, "Number of processes should be less than 24"

    @staticmethod
    def read_token(filepath):
        '''
        Read access token from file
        '''
        with open(filepath, 'r') as f:
            return f.read().strip()

    @staticmethod
    def get_content_list(current_dir):
        '''
        Get list of all files and folders in current_dir
        args:
            current_dir: path to directory
        returns:
            list of all files and folders in current_dir
        '''
        all_contents = listdir(current_dir)
        return all_contents

    @staticmethod
    def compress_dir(name, path=None):
        '''
        Compress directory using tar and pigz to .tgz
        args:
            name: name of directory to compress
            path: path to directory to compress
        '''
        # If the name an absolute path, then parse it for dir_name
        if isabs(name):
            dir_name = name.split('/')[-1]
        else:
            dir_name = name

        # compression command using pigz
        command = f"tar -I pigz -cf {dir_name}.tgz {name}"
        start = time.time()
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, cwd=str(path.parent.absolute())) # new process at parent directory
        output, error = process.communicate() # wait till the process is finished
        print(f'time taken for compression of {name}: {time.time() - start}')

    @staticmethod
    def uncompress(file, path=None):
        '''
        Uncompress .tgz file using tar and pigz
        args:
            file: file to uncompress
            path: path to file to uncompress
        '''

        command = f"tar -I pigz -xf {file}"
        start = time.time()
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, cwd=str(path.parent.absolute())) # new process at parent directory
        output, error = process.communicate() # wait till the process is finished
        print(f'time taken for decompression of {file}: {time.time() - start}')
    
    @staticmethod
    def delete_tgz(name):
        '''
        Delete .tgz file
        args:
            name: name of file to delete
        '''
        tarfile =  f"{name}.tgz"
        os.remove(tarfile)
        print(f"deleted {tarfile}")

    def _upload(
            self,
            file_path,
            target_path,
            timeout=900,
            chunk_size=150 * 1024 * 1024,
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

    def _create_backup_content(self, content):
        '''
        Create backup of content
        args:
            content: content to backup
        '''
        # If file, directly upload it
        if(isfile(join(self.source_dir, content))):
            print(f'file: {join(self.source_dir, content)}')
            self._upload(join(self.source_dir, content), join('/', content))

        # If folder, compress it and upload it and then delete the compressed file
        elif(isdir(join(self.source_dir, content))):
            print(f'dir: {join(self.source_dir, content)}')
            self.compress_dir(content, path = Path(join(self.source_dir, content)))
            print(f"uploading: {join(self.source_dir, content)+'.tgz'}...")
            self._upload(join(self.source_dir, content)+'.tgz', join('/', content+'.tgz'))
            print('finished uploading')
            self.delete_tgz(os.path.join(self.source_dir, content))

    def _create_backup(self):
        '''
        Create backup of source_dir
        '''
        for content in self.contents:
            self._create_backup_content(content)

    def _create_backup_mp(self):
        '''
        Create backup of source_dir using multiprocessing
        '''
        with multiprocessing.Pool(self.num_processes) as pool:
            pool.map(self._create_backup_content, self.contents)

    def backup_single_dir(self, dirpath):
        '''
        Create backup of single directory
        args:
            dirpath: path to directory to backup
        '''
        # create a path object
        path = Path(dirpath)

        # check if directory exists
        if not path.exists():
            raise NotADirectoryError("Can't find directory")
        if isabs(dirpath):
            dir_name = dirpath.split('/')[-1]
        else:
            dir_name = dirpath

        start = time.time()
        print(f'dir: {dirpath}')
        self.compress_dir(dirpath, path)
        print(f"uploading: {join(str(path.parent.absolute()), dir_name)+'.tgz'}...")
        self._upload(join(str(path.parent.absolute()), f'{dir_name}.tgz'), join('/', dir_name+'.tgz'))
        print('finished uploading')
        self.delete_tgz(dirpath)
        print(f"Total time taken for backup of {dirpath}: {time.time() - start}")

    def backup_all(self):
        '''
        Create backup of source_dir by choose between single process or multiprocessing
        '''
        start = time.time()
        if self.num_processes == 1:
            self._create_backup()
        else:
            self._create_backup_mp()
        print(f"Total time taken for backup: {time.time() - start}")

    @staticmethod
    def check_tar():
        'tar --compare --file=archive-file.tar -C /some/where/'

    def run(self):
        '''
        Run tool
        '''
        if self.mode == 'single':
            self.backup_single_dir(self.source_dir)
        elif self.mode == 'all':
            self.backup_all()
        else:
            NotImplementedError("Mode not implemented")


if __name__ == '__main__':
    with open("/hdd2/extra_home/sdash38/dropbox_keys/backup.txt", "r") as f:
        access_token = f.read().strip()

    # dbtool = DropboxBackupTool(access_token, '/hdd2/extra_home/sdash38/test_folder', num_processes=2)
    # dbtool.backup_all()
