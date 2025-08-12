#!/bin/bash
# PanVITA - Virtual Environment Activation Script
# ================================================

echo ""
echo "🔧 Activating PanVITA virtual environment..."
echo ""

# Navigate to the parent directory (where panvita.py is located)
cd "$(dirname "$0")/.."

# Checks if the virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ ERROR: Virtual environment not found!"
    echo "   Run first: ./scripts/install_linux.sh"
    exit 1
fi

# Activate the virtual environment
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to activate virtual environment."
    exit 1
fi

echo "✅ Virtual environment activated!"
echo "   Python: $(which python)"
echo "   Pip: $(which pip)"
echo ""
echo "📋 Now you can run:"
echo "   python panvita.py [opções]"
echo ""
echo "💡 To deactivate the virtual environment, type: deactivate"
echo ""

# Inicia um shell interativo para o usuário
exec "$SHELL"
