#!/bin/bash
# PanVITA - Script de Instalação para Linux/macOS
# ===============================================

echo ""
echo "============================================================"
echo "  PanVITA - Instalador de Dependências (Linux/macOS)"
echo "  Versão: 2.0.0"
echo "============================================================"
echo ""

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ ERRO: Python3 não encontrado!"
    echo "   Por favor, instale Python 3.7+ e tente novamente."
    echo ""
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   CentOS/RHEL:   sudo yum install python3 python3-pip python3-venv"
    echo "   macOS:         brew install python3"
    exit 1
fi

echo "✅ Python encontrado:"
python3 --version
echo ""

# Verifica se python3-venv está disponível
if ! python3 -m venv --help &> /dev/null; then
    echo "📦 python3-venv não encontrado. Tentando instalar..."
    
    # Tenta instalar venv
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install python3-venv -y
    elif command -v yum &> /dev/null; then
        sudo yum install python3-venv -y
    elif command -v dnf &> /dev/null; then
        sudo dnf install python3-venv -y
    else
        echo "⚠️  Aviso: Não foi possível instalar python3-venv automaticamente."
        echo "   O script tentará continuar mesmo assim."
    fi
fi

# Navega para o diretório pai (onde está o panvita.py)
cd "$(dirname "$0")/.."

# Cria ambiente virtual se não existir
if [ ! -d ".venv" ]; then
    echo "� Criando ambiente virtual Python..."
    python3 -m venv .venv
    
    if [ $? -ne 0 ]; then
        echo "❌ ERRO: Falha ao criar ambiente virtual."
        echo "   Certifique-se de que python3-venv está instalado:"
        echo "   Ubuntu/Debian: sudo apt install python3-venv"
        echo "   CentOS/RHEL:   sudo yum install python3-venv"
        exit 1
    fi
    
    echo "✅ Ambiente virtual criado em .venv/"
else
    echo "✅ Ambiente virtual já existe em .venv/"
fi

# Ativa o ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ ERRO: Falha ao ativar ambiente virtual."
    exit 1
fi

echo "✅ Ambiente virtual ativado"
echo "   Python: $(which python)"
echo ""

# Atualiza pip no ambiente virtual
echo "📦 Atualizando pip no ambiente virtual..."
python -m pip install --upgrade pip

if [ $? -ne 0 ]; then
    echo "⚠️  Aviso: Falha ao atualizar pip, continuando mesmo assim..."
fi
echo ""

# Executa o script de instalação Python
echo "🔧 Executando instalador de dependências..."
echo ""

python scripts/install_dependencies.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERRO: Falha na instalação das dependências."
    echo "   Tente executar manualmente:"
    echo "   source .venv/bin/activate"
    echo "   python scripts/install_dependencies.py"
    exit 1
fi

echo ""
echo "============================================================"
echo "  INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "============================================================"
echo ""
echo "📋 Para executar o PanVITA:"
echo "   source .venv/bin/activate    # Ativar ambiente virtual"
echo "   python panvita.py [opções]   # Executar PanVITA"
echo ""
echo "   OU use o script de ativação:"
echo "   ./scripts/activate_env.sh    # Ativar ambiente"
echo ""
echo "📁 Certifique-se de que você tem os arquivos necessários:"
echo "   - Arquivos GenBank (.gbk, .gbf, .gbff)"
echo "   - BLAST e/ou DIAMOND instalados"
echo ""
