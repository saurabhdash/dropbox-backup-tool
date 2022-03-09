from dropboxbackuptool.db_uploader import DropboxBackupTool
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DropBox backup tool')
    parser.add_argument('--mode',    type=str, default='all', help='all for all subfolders of the current dir \
                                                                    and single for the entire current dir as a single tar')
    parser.add_argument('--token_file', type=str, default='/hdd2/extra_home/sdash38/dropbox_keys/backup.txt', help='path to the file containing the dropbox token')
    parser.add_argument('--source_dir', type=str, default=None, help='path to the directory to backup')
    parser.add_argument('--num_processes', type=int, default=1, help='number of processes to use for multiprocessing')
    args = parser.parse_args()

    dbtool = DropboxBackupTool(args)
    dbtool.run()