# File: bank.py
# Description: Database management (download and indexing)

import os
import shutil
import zipfile
import re
from config import PanViTaConfig
from utils import FileHandler

class DatabaseManager:
    def __init__(self, dppath):
        self.home = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.home, ".panvita.db.paths")
        self.dppath = dppath
        self.dbpath = self._get_database_path()

    def _get_database_path(self):
        """Get or create the database path"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "rt") as file:
                dbpath = file.readline().strip()
        else:
            dbpath = os.path.join(os.getcwd(), "DB")
            with open(self.config_file, "w") as file:
                file.write(dbpath)
        
        # Ensure the directory exists
        parent_dir = os.path.dirname(dbpath.rstrip("/"))
        if "DB" not in os.listdir(parent_dir):
            os.makedirs(dbpath, exist_ok=True)
            
        return dbpath

    def _fix_fasta_headers(self, filepath):
        """Fix split headers in downloaded FASTA files to prevent alignment errors"""
        if not os.path.exists(filepath):
            return
            
        print(f"Checking and fixing possible broken headers in {os.path.basename(filepath)}...")
        with open(filepath, 'r', encoding='utf-8', errors='replace') as infile:
            lines = infile.readlines()
            
        with open(filepath, 'w', encoding='utf-8') as outfile:
            header = ""
            sequence = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith(">"):
                    if header:
                        outfile.write(header + "\n")
                        outfile.write("\n".join(sequence) + "\n")
                    header = line
                    sequence = []
                else:
                    if re.search(r'[^A-Za-z\-\*]', line):
                        header += " " + line
                    else:
                        sequence.append(line)
                        
            if header:
                outfile.write(header + "\n")
                outfile.write("\n".join(sequence) + "\n")

    def check_databases(self, diamond_exe, custom_db_path=None):
        """Check and download all required databases"""
        print("\nChecking your databases...")
        
        # BacMet database
        self._check_bacmet(diamond_exe)
        
        # VFDB database
        self._check_vfdb(diamond_exe)
        
        # CARD database
        self._check_card(diamond_exe)
        
        # Coordinates file
        self._check_latlon()
        
        # MEGARes database
        self._check_megares(diamond_exe)

        # ResFinder database
        self._check_resfinder(diamond_exe)
        
        # ARG-ANNOT database
        self._check_argannot(diamond_exe)
        
        # Victors database
        self._check_victors(diamond_exe)
        
        # Custom database
        if custom_db_path:
            self._check_custom(diamond_exe, custom_db_path)
        
        return self.dbpath

    def _check_bacmet(self, diamond_exe):
        """Check and download BacMet database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        # Check for both the FASTA and the MAPPING file
        if ("bacmet_2.fasta" not in os.listdir(self.dbpath)) or ("bacmet_2.txt" not in os.listdir(self.dbpath)):
            print("\nDownloading BacMet database...")
            # We use the Experimentally Confirmed (EXP) database for better accuracy
            bacmet = FileHandler.safe_download(
                "http://bacmet.biomedicine.gu.se/download/BacMet2_EXP_database.fasta")
            os.rename(bacmet, os.path.join(self.dbpath, "bacmet_2.fasta"))
            print("")
            
            # Create DIAMOND index
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'bacmet_2.fasta')} "
                f"-d {os.path.join(self.dbpath, 'bacmet_2')} --quiet")
            
            print("\nDownloading BacMet annotation file...")
            # Downloading the corresponding mapping file
            bacmet_an = FileHandler.safe_download(
                "http://bacmet.biomedicine.gu.se/download/BacMet2_EXP.753.mapping.txt")
            os.rename(bacmet_an, os.path.join(self.dbpath, "bacmet_2.txt"))

        # Check if BacMet DIAMOND index exists
        if ("bacmet_2.fasta" in os.listdir(self.dbpath) and 
            "bacmet_2.dmnd" not in os.listdir(self.dbpath)):
            print("\nCreating BacMet DIAMOND index...")
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'bacmet_2.fasta')} "
                f"-d {os.path.join(self.dbpath, 'bacmet_2')} --quiet")

        # Check if BacMet BLAST index exists
        if ("bacmet_2.fasta" in os.listdir(self.dbpath) and 
            not any(f.startswith("bacmet_2.p") for f in os.listdir(self.dbpath))):
            print("\nCreating BacMet BLAST index...")
            os.system(
                f"{makeblastdb_exe} -in {os.path.join(self.dbpath, 'bacmet_2.fasta')} "
                f"-dbtype prot -out {os.path.join(self.dbpath, 'bacmet_2')}")

    def _check_vfdb(self, diamond_exe):
        """Check and download VFDB database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        if "vfdb_core.fasta" not in os.listdir(self.dbpath):
            print("\nDownloading VFDB database...")
            vfdb = FileHandler.safe_download("http://www.mgc.ac.cn/VFs/Down/VFDB_setA_pro.fas.gz")

            # Remove existing file if it exists
            if os.path.exists("vfdb_core.fasta.gz"):
                os.remove("vfdb_core.fasta.gz")

            os.rename(vfdb, "vfdb_core.fasta.gz")
            FileHandler.extract_gz_file("vfdb_core.fasta.gz", "vfdb_core.fasta")
            os.rename("vfdb_core.fasta", os.path.join(self.dbpath, "vfdb_core.fasta"))

            # Remove temporary .gz file after extraction
            if os.path.exists("vfdb_core.fasta.gz"):
                os.remove("vfdb_core.fasta.gz")

            print("")
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'vfdb_core.fasta')} "
                f"-d {os.path.join(self.dbpath, 'vfdb_core')} --quiet")

        # Check if VFDB DIAMOND index exists
        if ("vfdb_core.fasta" in os.listdir(self.dbpath) and 
            "vfdb_core.dmnd" not in os.listdir(self.dbpath)):
            print("\nCreating VFDB DIAMOND index...")
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'vfdb_core.fasta')} "
                f"-d {os.path.join(self.dbpath, 'vfdb_core')} --quiet")

        # Check if VFDB BLAST index exists
        if ("vfdb_core.fasta" in os.listdir(self.dbpath) and 
            not any(f.startswith("vfdb_core.p") for f in os.listdir(self.dbpath))):
            print("\nCreating VFDB BLAST index...")
            os.system(
                f"{makeblastdb_exe} -in {os.path.join(self.dbpath, 'vfdb_core.fasta')} "
                f"-dbtype prot -out {os.path.join(self.dbpath, 'vfdb_core')}")

    def _check_card(self, diamond_exe):
        """Check and download CARD database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        if "card_protein_homolog_model.fasta" not in os.listdir(self.dbpath):
            current_files = os.listdir()
            print("\nDownloading CARD database...")
            card = FileHandler.safe_download("https://card.mcmaster.ca/latest/data")
            FileHandler.extract_tar_file(card)
            os.rename("protein_fasta_protein_homolog_model.fasta",
                      os.path.join(self.dbpath, "card_protein_homolog_model.fasta"))
            os.rename("aro_index.tsv", os.path.join(self.dbpath, "aro_index.tsv"))
            FileHandler.clean_up_files(current_files)
            print("")
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'card_protein_homolog_model.fasta')} "
                f"-d {os.path.join(self.dbpath, 'card_protein_homolog_model')} --quiet")

        # Check if CARD DIAMOND index exists
        if ("card_protein_homolog_model.fasta" in os.listdir(self.dbpath) and 
            "card_protein_homolog_model.dmnd" not in os.listdir(self.dbpath)):
            print("\nCreating CARD DIAMOND index...")
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'card_protein_homolog_model.fasta')} "
                f"-d {os.path.join(self.dbpath, 'card_protein_homolog_model')} --quiet")

        # Check if CARD BLAST index exists
        if ("card_protein_homolog_model.fasta" in os.listdir(self.dbpath) and 
            not any(f.startswith("card_protein_homolog_model.p") for f in os.listdir(self.dbpath))):
            print("\nCreating CARD BLAST index...")
            os.system(
                f"{makeblastdb_exe} -in {os.path.join(self.dbpath, 'card_protein_homolog_model.fasta')} "
                f"-dbtype prot -out {os.path.join(self.dbpath, 'card_protein_homolog_model')}")

    def _check_latlon(self):
        """Check and download coordinates file if needed"""
        if "latlon.csv" not in os.listdir(self.dbpath):
            print("\nDownloading coordinates keys file...")
            latlon = FileHandler.safe_download(
                "https://raw.githubusercontent.com/dlnrodrigues/panvita/dlnrodrigues-Supplementary/latlon.csv")
            os.rename(latlon, os.path.join(self.dbpath, "latlon.csv"))
            print("")

    def _check_megares(self, diamond_exe):
        """Check and download MEGARes database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        if "megares_v3.fasta" not in os.listdir(self.dbpath):
            print("\nDownloading MEGARes v3.00 database...")
            current_files = os.listdir()
            
            # Try to download the main database file directly first
            try:
                print("Attempting direct download of main database file...")
                megares_file = FileHandler.safe_download("https://www.meglab.org/downloads/megares_v3.00/megares_database_v3.00.fasta")
                os.rename(megares_file, os.path.join(self.dbpath, "megares_v3.fasta"))
                print("Direct download successful!")
                
            except Exception as e:
                print(f"Direct download failed: {e}")
                print("Trying ZIP download...")
                
                megares_zip = FileHandler.safe_download("https://www.meglab.org/downloads/megares_v3.00.zip")
                
                # Extract the zip file
                with zipfile.ZipFile(megares_zip, 'r') as zip_ref:
                    zip_ref.extractall('.')
                
                # Find the main database file
                megares_main_file = None
                for item in os.listdir('.'):
                    if item.endswith('.fasta'):
                        if 'database' in item.lower() or 'megares_v3' in item.lower():
                            megares_main_file = item
                            break
                
                # If no main database file found, use the first .fasta file
                if megares_main_file is None:
                    for item in os.listdir('.'):
                        if item.endswith('.fasta'):
                            megares_main_file = item
                            break
                
                if megares_main_file:
                    os.rename(megares_main_file, os.path.join(self.dbpath, "megares_v3.fasta"))
                    print(f"Using MEGARes file: {megares_main_file}")
                else:
                    print("Warning: No .fasta file found in MEGARes archive!")
                    return  # Skip MEGARes setup if no file found
                
                FileHandler.clean_up_files(current_files)
            
            print("")
            # Create DIAMOND index
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'megares_v3.fasta')} "
                f"-d {os.path.join(self.dbpath, 'megares_v3')} --quiet")

        # Check if MEGARes BLAST index exists
        if ("megares_v3.fasta" in os.listdir(self.dbpath) and 
            not any(f.startswith("megares_v3.n") for f in os.listdir(self.dbpath))):
            print("\nCreating MEGARes BLAST index (nucleotide)...")
            os.system(
                f"{makeblastdb_exe} -in {os.path.join(self.dbpath, 'megares_v3.fasta')} "
                f"-dbtype nucl -out {os.path.join(self.dbpath, 'megares_v3')}")

    def _check_resfinder(self, diamond_exe):
        """Check and download ResFinder database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        if "resfinder.fasta" not in os.listdir(self.dbpath):
            print("\nDownloading ResFinder database...")
            url = "https://raw.githubusercontent.com/VictorCaricatte/DataBase-for-Bioinformatics/main/Database/Prokaryotes/Resistance/Resfinder/ForScripts/resfinder.fasta"
            try:
                resfinder = FileHandler.safe_download(url)
                os.rename(resfinder, os.path.join(self.dbpath, "resfinder.fasta"))
                print("ResFinder download complete.")
                
            except Exception as e:
                print(f"Error downloading ResFinder: {e}")

        if ("resfinder.fasta" in os.listdir(self.dbpath) and 
            not any(f.startswith("resfinder.n") for f in os.listdir(self.dbpath))):
            print("\nCreating ResFinder BLAST index (Nucleotide)...")
            os.system(
                f"{makeblastdb_exe} -in {os.path.join(self.dbpath, 'resfinder.fasta')} "
                f"-dbtype nucl -out {os.path.join(self.dbpath, 'resfinder')}")

    def _check_argannot(self, diamond_exe):
        """Check and download ARG-ANNOT database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        if "argannot.fasta" not in os.listdir(self.dbpath):
            print("\nDownloading ARG-ANNOT database...")
            url = "https://raw.githubusercontent.com/VictorCaricatte/DataBase-for-Bioinformatics/main/Database/Prokaryotes/Resistance/ARG-ANNOT/ARG-ANNOT_AA_V6_July2019.fasta"
            try:
                argannot = FileHandler.safe_download(url)
                os.rename(argannot, os.path.join(self.dbpath, "argannot.fasta"))
                print("ARG-ANNOT download complete.")
                
                print("Creating ARG-ANNOT DIAMOND index...")
                os.system(
                    f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'argannot.fasta')} "
                    f"-d {os.path.join(self.dbpath, 'argannot')} --quiet")
            except Exception as e:
                print(f"Error downloading ARG-ANNOT: {e}")

        # BLAST Index check
        if ("argannot.fasta" in os.listdir(self.dbpath) and 
            not any(f.startswith("argannot.p") for f in os.listdir(self.dbpath))):
            print("\nCreating ARG-ANNOT BLAST index...")
            os.system(
                f"{makeblastdb_exe} -in {os.path.join(self.dbpath, 'argannot.fasta')} "
                f"-dbtype prot -out {os.path.join(self.dbpath, 'argannot')}")

    def _check_victors(self, diamond_exe):
        """Check and download Victors database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        prot_path = os.path.join(self.dbpath, "victorsprotein.fasta")
        gene_path = os.path.join(self.dbpath, "victorsgene.fasta")
        
        # Download both files se eles não existirem
        if not os.path.exists(prot_path) or not os.path.exists(gene_path):
            print("\nDownloading Victors database...")
            url_protein = "https://raw.githubusercontent.com/VictorCaricatte/DataBase-for-Bioinformatics/main/Database/Prokaryotes/Virulance/Victors/victorsprotein.fasta"
            url_gene = "https://raw.githubusercontent.com/VictorCaricatte/DataBase-for-Bioinformatics/main/Database/Prokaryotes/Virulance/Victors/victorsgene.fasta"
            
            try:
                prot = FileHandler.safe_download(url_protein)
                os.rename(prot, prot_path)
                
                gene = FileHandler.safe_download(url_gene)
                os.rename(gene, gene_path)
                print("Victors download complete.")
                    
            except Exception as e:
                print(f"Error downloading Victors: {e}")

        # SEMPRE verifica e concerta o arquivo antes de criar qualquer index
        
        # DIAMOND Index check (Protein)
        if (os.path.exists(prot_path) and "victors.dmnd" not in os.listdir(self.dbpath)):
            self._fix_fasta_headers(prot_path)
            print("Creating Victors DIAMOND index (Protein)...")
            os.system(
                f"{diamond_exe} makedb --in {prot_path} "
                f"-d {os.path.join(self.dbpath, 'victors')} --quiet")

        # BLAST Index check (Protein)
        if (os.path.exists(prot_path) and not any(f.startswith("victors.p") for f in os.listdir(self.dbpath))):
            self._fix_fasta_headers(prot_path)
            print("\nCreating Victors BLAST index (Protein)...")
            os.system(
                f"{makeblastdb_exe} -in {prot_path} "
                f"-dbtype prot -out {os.path.join(self.dbpath, 'victors')}")

        # BLAST Index check (Nucleotide)
        if (os.path.exists(gene_path) and not any(f.startswith("victors_nucl.n") for f in os.listdir(self.dbpath))):
            self._fix_fasta_headers(gene_path)
            print("\nCreating Victors BLAST index (Nucleotide)...")
            os.system(
                f"{makeblastdb_exe} -in {gene_path} "
                f"-dbtype nucl -out {os.path.join(self.dbpath, 'victors_nucl')}")

    def _check_custom(self, diamond_exe, custom_path):
        """Check and index user Custom database"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        if not os.path.exists(custom_path):
            print(f"Error: Custom database file not found at {custom_path}")
            exit(1)
            
        print(f"\nProcessing Custom database: {custom_path}")
        
        dest_path = os.path.join(self.dbpath, "custom.fasta")
        
        try:
            shutil.copy2(custom_path, dest_path)
            
            print("Creating Custom DIAMOND index...")
            os.system(
                f"{diamond_exe} makedb --in {dest_path} "
                f"-d {os.path.join(self.dbpath, 'custom')} --quiet")
            
            print("Creating Custom BLAST index...")
            os.system(
                f"{makeblastdb_exe} -in {dest_path} "
                f"-dbtype prot -out {os.path.join(self.dbpath, 'custom')}")
                
        except Exception as e:
            print(f"Error processing custom database: {e}")