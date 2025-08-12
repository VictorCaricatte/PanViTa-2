#!/usr/bin/env python3
"""
PanVITA - Dependency Installation Script
===============================================

This script automatically installs all the necessary dependencies
to run PanVITA (Pan-genome Virulence and Antimicrobial Resistance Tool).

Date: August 12, 2025
"""

import sys
import subprocess
import importlib
import os

def print_banner():
    """Displays the script banner"""
    print("=" * 60)
    print("  PanVITA - Python Dependency Installer")
    print("  Versão: 2.0.0")
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
        response = input("   Continue anyway? (s/N)): ").strip().lower()
        if response not in ['s', 'sim', 'y', 'yes']:
            print("   Installation canceled. Run in a virtual environment..")
            return False
    
    return True

def check_python_version():
    """Check if the Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ ERROR: PanVITA requires Python 3.7 or higher.")
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
            print(f"⚠️  {package_name} was installed but could not be imported. A restart may be required..")
            return False

def install_basemap():
    """Special installation for basemap (more complex)"""
    try:
        from mpl_toolkits.basemap import Basemap
        print("✅ basemap is already installed")
        return True
    except ImportError:
        print("📦 Installing basemap (may take a few minutes)...")
        
        # Try different installation methods for basemap
        methods = [
            # Método 1: conda (if available)
            ["conda", "install", "-c", "conda-forge", "basemap", "-y"],
            # Method 2: pip with specific repository
            [sys.executable, "-m", "pip", "install", "basemap-data"],
            [sys.executable, "-m", "pip", "install", "basemap", "--upgrade"]
        ]
        
        for method in methods:
            try:
                print(f"   Trying: {' '.join(method)}")
                subprocess.check_call(method)
                # Check if the installation worked
                from mpl_toolkits.basemap import Basemap
                print("✅ basemap installed successfully")
                return True
            except (subprocess.CalledProcessError, ImportError, FileNotFoundError):
                continue
        
        print("⚠️  Warning: Unable to install basemap automatically.")
        print("   PanVITA will work, but map functionality may not be available.")
        print("   To install manually:")
        print("   - With conda: conda install -c conda-forge basemap")
        print("   - With pip: pip install basemap basemap-data")
        return False

def install_all_dependencies():
    """Installs all required dependencies"""
    print("🔧 Installing PanVITA dependencies...\n")
    
    # List of required packages (core)
    packages = [
        ("pandas", "pandas"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("wget", "wget"),
        ("numpy", "numpy"),          # Explicitly added
        ("scipy", "scipy"),          # Seaborn dependence
    ]
    
    success_count = 0
    total_count = len(packages) + 1  # +1 for basemap
    
    # Install regular packages
    for package_name, import_name in packages:
        if install_package(package_name, import_name):
            success_count += 1
        else:
            print(f"⚠️  Failed to install {package_name}, trying to continue...")
    
    # Install basemap (special case) - optional
    print("\n📍 Installing basemap (optional for map functionality)...")
    if install_basemap():
        success_count += 1
    else:
        print("⚠️  Basemap was not installed, but PanVITA will work without maps.")
    
    print(f"\n📊 Installation result: {success_count}/{total_count} packages")
    
    # Even if not all packages have been installed, check the essential ones
    essential_packages = ["pandas", "matplotlib", "seaborn", "wget", "numpy"]
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
        print("   PanVITA may not work properly.")
        return False

def test_imports():
    """Tests that all imports work correctly"""
    print("\n🧪 Testing imports...")
    
    imports_to_test = [
        ("import pandas as pd", "pandas"),
        ("import matplotlib.pyplot as plt", "matplotlib"),
        ("import seaborn as sns", "seaborn"),
        ("import wget", "wget"),
    ]
    
    # Special test for basemap
    try:
        exec("from mpl_toolkits.basemap import Basemap")
        print("✅ basemap - OK")
    except ImportError:
        print("⚠️  basemap - Not available (limited map functionality)")
    
    failed_imports = []
    
    for import_statement, package_name in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {package_name} - OK")
        except ImportError as e:
            print(f"❌ {package_name} - FALHOU: {e}")
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
        print("📋 Next steps (ambiente virtual ativo):")
        print("   python panvita.py [opções]")
        print()
        print("💡 For future executions:")
        if os.name == 'nt':  # Windows
            print("   scripts\\activate_env.bat    # Ativar ambiente")
        else:  # Unix/Linux
            print("   source .venv/bin/activate   # Ativar ambiente")
            print("   # OU")
            print("   ./scripts/activate_env.sh   # Script de ativação")
    else:
        print("📋 Next steps:")
        if os.name == 'nt':  # Windows
            print("   python panvita.py [opções]")
        else:  # Unix/Linux
            print("   python3 panvita.py [opções]")
    
    print()
    print("📁 Make sure you have:")
    print("   - GenBank Files (.gbk, .gbf, .gbff)")
    print("   - Configured database")
    print("   - BLAST and/or DIAMOND installed")
    print()
    print("🔗 For more information, see README.md")
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
            print("   Example command: pip install pandas numpy matplotlib seaborn wget scipy")
        else:
            if os.name == 'nt':
                print("   Example command: python -m pip install pandas numpy matplotlib seaborn wget scipy")
            else:
                print("   Example command: pip3 install pandas numpy matplotlib seaborn wget scipy")
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
