import urllib.request
import os,gzip
import shutil as sh
import tarfile
from pathlib import Path
import shutil

# Download the Megares data (fasta and csv).
magares = urllib.request.urlretrieve('https://www.meglab.org/downloads/megares_v3.00/megares_database_v3.00.fasta', "megares_database_v3.00.fasta" ) [0]
megares = urllib.request.urlretrieve('https://www.meglab.org/downloads/megares_v3.00/megares_annotations_v3.00.csv', "megares_annotations_v3.00.csv") [0]


# Move the archive to the DB file in home, in your system.
home = os.path.expanduser('~')
file_name = f'.{os.sep}megares_database_v3.00.fasta' 
file_name1 = f'.{os.sep}megares_annotations_v3.00.csv'
file_path = f'{home}{os.sep}DB{os.sep}'
shutil.move(str(file_name),str(file_path))
shutil.move(str(file_name1),str(file_path))
