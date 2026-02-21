#!/usr/bin/env python3
"""
PanVita 2 - Dependency Installation Script
===============================================

This script automatically installs all the necessary dependencies
to run PanVita 2 (Advanced Bioinformatics GUI).

Date: February 21, 2026
"""

import sys
import subprocess
import importlib
import os

def print_banner():
    """Displays the script banner"""
    print("=" * 60)
    print("  PanVita 2 - Python Dependency Installer")
    print("  Version: 2.0.4")
    print("=" * 60)
    print()

def check_virtual_env():
    """Checks if we are in a virtual environment"""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV') is not None
    )
    
    if in_venv:
        venv_path = os.environ.get('VIRTUAL_ENV', 'Unknown')
        print(f"✅ Running in a virtual environment: {venv_path}")
    else:
        print("⚠️  WARNING: No active virtual environment detected.")
        print("   We recommend using a virtual environment to avoid conflicts.")
        print("   Dependencies will be installed on the global system.")
        response = input("   Continue anyway? (y/N): ").strip().lower()
        if response not in ['s', 'sim', 'y', 'yes']:
            print("   Installation canceled. Run in a virtual environment.")
            return False
    
    return True

def check_python_version():
    """Check if the Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ ERROR: PanVita 2 requires Python 3.7 or higher.")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print("   Please update Python and try again.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        import pip
        print("✅ pip is available")
        return True
    except ImportError:
        print("❌ pip not found. Trying to install...")
        try:
            # Try installing pip
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            print("✅ pip installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install pip. Please install manually and try again.")
            return False

def install_package(package_name, import_name=None, upgrade=True):
    """
    Install a Python package using pip
    
    Args:
        package_name (str): Package name to install via pip
        import_name (str): Name to import (if different from package_name)
        upgrade (bool): Whether to try updating the package
    """
    if import_name is None:
        import_name = package_name
    
    try:
        # Try importing the package
        importlib.import_module(import_name)
        print(f"✅ {package_name} is already installed")
        return True
    except ImportError:
        print(f"📦 Installing {package_name}...")
        try:
            # Mount installation command
            cmd = [sys.executable, "-m", "pip", "install", package_name]
            if upgrade:
                cmd.append("--upgrade")
            
            # Install the package
            subprocess.check_call(cmd)
            print(f"✅ {package_name} successfully installed")
            
            # Check if it was actually installed
            importlib.import_module(import_name)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error when installing {package_name}: {e}")
            return False
        except ImportError:
            print(f"⚠️  {package_name} was installed but could not be imported. A restart may be required.")
            return False

def install_all_dependencies():
    """Installs all required dependencies for PanVita 2"""
    print("🔧 Installing PanVita 2 dependencies...\n")
    
    # List of required packages: (pip_name, import_name)
    packages = [
        ("PyQt6", "PyQt6.QtCore"),
        ("PyQt6-WebEngine", "PyQt6.QtWebEngineCore"),
        ("psutil", "psutil"),
        ("pandas", "pandas"),
        ("seaborn", "seaborn"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("networkx", "networkx"),
        ("scikit-learn", "sklearn"),
        ("scipy", "scipy"),
        ("UpSetPlot", "upsetplot"),
        ("plotly", "plotly"),
        ("adjustText", "adjustText"),
        ("wget", "wget")
    ]
    
    success_count = 0
    total_count = len(packages)
    
    # Install regular packages
    for package_name, import_name in packages:
        if install_package(package_name, import_name):
            success_count += 1
        else:
            print(f"⚠️  Failed to install {package_name}, trying to continue...")
    
    print(f"\n📊 Installation result: {success_count}/{total_count} packages")
    
    # Essential packages for the core functionality
    essential_packages = ["PyQt6.QtCore", "pandas", "matplotlib", "seaborn", "numpy", "sklearn"]
    essential_installed = 0
    
    for package in essential_packages:
        try:
            importlib.import_module(package)
            essential_installed += 1
        except ImportError:
            pass
    
    if essential_installed == len(essential_packages):
        print("🎉 All essential dependencies have been installed successfully!")
        return True
    else:
        print(f"⚠️  Some essential dependencies were not installed ({essential_installed}/{len(essential_packages)}).")
        print("   PanVita 2 may not work properly.")
        return False

def test_imports():
    """Tests that all PanVita 2 imports work correctly"""
    print("\n🧪 Testing imports...")
    
    imports_to_test = [
        ("from PyQt6.QtWidgets import QApplication", "PyQt6"),
        ("from PyQt6.QtWebEngineWidgets import QWebEngineView", "PyQt6-WebEngine"),
        ("import psutil", "psutil"),
        ("import pandas as pd", "pandas"),
        ("import matplotlib.pyplot as plt", "matplotlib"),
        ("import seaborn as sns", "seaborn"),
        ("import numpy as np", "numpy"),
        ("import networkx as nx", "networkx"),
        ("import sklearn", "scikit-learn"),
        ("import scipy", "scipy"),
        ("from upsetplot import UpSet", "UpSetPlot"),
        ("import plotly", "plotly"),
        ("from adjustText import adjust_text", "adjustText"),
        ("import wget", "wget")
    ]
    
    failed_imports = []
    
    for import_statement, package_name in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {package_name} - OK")
        except ImportError as e:
            print(f"❌ {package_name} - FAILED: {e}")
            failed_imports.append(package_name)
    
    if not failed_imports:
        print("\n🎉 All imports were successful!")
        return True
    else:
        print(f"\n❌ Import failure: {', '.join(failed_imports)}")
        return False

def show_usage_instructions():
    """Shows instructions for use after installation"""
    print("\n" + "=" * 60)
    print("  INSTALLATION COMPLETE")
    print("=" * 60)
    print()
    
    # Detects the environment
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV') is not None
    )
    
    if in_venv:
        print("📋 Next steps (active virtual environment):")
        print("   python interface.py")
        print()
        print("💡 For future executions:")
        if os.name == 'nt':  # Windows
            print("   scripts\\activate      # Activate environment")
        else:  # Unix/Linux
            print("   source .venv/bin/activate   # Activate environment")
    else:
        print("📋 Next steps:")
        if os.name == 'nt':  # Windows
            print("   python interface.py")
        else:  # Unix/Linux
            print("   python3 interface.py")
    
    print()
    print("📁 Make sure you have:")
    print("   - All core files (interface.py, panvita.py, etc.) in the same folder.")
    print("   - GenBank or FASTA Files ready for analysis.")
    print()

def main():
    """Main function of the script"""
    print_banner()
    
    # Check Python
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # Check virtual environment
    if not check_virtual_env():
        sys.exit(1)
    
    print()
    
    # Check pip
    if not check_pip():
        sys.exit(1)
    
    print()
    
    # Install dependencies
    installation_success = install_all_dependencies()
    
    # Test imports
    import_success = test_imports()
    
    # Shows final instructions
    if installation_success and import_success:
        show_usage_instructions()
        sys.exit(0)
    else:
        print("\n❌ Installation was not fully successful.")
        print("   Check the errors above and try manually installing the failed packages.")
        if os.environ.get('VIRTUAL_ENV'):
            print("   Example command: pip install PyQt6 pandas scikit-learn seaborn plotly")
        else:
            if os.name == 'nt':
                print("   Example command: python -m pip install PyQt6 pandas scikit-learn seaborn plotly")
            else:
                print("   Example command: pip3 install PyQt6 pandas scikit-learn seaborn plotly")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation canceled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("   Please report this bug in the project repository.")
        sys.exit(1)
