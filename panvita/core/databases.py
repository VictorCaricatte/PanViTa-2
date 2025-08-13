import os

from .config import PanViTaConfig
from .file_handler import FileHandler


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

    def check_databases(self, diamond_exe):
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
        
        return self.dbpath

    def _check_bacmet(self, diamond_exe):
        """Check and download BacMet database if needed"""
        makeblastdb_exe = os.path.join(self.dppath, "makeblastdb.exe" if PanViTaConfig.is_windows() else "makeblastdb")
        
        if ("bacmet_2.fasta" not in os.listdir(self.dbpath)) or ("bacmet_2.txt" not in os.listdir(self.dbpath)):
            print("\nDownloading BacMet database...")
            bacmet = FileHandler.safe_download(
                "http://bacmet.biomedicine.gu.se/download/BacMet2_EXP_database.fasta")
            os.rename(bacmet, os.path.join(self.dbpath, "bacmet_2.fasta"))
            print("")
            
            # Create DIAMOND index
            os.system(
                f"{diamond_exe} makedb --in {os.path.join(self.dbpath, 'bacmet_2.fasta')} "
                f"-d {os.path.join(self.dbpath, 'bacmet_2')} --quiet")
            
            print("\nDownloading BacMet annotation file...")
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

