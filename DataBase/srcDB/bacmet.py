import urllib.request
import shutil as sh
import requests
import os
import shutil

# Bacmet.py - Module desinged to download Bacmet data for PanVita use.

# Download the BacMet data.
bacmet = urllib.request.urlretrieve('http://bacmet.biomedicine.gu.se/download/BacMet2_EXP_database.fasta')[0] 
print(bacmet)
os.rename(bacmet,'Bacmet.fasta')

# Move the archive to the DB file in home, in your system.
home = os.path.expanduser('~')
file_name = f'.{os.sep}Bacmet.fasta' 
file_path = f'{home}{os.sep}DB{os.sep}'
shutil.move(str(file_name),str(file_path))
shutil.move(str(file_name),str(file_path)
