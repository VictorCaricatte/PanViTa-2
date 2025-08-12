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
            # Método 1: conda (se disponível)
            ["conda", "install", "-c", "conda-forge", "basemap", "-y"],
            # Método 2: pip com repositório específico
            [sys.executable, "-m", "pip", "install", "basemap-data"],
            [sys.executable, "-m", "pip", "install", "basemap", "--upgrade"]
        ]
        
        for method in methods:
            try:
                print(f"   Tentando: {' '.join(method)}")
                subprocess.check_call(method)
                # Verifica se a instalação funcionou
                from mpl_toolkits.basemap import Basemap
                print("✅ basemap instalado com sucesso")
                return True
            except (subprocess.CalledProcessError, ImportError, FileNotFoundError):
                continue
        
        print("⚠️  Aviso: Não foi possível instalar basemap automaticamente.")
        print("   O PanVITA funcionará, mas funcionalidades de mapa podem não estar disponíveis.")
        print("   Para instalar manualmente:")
        print("   - Com conda: conda install -c conda-forge basemap")
        print("   - Com pip: pip install basemap basemap-data")
        return False

def install_all_dependencies():
    """Instala todas as dependências necessárias"""
    print("🔧 Instalando dependências do PanVITA...\n")
    
    # Lista de pacotes necessários (core)
    packages = [
        ("pandas", "pandas"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("wget", "wget"),
        ("numpy", "numpy"),          # Adicionado explicitamente
        ("scipy", "scipy"),          # Dependência do seaborn
    ]
    
    success_count = 0
    total_count = len(packages) + 1  # +1 para basemap
    
    # Instala pacotes regulares
    for package_name, import_name in packages:
        if install_package(package_name, import_name):
            success_count += 1
        else:
            print(f"⚠️  Falha ao instalar {package_name}, tentando continuar...")
    
    # Instala basemap (caso especial) - opcional
    print("\n📍 Instalando basemap (opcional para funcionalidades de mapa)...")
    if install_basemap():
        success_count += 1
    else:
        print("⚠️  Basemap não foi instalado, mas o PanVITA funcionará sem mapas.")
    
    print(f"\n📊 Resultado da instalação: {success_count}/{total_count} pacotes")
    
    # Mesmo que nem todos os pacotes tenham sido instalados, verifica os essenciais
    essential_packages = ["pandas", "matplotlib", "seaborn", "wget", "numpy"]
    essential_installed = 0
    
    for package in essential_packages:
        try:
            importlib.import_module(package)
            essential_installed += 1
        except ImportError:
            pass
    
    if essential_installed == len(essential_packages):
        print("🎉 Todas as dependências essenciais foram instaladas com sucesso!")
        return True
    else:
        print(f"⚠️  Algumas dependências essenciais não foram instaladas ({essential_installed}/{len(essential_packages)}).")
        print("   O PanVITA pode não funcionar corretamente.")
        return False

def test_imports():
    """Testa se todos os imports funcionam corretamente"""
    print("\n🧪 Testando imports...")
    
    imports_to_test = [
        ("import pandas as pd", "pandas"),
        ("import matplotlib.pyplot as plt", "matplotlib"),
        ("import seaborn as sns", "seaborn"),
        ("import wget", "wget"),
    ]
    
    # Teste especial para basemap
    try:
        exec("from mpl_toolkits.basemap import Basemap")
        print("✅ basemap - OK")
    except ImportError:
        print("⚠️  basemap - Não disponível (funcionalidades de mapa limitadas)")
    
    failed_imports = []
    
    for import_statement, package_name in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {package_name} - OK")
        except ImportError as e:
            print(f"❌ {package_name} - FALHOU: {e}")
            failed_imports.append(package_name)
    
    if not failed_imports:
        print("\n🎉 Todos os imports foram bem-sucedidos!")
        return True
    else:
        print(f"\n❌ Falha nos imports: {', '.join(failed_imports)}")
        return False

def show_usage_instructions():
    """Mostra instruções de uso após a instalação"""
    print("\n" + "=" * 60)
    print("  INSTALAÇÃO CONCLUÍDA")
    print("=" * 60)
    print()
    
    # Detecta o ambiente
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV') is not None
    )
    
    if in_venv:
        print("📋 Próximos passos (ambiente virtual ativo):")
        print("   python panvita.py [opções]")
        print()
        print("💡 Para futuras execuções:")
        if os.name == 'nt':  # Windows
            print("   scripts\\activate_env.bat    # Ativar ambiente")
        else:  # Unix/Linux
            print("   source .venv/bin/activate   # Ativar ambiente")
            print("   # OU")
            print("   ./scripts/activate_env.sh   # Script de ativação")
    else:
        print("📋 Próximos passos:")
        if os.name == 'nt':  # Windows
            print("   python panvita.py [opções]")
        else:  # Unix/Linux
            print("   python3 panvita.py [opções]")
    
    print()
    print("📁 Certifique-se de que você tem:")
    print("   - Arquivos GenBank (.gbk, .gbf, .gbff)")
    print("   - Banco de dados configurado")
    print("   - BLAST e/ou DIAMOND instalados")
    print()
    print("🔗 Para mais informações, consulte o README.md")
    print()

def main():
    """Função principal do script"""
    print_banner()
    
    # Verifica Python
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # Verifica ambiente virtual
    if not check_virtual_env():
        sys.exit(1)
    
    print()
    
    # Verifica pip
    if not check_pip():
        sys.exit(1)
    
    print()
    
    # Instala dependências
    installation_success = install_all_dependencies()
    
    # Testa imports
    import_success = test_imports()
    
    # Mostra instruções finais
    if installation_success and import_success:
        show_usage_instructions()
        sys.exit(0)
    else:
        print("\n❌ Instalação não foi totalmente bem-sucedida.")
        print("   Verifique os erros acima e tente instalar manualmente os pacotes que falharam.")
        if os.environ.get('VIRTUAL_ENV'):
            print("   Comando exemplo: pip install pandas numpy matplotlib seaborn wget scipy")
        else:
            if os.name == 'nt':
                print("   Comando exemplo: python -m pip install pandas numpy matplotlib seaborn wget scipy")
            else:
                print("   Comando exemplo: pip3 install pandas numpy matplotlib seaborn wget scipy")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("   Por favor, reporte este erro no repositório do projeto.")
        sys.exit(1)
