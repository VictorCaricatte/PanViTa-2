# File: utils.py
# Description: File handling utilities (download, extract, clean)

import os
import shutil
import gzip
import tarfile
import urllib.request
import ssl
import wget
from config import PanViTaConfig

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