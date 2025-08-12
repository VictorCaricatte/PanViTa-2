import urllib.request
import shutil as sh
import requests
import os
import shutil
import os,gzip

# Download the VFDB data.
vfdb = urllib.request.urlretrieve('http://www.mgc.ac.cn/VFs/Down/VFDB_setA_pro.fas.gz')[0]
with gzip.open(vfdb,"rb") as file_input:
    with open(f"vfdb_fasta",'wb') as file_output:
        sh.copyfileobj(file_input,file_output)

# Move the archive to the DB file in home, in your system.
home = os.path.expanduser('~')
file_name = f'.{os.sep}vfdb_fasta' 
file_name1 = f'.{os.sep}vfdb_fasta'
file_path = f'{home}{os.sep}DB{os.sep}'
shutil.move(str(file_name),str(file_path))
shutil.move(str(file_name1),str(file_path))
