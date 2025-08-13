#!/usr/bin/env python3
"""
PanViTa - Interface Streamlit
Entry point para a versão web do PanViTa
"""

import sys
import os
from pathlib import Path
import subprocess

# Adicionar o diretório panvita ao path
sys.path.insert(0, str(Path(__file__).parent / "panvita"))

def main():
    """Executa a aplicação Streamlit"""
    try:
        # Verificar se streamlit está instalado
        import streamlit
        
        # Caminho para o arquivo da aplicação Streamlit
        app_path = Path(__file__).parent / "panvita" / "interfaces" / "streamlit_app.py"
        
        if not app_path.exists():
            print(f"Erro: Arquivo da aplicação não encontrado: {app_path}")
            sys.exit(1)
        
        # Executar streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
        
        print("Iniciando PanViTa Web Interface...")
        print("A aplicação será aberta no seu navegador em instantes...")
        print("Para encerrar, pressione Ctrl+C no terminal")
        
        subprocess.run(cmd)
        
    except ImportError:
        print("Erro: Streamlit não está instalado.")
        print("Para instalar, execute: pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAplicação encerrada pelo usuário.")
    except Exception as e:
        print(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
