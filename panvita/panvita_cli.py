#!/usr/bin/env python3
"""
PanViTa - Interface de linha de comando
Entry point para a versão CLI do PanViTa
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório panvita ao path
sys.path.insert(0, str(Path(__file__).parent / "panvita"))

try:
    from interfaces.cli import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Erro ao importar módulos do PanViTa: {e}")
    print("Verifique se a estrutura do projeto está correta.")
    sys.exit(1)
except Exception as e:
    print(f"Erro inesperado: {e}")
    sys.exit(1)
