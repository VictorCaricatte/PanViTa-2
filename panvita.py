# ==============================================================================
# Author:       Victor S Caricatte De Araújo
# Co-author:    Diego Neres, Vinicius Oliveira
# Email:        victorsc@ufmg.br , dlnrodrigues@ufmg.br , vinicius.oliveira.1444802@sga.pucminas.br
# Intitution:   Universidade federal de Minas Gerais
# Version:      2.0.0
# Date:         September 24, 2025
# Notes: You may need deactivate conda. 
# ==============================================================================


# Standard library imports
import concurrent.futures
import gzip
import math
import os
import platform
import random
import re
import shutil
import ssl
import string
import sys
import tarfile
import time
import urllib.request
import zipfile
from datetime import datetime

# Third-party imports
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import wget


class PanViTaConfig:
    VERSION = "2.1.0"
    
    @staticmethod
    def is_windows():
        return platform.system().lower() == 'windows'
    
    @staticmethod
    def setup_ssl_context():
        """Setup SSL context to handle certificate issues"""
        # Create an SSL context that doesn't verify certificates
        # This is necessary for some corporate environments or older systems
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Install the context globally for urllib
        ssl._create_default_https_context = lambda: ssl_context
        
        # Also set up for wget module
        try:
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
            urllib.request.install_opener(opener)
        except ImportError:
            pass
        
        print("SSL certificate verification disabled for downloads.")

    @staticmethod
    def check_windows_dependencies():
        """Check for required Windows dependencies like Visual C++ Redistributable"""
        if not PanViTaConfig.is_windows():
            return True
        
        import ctypes
        
        # Check for msvcp140.dll (Visual C++ 2015-2022 Redistributable)
        try:
            # Try to load the DLL
            ctypes.cdll.LoadLibrary("msvcp140.dll")
            print("✅ Visual C++ Redistributable found.")
            return True
        except OSError:
            print("❌ Microsoft Visual C++ Redistributable is missing!")
            print("\n" + "="*60)
            print("ERRO CRÍTICO: Sistema sem dependências necessárias")
            print("="*60)
            print("O DIAMOND/BLAST requer o Microsoft Visual C++ Redistributable.")
            print("Este é provavelmente o motivo do erro que você está enfrentando.")
            print()
            print("SOLUÇÃO:")
            print("1. Baixe e instale o Microsoft Visual C++ Redistributable:")
            print("   https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist")
            print("2. Ou baixe diretamente:")
            print("   x64: https://aka.ms/vs/17/release/vc_redist.x64.exe")
            print("   x86: https://aka.ms/vs/17/release/vc_redist.x86.exe")
            print()
            print("3. Após a instalação, reinicie o computador e execute o PanVITA novamente.")
            print("="*60)
            return False

    @staticmethod
    def check_linux_dependencies():
        """Check for required Linux dependencies like glibc, libstdc++, etc."""
        if PanViTaConfig.is_windows():
            return True
        
        import ctypes
        import ctypes.util
        
        print("🐧 Verificando dependências do Linux...")
        dependencies_ok = True
        
        # Check essential shared libraries
        essential_libs = {
            'c': 'GNU C Library (glibc)',
            'stdc++': 'GNU Standard C++ Library', 
            'gcc_s': 'GCC Runtime Library',
            'gomp': 'OpenMP Runtime Library'
        }
        
        for lib_name, description in essential_libs.items():
            try:
                lib_path = ctypes.util.find_library(lib_name)
                if lib_path:
                    # Try to load the library
                    ctypes.CDLL(lib_path)
                    print(f"✅ {description} - OK")
                else:
                    print(f"❌ {description} - NÃO ENCONTRADA")
                    dependencies_ok = False
            except Exception as e:
                print(f"❌ {description} - ERRO: {e}")
                dependencies_ok = False
        
        if not dependencies_ok:
            print("\n" + "="*60)
            print("ERRO CRÍTICO: Dependências do sistema em falta")
            print("="*60)
            print("O DIAMOND/BLAST requer bibliotecas runtime do sistema.")
            print("Este é provavelmente o motivo do erro que você está enfrentando.")
            print()
            print("SOLUÇÃO:")
            print("Execute o script de diagnóstico:")
            print("   python3 check_dependencies_linux.py")
            print()
            print("Ou instale as dependências:")
            print("Ubuntu/Debian:")
            print("   sudo apt install build-essential libstdc++6 libgomp1")
            print("CentOS/RHEL:")
            print("   sudo yum groupinstall 'Development Tools'")
            print("   sudo yum install libstdc++-devel libgomp")
            print()
            print("Veja DEPENDENCIAS_LINUX.md para instruções detalhadas.")
            print("="*60)
        
        return dependencies_ok

    @staticmethod
    def check_system_dependencies():
        """Check system dependencies for both Windows and Linux"""
        if PanViTaConfig.is_windows():
            return PanViTaConfig.check_windows_dependencies()
        else:
            return PanViTaConfig.check_linux_dependencies()

