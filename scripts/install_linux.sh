#!/bin/bash
# PanVITA - Installation Script for Linux/macOS
# ===============================================

echo ""
echo "============================================================"
echo "  PanVITA - Dependency Installer (Linux/macOS)"
echo "  Versão: 2.0.0"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python3 not found!"
    echo "   Please install Python 3.7+ and try again.."
    echo ""
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   CentOS/RHEL:   sudo yum install python3 python3-pip python3-venv"
    echo "   macOS:         brew install python3"
    exit 1
fi

echo "✅ Python found:"
python3 --version
echo ""

# Checks if python3-venv is available
if ! python3 -m venv --help &> /dev/null; then
    echo "📦 python3-venv not found. Trying to install..."
    
    # Try installing venv
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install python3-venv -y
    elif command -v yum &> /dev/null; then
        sudo yum install python3-venv -y
    elif command -v dnf &> /dev/null; then
        sudo dnf install python3-venv -y
    else
        echo "⚠️  Warning: Unable to install python3-venv automatically."
        echo "   The script will try to continue anyway.."
    fi
fi

# Navigate to the parent directory (where panvita.py is located)
cd "$(dirname "$0")/.."

# Creates virtual environment if it does not exist
if [ ! -d ".venv" ]; then
    echo "� Creating a Python virtual environment..."
    python3 -m venv .venv
    
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Failed to create virtual environment."
        echo "   Make sure python3-venv is installed:"
        echo "   Ubuntu/Debian: sudo apt install python3-venv"
        echo "   CentOS/RHEL:   sudo yum install python3-venv"
        exit 1
    fi
    
    echo "✅ Virtual environment created in .venv/"
else
    echo "✅ Virtual environment already exists in .venv/"
fi

# Activate the virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to activate virtual environment."
    exit 1
fi

echo "✅ Virtual environment activated"
echo "   Python: $(which python)"
echo ""

# Update pip in the virtual environment
echo "📦 Updating pip in the virtual environment..."
python -m pip install --upgrade pip

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Failed to update pip, continuing anyway..."
fi
echo ""

# Run the Python installation script
echo "🔧 Running dependency installer..."
echo ""

python scripts/install_dependencies.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Dependencies failed to install."
    echo "   Try running manually:"
    echo "   source .venv/bin/activate"
    echo "   python scripts/install_dependencies.py"
    exit 1
fi

echo ""
echo "============================================================"
echo "  INSTALLATION COMPLETED SUCCESSFULLY!"
echo "============================================================"
echo ""
echo "📋 To run PanVITA:"
echo "   source .venv/bin/activate    # Ativar ambiente virtual"
echo "   python panvita.py [opções]   # Executar PanVITA"
echo ""
echo "   OR use the activation script:"
echo "   ./scripts/activate_env.sh    # Ativar ambiente"
echo ""
echo "📁 Make sure you have the necessary files:"
echo "   - GenBank Files (.gbk, .gbf, .gbff)"
echo "   - BLAST and/or DIAMOND installed"
echo ""
