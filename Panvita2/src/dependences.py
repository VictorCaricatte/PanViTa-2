# File: dependences.py
# Description: Management of external tools (BLAST, DIAMOND)


import os
import shutil
import zipfile
from config import PanViTaConfig
from utils import FileHandler

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
                    "https://github.com/bbuchfink/diamond/releases/download/v2.1.21/diamond-windows.zip")
                with zipfile.ZipFile(diamond_file, 'r') as zip_ref:
                    zip_ref.extractall('.')
                diamond_exe = "diamond.exe"
            else:
                diamond_file = FileHandler.safe_download(
                    "https://github.com/bbuchfink/diamond/releases/download/v2.1.21/diamond-linux64.tar.gz")
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