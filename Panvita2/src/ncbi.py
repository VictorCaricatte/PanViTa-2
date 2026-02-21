# File: ncbi.py
# Description: NCBI Download handler

import os
import sys
import re
import random
import string
import time
import shutil
from utils import FileHandler

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
                
            # FIX: Adicionando 'i' (a chave do dicionário) na tupla para não perder a referência
            attempts.append((ftp, species, genus, strain, ltag, i))
            
        indic = 0
        while len(attempts) != 0:
            current_attempt = attempts[0]
            ftp_url, species, genus, strain, ltag, dict_key = current_attempt
            
            try:
                print(f"Strain {strain}: attempt {indic + 1}\n{ftp_url}")
                file = FileHandler.safe_download(ftp_url)
                print("\n")
                newfile = re.sub(r"((?![\.A-z0-9_-]).)", "_", str(file))
                os.rename(file, newfile)
                removal.append(newfile)
                file = newfile
                FileHandler.extract_gz_file(file)
                file = file.replace(".gz", "")
                
                # FIX: Usando dict_key para atualizar o dicionário corretamente
                self.dic[dict_key] = (self.dic[dict_key][0], file)
                
                try:
                    if ltag not in all_strains:
                        temp_string = ltag
                        os.rename(file, ltag + ".gbf")
                        all_strains.append(ltag)
                    else:
                        temp_string = f"{ltag}_dup_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
                        os.rename(file, f"{temp_string}.gbf")
                except BaseException:
                    time.sleep(3)
                    if ltag not in all_strains:
                        temp_string = ltag
                        os.rename(file, ltag + ".gbf")
                        all_strains.append(ltag)
                    else:
                        temp_string = f"{ltag}_dup_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
                        os.rename(file, f"{temp_string}.gbf")
                        
                gbff.append(f"./{temp_string}.gbf")
                attempts.pop(0)
                indic = 0
            except BaseException:
                indic = indic + 1
                if indic > 4:
                    attempts.pop(0)
                    erro_string = f"ERROR: It wasn't possible to download the GenBank file for the strain {strain} even after 5 attempts.\nPlease check the internet connection, the log and input files.\n"
                    self.erro.append(erro_string)
                    print(erro_string)
                    indic = 0
                    continue
                else:
                    continue
                    
        for temp_file in os.listdir("."):
            if temp_file.endswith(".tmp"):
                os.remove(temp_file)
            elif temp_file in removal:
                os.remove(temp_file)
                
        return gbff

    def get_ncbi_fna(self):
        """Download FASTA files from NCBI and optionally annotate with PROKKA"""
        
        # PROKKA Executable Lookup / Argument Parse
        prokka_path = None
        if "--prokka" in sys.argv:
            try:
                idx = sys.argv.index("--prokka")
                if idx + 1 < len(sys.argv) and not sys.argv[idx+1].startswith("-"):
                    prokka_path = sys.argv[idx+1]
            except ValueError:
                pass
        
        if not prokka_path:
            prokka_path = shutil.which("prokka")
            
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
                    if prokka_path:
                        cmd = (
                            f"{prokka_path} --addgenes --force --species {species} --genus {genus} "
                            f"--strain {strain} {file} --prefix {ltag} --outdir {ltag} "
                            f"--locustag {ltag}")
                        if ltag not in os.listdir():
                            pk.append(cmd)
                    print(f"Skipping file {new_file}.fna. File already exists.\n")
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
                        # FIX: Removido "file =" antes do os.rename
                        os.rename(file, new_file + ".fna")
                    except BaseException:
                        time.sleep(1)
                        os.rename(file, new_file + ".fna")
                        
                    file = new_file + ".fna"
                    ltag = genus[0] + species[0] + "_" + strain
                    temp = "./" + ltag + "/" + strain + ".gbf"
                    pkgbf.append(temp)
                    if prokka_path:
                        cmd = (
                            f"{prokka_path} --addgenes --force --species {species} --genus {genus} "
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
        for cmd in pk:
            uscript.write(cmd + "\n")
        uscript.close()
        
        if "-a" in sys.argv:
            if isinstance(prokka_path, str) and prokka_path != "":
                for cmd in pk:
                    print(cmd)
                    os.system(cmd)
            else:
                erro_string = "Sorry but we didn't find PROKKA in your computer.\nBe sure that the installation was performed well or provide its path using --prokka <path>.\nThe annotation will not occur.\nIf you install PROKKA some day, you can use a script we made specially for you!\n"
                print(erro_string)
                self.erro.append(erro_string)
                pkgbf = [""]
                
        return pkgbf