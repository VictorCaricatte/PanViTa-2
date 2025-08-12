import urllib.request
import os,gzip
import shutil as sh
import tarfile
from pathlib import Path
import shutil

# Download the card data.
home = os.path.expanduser('~')
card = urllib.request.urlretrieve('https://card.mcmaster.ca/download/0/broadstreet-v3.3.0.tar.bz2', "broadstreet-v3.3.0.tar.bz2")[0]
print(card)
with tarfile.open(card, 'r:bz2') as tar_ref:
	tar_ref.extractall('card-data.tar.bz2')
	os.remove('broadstreet-v3.3.0.tar.bz2')

# Create a file in your home system.
pasta = f"{home}{os.sep}DB"
if (not os.path.exists(pasta)):
	os.makedirs(pasta, exist_ok=True)


# Move the archive to the DB file in home, in your system.
file_name = f'.{os.sep}card-data.tar.bz2{os.sep}protein_fasta_protein_homolog_model.fasta' 
file_name2 = f'.{os.sep}card-data.tar.bz2{os.sep}aro_index.tsv'
file_path = f'{home}{os.sep}DB{os.sep}'
shutil.move(str(file_name),str(file_path))
shutil.move(str(file_name2),str(file_path))
shutil.rmtree('card-data.tar.bz2'