class FileHandler:
    @staticmethod
    def safe_download(url, filename=None):
        """Safe download with SSL handling and fallback options"""
        
        if filename is None:
            filename = url.split('/')[-1]
        
        # Method 1: Try wget first (usually works with SSL context setup)
        try:
            print(f"Attempting download with wget: {url}")
            downloaded_file = wget.download(url, out=filename)
            print(f"\nDownload successful: {downloaded_file}")
            return downloaded_file
        except Exception as e:
            print(f"wget failed: {e}")
        
        # Method 2: Try urllib with custom SSL context
        try:
            print(f"Attempting download with urllib: {url}")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
                with open(filename, 'wb') as f:
                    shutil.copyfileobj(response, f)
            
            print(f"\nDownload successful: {filename}")
            return filename
        except Exception as e:
            print(f"urllib failed: {e}")
                
        raise Exception(f"All download methods failed for {url}")

    @staticmethod
    def extract_gz_file(gz_file, output_file=None):
        """Extract a .gz file, works on both Windows and Unix"""
        if output_file is None:
            output_file = gz_file[:-3]  # Remove .gz extension

        with gzip.open(gz_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return output_file

    @staticmethod
    def extract_tar_file(tar_file, extract_dir='.'):
        """Extract tar files using Python's tarfile module"""
        with tarfile.open(tar_file, 'r:*') as tar:
            tar.extractall(extract_dir)

    @staticmethod
    def clean_up_files(current_files, exceptions=None):
        """Clean up temporary files"""
        if exceptions is None:
            exceptions = []
            
        for i in os.listdir():
            if i not in current_files and i not in exceptions:
                if os.path.isfile(i):
                    try:
                        os.remove(i)
                    except:
                        pass
                elif os.path.isdir(i):
                    try:
                        shutil.rmtree(i)
                    except:
                        pass

class DependencyManager:
    def __init__(self):
        self.home = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.home, ".panvita.dp.paths")
        self.dppath = self._get_dependency_path()

    def _get_dependency_path(self):
        """Get or create the dependency path"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "rt") as file:
                dppath = file.readline().strip()
        else:
            dppath = os.path.join(os.getcwd(), "Dependences")
            with open(self.config_file, "w") as file:
                file.write(dppath)
        
        # Ensure the directory exists
        parent_dir = os.path.dirname(dppath.rstrip("/"))
        if "Dependences" not in os.listdir(parent_dir):
            os.makedirs(dppath, exist_ok=True)
            
        return dppath

    def check_dependencies(self):
        """Check and download all required dependencies"""
        print("\nChecking your dependences...")
        
        # Check system dependencies first
        if not PanViTaConfig.check_system_dependencies():
            print("\n❌ Encerrando devido à falta de dependências críticas do sistema.")
            if PanViTaConfig.is_windows():
                print("Por favor, instale o Microsoft Visual C++ Redistributable e tente novamente.")
            else:
                print("Por favor, instale as bibliotecas de desenvolvimento e tente novamente.")
            exit(1)
        
        # Setup SSL context for downloads
        PanViTaConfig.setup_ssl_context()
        
        # Check and download DIAMOND
        self._check_diamond()
        
        # Check and download BLAST
        self._check_blast()
        
        return self.dppath

    def _check_diamond(self):
        """Check and download DIAMOND if needed"""
        diamond_exe = "diamond.exe" if PanViTaConfig.is_windows() else "diamond"
        if diamond_exe not in os.listdir(self.dppath):
            print("You may not have DIAMOND.\nWe will try to get it.\n")
            current_files = os.listdir()

            if PanViTaConfig.is_windows():
                diamond_file = FileHandler.safe_download(
                    "https://github.com/bbuchfink/diamond/releases/download/v2.1.14/diamond-windows.zip")
                with zipfile.ZipFile(diamond_file, 'r') as zip_ref:
                    zip_ref.extractall('.')
                diamond_exe = "diamond.exe"
            else:
                diamond_file = FileHandler.safe_download(
                    "https://github.com/bbuchfink/diamond/releases/download/v2.1.14/diamond-linux64.tar.gz")
                FileHandler.extract_tar_file(diamond_file)
                diamond_exe = "diamond"
                if not PanViTaConfig.is_windows():
                    os.chmod(diamond_exe, 0o755)

            os.rename(diamond_exe, os.path.join(self.dppath, diamond_exe))
            FileHandler.clean_up_files(current_files)
            print("\nDIAMOND - Download complete!")

    def _check_blast(self):
        """Check and download BLAST if needed"""
        blast_exe = "blastp.exe" if PanViTaConfig.is_windows() else "blastp"
        if blast_exe not in os.listdir(self.dppath):
            print("You may not have BLAST.\nWe will try to get it.\n")
            current_files = os.listdir()

            if PanViTaConfig.is_windows():
                self._download_blast_windows()
            else:
                self._download_blast_linux()

            FileHandler.clean_up_files(current_files)
            print("BLAST - Download complete!")
            
            # Verify BLAST installation
            blast_path = os.path.join(self.dppath, blast_exe)
            if os.path.exists(blast_path):
                print("✅ BLAST installation verified successfully!")
                if PanViTaConfig.is_windows():
                    print("✅ All Windows dependencies (including nghttp2.dll) should be available!")
            else:
                print("❌ BLAST installation verification failed!")

    def _download_blast_windows(self):
        """Download and install BLAST for Windows"""
        print("Downloading BLAST for Windows (with all dependencies)...")
        blast_file = FileHandler.safe_download(
            "https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.12.0/ncbi-blast-2.12.0+-x64-win64.tar.gz")
        
        
        FileHandler.extract_tar_file(blast_file)
        
        # Rest of the method remains the same...
        blast_dir = None
        for item in os.listdir('.'):
            if item.startswith('ncbi-blast') and os.path.isdir(item):
                blast_dir = item
                break
        
        if blast_dir and os.path.exists(os.path.join(blast_dir, "bin")):
            print(f"Found BLAST directory: {blast_dir}")
            print("Copying ALL BLAST files (including DLLs) to dependencies folder...")
            
            bin_files = os.listdir(os.path.join(blast_dir, "bin"))
            copied_count = 0
            
            for file_name in bin_files:
                src_path = os.path.join(blast_dir, "bin", file_name)
                dst_path = os.path.join(self.dppath, file_name)
                
                if os.path.isfile(src_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        copied_count += 1
                        if file_name.endswith('.exe') or file_name.endswith('.dll'):
                            print(f"  - Copied {file_name}")
                    except Exception as e:
                        print(f"  - Warning: Could not copy {file_name}: {e}")
            
            print(f"Total files copied: {copied_count}")
            print("All BLAST dependencies (including nghttp2.dll) should now be available!")
        else:
            print("Error: Could not find BLAST bin directory")
            print("Manual installation may be required")

    def _download_blast_linux(self):
        """Download and install BLAST for Linux"""
        print("Downloading BLAST for Linux...")
        blast_file = FileHandler.safe_download(
            "https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.17.0+-x64-linux.tar.gz")
        FileHandler.extract_tar_file(blast_file)
        # Find the extracted BLAST directory
        blast_dir = None
        for item in os.listdir('.'):
            if item.startswith('ncbi-blast') and os.path.isdir(item):
                blast_dir = item
                break
        
        if blast_dir and os.path.exists(os.path.join(blast_dir, "bin")):
            print(f"Found BLAST directory: {blast_dir}")
            print("Copying ALL BLAST files to dependencies folder...")
            
            bin_files = os.listdir(os.path.join(blast_dir, "bin"))
            copied_count = 0
            
            for file_name in bin_files:
                src_path = os.path.join(blast_dir, "bin", file_name)
                dst_path = os.path.join(self.dppath, file_name)
                
                if os.path.isfile(src_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        os.chmod(dst_path, 0o755)
                        copied_count += 1
                        print(f"  - Copied {file_name}")
                    except Exception as e:
                        print(f"  - Warning: Could not copy {file_name}: {e}")
            
            print(f"Total files copied: {copied_count}")

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

class GBKProcessor:
    @staticmethod
    def extract_faa(gbk_file):
        """Extract protein sequences from GenBank file"""
        with open(gbk_file, 'rt') as gbk:
            cds = gbk.readlines()
            
        final = []
        for i in range(0, len(cds)):
            if "   CDS   " in cds[i]:
                locus_tag = ""
                product = ""
                sequence = []
                
                for j in range(i, len(cds)):
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 2):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 1):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        locus_tag2 = cds[j + 1].strip()
                        locus_tag2 = locus_tag2.replace("\"", "")
                        locus_tag2 = locus_tag2.replace("\n", "")
                        locus_tag = f"{locus_tag}{locus_tag2}"
                        
                    elif "/product=" in cds[j]:
                        product = cds[j].replace("/product=", "")
                        product = product.strip()
                        product = product.replace("\"", "")
                        product = product.replace("\n", '')
                        
                    elif "/translation=" in cds[j]:
                        if cds[j].count("\"") == 2:
                            seq = cds[j].replace("/translation=", "")
                            seq = seq.replace("\"", "")
                            seq = seq.strip() + "\n"
                            header = ">" + locus_tag + " " + product + "\n"
                            final.append(header)
                            final.append(seq)
                            break
                        else:
                            seq = cds[j].replace("/translation=", "")
                            seq = seq.replace("\"", "")
                            seq = seq.strip() + "\n"
                            sequence.append(seq)
                            k = j + 1
                            if "\"" in cds[k]:
                                seq = cds[k].replace(" ", "")
                                seq = seq.replace("\"", "")
                                sequence.append(seq)
                            else:
                                while ("\"" not in cds[k]):
                                    seq = cds[k].replace(" ", "")
                                    seq = seq.replace("\"", "")
                                    sequence.append(seq)
                                    k = k + 1
                                seq = cds[k].replace(" ", "")
                                seq = seq.replace("\"", "")
                                sequence.append(seq)
                            header = ">" + locus_tag + " " + product + "\n"
                            final.append(header)
                            for l in sequence:
                                final.append(l)
                            break
        return final

    @staticmethod
    def extract_positions(gbk_file):
        """Extract CDS positions from GenBank file"""
        with open(gbk_file, 'rt') as gbk:
            cds = gbk.readlines()
            
        positions = {}
        lenght = 0
        totalcds = 0
        
        for i in range(0, len(cds)):
            if ("   CDS   " in cds[i]) and ("   ::" not in cds[i]):
                locus_tag = ""
                position = ""
                
                for j in range(i, len(cds)):
                    if "   CDS   " in cds[j]:
                        totalcds = totalcds + 1
                        position = cds[j].replace('\n', '')
                        position = position.replace("CDS", "")
                        position = position.strip()
                        
                        if (">" in position) or ("<" in position):
                            position = position.replace(">", "").replace("<", "")
                            
                        if "complement(join(" in position:
                            position = position.replace("complement(join(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            if "," in position[0]:
                                temp = position[0].split(",")
                                position[0] = temp[0]
                            if totalcds == 1:
                                try:
                                    position = [int(position[0]) + lenght, int(position[1]) + lenght]
                                except BaseException:
                                    position = [int(position[0]) + lenght, int(position[2]) + lenght]
                                    
                        elif "complement(" in position:
                            position = position.replace("complement(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            position = [int(position[0]) + lenght, int(position[1]) + lenght]
                            
                        elif "join(" in position:
                            position = position.replace("join(", "")
                            position = position.replace(")", "").strip()
                            position = position.split("..")
                            if "," in position[0]:
                                temp = position[0].split(",")
                                position[0] = temp[0]
                            if totalcds == 1:
                                try:
                                    position = [int(position[0]) + lenght, int(position[1]) + lenght]
                                except BaseException:
                                    position = [int(position[0]) + lenght, int(position[2]) + lenght]
                        else:
                            position = position.replace("<", "").replace(">", "").strip()
                            position = position.split("..")
                            position = [int(position[0]) + lenght, int(position[1]) + lenght]
                            
                    if ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 2):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        positions[locus_tag] = str(position[0]) + "\t" + str(position[1])
                        break
                        
                    elif ("/locus_tag=" in cds[j]) and (cds[j].count('\"') == 1):
                        locus_tag = cds[j].replace("/locus_tag=", "")
                        locus_tag = locus_tag.strip()
                        locus_tag = locus_tag.replace("\"", "")
                        locus_tag = locus_tag.replace("\n", "")
                        locus_tag2 = cds[j + 1].strip()
                        locus_tag2 = locus_tag2.replace("\"", "")
                        locus_tag2 = locus_tag2.replace("\n", "")
                        locus_tag = f"{locus_tag}{locus_tag2}"
                        positions[locus_tag] = str(position[0]) + "\t" + str(position[1])
                        break
                        
            if "CONTIG " in cds[i]:
                lenght = lenght + int(cds[i].strip().replace(")", "").split("..")[-1])
                
        return positions

class Aligner:
    def __init__(self, dppath):
        self.dppath = dppath
        self.diamond_exe = os.path.join(dppath, "diamond.exe" if PanViTaConfig.is_windows() else "diamond")
        self.blastp_exe = os.path.join(dppath, "blastp.exe" if PanViTaConfig.is_windows() else "blastp")
        self.tblastn_exe = os.path.join(dppath, "tblastn.exe" if PanViTaConfig.is_windows() else "tblastn")

    def choose_aligner(self):
        """Determine which aligner(s) to use based on availability and user choice"""
        diamond_available = os.path.exists(self.diamond_exe)
        blast_available = os.path.exists(self.blastp_exe)
        tblastn_available = os.path.exists(self.tblastn_exe)
        
        if not diamond_available and not blast_available:
            print("ERROR: Neither DIAMOND nor BLAST were found!")
            return None, None, None
        
        # Check if MEGARes is being used (requires tblastn for nucleotide sequences)
        megares_used = "-megares" in sys.argv
        
        if not diamond_available:
            print("DIAMOND not found. Using BLAST only.")
            return ["blast"], [self.blastp_exe], ["BLAST"]
        
        if not blast_available:
            if megares_used:
                print("WARNING: MEGARes analysis requires BLAST (tblastn), but BLAST was not found!")
                print("MEGARes will be skipped. Using DIAMOND for other databases.")
            else:
                print("BLAST not found. Using DIAMOND only.")
            return ["diamond"], [self.diamond_exe], ["DIAMOND"]
        
        # Both are available, ask user
        print("\nBoth DIAMOND and BLAST are available.")
        if megares_used:
            print("Note: MEGARes analysis will use BLAST (tblastn) for nucleotide sequences.")
        print("Which aligner would you like to use?")
        print("1. DIAMOND only (faster)" + (" - Note: MEGARes will be skipped with DIAMOND" if megares_used else ""))
        print("2. BLAST only (more sensitive)")
        print("3. Both DIAMOND and BLAST")
        
        while True:
            try:
                choice = input("Enter your choice (1, 2, or 3): ").strip()
                if choice == "1":
                    if megares_used:
                        print("Warning: DIAMOND cannot analyze MEGARes (nucleotide database). MEGARes will be skipped.")
                    return ["diamond"], [self.diamond_exe], ["DIAMOND"]
                elif choice == "2":
                    return ["blast"], [self.blastp_exe], ["BLAST"]
                elif choice == "3":
                    return ["diamond", "blast"], [self.diamond_exe, self.blastp_exe], ["DIAMOND", "BLAST"]
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
            except (EOFError, KeyboardInterrupt):
                print("\nUsing BLAST by default (required for MEGARes)." if megares_used else "\nUsing DIAMOND by default.")
                return (["blast"], [self.blastp_exe], ["BLAST"]) if megares_used else (["diamond"], [self.diamond_exe], ["DIAMOND"])

    def align(self, input_file, db_path, output_file, aligner_type="diamond", db_type="protein"):
        """Perform alignment using the specified aligner"""
        if aligner_type == "diamond":
            if db_type == "nucleotide":
                # DIAMOND doesn't support tblastn, so skip MEGARes for DIAMOND
                print(f"Warning: DIAMOND cannot be used with nucleotide databases (MEGARes). Skipping alignment for {os.path.basename(input_file)}...")
                # Create empty output file
                with open(output_file, 'w') as f:
                    pass
                return f"Skipped {os.path.basename(input_file)} for DIAMOND (nucleotide db)"
            else:
                # Use blastp for protein databases (protein query vs protein db)
                cmd = (f"{self.diamond_exe} blastp -q {input_file} -d {db_path}.dmnd -o {output_file} "
                       "--quiet -k 1 -e 5e-6 -f 6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore")
        elif aligner_type == "blast":
            if db_type == "nucleotide":
                # Use tblastn for nucleotide databases (protein query vs translated nucleotide db)
                cmd = (f"{self.tblastn_exe} -query {input_file} -db {db_path} -out {output_file} "
                       '-max_target_seqs 1 -evalue 5e-6 -outfmt "6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore"')
            else:
                # Use blastp for protein databases
                cmd = (f"{self.blastp_exe} -query {input_file} -db {db_path} -out {output_file} "
                       '-max_target_seqs 1 -evalue 5e-6 -outfmt "6 qseqid sseqid pident qcovhsp mismatch gapopen qstart qend sstart send evalue bitscore"')
        
        # print(f"Aligning {input_file}...")
        os.system(cmd)
        return f"Aligned {os.path.basename(input_file)}"

class DataProcessor:
    @staticmethod
    def blastmining_specific(input_file, input_dir, output_dir):
        """Filter alignment results based on thresholds"""
        _in = os.path.join(input_dir, input_file)
        _out = os.path.join(output_dir, input_file)
        evalue = 5e-06
        identidade = 70
        cobertura = 70
        
        if "-i" in sys.argv:
            try:
                identidade = float(sys.argv[sys.argv.index("-i") + 1])
            except BaseException:
                identidade = 70
                
        if "-c" in sys.argv:
            try:
                cobertura = float(sys.argv[sys.argv.index("-c") + 1])
            except BaseException:
                cobertura = 70
                
        # print(_out)
        try:
            with open(_in, 'rt') as fileO:
                file = fileO.readlines()
                
            with open(_out, 'w') as saida:
                for j in file:
                    linha = j.split('\t')
                    if float(linha[10]) <= evalue:
                        if float(linha[2]) >= identidade:
                            if float(linha[3]) >= cobertura:
                                saida.write(j)
        except BaseException:
            print(f"Warning: mining file not found - {_in}")

    @staticmethod
    def extract_keys(db_param, dbpath):
        """Extract gene keys and annotations from database files"""
        comp = {}
        genes_comp = {}
        
        print(f"Extracting gene keys for {db_param}...")
        
        # BACMET
        if "-bacmet" == db_param:
            try:
                with open(os.path.join(dbpath, 'bacmet_2.fasta'), 'rt') as bacmetFile:
                    bacmet = bacmetFile.readlines()
                
                for i in bacmet:
                    if '>' in i:
                        # Format: >BAC0001|abeM|tr|Q5FAM9|Q5FAM9_ACIBA
                        parts = i.split('|')
                        if len(parts) >= 2:
                            ident = parts[0][1:]  # Remove '>' and get BAC0001
                            gene = parts[1]       # Get abeM
                            comp[str(ident)] = str(gene)
                
                print(f"  - BacMet: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading BacMet database: {e}")
        
        # CARD
        elif "-card" == db_param:
            try:
                with open(os.path.join(dbpath, 'card_protein_homolog_model.fasta'), 'rt') as cardFile:
                    card = cardFile.readlines()
                
                for i in card:
                    if '>' in i:
                        # Format: >gb|ACT97415.1|ARO:3002999|CblA-1 [mixed culture bacterium AX_gF3SD01_15]
                        parts = i.split("|")
                        if len(parts) >= 4:
                            ident = parts[1]     # Get ACT97415.1
                            gene = parts[3].split()[0]  # Get CblA-1 (before space)
                            comp[str(ident)] = str(gene)
                
                print(f"  - CARD: {len(comp)} gene mappings extracted")
                
            except Exception as e:
                print(f"Warning: Error reading CARD database: {e}")
        
        # VFDB
        elif "-vfdb" == db_param:
            try:
                with open(os.path.join(dbpath, 'vfdb_core.fasta'), 'rt') as vfdbFile:
                    vfdb = vfdbFile.readlines()
                
                for i in vfdb:
                    if '>' in i:
                        # Format: >VFG037176(gb|WP_001081735) (plc1) phospholipase C [Phospholipase C (VF0470) - Exotoxin (VFC0235)] [Acinetobacter baumannii ACICU]
                        # Extract mechanism using regex
                        mech = re.findall(r"(?<=\)\s-\s)[A-z\/\-\s]*(?=\s\()", i, flags=0)
                        if len(mech) == 1:
                            mech = mech[0]
                        else:
                            mech = "Unknown"
                        
                        # Extract identifier and gene name
                        if '(' in i and ')' in i:
                            # Get the part between first ( and first )
                            start = i.find('(') + 1
                            end = i.find(')', start)
                            if start < end:
                                gene_part = i[start:end]
                                # Handle different formats like (gb|WP_001081735) or (plc1)
                                if '|' in gene_part:
                                    parts = gene_part.split('|')
                                    ident = parts[-1]  # Get the last part after |
                                else:
                                    ident = gene_part
                            else:
                                continue
                            
                            # Get gene name from the second parentheses if exists
                            second_paren = i.find('(', end)
                            if second_paren != -1:
                                gene_end = i.find(')', second_paren)
                                if gene_end != -1:
                                    gene = i[second_paren + 1:gene_end]
                                else:
                                    gene = ident
                            else:
                                gene = ident
                            
                            comp[str(ident)] = str(gene)
                            genes_comp[str(gene)] = str(mech)
                
                print(f"  - VFDB: {len(comp)} gene mappings extracted")
                print(f"  - VFDB mechanisms: {len(genes_comp)} mechanisms extracted")
                
            except Exception as e:
                print(f"Warning: Error reading VFDB database: {e}")
        
        # MEGARes
        elif "-megares" == db_param:
            try:
                with open(os.path.join(dbpath, 'megares_v3.fasta'), 'rt') as megaresFile:
                    megares = megaresFile.readlines()
                
                unique_genes = set()  # Track unique gene names for debugging
                mechanisms_comp = {}  # Additional mapping for mechanisms
                
                for i in megares:
                    if '>' in i:
                        # Format: >MEG_1|Drugs|Aminoglycosides|Aminoglycoside-resistant_16S_ribosomal_subunit_protein|A16S|RequiresSNPConfirmation
                        parts = i.split('|')
                        if len(parts) >= 5:
                            ident = parts[0][1:]  # Remove '>' and get MEG_1
                            drug_type = parts[1]  # Get Drugs
                            drug_class = parts[2] # Get Aminoglycosides  
                            mechanism = parts[3]  # Get Aminoglycoside-resistant_16S_ribosomal_subunit_protein
                            gene = parts[4]       # Get A16S
                            
                            gene_clean = str(gene).strip()
                            comp[str(ident)] = gene_clean  # Clean whitespace/newlines
                            genes_comp[gene_clean] = str(drug_class).strip()  # Map gene to drug class
                            mechanisms_comp[gene_clean] = str(mechanism).strip()  # Map gene to mechanism
                            unique_genes.add(gene_clean)
                
                print(f"  - MEGARes: {len(comp)} gene mappings extracted")
                print(f"  - MEGARes drug classes: {len(set(genes_comp.values()))} unique drug classes")
                print(f"  - MEGARes mechanisms: {len(set(mechanisms_comp.values()))} unique mechanisms")
                print(f"  - MEGARes unique genes found: {len(unique_genes)}")
                
                # Debug: Print first few unique genes
                if unique_genes:
                    sample_genes = sorted(list(unique_genes))[:10]
                    # print(f"  - Sample genes: {', '.join(sample_genes)}")
                
                # Return the mechanisms mapping for MEGARes as third element
                return comp, genes_comp, mechanisms_comp
                
            except Exception as e:
                print(f"Warning: Error reading MEGARes database: {e}")
        
        if len(comp) == 0:
            print(f"Warning: No gene mappings found for {db_param}! This may cause issues with analysis.")
        
        return comp, genes_comp

class Visualization:
    @staticmethod
    def generate_matrix(db_param, outputs, comp, aligner_suffix=""):
        """Generate presence/absence matrix from alignment results"""
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        if aligner_suffix:
            titulo = f"matriz_{db_name}_{aligner_suffix}.csv"
            tabular_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
        else:
            titulo = f"matriz_{db_name}.csv"
            tabular_dir = f"Tabular_2_{db_name}"
        
        outputs.append(titulo)

        print(f"\nGenerating the presence and identity matrix for {db_param}{f' ({aligner_suffix})' if aligner_suffix else ''}...")

        dicl = {}
        totalgenes = set()  # Use set for better performance
        found_genes_per_strain = {}  # Track found genes per strain for save-genes functionality
        
        # Check if directory exists and has files
        if not os.path.exists(tabular_dir):
            print(f"Warning: Directory {tabular_dir} not found!")
            return titulo, dicl, [], found_genes_per_strain
            
        files_in_dir = os.listdir(tabular_dir)
        if not files_in_dir:
            print(f"Warning: No files found in {tabular_dir}!")
            return titulo, dicl, [], found_genes_per_strain
        
        print(f"Processing {len(files_in_dir)} strain files...")
        
        # Debug: Print sample of comp dictionary for MEGARes.
        if db_param == "-megares" and comp:
            # print(f"Sample comp mappings for MEGARes:")
            sample_keys = list(comp.keys())[:5]  # Show first 5 mappings
            # for k in sample_keys:
                # print(f"  {k} -> {comp[k]}")
        
        for i in files_in_dir:
            if not i.endswith('.tab'):
                continue
                
            linhagem = i[:-4]  # Remove .tab extension
            file_path = os.path.join(tabular_dir, i)
            
            try:
                with open(file_path, 'rt') as file:
                    linhas = file.readlines()
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}")
                continue
            
            genes = {}
            genes_found = 0
            debug_sample_count = 0
            strain_found_genes = {}  # Track locus_tags and genes for this strain
            
            for j in linhas:
                linha = j.strip()
                if not linha:  # Skip empty lines
                    continue
                    
                linha = linha.split('\t')
                if len(linha) < 3:  # Need at least query, subject, identity
                    continue
                
                # Debug: Print first few subject IDs for MEGARes to understand format
                if db_param == "-megares" and debug_sample_count < 3:
                    # print(f"  Debug - Subject ID: {linha[1]}")
                    debug_sample_count += 1
                    
                gene = None
                original_gene = None  # For debugging
                locus_tag = linha[0]  # First column is the locus_tag
                
                # Special handling for MEGARes first - extract exact MEG_ID
                if 'MEG_' in linha[1] and '|' in linha[1]:
                    # Subject ID format: MEG_7303|Drugs|Elfamycins|EF-Tu_inhibition|TUFAB|RequiresSNPConfirmation
                    parts = linha[1].split('|')
                    if len(parts) >= 5:
                        meg_id = parts[0]  # Get MEG_7303 (exact match)
                        actual_gene = parts[4]  # Get TUFAB (the real gene name)
                        
                        # Check if we have this exact MEG_ID in our comp dictionary
                        if meg_id in comp:
                            gene = comp[meg_id]
                            original_gene = "exact_comp_match:" + meg_id
                        # If not found, use the actual gene from the header
                        elif actual_gene.strip():
                            gene = actual_gene.strip().replace('\n', '').replace('\r', '')  # Clean newlines
                            original_gene = "header_gene:" + actual_gene.strip()
                            # Debug print for this case
                            # if db_param == "-megares" and debug_sample_count <= 10:
                                # print(f"    Using gene from header: {meg_id} -> {gene}")
                
                # If no MEGARes match, try regular substring matching for other databases
                if gene is None:
                    for k in comp.keys():
                        if k in linha[1]:  # linha[1] is the subject sequence ID
                            gene = comp[k]
                            original_gene = "substring_match:" + k
                            break
                
                # Debug print for MEGARes
                # if db_param == "-megares" and gene and debug_sample_count <= 10:
                    # print(f"    Matched gene: {gene} (from {original_gene})")
                
                if gene:
                    try:
                        identidade = float(linha[2])  # Convert identity to float
                        genes[gene] = identidade
                        totalgenes.add(gene)
                        genes_found += 1
                        
                        # Store locus_tag for save-genes functionality
                        if gene not in strain_found_genes:
                            strain_found_genes[gene] = []
                        strain_found_genes[gene].append(locus_tag)
                        
                    except (ValueError, IndexError):
                        print(f"Warning: Invalid identity value in {file_path}: {linha}")
                        continue
            
            dicl[str(linhagem)] = genes
            found_genes_per_strain[str(linhagem)] = strain_found_genes
            # print(f"  - {linhagem}: {genes_found} genes found")
        
        # Convert set back to sorted list for consistent output
        totalgenes = sorted(list(totalgenes))
        
        print(f"Total unique genes found: {len(totalgenes)}")
        print(f"Total strains processed: {len(dicl)}")
        
        # Generate the matrix file
        if not totalgenes:  # If no genes were found, create empty matrix
            print(f"Warning: No genes found for {db_param}. Creating empty matrix.")
            with open(titulo, 'w') as saida:
                saida.write('Strains\n')
                for strain in dicl.keys():
                    saida.write(strain + '\n')
            return titulo, dicl, [], found_genes_per_strain
        
        with open(titulo, 'w') as saida:
            saida.write('Strains')
            for gene in totalgenes:
                saida.write(f';{gene}')
            saida.write('\n')
            
            for strain in dicl.keys():
                saida.write(strain)
                for gene in totalgenes:
                    if gene in dicl[strain]:
                        saida.write(f';{dicl[strain][gene]}')
                    else:
                        saida.write(';0')
                saida.write('\n')
        
        print(f"Matrix saved as: {titulo}")
        return titulo, dicl, totalgenes, found_genes_per_strain

    @staticmethod
    def generate_heatmap(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Generate clustermap visualization from matrix"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"
        
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        if aligner_suffix:
            out = f"heatmap_{db_name}_{aligner_suffix}.{fileType}"
        else:
            out = f"heatmap_{db_name}.{fileType}"
        
        outputs.append(out)
        
        if db_param == "-card":
            color = "Blues"
        elif db_param == "-vfdb":
            color = "Reds"
        elif db_param == "-bacmet":
            color = "Greens"
        elif db_param == "-megares":
            color = "Oranges"

        df = pd.read_csv(data_file, sep=';')
        df = df.set_index('Strains')
        headers = list(df.columns.values)
        lines = list(df.index.values)
        for i in headers:
            if "Unnamed:" in i:
                df = df.drop(columns=[i])


        x = math.ceil(len(headers) * 0.65)
        y = math.ceil(len(lines) * 0.65)


        print(f"\nPlotting final heatmap{f' ({aligner_suffix})' if aligner_suffix else ''}...")
        try:

            plt.figure(figsize=(x, y))
            p2 = sns.heatmap(df, cmap=color, annot=True, fmt='.0f', cbar_kws={'label': 'Identity (%)'})
            p2.figure.savefig(out, format=fileType, dpi=300, bbox_inches="tight")

            plt.close()

        except BaseException:
            erro_string = f"\nIt was not possible to plot the {out} figure...\nPlease verify the GenBank files and the matrix_x.csv output."
            erro.append(erro_string)
            print(erro_string)

    @staticmethod
    def generate_barplot(data_file, index_col, output_file, fileType, outputs):
        """
        Generates a bar chart from a data file, with sorting and dynamic sizing for clarity.
        This is the appropriate method for comparing counts across unordered categories.
        """
        try:
            data = pd.read_csv(data_file, sep=";", index_col=index_col)
            if data.empty:
                print(f"Warning: No data to plot in {output_file}")
                return

            # Sum counts to sort categories from highest to lowest for better readability
            data['Total'] = data.sum(axis=1)
            data_sorted = data.sort_values('Total', ascending=False).drop(columns='Total')

            # Melt dataframe to long format for seaborn
            data_melted = data_sorted.reset_index().melt(id_vars=index_col, var_name='Category', value_name='Count')

            num_categories = len(data_sorted.index)
            # Dynamic figure sizing
            width = max(12, min(30, 8 + num_categories * 0.8))
            height = 8

            plt.figure(figsize=(width, height))
            ax = sns.barplot(data=data_melted, x=index_col, y='Count', hue='Category',
                             palette={"Core": "#1f77b4", "Accessory": "#ff7f0e", "Exclusive": "#2ca02c"})

            ax.set_xlabel(index_col.replace('_', ' ').title(), fontsize=12, fontweight='bold')
            ax.set_ylabel('Number of Genes', fontsize=12, fontweight='bold')
            ax.set_title(f'Distribution of Genes by {index_col.replace("_", " ").title()}', fontsize=16, fontweight='bold')

            plt.xticks(rotation=45, ha='right')
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            plt.tight_layout()

            plt.savefig(output_file, format=fileType, dpi=300)
            plt.close()
            
            outputs.append(output_file)
            print(f"Bar chart saved as: {output_file}")
        
        except Exception as e:
            print(f"Error generating bar chart {output_file}: {e}")

    @staticmethod
    def generate_bubble_plot(data_file, index_col, output_file, fileType, outputs):
        """
        Creates a bubble plot to visualize three dimensions of data:
        X-axis: Count of Core genes.
        Y-axis: Count of Accessory genes.
        Bubble size and color: Count of Exclusive genes.
        """
        try:
            data = pd.read_csv(data_file, sep=';', index_col=index_col)
            if data.empty:
                print(f"Warning: No data to plot in {output_file}")
                return

            # Ensure required columns exist
            required_cols = ['Core', 'Accessory', 'Exclusive']
            if not all(col in data.columns for col in required_cols):
                print(f"Error: Data for bubble plot must contain columns 'Core', 'Accessory', and 'Exclusive'.")
                return
            
            # Filter out rows where all counts are zero
            data_filtered = data[(data[required_cols] > 0).any(axis=1)]
            if data_filtered.empty:
                print(f"Warning: All data points have zero values. Cannot create bubble plot for {output_file}.")
                return

            plt.figure(figsize=(14, 10))
            
            bubble_plot = sns.scatterplot(
                data=data_filtered,
                x="Core",
                y="Accessory",
                size="Exclusive",
                hue="Exclusive",
                sizes=(20, 500),  # Min and max bubble sizes
                palette="viridis_r",
                alpha=0.8,
                edgecolor="black",
                linewidth=0.5
            )

            title = f'Core vs. Accessory Gene Distribution by {index_col.replace("_", " ").title()}'
            bubble_plot.set_title(title, fontsize=16, fontweight='bold')
            bubble_plot.set_xlabel("Core Gene Count", fontsize=12, fontweight='bold')
            bubble_plot.set_ylabel("Accessory Gene Count", fontsize=12, fontweight='bold')

            bubble_plot.grid(True, linestyle="--", alpha=0.6)
            
            # Improve legend
            handles, labels = bubble_plot.get_legend_handles_labels()
            bubble_plot.legend(handles, labels, title="Exclusive Gene Count", bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, shadow=True)

            plt.tight_layout()
            plt.savefig(output_file, format=fileType, dpi=300)
            plt.close()
            
            outputs.append(output_file)
            print(f"Bubble plot saved as: {output_file}")

        except Exception as e:
            print(f"Error generating bubble plot {output_file}: {e}")

    @staticmethod
    def generate_joint_and_marginal_distributions(data_file, db_param, outputs, erro, aligner_suffix=""):
        """Hexbin joint plot with marginal distributions using seaborn"""
        try:
            fileType = "pdf" if "-pdf" in sys.argv or "-png" not in sys.argv else "png"
            if "-png" in sys.argv:
                fileType = "png"
            db_name = db_param[1:]
            out = f"joint_hexbin_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
            outputs.append(out)

            # Database-specific color palettes (matching other generate methods)
            if db_param == "-card":
                color_palette = "Blues"
                main_color = "#2171b5"  # Blue
            elif db_param == "-vfdb":
                color_palette = "Reds"
                main_color = "#cb181d"  # Red
            elif db_param == "-bacmet":
                color_palette = "Greens"
                main_color = "#238b45"  # Green
            elif db_param == "-megares":
                color_palette = "Oranges"
                main_color = "#d94801"  # Orange
            else:
                color_palette = "viridis"
                main_color = "#4CB391"  # Default

            df = pd.read_csv(data_file, sep=';').set_index('Strains')
            for col in list(df.columns):
                if "Unnamed:" in col:
                    df = df.drop(columns=[col])

            # Metrics
            genes_present = (df > 0).sum(axis=1).astype(int)
            df_numeric = df.apply(pd.to_numeric, errors='coerce')
            # Calculate mean identity, replacing 0 with NaN for calculation, then fill NaN with 0
            mean_identity_temp = df_numeric.replace(0, pd.NA).mean(axis=1, skipna=True)
            mean_identity = pd.to_numeric(mean_identity_temp.fillna(0), errors='coerce')
            metrics = pd.DataFrame({"GenesPresent": genes_present, "MeanIdentity": mean_identity})

            if metrics.empty:
                print(f"Warning: No data to plot for hexbin jointplot ({db_param})")
                return

            # Check if we have enough data points for a meaningful hexbin plot
            if len(metrics) < 2:
                print(f"Warning: Not enough data points ({len(metrics)}) for hexbin jointplot ({db_param}). Need at least 2 strains.")
                return
            
            # Check for valid numeric ranges to avoid division by zero
            x_range = metrics["GenesPresent"].max() - metrics["GenesPresent"].min()
            y_range = metrics["MeanIdentity"].max() - metrics["MeanIdentity"].min()
            
            if x_range == 0 and y_range == 0:
                print(f"Warning: No variation in data for hexbin jointplot ({db_param}). All values are identical.")
                return
            elif x_range == 0:
                print(f"Warning: No variation in genes present for hexbin jointplot ({db_param})")
                return
            elif y_range == 0:
                print(f"Warning: No variation in mean identity for hexbin jointplot ({db_param})")
                return

            # Calculate dynamic figure size based on data range
            data_span_x = x_range if x_range > 0 else 10
            data_span_y = y_range if y_range > 0 else 10
            
            # Base size with scaling factor
            base_size = 6
            scale_factor = min(1.5, max(0.8, (data_span_x + data_span_y) / 100))
            fig_size = base_size * scale_factor
            
            # Set the correct theme
            sns.set_theme(style="ticks")
            
            try:
                x = metrics["GenesPresent"].to_numpy()
                y = metrics["MeanIdentity"].to_numpy()

                # Create hexbin plot with consistent colors and appropriate scaling
                g = sns.jointplot(
                    x=x, y=y, 
                    kind="hex", 
                    color=main_color,
                    height=fig_size,
                    joint_kws={
                        'gridsize': 15,  # Moderate hexagon size
                        'cmap': color_palette,
                        'alpha': 0.8,  # Full opacity for hexagons
                        'edgecolors': 'white'  # White edges for better definition
                    },
                    marginal_kws={
                        'color': main_color,
                        'alpha': 0.8,
                        'bins': 15
                    }
                )
                
                # Set labels and title
                g.set_axis_labels("Genes Present", "Mean Identity (%)", fontsize=12, fontweight='bold')
                g.figure.suptitle(f"Hexbin plot with marginal distributions - {db_name.upper()}", 
                                y=1.02, fontsize=14, fontweight="bold")
                
                # Improve axis appearance
                g.ax_joint.tick_params(labelsize=10)
                
                # Add some padding to the axes
                x_padding = x_range * 0.05 if x_range > 0 else 1
                y_padding = y_range * 0.05 if y_range > 0 else 1
                
                g.ax_joint.set_xlim(
                    metrics["GenesPresent"].min() - x_padding,
                    metrics["GenesPresent"].max() + x_padding
                )
                g.ax_joint.set_ylim(
                    metrics["MeanIdentity"].min() - y_padding,
                    metrics["MeanIdentity"].max() + y_padding
                )

                g.figure.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
                plt.close(g.figure)
                print(f"Hexbin jointplot saved as: {out}")
                
            finally:
                # Reset theme to default after plotting
                sns.reset_defaults()
                
        except Exception as e:
            erro_string = f"\nFailed to plot hexbin jointplot ({db_param}): {e}"
            erro.append(erro_string)
            print(erro_string)

    @staticmethod
    def generate_scatterplot_heatmap(data_file, db_param, outputs, erro, aligner_suffix=""):
        """
        Generates a highly dynamic scatterplot-based heatmap (dot plot) that robustly scales 
        to handle very large datasets (from 10 to 2000+ genomes). The plot dimensions,
        dot sizes, and font sizes all adjust automatically to ensure readability at any scale.
        """
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"

        db_name = db_param[1:]
        out = f"scatter_heatmap_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        outputs.append(out)

        try:
            with sns.axes_style("whitegrid"):
                df = pd.read_csv(data_file, sep=';').set_index('Strains')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

                long_df = df.reset_index().melt(id_vars='Strains', var_name='Gene', value_name='Identity')
                long_df['Identity'] = pd.to_numeric(long_df['Identity'], errors='coerce')
                long_df = long_df[long_df['Identity'] > 0]

                if long_df.empty:
                    print(f"Warning: No data to plot for scatter heatmap {out}. All gene identities are zero.")
                    return

                id_min = float(long_df['Identity'].min())
                id_max = float(long_df['Identity'].max())
                if id_max <= id_min: id_max = id_min + 1.0

                palette_map = {"-card": "Blues", "-vfdb": "Reds", "-bacmet": "Greens", "-megares": "Oranges"}
                palette = palette_map.get(db_param, "viridis")

                n_genes = long_df['Gene'].nunique()
                n_strains = long_df['Strains'].nunique()

                # --- ADVANCED DYNAMIC SCALING LOGIC ---

                # 1. Figure Sizing (non-linear scaling)
                # Height scales with the square root of strains, ensuring it grows but doesn't become enormous.
                # A base size ensures small plots are still readable.
                height = min(100, 4 + np.sqrt(n_strains) * 1.5) 
                
                # Aspect ratio (width/height) scales similarly with genes.
                # This makes the plot wider for more genes.
                width = min(120, 5 + np.sqrt(n_genes) * 2.0)
                aspect_ratio = width / height

                # 2. Dot Sizing (inversely proportional to data density)
                # As the number of strains/genes increases, the dots get smaller.
                # We use a logarithmic scale to gracefully handle the wide range of inputs.
                density_factor = np.log1p(n_strains + n_genes) # log1p is log(1+x)
                max_dot_size = max(30, 250 / density_factor)
                min_dot_size = max(5, max_dot_size / 5)
                dot_size_range = (min_dot_size, max_dot_size)

                # 3. Font and Line Sizing
                y_labelsize = max(4, 12 - np.log2(max(1, n_strains))) # Font size decreases slowly
                grid_linewidth = max(0.2, 1.0 - density_factor * 0.1)

                print(f"\nPlotting fully dynamic scatter heatmap{f' ({aligner_suffix})' if aligner_suffix else ''}...")
                print(f"  - Dimensions: {n_strains} strains, {n_genes} genes.")
                print(f"  - Calculated Figure (H x W): {height:.1f}in x {width:.1f}in")
                print(f"  - Calculated Dot Size Range: ({min_dot_size:.1f}, {max_dot_size:.1f})")

                # Set the figure grid first to control overall aesthetics
                g = sns.relplot(
                    data=long_df,
                    x="Gene", y="Strains",
                    hue="Identity", size="Identity",
                    palette=palette, legend=True,
                    hue_norm=(id_min, id_max),
                    edgecolor=".7",
                    height=height,
                    sizes=dot_size_range,
                    size_norm=(id_min, id_max),
                    aspect=aspect_ratio,
                    kind='scatter'
                )

                # --- AESTHETIC ADJUSTMENTS ---
                g.set(xlabel="Genes", ylabel="Strains")
                g.despine(left=True, bottom=True)
                
                # Apply dynamic grid and font sizes
                g.ax.grid(True, which='major', axis='both', linestyle='--', linewidth=grid_linewidth)
                g.ax.tick_params(axis='y', labelsize=y_labelsize)
                
                for label in g.ax.get_xticklabels():
                    label.set_rotation(90)

                g.figure.suptitle(f"Gene Presence Scatter Heatmap - {db_name.upper()}", y=1.02, fontweight="bold")
                
                # Use a tight layout before saving
                plt.tight_layout(rect=[0, 0, 1, 0.98]) 

                g.figure.savefig(out, format=fileType, dpi=300)
                plt.close(g.figure)
                print(f"Dynamic scatter heatmap saved as: {out}")

        except Exception as e:
            error_message = (
                f"\nIt was not possible to plot the scatter heatmap {out}...\n"
                f"Error: {e}\nPlease verify the matrix file is not empty."
            )
            erro.append(error_message)
            print(error_message)
            import traceback
            traceback.print_exc()

    @staticmethod
    def generate_clustermap(data_file, db_param, outputs, erro, aligner_suffix=""):
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"

        db_name = db_param[1:]
        out = f"clustermap_{db_name}{f'_{aligner_suffix}' if aligner_suffix else ''}.{fileType}"
        outputs.append(out)

        cmap_map = {
            "-card": "Blues", "-vfdb": "Reds",
            "-bacmet": "Greens", "-megares": "Oranges"
        }
        cmap = cmap_map.get(db_param, "viridis")

        try:
            df = pd.read_csv(data_file, sep=';').set_index('Strains')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            # Check if there is data to plot
            if df.empty or df.shape[1] == 0:
                print(f"Warning: Empty data for clustermap: {data_file}. Skipping plot.")
                return

            # Clustermap requires at least 2 rows and 2 columns to perform clustering.
            num_rows, num_cols = df.shape
            if num_rows < 2 or num_cols < 2:
                print(f"Warning: Not enough data for clustering ({num_rows} strains x {num_cols} genes).")
                print("Clustermap requires at least 2 of each. Skipping plot.")
                return

            # Dynamic figsize to make cells more square-like
            fig_width = max(10, 0.3 * num_cols)
            fig_height = max(8, 0.5 * num_rows)
            
            print(f"\nPlotting clustermap ({fig_width:.1f} x {fig_height:.1f} inches)...")

            g = sns.clustermap(
                df,
                cmap=cmap,
                method="average",
                metric="euclidean",
                linewidths=0,          
                linecolor='white',       
                cbar_kws={'label': 'Identity (%)'},
                figsize=(fig_width, fig_height)
            )
            
            g.fig.suptitle(f"Hierarchical Clustermap - {db_name.upper()}", y=1.02, fontweight="bold")
            plt.setp(g.ax_heatmap.get_xticklabels(), rotation=90)
            
            g.savefig(out, format=fileType, dpi=300, bbox_inches="tight")
            plt.close(g.fig)
            print(f"Hierarchical clustermap saved as: {out}")
            
        except Exception as e:
            erro_string = f"\nIt was not possible to plot the clustermap {out}: {e}"
            erro.append(erro_string)
            print(erro_string)


    @staticmethod
    def generate_lineplot(data_file, title, pan_label, core_label, output_file, fileType, outputs):
        """Generate pan-genome lineplot with improved axis tick handling for readability."""
        try:
            df_pan = pd.read_csv(data_file, sep=";")
            
            if len(df_pan) == 0:
                print("Warning: No data found for pan-genome analysis!")
                return
            
            df_pan["Number of Genomes"] = list(range(1, len(df_pan["Strains"]) + 1))
            df_pan = df_pan.rename(columns={'Core': 'Core Genes'})
            
            # Validate that core never exceeds pan
            if "Core Genes" in df_pan.columns and "Pan" in df_pan.columns:
                invalid_rows = df_pan[df_pan["Core Genes"] > df_pan["Pan"]]
                if not invalid_rows.empty:
                    print("Warning: Found rows where core > pan, correcting...")
                    df_pan.loc[df_pan["Core Genes"] > df_pan["Pan"], "Core Genes"] = df_pan["Pan"]
            
            plt.figure(figsize=(12, 8)) # Standardized figure size
            
            # Create line plots with better styling
            sns.lineplot(x="Number of Genomes", y="Pan", data=df_pan, 
                         marker='o', linewidth=2.5, markersize=8, color='#1f77b4', alpha=0.8, label=pan_label)
            sns.lineplot(x="Number of Genomes", y="Core Genes", data=df_pan, 
                         marker='s', linewidth=2.5, markersize=8, color='#ff7f0e', alpha=0.8, label=core_label)
            
            plt.xlabel('Number of Genomes', fontsize=14, fontweight='bold')
            plt.ylabel('Number of Genes', fontsize=14, fontweight='bold')
            plt.title(title, fontsize=16, fontweight='bold', pad=20)
            plt.legend(fontsize=12, frameon=True, shadow=True, loc='best')
            plt.grid(True, alpha=0.4, linestyle='--')
            
            # --- IMPROVED TICK HANDLING ---
            # Use MaxNLocator to automatically find the best integer ticks for both axes
            from matplotlib.ticker import MaxNLocator
            plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
            plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.xlim(left=0) # Start x-axis at 0 for better visualization
            plt.ylim(bottom=0) # Start y-axis at 0
            
            # Add annotations for the final points
            if len(df_pan) > 0:
                final_pan = df_pan["Pan"].iloc[-1]
                final_core = df_pan["Core Genes"].iloc[-1]
                num_genomes = len(df_pan)
                
                plt.annotate(f'Final Pan: {final_pan}', 
                            xy=(num_genomes, final_pan), 
                            xytext=(0, 15), textcoords='offset points',
                            ha='right', va='bottom',
                            bbox=dict(boxstyle='round,pad=0.4', fc='lightblue', alpha=0.8),
                            fontsize=10)
                plt.annotate(f'Final Core: {final_core}', 
                            xy=(num_genomes, final_core), 
                            xytext=(0, -15), textcoords='offset points',
                            ha='right', va='top',
                            bbox=dict(boxstyle='round,pad=0.4', fc='orange', alpha=0.8),
                            fontsize=10)
            
            plt.tight_layout()
            
            if not isinstance(output_file, str):
                output_file = str(output_file)
            if not output_file.endswith(f'.{fileType}'):
                output_file = f"{output_file}.{fileType}"
            
            plt.savefig(output_file, format=fileType, dpi=300)
            plt.close()
            outputs.append(output_file)
            
            print(f"Pan-genome analysis completed and plot saved as: {output_file}")
                
        except Exception as e:
            print(f"Error generating lineplot {output_file}: {e}")

class PanViTa:
    def __init__(self):
        self.erro = []
        self.dppath = None
        self.dbpath = None
        self.dic = None
        self.dic2 = None
        self.dic3 = None
        self.strains = None
        self.gbff = None
        self.pkgbf = None
        self.files = None
        self.parameters = None

    def run(self):
        """Main execution method for PanViTa"""
        self._handle_help_and_version()
        
        # Setup dependencies and databases
        dependency_manager = DependencyManager()
        self.dppath = dependency_manager.check_dependencies()
        
        # Determine which aligner(s) to use
        aligner = Aligner(self.dppath)
        aligner_types, aligner_exes, aligner_names = self._determine_aligners(aligner)
        
        if aligner_types is None:
            print("ERROR: No aligners available. Exiting.")
            exit(1)

        # Initialize variables
        self._setup_databases_and_dicts(aligner_exes)
        
        # Download operations
        if "-b" in sys.argv:
            self._download_genbank_files()
        if "-a" in sys.argv or "-g" in sys.argv:
            self._download_fasta_files()
            
        # Process files and parameters
        self._process_files_and_parameters()
        
        # If no analysis parameters, just organize downloaded files
        if len(self.parameters) == 0:
            self._organize_downloaded_files()
            return
            
        # Extract and save positions
        self._extract_and_save_positions()
        
        # Extract and save proteins
        self._extract_and_save_proteins()
        
        # *** OPTIMIZATION: Align and mine in parallel ***
        self._align_and_mine_parallel(aligner_types, aligner_exes, aligner_names)
        
        # Run main analysis workflow
        self._run_analysis_workflow(aligner_types, aligner_names)
        
        # Cleanup
        self._remove_intermediate_files()
        
        # Final messages
        self._print_final_messages()
        
    def _handle_help_and_version(self):
        """Handle version and help commands"""
        if ("-v" in sys.argv) or ("-version" in sys.argv):
            print("-----------------------------------------------")
            print("PanViTa - Pan Virulence and resisTance Analysis")
            print("https://doi.org/10.3389/fbinf.2023.1070406")
            print("version", PanViTaConfig.VERSION)
            print("-----------------------------------------------")
            exit()

        if (("-card" not in sys.argv) and ("-bacmet" not in sys.argv) and ("-vfdb" not in sys.argv) and 
            ("-megares" not in sys.argv) and ("-u" not in sys.argv) and ("-update" not in sys.argv) and
            ("-g" not in sys.argv) and ("-a" not in sys.argv) and ("-m" not in sys.argv) and 
            ("-b" not in sys.argv)) or ("-h" in sys.argv) or ("-help" in sys.argv):
            self._print_help()
            exit()

        print('''
Hello user!

This script has the function of comparing multiple genomes against previously selected databases.
The result consists of a clustermap and a presence matrix.

Contact: dlnrodrigues@ufmg.br - victorsc@ufmg.br - vinicius.oliveira.1444802@sga.pucminas.br

Let's continue with your analysis.''')

    def _print_help(self):
        """Print help information"""
        print('''
Hello user!

PanViTa has the function of comparing multiple genomes against previously selected databases.
The result consists of a clustermap and a presence matrix.

As input use GBF or GBK files derived from Prokka or available on NCBI.
WARNING! Files from NCBI MUST have .gbf or .gbff extension.

USAGE:
python3 ''' + sys.argv[0] + ''' -card -vfdb -bacmet -megares files.gbk\n
Databases:
-bacmet\tAntibacterial Biocide and Metal Resistance Genes Database
-card\tComprehensive Antibiotic Resistance Database
-megares\tMEGARes Antimicrobial Resistance Database
-vfdb\tVirulence Factor Database

Parameters:
-update\tUpdate databases and dependences
-u\tSame as -update
-help\tPrint this help
-h\tSame as -help
-v\tPrint version and exit
-keep\tMaintains the protein sequences used, as well as the CDS position files
-k\tSame as -keep
-i\tMinimum identity to infer presence (default = 70)
-c\tMinimum coverage to infer presence (default = 70)
-d\tForce to use DIAMOND from system
-diamond\tForce to use DIAMOND only for alignments
-blast\tForce to use BLAST only for alignments
-both\tUse both DIAMOND and BLAST for alignments
-pdf\tFigures will be saved as PDF (default)
-png\tFigures will be saved as PNG (WARNING! High memory consumption)
-save-genes\tSave found genes in individual .faa files for each genome
-g\tDownload the genomes fasta files (require CSV table from NCBI)
-a\tDownload and annote the genomes using PROKKA pipeline (require CSV table from NCBI)
-b\tDownload the genome GenBank files (require CSV table from NCBI)
-s\tKeep the locus_tag as same as the strain (require -b)
-m\tGet the metadata from BioSample IDs (require CSV table from NCBI)

Note: If no aligner is specified, the program will prompt you to choose between DIAMOND, BLAST, or both.

Contact: victorsc@ufmg.br , dlnrodrigues@ufmg.br
        ''')

    def _determine_aligners(self, aligner):
        """Determine which aligner(s) to use based on command line arguments"""
        if "-diamond" in sys.argv:
            aligner_types = ["diamond"]
            diamond_exe = os.path.join(self.dppath, "diamond.exe" if PanViTaConfig.is_windows() else "diamond")
            if "-d" in sys.argv:
                if isinstance(shutil.which("diamond-aligner"), str):
                    diamond_exe = shutil.which("diamond-aligner")
                elif isinstance(shutil.which("diamond"), str):
                    diamond_exe = shutil.which("diamond")
                else:
                    erro_string = "\nWe couldn't locate DIAMOND on your system.\nWe'll try to use the default option.\nPlease verify the alignment outputs.\n"
                    print(erro_string)
                    self.erro.append(erro_string)
            aligner_exes = [diamond_exe]
            aligner_names = ["DIAMOND"]
        elif "-blast" in sys.argv:
            aligner_types = ["blast"]
            blastp_exe = os.path.join(self.dppath, "blastp.exe" if PanViTaConfig.is_windows() else "blastp")
            aligner_exes = [blastp_exe]
            aligner_names = ["BLAST"]
        elif "-both" in sys.argv:
            aligner_types = ["diamond", "blast"]
            diamond_exe = os.path.join(self.dppath, "diamond.exe" if PanViTaConfig.is_windows() else "diamond")
            blastp_exe = os.path.join(self.dppath, "blastp.exe" if PanViTaConfig.is_windows() else "blastp")
            if "-d" in sys.argv:
                if isinstance(shutil.which("diamond-aligner"), str):
                    diamond_exe = shutil.which("diamond-aligner")
                elif isinstance(shutil.which("diamond"), str):
                    diamond_exe = shutil.which("diamond")
                else:
                    erro_string = "\nWe couldn't locate DIAMOND on your system.\nWe'll try to use the default option.\nPlease verify the alignment outputs.\n"
                    print(erro_string)
                    self.erro.append(erro_string)
            aligner_exes = [diamond_exe, blastp_exe]
            aligner_names = ["DIAMOND", "BLAST"]
        else:
            # Let user choose interactively
            return aligner.choose_aligner()
            
        return aligner_types, aligner_exes, aligner_names

    def _setup_databases_and_dicts(self, aligner_exes):
        """Setup databases and dictionaries if needed"""
        if "-a" in sys.argv or "-b" in sys.argv or "-g" in sys.argv or "-m" in sys.argv:
            db_manager = DatabaseManager(self.dppath)
            self.dbpath = db_manager.check_databases(aligner_exes[0])
            
            for i in sys.argv:
                if i.endswith(".csv"):
                    table = i
                    
            df = pd.read_csv(table, sep=',')
            species = df["#Organism Name"].tolist()
            self.strains = df["Strain"].tolist()
            biosample = df["BioSample"].tolist()
            size = df["Size(Mb)"].tolist()
            GC = df["GC%"].tolist()
            refseq = df["RefSeq FTP"].tolist()
            genbank = df["GenBank FTP"].tolist()
            data = df["Release Date"].tolist()
            self.dic = {}
            self.dic2 = {}
            self.dic3 = {}
            
            ind = 0
            while ind in range(0, len(self.strains)):
                if "-b" in sys.argv:
                    self.dic[biosample[ind]] = (
                        species[ind], refseq[ind], genbank[ind], self.strains[ind], 
                        size[ind], GC[ind], data[ind])
                if "-m" in sys.argv:
                    self.dic2[biosample[ind]] = (
                        species[ind], refseq[ind], genbank[ind], self.strains[ind], 
                        size[ind], GC[ind], data[ind])
                if "-a" in sys.argv or "-g" in sys.argv:
                    self.dic3[biosample[ind]] = (
                        species[ind], refseq[ind], genbank[ind], self.strains[ind], 
                        size[ind], GC[ind], data[ind])
                ind = ind + 1
        else:
            # If no CSV operations, still need to setup databases
            db_manager = DatabaseManager(self.dppath)
            self.dbpath = db_manager.check_databases(aligner_exes[0])

    def _download_genbank_files(self):
        """Download GenBank files from NCBI"""
        downloader = NCBIDownloader(self.dic)
        self.gbff = downloader.get_ncbi_gbf()
        self.erro.extend(downloader.erro)

    def _download_fasta_files(self):
        """Download FASTA files from NCBI and optionally annotate with PROKKA"""
        downloader = NCBIDownloader(self.dic3)
        self.pkgbf = downloader.get_ncbi_fna()
        self.erro.extend(downloader.erro)

    def _process_files_and_parameters(self):
        """Process input files and parameters"""
        print("Separating files")
        self.files = []
        for i in sys.argv:
            if i.endswith(".gbk") or i.endswith(".gbf") or i.endswith(".gbff"):
                self.files.append(i)
                
        for i in sys.argv:
            if i.endswith(".csv"):
                prokaryotes = i
                break
                
        if "-a" in sys.argv and "-b" not in sys.argv:
            if self.pkgbf and self.pkgbf[0] != "":
                for i in self.pkgbf:
                    self.files.append(i)
        elif "-b" in sys.argv:
            if self.gbff:
                for i in self.gbff:
                    self.files.append(i)
                    
        print("Separating parameters")
        self.parameters = []
        for i in sys.argv:
            if i in ["-card", "-bacmet", "-vfdb", "-megares"]:
                self.parameters.append(i)

    def _organize_downloaded_files(self):
        """Organize downloaded files if no analysis parameters"""
        if "-b" in sys.argv:
            pasta = "GenBank_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            os.mkdir(pasta)
            for i in self.gbff:
                try:
                    shutil.move(i, pasta)
                except BaseException:
                    erro_string = "It was not possible to move the file " + str(i) + " to the final directory.\nPlease, check the output path.\n"
                    self.erro.append(erro_string)
                    print(erro_string)
        
        if len(self.erro) > 0:
            final_erro = self._write_error_file()
            print("\nNumber of errors reported: " + str(len(self.erro)))
            print("Please check the " + str(final_erro) + " file.\n")
        else:
            print("\nNo error reported!")
        print("\nThat's all folks...\nThank you so much for using this program!\n")
        exit()

    def _extract_and_save_positions(self):
        """Extract and save CDS positions from GenBank files"""
        print("\nExtracting CDS positions from GenBank files\n")
        if self.strains is None:
            self.strains = []
            
        pos = {}
        tempfiles = []
        
        for i in self.files:
            try:
                k = GBKProcessor.extract_positions(i)
            except BaseException:
                try:
                    f = i.replace(".gbff", ".gbk")
                    k = GBKProcessor.extract_positions(f)
                except BaseException:
                    try:
                        f = i.replace(".gbf", ".gbk")
                        k = GBKProcessor.extract_positions(f)
                    except BaseException:
                        if os.path.exists(i):
                            erro_string = "\n**WARNING**\nIt was not possible to handle the file " + str(i) + "...\nIt will be skipped.\nPlease verify the input format.\n"
                            print(erro_string)
                            self.erro.append(erro_string)
                            continue
                        else:
                            erro_string = "\n**WARNING**\nIt was not possible to handle the file " + str(i) + "...\nIt will be skipped.\\Please verify the absolute path of the files.\n"
                            print(erro_string)
                            self.erro.append(erro_string)
                            continue
                            
            if len(k) < 10:
                erro_string = "\n**WARNING**\nThe file " + str(i) + " seems to be empty...\nIt will be skipped.\nPlease verify the input format.\n"
                print(erro_string)
                self.erro.append(erro_string)
                continue
                
            print("The positions of the " + i + " file have been extracted")
            tempfiles.append(i)
            strain = str(i)[::-1].split('/')[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
            self.strains.append(strain)
            pos[i] = k
            
        self.files = tempfiles
        del tempfiles
        
        if "Positions_1" not in os.listdir():
            os.mkdir("Positions_1")
        else:
            shutil.rmtree("Positions_1")
            os.mkdir("Positions_1")
            
        for i in self.strains:
            for j in pos.keys():
                tempName = j[::-1].split("/")[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                if i == tempName:
                    with open(os.path.join("Positions_1", i + ".tab"), 'w') as positions:
                        for k in pos[j].keys():
                            positions.write(k + '\t')
                            positions.write(pos[j][k])
                            positions.write('\n')

    def _extract_and_save_proteins(self):
        """Extract and save protein sequences from GenBank files"""
        if "faa" not in os.listdir():
            os.mkdir("faa")
        else:
            shutil.rmtree("faa")
            os.mkdir("faa")
            
        print("\nExtracting protein sequences from GenBank files\n")
        
        for i in self.files:
            for j in self.strains:
                tempName = i[::-1].split("/")[0][::-1].replace(".gbk", "").replace(".gbff", "").replace(".gbf", "")
                if j == tempName:
                    print("Extracting " + j)
                    with open(os.path.join("faa", j + ".faa"), 'w') as faa:
                        try:
                            k = GBKProcessor.extract_faa(i)
                        except BaseException:
                            try:
                                temp = i.replace(".gbff", ".gbk")
                                k = GBKProcessor.extract_faa(temp)
                            except BaseException:
                                try:
                                    temp = i.replace(".gbf", ".gbk")
                                    k = GBKProcessor.extract_faa(temp)
                                except BaseException:
                                    print(f"Error extracting proteins from {i}")
                                    k = []
                        for l in k:
                            faa.write(l)
    
    def _run_single_alignment(self, strain, db_path, tabular1_dir, aligner_type, db_type):
        """Helper function to run a single alignment process for parallel execution."""
        aligner = Aligner(self.dppath)
        input_file = os.path.join("faa", f"{strain}.faa")
        output_file = os.path.join(tabular1_dir, f"{strain}.tab")
        return aligner.align(input_file, db_path, output_file, aligner_type, db_type)

    def _align_and_mine_parallel(self, aligner_types, aligner_exes, aligner_names):
        """Perform alignments in parallel and then mine the results."""
        # Use as many workers as CPU cores, but cap at a reasonable number if needed
        max_workers = os.cpu_count()
        print(f"\nUsing up to {max_workers} CPU cores for parallel alignments.")

        for p in self.parameters:
            db_name = p[1:]  # Remove '-'

            for aligner_type, aligner_exe, aligner_name in zip(aligner_types, aligner_exes, aligner_names):
                if len(aligner_types) > 1:
                    suffix = f"_{aligner_name.lower()}"
                else:
                    suffix = ""
                
                tabular1_dir = f"Tabular_1_{db_name}{suffix}"
                tabular2_dir = f"Tabular_2_{db_name}{suffix}"
                
                # Setup directories
                for d in [tabular1_dir, tabular2_dir]:
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    os.mkdir(d)
                
                # Determine DB path and type
                if p == "-card":
                    db_path = os.path.join(self.dbpath, "card_protein_homolog_model")
                    db_type = "protein"
                elif p == "-vfdb":
                    db_path = os.path.join(self.dbpath, "vfdb_core")
                    db_type = "protein"
                elif p == "-bacmet":
                    db_path = os.path.join(self.dbpath, "bacmet_2")
                    db_type = "protein"
                elif p == "-megares":
                    db_path = os.path.join(self.dbpath, "megares_v3")
                    db_type = "nucleotide"
                else:
                    continue

                print(f"\nStarting PARALLEL {aligner_name} alignments for {db_name.upper()}...")
                
                # *** PARALLEL EXECUTION ***
                tasks = []
                with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                    for strain in self.strains:
                        tasks.append(
                            executor.submit(self._run_single_alignment, strain, db_path, tabular1_dir, aligner_type, db_type)
                        )
                    
                    # Wait for all jobs to complete and print progress
                    for i, future in enumerate(concurrent.futures.as_completed(tasks)):
                        try:
                            result = future.result()
                            print(f"({i+1}/{len(self.strains)}) - {result}")
                        except Exception as exc:
                            print(f'Alignment generated an exception: {exc}')

                print(f"\nAll alignments for {db_name.upper()} complete.")
                print(f"Mining {aligner_name} alignments for {db_name.upper()}...")
                
                # Mining step (still sequential, but fast)
                for i in os.listdir(tabular1_dir):
                    DataProcessor.blastmining_specific(i, tabular1_dir, tabular2_dir)

    def _run_analysis_workflow(self, aligner_types, aligner_names):
        """Run the main analysis workflow for each database"""
        for p in self.parameters:
            db_name = p[1:]  

            # Extract keys and handle MEGARes special case with mechanisms mapping
            if p == "-megares":
                comp, genes_comp, mechanisms_comp = DataProcessor.extract_keys(p, self.dbpath)
                self.genes_comp = genes_comp
                self.mechanisms_comp = mechanisms_comp  # Store mechanisms for MEGARes
            else:
                comp, genes_comp = DataProcessor.extract_keys(p, self.dbpath)
                self.genes_comp = genes_comp
            
            # Check if we have multiple aligners by looking for directories with suffixes
            aligner_dirs = []
            for dir_name in os.listdir('.'):
                if dir_name.startswith(f"Tabular_2_{db_name}_"):
                    aligner_suffix = dir_name.replace(f"Tabular_2_{db_name}_", "")
                    aligner_dirs.append(aligner_suffix)
            
            # If no aligner-specific directories found, check for unified directory
            if not aligner_dirs and os.path.exists(f"Tabular_2_{db_name}"):
                aligner_dirs.append("")  # Empty suffix for unified directory
            
            if not aligner_dirs:
                print(f"Warning: No analysis directories found for {p}")
                continue
                
            # Process each aligner separately
            for aligner_suffix in aligner_dirs:
                outputs = []
                
                print(f"\nProcessing analysis for {p}{f' with {aligner_suffix}' if aligner_suffix else ''}...")
                
                # Extract keys for the current database
                if p == "-megares":
                    comp, genes_comp, mechanisms_comp = DataProcessor.extract_keys(p, self.dbpath)
                    self.mechanisms_comp = mechanisms_comp  # Store mechanisms for MEGARes
                else:
                    comp, genes_comp = DataProcessor.extract_keys(p, self.dbpath)
                
                self.genes_comp = genes_comp
                
                # Generate matrix
                titulo, dicl, totalgenes, found_genes_per_strain = Visualization.generate_matrix(p, outputs, comp, aligner_suffix)
                
                # Check if the matrix file was created and is not empty before proceeding.
                # This prevents crashes in all downstream plotting functions.
                if not os.path.exists(titulo) or os.path.getsize(titulo) == 0:
                    print(f"\n❌ CRITICAL WARNING: Matrix file '{titulo}' was not generated or is empty.")
                    print("   This usually means no significant alignment results were found for this database.")
                    print(f"   Skipping the rest of the analysis for {p}{f' with {aligner_suffix}' if aligner_suffix else ''}.")
                    # Move to the next item in the loop (e.g., next aligner or database).
                    continue

                # Save found genes to individual .faa files if requested
                if "-save-genes" in sys.argv:
                    self._save_found_genes(found_genes_per_strain, p, aligner_suffix)
                
                # Generate positions files (only for the first aligner to avoid conflicts)
                if aligner_suffix == aligner_dirs[0]:
                    self._generate_positions_files(p, comp, aligner_suffix)
                
                # Load matrix for visualization
                df = pd.read_csv(titulo, sep=';')
                df = df.set_index('Strains')
                
                # Generate heatmap
                Visualization.generate_heatmap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_clustermap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_scatterplot_heatmap(titulo, p, outputs, self.erro, aligner_suffix)
                Visualization.generate_joint_and_marginal_distributions(titulo, p, outputs, self.erro, aligner_suffix)
                
                # Process omics analysis
                lines = list(df.index.values)
                analysis_outputs = self._process_omics_analysis(df, lines, p, aligner_suffix)
                outputs.extend(analysis_outputs)
                
                # Organize results
                self._organize_results(outputs, p, aligner_suffix)

    def _save_found_genes(self, found_genes_per_strain, db_param, aligner_suffix=""):
        """Save found genes in individual .faa files for each genome"""
        print(f"\nSaving found genes to individual .faa files for {db_param}{f' ({aligner_suffix})' if aligner_suffix else ''}...")
        
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        # Create output directory
        if aligner_suffix:
            output_dir = f"Found_genes_{db_name}_{aligner_suffix}"
        else:
            output_dir = f"Found_genes_{db_name}"
            
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        
        # Read all .faa files to create a lookup dictionary
        faa_sequences = {}
        faa_dir = "faa"
        
        if not os.path.exists(faa_dir):
            print(f"Warning: {faa_dir} directory not found. Cannot extract gene sequences.")
            return
            
        # Load all sequences from faa files
        for strain_name, strain_genes in found_genes_per_strain.items():
            faa_file = os.path.join(faa_dir, strain_name + ".faa")
            
            if not os.path.exists(faa_file):
                print(f"Warning: {faa_file} not found. Skipping strain {strain_name}.")
                continue
                
            # Parse the .faa file to extract sequences
            strain_sequences = {}
            try:
                with open(faa_file, 'r') as f:
                    current_header = None
                    current_seq = []
                    
                    for line in f:
                        line = line.strip()
                        if line.startswith('>'):
                            # Save previous sequence if exists
                            if current_header and current_seq:
                                # Extract locus_tag from header (first part after >)
                                locus_tag = current_header.split()[0].replace('>', '')
                                strain_sequences[locus_tag] = {
                                    'header': current_header,
                                    'sequence': ''.join(current_seq)
                                }
                            
                            # Start new sequence
                            current_header = line
                            current_seq = []
                        else:
                            current_seq.append(line)
                    
                    # Save last sequence
                    if current_header and current_seq:
                        locus_tag = current_header.split()[0].replace('>', '')
                        strain_sequences[locus_tag] = {
                            'header': current_header,
                            'sequence': ''.join(current_seq)
                        }
                        
            except Exception as e:
                print(f"Error reading {faa_file}: {e}")
                continue
            
            # Create output file for this strain
            output_file = os.path.join(output_dir, f"{strain_name}_{db_name}_genes.faa")
            genes_saved = 0
            
            try:
                with open(output_file, 'w') as out:
                    for gene_name, locus_tags in strain_genes.items():
                        for locus_tag in locus_tags:
                            if locus_tag in strain_sequences:
                                # Write header with gene annotation
                                original_header = strain_sequences[locus_tag]['header']
                                # Add gene annotation to header
                                annotated_header = f"{original_header} | {db_name.upper()}_GENE:{gene_name}"
                                out.write(annotated_header + '\n')
                                
                                # Write sequence
                                sequence = strain_sequences[locus_tag]['sequence']
                                # Write sequence in lines of 80 characters
                                for i in range(0, len(sequence), 80):
                                    out.write(sequence[i:i+80] + '\n')
                                
                                genes_saved += 1
                            else:
                                print(f"Warning: Locus tag {locus_tag} not found in {strain_name}.faa")
                
                if genes_saved > 0:
                    print(f"  - {strain_name}: {genes_saved} genes saved to {output_file}")
                else:
                    # Remove empty file
                    os.remove(output_file)
                    print(f"  - {strain_name}: No genes found, file not created")
                    
            except Exception as e:
                print(f"Error writing to {output_file}: {e}")
        
        print(f"Found genes saved in directory: {output_dir}")

    def _generate_positions_files(self, db_param, comp, aligner_suffix=""):
        """Generate position files for genes"""
        if "Positions" not in os.listdir():
            os.mkdir("Positions")
        else:
            shutil.rmtree("Positions")
            os.mkdir("Positions")
            
        print(f"\nExtracting positions from specific factors for {db_param}{f' ({aligner_suffix})' if aligner_suffix else ''}...")
        
        for i in self.strains:
            pos = {}
            positions = os.path.join("Positions_1", i + ".tab")
            positions2 = os.path.join("Positions", i + ".tab")
            
            with open(positions, 'rt') as tab:
                arq = tab.readlines()
            
            for j in arq:
                line = j.split("\t")
                try:
                    pos[line[0]] = [line[1], line[2]]
                except BaseException:
                    pass
            
            # Determine the specific tabular directory for this database
            db_name = db_param[1:]
            if aligner_suffix:
                tabular_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
            else:
                tabular_dir = f"Tabular_2_{db_name}"
                
            file_path = os.path.join(tabular_dir, i + ".tab")
            # Check if file exists before trying to read it
            if not os.path.exists(file_path):
                print(f"Warning: File {file_path} not found!")
                continue
                
            with open(file_path, 'rt') as tab:
                file_lines = tab.readlines()
            
            final = {}
            for j in file_lines:
                linha = j.split('\t')
                gene = None
                for k in comp.keys():
                    if k in linha[1]:
                        gene = comp[k]
                        break
                if gene and linha[0] in pos:
                    final[linha[0]] = gene, pos[linha[0]]
            
            with open(positions2, 'w') as out:
                for j in final.keys():
                    if "-card" == db_param:
                        color = "blue\n"
                    elif "-vfdb" == db_param:
                        color = "red\n"
                    elif "-bacmet" == db_param:
                        color = "green\n"
                    elif "-megares" == db_param:
                        color = "yellow\n"
                    else:
                        color = "black\n"
                    out.write(final[j][1][0] + '\t' + final[j][1][1].strip() + '\t' + final[j][0] + '\t' + color)

    def _process_omics_analysis(self, df, lines, db_param, aligner_suffix=""):
        """Process omics analysis and generate output files"""
        fileType = "pdf"
        if "-pdf" in sys.argv:
            fileType = "pdf"
        elif "-png" in sys.argv:
            fileType = "png"
        
        print("\nDoing presence analysis...")
        
        # Setup output files based on database type
        output_setup = self._setup_output_files(db_param, fileType, aligner_suffix)
        
        # Unpack based on actual length returned
        if db_param in ["-card", "-megares"]:  # 11 elements
             outputs, t1, t2, t3, t4, l1, l2, t6, t7, t8, t9, t10, t11 = output_setup
        elif db_param == "-vfdb":  # 8 elements
            outputs, t1, t2, t3, t4, l1, l2, t6, t7, t10 = output_setup
        elif db_param == "-bacmet": # 9 elements
            outputs, t1, t2, t3, t4, l1, l2, t6, t7, t8, t10 = output_setup
        
        t5 = t3.replace("csv", fileType)
        outputs.append(t5)
        
        # Per genes analysis - improved binary conversion
        df2 = df.copy()
        headers = list(df2.columns.values)
        
        # Remove unnamed columns first
        headers_to_remove = []
        for i in headers:
            if "Unnamed:" in i:
                headers_to_remove.append(i)
        
        for col in headers_to_remove:
            df2 = df2.drop(columns=[col])
        
        # Update headers after removing unnamed columns
        headers = list(df2.columns.values)
        
        # Convert to binary (presence/absence) data
        # Any non-zero value (including identity percentages) becomes 1
        df2_binary = df2.copy()
        for col in headers:
            df2_binary[col] = (df2[col] != 0).astype(int)
        
        with open(t1, "w") as count:
            count.write("Genes;Presence Number;Strains\n")
            
            for gene in headers:
                # Get list of strains where this gene is present
                present_strains = []
                for idx, strain in enumerate(df2_binary.index):
                    if df2_binary[gene].iloc[idx] == 1:
                        present_strains.append(str(strain))
                
                presence_count = len(present_strains)
                strains_str = ','.join(present_strains) if present_strains else ""
                count.write(f"{gene};{presence_count};{strains_str}\n")
        
        # Per strains analysis
        strain_list = list(df2_binary.index.values)
        with open(t2, "w") as count:
            count.write("Strains;Presence Number;Genes\n")
            dic = {}
            
            for strain in strain_list:
                # Get list of genes present in this strain
                present_genes = []
                for gene in headers:
                    if df2_binary.loc[strain, gene] == 1:
                        present_genes.append(gene)
                
                dic[strain] = present_genes
                genes_str = ','.join(present_genes) if present_genes else ""
                count.write(f"{strain};{len(present_genes)};{genes_str}\n")
        
        # PanOmic analysis - corrected to calculate cumulative pan and core genomes
        with open(t3, "w") as panomic:
            panomic.write("Strains;Core;Pan\n")
            
            # Get strain names in order
            strain_names = list(dic.keys())
            
            # Initialize containers for cumulative analysis
            pan_results = []
            
            # Calculate pan and core genomes progressively
            for i in range(len(strain_names)):
                # Get genes from current subset of strains (0 to i+1)
                current_strains = strain_names[:i+1]
                
                # Calculate pan-genome (union of all genes in current strains)
                pan_genes = set()
                for strain in current_strains:
                    pan_genes.update(dic[strain])
                
                # Calculate core-genome (intersection of all genes in current strains)
                if len(current_strains) == 1:
                    core_genes = set(dic[current_strains[0]])
                else:
                    core_genes = set(dic[current_strains[0]])
                    for strain in current_strains[1:]:
                        core_genes = core_genes.intersection(set(dic[strain]))
                
                # Store results
                pan_results.append({
                    'strain': strain_names[i],
                    'core': len(core_genes),
                    'pan': len(pan_genes),
                    'genome_number': i + 1
                })
                
                # Write to file
                panomic.write(f"{strain_names[i]};{len(core_genes)};{len(pan_genes)}\n")
        
        # Generate pan-genome plot using the new method
        Visualization.generate_lineplot(t3, t4, l1, l2, t5, fileType, outputs)
        
        # Pan-distribution analysis
        if db_param == "-card":
            self._process_card_distribution(t1, t6, t7, t8, t9, t10, t11, fileType, outputs)
        elif db_param == "-vfdb":
            self._process_vfdb_distribution(t1, t6, t7, t10, fileType, outputs)
        elif db_param == "-bacmet":
            self._process_bacmet_distribution(t1, t6, t7, t8, t10, fileType, outputs)
        elif db_param == "-megares":
            self._process_megares_distribution(t1, t6, t7, t8, t9, t10, t11, fileType, outputs)
        
        return outputs

    def _setup_output_files(self, db_param, fileType, aligner_suffix=""):
        """Setup output file names based on database type with a clear, validated structure."""
        db_name = db_param[1:]
        suffix = f"_{aligner_suffix}" if aligner_suffix else ""
        
        # Base file definitions common to all databases
        base_files = {
            "gene_count": f"{db_name}_gene_count{suffix}.csv",
            "strain_count": f"{db_name}_strain_count{suffix}.csv",
            "pan_analysis": f"{db_name}_pan{suffix}.csv",
        }
        
        # Database-specific titles and additional files
        db_configs = {
            "-card": {
                "title": "Pan-resistome development", "pan_label": "Pan-resistome", "core_label": "Core-resistome",
                "files": {
                    "mechanisms": f"card_mechanisms{suffix}.csv",
                    "drug_classes": f"card_drug_classes{suffix}.csv",
                    "mechanisms_barplot": f"card_mechanisms_barplot{suffix}.{fileType}",
                    "drug_classes_barplot": f"card_drug_classes_barplot{suffix}.{fileType}",
                    "mechanisms_bubble_plot": f"card_mechanisms_bubble_plot{suffix}.{fileType}",
                    "drug_classes_bubble_plot": f"card_drug_classes_bubble_plot{suffix}.{fileType}",
                }
            },
            "-vfdb": {
                "title": "Pan-virulome development", "pan_label": "Pan-virulome", "core_label": "Core-virulome",
                "files": {
                    "mechanisms": f"vfdb_mechanisms{suffix}.csv",
                    "mechanisms_barplot": f"vfdb_mechanisms_barplot{suffix}.{fileType}",
                    "mechanisms_bubble_plot": f"vfdb_mechanisms_bubble_plot{suffix}.{fileType}",
                }
            },
            "-bacmet": {
                "title": "Pan-resistome development", "pan_label": "Pan-resistome", "core_label": "Core-resistome",
                "files": {
                    "heavy_metals": f"bacmet_heavy_metals{suffix}.csv",
                    "all_compounds": f"bacmet_all_compounds{suffix}.csv",
                    "heavy_metals_barplot": f"bacmet_heavy_metals_barplot{suffix}.{fileType}",
                    "heavy_metals_bubble_plot": f"bacmet_heavy_metals_bubble_plot{suffix}.{fileType}",
                }
            },
            "-megares": {
                "title": "Pan-resistome development", "pan_label": "Pan-resistome", "core_label": "Core-resistome",
                "files": {
                    "mechanisms": f"megares_mechanisms{suffix}.csv",
                    "drug_classes": f"megares_drug_classes{suffix}.csv",
                    "mechanisms_barplot": f"megares_mechanisms_barplot{suffix}.{fileType}",
                    "drug_classes_barplot": f"megares_drug_classes_barplot{suffix}.{fileType}",
                    "mechanisms_bubble_plot": f"megares_mechanisms_bubble_plot{suffix}.{fileType}",
                    "drug_classes_bubble_plot": f"megares_drug_classes_bubble_plot{suffix}.{fileType}",
                }
            }
        }
        
        config = db_configs[db_param]
        all_files = {**base_files, **config['files']}
        outputs = list(all_files.values())
        
        # Return a structured list of parameters for clarity
        base_return = [
            outputs,
            all_files["gene_count"], all_files["strain_count"], all_files["pan_analysis"],
            config["title"], config["pan_label"], config["core_label"]
        ]
        
        if db_param in ["-card", "-megares"]:
            return base_return + [
                all_files["mechanisms"], all_files["drug_classes"],
                all_files["mechanisms_barplot"], all_files["drug_classes_barplot"],
                all_files["mechanisms_bubble_plot"], all_files["drug_classes_bubble_plot"]
            ]
        elif db_param == "-vfdb":
            return base_return + [
                all_files["mechanisms"], all_files["mechanisms_barplot"], all_files["mechanisms_bubble_plot"]
            ]
        elif db_param == "-bacmet":
            return base_return + [
                all_files["heavy_metals"], all_files["all_compounds"],
                all_files["heavy_metals_barplot"], all_files["heavy_metals_bubble_plot"]
            ]
        return base_return

    def _process_card_distribution(self, t1, t6, t7, t8, t9, t10, t11, fileType, outputs):
        """Process CARD database distribution analysis"""
        print("\nMaking the pan-distribution...")
        aro = pd.read_csv(os.path.join(self.dbpath, "aro_index.tsv"), sep="\t")
        aro_genes = aro["ARO Name"].tolist()
        aro_drug = aro["Drug Class"].tolist()
        aro_mech = aro["Resistance Mechanism"].tolist()
        aro_dict = {}
        
        for i in range(0, len(aro_genes)):
            aro_dict[aro_genes[i]] = (aro_drug[i], aro_mech[i])

        mech = []
        drug = []
        for i in aro_dict.keys():
            if ";" in str(aro_dict[i][1]):
                temp = str(aro_dict[i][1]).split(";")
                for j in temp:
                    if j not in mech:
                        mech.append(j)
            else:
                temp = aro_dict[i][1]
                if temp not in mech:
                    mech.append(temp)
            if ";" in str(aro_dict[i][0]):
                temp = str(aro_dict[i][0]).split(";")
                for j in temp:
                    if j not in drug:
                        drug.append(j)
            else:
                temp = aro_dict[i][0]
                if temp not in drug:
                    drug.append(temp)

        genes = pd.read_csv(t1, sep=";")
        core = []
        acce = []
        exclusive = []
        g = genes["Genes"].tolist()
        n = genes["Presence Number"].tolist()
        
        for i in range(0, len(g)):
            if n[i] == len(self.strains):
                core.append(g[i])
            elif (n[i] > 1) and (n[i] < len(self.strains)):
                acce.append(g[i])
            elif n[i] == 1:
                exclusive.append(g[i])

        # Resistance mechanisms
        with open(t6, "w") as out:
            out.write("Resistance Mechanism;Core;Accessory;Exclusive\n")
            for k in mech:
                coreM = accessoryM = exclusiveM = 0
                for i in core:
                    try:
                        if str(k) in str(aro_dict[i][1]):
                            coreM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][1]):
                                coreM += 1
                
                for i in acce:
                    try:
                        if str(k) in str(aro_dict[i][1]):
                            accessoryM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][1]):
                                accessoryM += 1
                
                for i in exclusive:
                    try:
                        if str(k) in str(aro_dict[i][1]):
                            exclusiveM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][1]):
                                exclusiveM += 1
                
                if (coreM != 0) or (accessoryM != 0) or (exclusiveM != 0):
                    out.write(str(k).capitalize() + ";" + str(coreM) + ";" + str(accessoryM) + ";" + str(exclusiveM) + "\n")

        # Drug classes
        with open(t7, "w") as out2:
            out2.write("Drug Class;Core;Accessory;Exclusive\n")
            for k in drug:
                if str(k).capitalize() == "Nan":
                    continue
                coreM = accessoryM = exclusiveM = 0
                
                for i in core:
                    try:
                        if str(k) in str(aro_dict[i][0]):
                            coreM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][0]):
                                coreM += 1
                
                for i in acce:
                    try:
                        if str(k) in str(aro_dict[i][0]):
                            accessoryM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][0]):
                                accessoryM += 1
                
                for i in exclusive:
                    try:
                        if str(k) in str(aro_dict[i][0]):
                            exclusiveM += 1
                    except KeyError:
                        for j in aro_dict.keys():
                            if i in j and str(k) in str(aro_dict[j][0]):
                                exclusiveM += 1
                
                if (coreM != 0) or (accessoryM != 0) or (exclusiveM != 0):
                    out2.write(str(k).capitalize() + ";" + str(coreM) + ";" + str(accessoryM) + ";" + str(exclusiveM) + "\n")

        # Generate barplots and bubble plots
        try:
            Visualization.generate_barplot(t6, "Resistance Mechanism", t8, fileType, outputs)
            Visualization.generate_bubble_plot(t6, "Resistance Mechanism", t10, fileType, outputs)
            Visualization.generate_barplot(t7, "Drug Class", t9, fileType, outputs)
            Visualization.generate_bubble_plot(t7, "Drug Class", t11, fileType, outputs)
        except Exception as e:
            print(f"Error generating CARD distribution plots: {e}")

    def _process_vfdb_distribution(self, t1, t6, t7, t10, fileType, outputs):
        """Process VFDB database distribution analysis"""
        print("\nMaking the pan-distribution...")
        
        comp, genes_comp = DataProcessor.extract_keys("-vfdb", self.dbpath)
        
        genes = pd.read_csv(t1, sep=";")
        core = []
        acce = []
        exclusive = []
        g = genes["Genes"].tolist()
        n = genes["Presence Number"].tolist()
        
        for i in range(0, len(g)):
            if n[i] == len(self.strains):
                core.append(g[i])
            elif (n[i] > 1) and (n[i] < len(self.strains)):
                acce.append(g[i])
            elif n[i] == 1:
                exclusive.append(g[i])

        with open(t6, "w") as out:
            out.write("Virulence Mechanism;Core;Accessory;Exclusive\n")
            mech = []
            for k in genes_comp:
                if genes_comp[k] not in mech:
                    mech.append(genes_comp[k])
            
            for mechanism in mech:
                core_number = accessory_number = exclusive_number = 0
                
                for gene in core:
                    if gene in genes_comp and genes_comp[gene] == mechanism:
                        core_number += 1
                for gene in acce:
                    if gene in genes_comp and genes_comp[gene] == mechanism:
                        accessory_number += 1
                for gene in exclusive:
                    if gene in genes_comp and genes_comp[gene] == mechanism:
                        exclusive_number += 1
                
                if (core_number != 0) or (accessory_number != 0) or (exclusive_number != 0):
                    out.write(str(mechanism).capitalize() + ";" + str(core_number) + ";" + str(accessory_number) + ";" + str(exclusive_number) + "\n")

        try:
            Visualization.generate_barplot(t6, "Virulence Mechanism", t7, fileType, outputs)
            Visualization.generate_bubble_plot(t6, "Virulence Mechanism", t10, fileType, outputs)
        except Exception as e:
            print(f"Error generating VFDB distribution plots: {e}")

    def _process_bacmet_distribution(self, t1, t6, t7, t8, t10, fileType, outputs):
        """Process BacMet database distribution analysis"""
        db = pd.read_csv(os.path.join(self.dbpath, "bacmet_2.txt"), sep="\t")
        genes_list = db["Gene_name"].tolist()
        compostos = db["Compound"].tolist()
        comp = []
        
        for i in compostos:
            if "," in i:
                temp = i.split(",")
                for j in temp:
                    if j.strip() not in comp:
                        comp.append(j.strip())
            else:
                if i.strip() not in comp:
                    comp.append(i.strip())
        
        dic = {}
        for i in range(0, len(genes_list)):
            if "," not in compostos[i]:
                dic[genes_list[i]] = compostos[i]
            else:
                temp = compostos[i].split(', ')
                for j in range(0, len(temp)):
                    temp[j] = temp[j].strip()
                dic[genes_list[i]] = temp
        
        matriz = pd.read_csv(t1, sep=";")
        my_genes = {}
        for i in range(0, len(matriz["Genes"].tolist())):
            my_genes[matriz["Genes"][i]] = matriz["Presence Number"][i]
        
        core_ome = []
        accessory_ome = []
        exclusive_ome = []
        for i in my_genes.keys():
            if my_genes[i] == len(self.strains):
                core_ome.append(i)
            elif my_genes[i] > 1:
                accessory_ome.append(i)
            else:
                exclusive_ome.append(i)
        
        # Heavy metals file
        with open(t6, 'w') as outa:
            outa.write("Compound;Core;Accessory;Exclusive\n")
            # All compounds file
            with open(t7, 'w') as outb:
                outb.write("Compound;Core;Accessory;Exclusive\n")
                
                for k in comp:
                    core = accessory = exclusive = 0
                    
                    for i in core_ome:
                        try:
                            if isinstance(dic[i], list) and k in dic[i]:
                                core += 1
                            elif isinstance(dic[i], str) and k == dic[i]:
                                core += 1
                        except KeyError:
                            for j in dic.keys():
                                if i in j:
                                    if isinstance(dic[j], list) and k in dic[j]:
                                        core += 1
                                    elif isinstance(dic[j], str) and k == dic[j]:
                                        core += 1
                    
                    for i in accessory_ome:
                        try:
                            if isinstance(dic[i], list) and k in dic[i]:
                                accessory += 1
                            elif isinstance(dic[i], str) and k == dic[i]:
                                accessory += 1
                        except KeyError:
                            for j in dic.keys():
                                if i in j:
                                    if isinstance(dic[j], list) and k in dic[j]:
                                        accessory += 1
                                    elif isinstance(dic[j], str) and k == dic[j]:
                                        accessory += 1
                    
                    for i in exclusive_ome:
                        try:
                            if isinstance(dic[i], list) and k in dic[i]:
                                exclusive += 1
                            elif isinstance(dic[i], str) and k == dic[i]:
                                exclusive += 1
                        except KeyError:
                            for j in dic.keys():
                                if i in j:
                                    if isinstance(dic[j], list) and k in dic[j]:
                                        exclusive += 1
                                    elif isinstance(dic[j], str) and k == dic[j]:
                                        exclusive += 1
                    
                    if (core != 0) or (accessory != 0) or (exclusive != 0):
                        if ("(" in k) and ("[" not in k):
                            outa.write(k + ";" + str(core) + ";" + str(accessory) + ";" + str(exclusive) + "\n")
                        outb.write(k + ";" + str(core) + ";" + str(accessory) + ";" + str(exclusive) + "\n")

        try:
            Visualization.generate_barplot(t6, "Compound", t8, fileType, outputs)
            Visualization.generate_bubble_plot(t6, "Compound", t10, fileType, outputs)
        except Exception as e:
            print(f"Error generating BacMet distribution plots: {e}")

    def _process_megares_distribution(self, t1, t6, t7, t8, t9, t10, t11, fileType, outputs):
        """Process MEGARes database distribution analysis"""
        print("\nMaking the MEGARes pan-distribution...")
        
        # Use the instance variables that were set in _run_analysis_workflow
        genes_comp = self.genes_comp  # Maps gene -> drug_class
        mechanisms_comp = self.mechanisms_comp  # Maps gene -> mechanism
        
        # Extract unique mechanisms and drug classes
        mechanisms = list(set(mechanisms_comp.values()))  # Unique mechanisms
        drug_classes = list(set(genes_comp.values()))     # Unique drug classes
        
        print(f"Found {len(mechanisms)} unique mechanisms")
        print(f"Found {len(drug_classes)} unique drug classes")
        
        genes = pd.read_csv(t1, sep=";")
        core = []
        acce = []
        exclusive = []
        g = genes["Genes"].tolist()
        n = genes["Presence Number"].tolist()
        
        for i in range(0, len(g)):
            if n[i] == len(self.strains):
                core.append(g[i])
            elif (n[i] > 1) and (n[i] < len(self.strains)):
                acce.append(g[i])
            elif n[i] == 1:
                exclusive.append(g[i])

        # Resistance mechanisms
        with open(t6, "w") as out:
            out.write("Resistance Mechanism;Core;Accessory;Exclusive\n")
            for mechanism in mechanisms:
                core_count = accessory_count = exclusive_count = 0
                
                for gene in core:
                    if gene in mechanisms_comp and mechanisms_comp[gene] == mechanism:
                        core_count += 1
                
                for gene in acce:
                    if gene in mechanisms_comp and mechanisms_comp[gene] == mechanism:
                        accessory_count += 1
                
                for gene in exclusive:
                    if gene in mechanisms_comp and mechanisms_comp[gene] == mechanism:
                        exclusive_count += 1
                
                if (core_count != 0) or (accessory_count != 0) or (exclusive_count != 0):
                    out.write(f"{mechanism};{core_count};{accessory_count};{exclusive_count}\n")

        # Drug classes (similar to mechanisms for MEGARes)
        with open(t7, "w") as out2:
            out2.write("Drug Class;Core;Accessory;Exclusive\n")
            for drug_class in drug_classes:
                core_count = accessory_count = exclusive_count = 0
                
                for gene in core:
                    if gene in genes_comp and genes_comp[gene] == drug_class:
                        core_count += 1
                
                for gene in acce:
                    if gene in genes_comp and genes_comp[gene] == drug_class:
                        accessory_count += 1
                
                for gene in exclusive:
                    if gene in genes_comp and genes_comp[gene] == drug_class:
                        exclusive_count += 1
                
                if (core_count != 0) or (accessory_count != 0) or (exclusive_count != 0):
                    out2.write(f"{drug_class};{core_count};{accessory_count};{exclusive_count}\n")

        try:
            Visualization.generate_barplot(t6, "Resistance Mechanism", t8, fileType, outputs)
            Visualization.generate_bubble_plot(t6, "Resistance Mechanism", t10, fileType, outputs)
            Visualization.generate_barplot(t7, "Drug Class", t9, fileType, outputs)
            Visualization.generate_bubble_plot(t7, "Drug Class", t11, fileType, outputs)
        except Exception as e:
            print(f"Error generating MEGARes distribution plots: {e}")

    def _organize_results(self, outputs, db_param, aligner_suffix=""):
        """Organize results into output directory"""
        print(f"\nGrouping the results{f' ({aligner_suffix})' if aligner_suffix else ''}...\n")
        
        if aligner_suffix:
            atual = f"Results_{db_param[1:]}_{aligner_suffix}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
        else:
            atual = "Results_" + db_param[1:] + "_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        
        os.mkdir(atual)
        
        # Add the database-specific Tabular directories to outputs
        db_name = db_param[1:]  # Remove the '-' from parameter name
        
        if aligner_suffix:
            tabular1_dir = f"Tabular_1_{db_name}_{aligner_suffix}"
            tabular2_dir = f"Tabular_2_{db_name}_{aligner_suffix}"
        else:
            tabular1_dir = f"Tabular_1_{db_name}"
            tabular2_dir = f"Tabular_2_{db_name}"
        
        # Add Tabular directories to outputs if they exist
        if os.path.exists(tabular1_dir):
            outputs.append(tabular1_dir)
        if os.path.exists(tabular2_dir):
            outputs.append(tabular2_dir)
        
        for i in outputs:
            try:
                if os.path.exists(i):
                    shutil.move(i, atual)
                    # print(f"Moved {i} to {atual}")
                else:
                    print(f"Warning: {i} not found, skipping...")
            except BaseException as e:
                erro_string = f"It was not possible to move the file {str(i)} to the final directory.\nError: {str(e)}\nPlease, check the output path.\n"
                print(erro_string)

    def _remove_intermediate_files(self):
        """Remove intermediate files if not keeping them"""
        if ("-keep" not in sys.argv) and ("-k" not in sys.argv):
            try:
                shutil.rmtree("Positions_1")
            except (PermissionError, FileNotFoundError):
                pass
            try:
                shutil.rmtree("faa")
            except (PermissionError, FileNotFoundError):
                pass

    def _write_error_file(self):
        """Write error messages to a file"""
        erro_file = "panvita_error_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".err"
        with open(erro_file, "w") as erro_out:
            string = "PanViTa " + str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S")) + "\n"
            erro_out.write(string)
            erro_out.write(
                "The following lines contains the errors from the last runing.\nPlease, check them carefully.\n")
            for i in self.erro:
                erro_out.write(i)
            erro_out.write(
                "\nIf the lines appear empty, no error has been computed for the current run.\n")
        return erro_file

    def _print_final_messages(self):
        """Print final messages and citations"""
        if len(self.erro) > 0:
            final_erro = self._write_error_file()
            print("\nNumber of errors reported: " + str(len(self.erro)))
            print("Please check the " + str(final_erro) + " file.\n")
        else:
            print("\nNo error reported!")

        self._print_citation()

    def _print_citation(self):
        """Print citation information"""
        print('''That's all, folks!
Thank you for using this script.
If you're going to use results from PanViTa, please cite us:

PanViTa\thttps://doi.org/10.3389/fbinf.2023.1070406\t2023

Do not forget to quote the databases used.\n''')
        if "-bacmet" in sys.argv:
            print("BacMet\thttps://doi.org/10.1093/nar/gkt1252\t2014")
        if "-card" in sys.argv:
            print("CARD\thttps://doi.org/10.1093/nar/gkz935\t2020")
        if "-megares" in sys.argv:
            print("MEGARes\thttps://doi.org/10.1093/nar/gkac1047\t2022")
        if "-vfdb" in sys.argv:
            print("VFDB\thttps://doi.org/10.1093/nar/gky1080\t2019")
        print("\nDon't forget to mention the optional software too, if you already used them.")
        if "-m" in sys.argv:
            print("mlst\thttps://doi.org/10.1186/1471-2105-11-595\t2010")
            print("mlst\thttps://github.com/tseemann/mlst")
        if "-a" in sys.argv:
            print("prokka\thttps://doi.org/10.1093/bioinformatics/btu153\t2014")
        print('')

if __name__ == '__main__':
    # This ensures multiprocessing works correctly on all platforms (especially Windows)
    panvita = PanViTa()
    panvita.run()
