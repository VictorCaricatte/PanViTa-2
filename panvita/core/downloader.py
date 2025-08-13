import os
import random
import re
import shutil
import string
import sys
import time

from .file_handler import FileHandler


class NCBIDownloader:
    def __init__(self, strain_dict):
        self.dic = strain_dict
        self.erro = []

    def get_ncbi_gbf(self):
        """Download GenBank files from NCBI"""
        gbff = []
        attempts = []
        removal = []
        all_strains = []
        
        for i in self.dic.keys():
            if isinstance(self.dic[i][1], str):
                ftp = self.dic[i][1]
                file = "/" + ftp[:: -1].split("/")[0][:: -1] + "_genomic.gbff.gz"
                ftp = ftp + file
            elif isinstance(self.dic[i][2], str):
                ftp = self.dic[i][2]
                file = "/" + ftp[:: -1].split("/")[0][:: -1] + "_genomic.gbff.gz"
                ftp = ftp + file
            else:
                erro_string = f"ERROR: It wasn't possible to download the file {str(i)}.\nIt doesn't have a FTP accession.\nPlease check the log file.\n"
                self.erro.append(erro_string)
                print(erro_string)
                continue
                
            genus = self.dic[i][0].split(" ")[0]
            species = self.dic[i][0].split(" ")[1]
            strain = re.sub(r"((?![\.A-z0-9_-]).)", "_", str(self.dic[i][3]))
            
            if "-s" in sys.argv:
                ltag = strain
            else:
                ltag = genus[0] + species + "_" + strain
                
            attempts.append((ftp, species, genus, strain, ltag))
            indic = 0
            
        while len(attempts) != 0:
            try:
                print(f"Strain {attempts[0][3]}: attempt {indic + 1}\n{attempts[0][0]}")
                file = FileHandler.safe_download(attempts[0][0])
                print("\n")
                newfile = re.sub(r"((?![\.A-z0-9_-]).)", "_", str(file))
                os.rename(file, newfile)
                removal.append(newfile)
                file = newfile
                FileHandler.extract_gz_file(file)
                file = file.replace(".gz", "")
                self.dic[i] = (self.dic[i][0], file)
                
                try:
                    if attempts[0][4] not in all_strains:
                        temp_string = attempts[0][4]
                        os.rename(file, attempts[0][4] + ".gbf")
                        all_strains.append(attempts[0][4])
                    else:
                        temp_string = f"{attempts[0][4]}_dup_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
                        os.rename(file, f"{temp_string}.gbf")
                except BaseException:
                    time.sleep(3)
                    if attempts[0][4] not in all_strains:
                        temp_string = attempts[0][4]
                        os.rename(file, attempts[0][4] + ".gbf")
                        all_strains.append(attempts[0][4])
                    else:
                        temp_string = f"{attempts[0][4]}_dup_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
                        os.rename(file, f"{temp_string}.gbf")
                        
                gbff.append(f"./{temp_string}.gbf")
                attempts.pop(0)
                indic = 0
            except BaseException:
                indic = indic + 1
                if indic > 4:
                    attempts.pop(0)
                    erro_string = f"ERROR: It wasn't possible to download the GenBank file for the strain {attempts[0][3]} even after 5 attempts.\nPlease check the internet connection, the log and input files.\n"
                    self.erro.append(erro_string)
                    print(erro_string)
                    indic = 0
                    continue
                else:
                    continue
                    
        for i in os.listdir("."):
            if i.endswith(".tmp"):
                os.remove(i)
            elif i in removal:
                os.remove(i)
                
        return gbff

    def get_ncbi_fna(self):
        """Download FASTA files from NCBI and optionally annotate with PROKKA"""
        prokka = shutil.which("prokka")
        pkgbf = []
        pk = []
        all_strains = []
        
        for i in self.dic.keys():
            attempts = 1
            while True:
                genus = self.dic[i][0].split(" ")[0]
                species = self.dic[i][0].split(" ")[1]
                strain = re.sub(r"((?![\.A-z0-9_-]).)", "_", str(self.dic[i][3]))
                
                if strain not in all_strains:
                    all_strains.append(strain)
                else:
                    strain = f"{strain}_dup_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
                    
                if "-s" in sys.argv:
                    new_file = strain
                else:
                    new_file = genus[0] + species + "_" + strain
                    
                if f"{new_file}.fna" in os.listdir():
                    file = new_file + ".fna"
                    ltag = genus[0] + species[0] + "_" + strain
                    temp = "./" + ltag + "/" + strain + ".gbf"
                    pkgbf.append(temp)
                    cmd = (
                        f"prokka --addgenes --force --species {species} --genus {genus} "
                        f"--strain {strain} {file} --prefix {ltag} --outdir {ltag} "
                        f"--locustag {ltag}")
                    print(f"Skipping file {new_file}.fna. File already exists.\n")
                    if ltag not in os.listdir():
                        pk.append(cmd)
                    break
                    
                try:
                    if isinstance(self.dic[i][1], str):
                        ftp = self.dic[i][1]
                        file = "/" + ftp[:: -1].split("/")[0][:: -1] + "_genomic.fna.gz"
                        ftp = ftp + file
                        print("Strain", self.dic[i][3], f"Attempt: {attempts}", "\n", ftp)
                    elif isinstance(self.dic[i][2], str):
                        ftp = self.dic[i][2]
                        file = "/" + ftp[:: -1].split("/")[0][:: -1] + "_genomic.fna.gz"
                        ftp = ftp + file
                        print("Strain", self.dic[i][3], f"Attempt: {attempts}", "\n", ftp)
                    else:
                        erro_string = "ERROR: It wasn't possible to download the file " + str(i) + ".\nPlease check the log file.\n"
                        self.erro.append(erro_string)
                        print(erro_string)
                        break
                        
                    file = FileHandler.safe_download(ftp)
                    print("\n")
                    FileHandler.extract_gz_file(file)
                    file = file.replace(".gz", "")
                    self.dic[i] = (self.dic[i][0], file)
                    
                    try:
                        file = os.rename(file, new_file + ".fna")
                    except BaseException:
                        time.sleep(1)
                        file = os.rename(file, new_file + ".fna")
                        
                    file = new_file + ".fna"
                    ltag = genus[0] + species[0] + "_" + strain
                    temp = "./" + ltag + "/" + strain + ".gbf"
                    pkgbf.append(temp)
                    cmd = (
                        f"prokka --addgenes --force --species {species} --genus {genus} "
                        f"--strain {strain} {file} --prefix {ltag} --outdir {ltag} "
                        f"--locustag {ltag}")
                    if ltag not in os.listdir():
                        pk.append(cmd)
                    break
                except BaseException:
                    if attempts < 5:
                        attempts = attempts + 1
                    else:
                        erro_string = f"ERROR: It wasn't possible to download the Fasta file for the strain {self.dic[i][3]} even after 5 attempts.\nPlease check the internet connection, the log and input files.\n"
                        print(erro_string)
                        self.erro.append(erro_string)
                        break
                        
        uscript = open("PROKKA.sh", "w")
        for i in pk:
            uscript.write(i + "\n")
        uscript.close()
        
        if "-a" in sys.argv:
            if isinstance(prokka, str):
                for i in pk:
                    print(i)
                    os.system(i)
            else:
                erro_string = "Sorry but we didn't find PROKKA in your computer.\nBe sure that the installation was performed well.\nThe annotation will not occur.\nIf you install PROKKA some day, you can use a script we made specially for you!\n"
                print(erro_string)
                self.erro.append(erro_string)
                pkgbf = [""]
                
        return pkgbf

