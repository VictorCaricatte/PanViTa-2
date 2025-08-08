#!/usr/bin/env python3
"""
PanVITA - Script de Instalação de Dependências
===============================================

Este script instala automaticamente todas as dependências necessárias 
para executar o PanVITA (Pan-genome Virulence and Antimicrobial resistance Tool).

Autor: Script gerado para PanVITA v2.0.0
Data: 03 de agosto de 2025
"""

import sys
import subprocess
import importlib
import os

def print_banner():
    """Exibe o banner do script"""
    print("=" * 60)
    print("  PanVITA - Instalador de Dependências Python")
    print("  Versão: 2.0.0")
    print("=" * 60)
    print()

def check_virtual_env():
    """Verifica se estamos em um ambiente virtual"""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV') is not None
    )
    
    if in_venv:
        venv_path = os.environ.get('VIRTUAL_ENV', 'Unknown')
        print(f"✅ Executando em ambiente virtual: {venv_path}")
    else:
        print("⚠️  AVISO: Não detectado ambiente virtual ativo.")
        print("   Recomendamos usar um ambiente virtual para evitar conflitos.")
        print("   As dependências serão instaladas no sistema global.")
        response = input("   Continuar mesmo assim? (s/N): ").strip().lower()
        if response not in ['s', 'sim', 'y', 'yes']:
            print("   Instalação cancelada. Execute em um ambiente virtual.")
            return False
    
    return True

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ ERRO: PanVITA requer Python 3.7 ou superior.")
        print(f"   Versão atual: {version.major}.{version.minor}.{version.micro}")
        print("   Por favor, atualize o Python e tente novamente.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatível")
    return True

def check_pip():
    """Verifica se o pip está disponível"""
    try:
        import pip
        print("✅ pip está disponível")
        return True
    except ImportError:
        print("❌ pip não encontrado. Tentando instalar...")
        try:
            # Tenta instalar o pip
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            print("✅ pip instalado com sucesso")
            return True
        except subprocess.CalledProcessError:
            print("❌ Falha ao instalar pip. Instale manualmente e tente novamente.")
            return False

def install_package(package_name, import_name=None, upgrade=True):
    """
    Instala um pacote Python usando pip
    
    Args:
        package_name (str): Nome do pacote para instalar via pip
        import_name (str): Nome para importar (se diferente do package_name)
        upgrade (bool): Se deve tentar atualizar o pacote
    """
    if import_name is None:
        import_name = package_name
    
    try:
        # Tenta importar o pacote
        importlib.import_module(import_name)
        print(f"✅ {package_name} já está instalado")
        return True
    except ImportError:
        print(f"📦 Instalando {package_name}...")
        try:
            # Monta comando de instalação
            cmd = [sys.executable, "-m", "pip", "install", package_name]
            if upgrade:
                cmd.append("--upgrade")
            
            # Instala o pacote
            subprocess.check_call(cmd)
            print(f"✅ {package_name} instalado com sucesso")
            
            # Verifica se realmente foi instalado
            importlib.import_module(import_name)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package_name}: {e}")
            return False
        except ImportError:
            print(f"⚠️  {package_name} foi instalado mas não pode ser importado. Pode ser necessário reiniciar.")
            return False

def install_basemap():
    """Instalação especial para basemap (mais complexa)"""
    try:
        from mpl_toolkits.basemap import Basemap
        print("✅ basemap já está instalado")
        return True
    except ImportError:
        print("📦 Instalando basemap (pode demorar alguns minutos)...")
        
        # Tenta diferentes métodos de instalação para basemap
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
