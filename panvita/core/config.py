"""
Configurações e utilitários do PanViTa
"""

import platform
import ssl
import urllib.request
import ctypes
import ctypes.util


class PanViTaConfig:
    VERSION = "2.0.0"
    
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
