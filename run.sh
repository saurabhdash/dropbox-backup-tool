#!bin/bash
mode='' # 'all' uploads subfolders of the current directory and single uploads current directory as a single tar file
token_file='' # location of the dropbox token file
source_dir='' # source directory to be backed up
num_processes=1 # number of processes to use for parallel uploads

python3 -m venv run_env
run_env/bin/pip install -r requirements.txt
run_env/bin/python3 main.py --mode=$mode --token_file=$token_file --source_dir=$source_dir --num_processes=$num_processes