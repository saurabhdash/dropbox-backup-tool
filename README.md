# Dropbox Backup Tool
This tool helps backup a directory or its contents to dropbox

## Requirements
<ul>
<li>pigz which can be installed using sudo apt install pigz </li>
<li>Dropbox app token </li>
</ul>

## Usage
To setup the tool, run:

'bash setup.sh'

To run the tool:
In run.sh, update the variables:
<ul>
<li>mode: 'all' uploads the contents of the directory to dropbox and 'single' uploads the entire directory as a .tgz to dropbox </li>
<li>token_file: path to a file that contains the dropbox app token</li>
<li>source_dir: path of a directory to be uploaded</li>
<li>num_processes: number of threads for parallel uploads</li>
</ul>

'bash run.sh'