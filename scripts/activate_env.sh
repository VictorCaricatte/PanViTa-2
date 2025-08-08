#!/bin/bash
# PanVITA - Script de Ativação do Ambiente Virtual
# ================================================

echo ""
echo "🔧 Ativando ambiente virtual do PanVITA..."
echo ""

# Navega para o diretório pai (onde está o panvita.py)
cd "$(dirname "$0")/.."

# Verifica se o ambiente virtual existe
if [ ! -d ".venv" ]; then
    echo "❌ ERRO: Ambiente virtual não encontrado!"
    echo "   Execute primeiro: ./scripts/install_linux.sh"
    exit 1
fi

# Ativa o ambiente virtual
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ ERRO: Falha ao ativar ambiente virtual."
    exit 1
fi

echo "✅ Ambiente virtual ativado!"
echo "   Python: $(which python)"
echo "   Pip: $(which pip)"
echo ""
echo "📋 Agora você pode executar:"
echo "   python panvita.py [opções]"
echo ""
echo "💡 Para desativar o ambiente virtual, digite: deactivate"
echo ""

# Inicia um shell interativo para o usuário
exec "$SHELL"
