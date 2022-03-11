# This tool helps backup a directory or its contents to dropbox

## Requirements
pigz which can be installed using sudo apt install pigz 
Dropbox app token


## Usage
In run.sh, update the variables:

mode: 'all' uploads the contents of the directory to dropbox and 'single' uploads the entire directory as a .tgz to dropbox

token_file: path to a file that contains the dropbox app token

source_dir: path of a directory to be uploaded

num_processes: number of threads for parallel uploads
