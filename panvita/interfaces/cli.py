"""
Interface de linha de comando para PanViTa
Mantém compatibilidade com a versão original
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório parent ao path para importar o core
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.engine import PanViTaEngine
except ImportError:
    print("Erro ao importar o engine do PanViTa. Verifique a instalação.")
    sys.exit(1)


def main():
    """Função principal da CLI - simplesmente chama o engine"""
    engine = PanViTaEngine()
    engine.run()


if __name__ == "__main__":
    main()