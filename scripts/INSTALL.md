# PanVITA - Dependency Installation Guide

This guide provides detailed instructions for installing all the dependencies required to run PanVITA using Python virtual environments.

## 📋 Sistem requiriment

- **Python**: 3.7 ou upper.
- **Operating System**: Windows, Linux, ou macOS
- **Memory**: Minimum 4GB RAM (recomended 8GB+)
- **Disk space**: Minimum 2GB livres

## 🚀 Fast instalation (RECOMENDED)

Installation scripts now automatically create a Python virtual environment to avoid conflicts with other installations.

### Windows
```batch
# Run the batch file (creates virtual environment automatically)
scripts\install_windows.bat
```

### Linux/macOS
```bash
# Make the script executable and run (creates virtual environment automatically)
chmod +x scripts/install_linux.sh
./scripts/install_linux.sh
```

### Manual Installation with Virtual Environment
```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate.bat

# 3. Run the installation script
python scripts/install_dependencies.py
```

## 🔧 Uso após Instalação

### Use after Installation

**Automatic Activation Scripts:**
```bash
# Linux/macOS
./scripts/activate_env.sh

# Windows
scripts\activate_env.bat
```

**Manual Activation:**
```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate.bat
```

### Execution of PanVITA
```bash
# With active virtual environment
python panvita.py [opções]

# To deactivate the virtual environment
deactivate
```

## 📦 Dependencies Included

### Required Packages
- **pandas** (>=1.3.0): Data manipulation and analysis
- **matplotlib** (>=3.3.0): Graphing
- **seaborn** (>=0.11.0): Statistical visualization
- **wget** (>=3.2): File download
- **numpy** (>=1.19.0): Numerical computation
- **scipy** (>=1.6.0): Scientific algorithms

### Optional Packages
- **basemap** (>=1.3.0): Viewing geographic maps (may fail on some installations)

## 🛠️ Manual Installation per Package

If the automatic installation fails, you can install each package individually in the virtual environment.:

```bash
# Activate the virtual environment first
source .venv/bin/activate  # Linux/macOS
# Or
.venv\Scripts\activate.bat  # Windows

# Install the packages
pip install pandas>=1.3.0
pip install matplotlib>=3.3.0
pip install seaborn>=0.11.0
pip install wget>=3.2
pip install basemap basemap-data
```

### Using requirements.txt
```bash
pip install -r requirements.txt
```

## 🔧 Troubleshooting

### Error: "Python not found"
**Solution**: Install Python 3.7+ and add it to your system PATH
- Windows: https://www.python.org/downloads/
- Linux: `sudo apt install python3 python3-pip` (Ubuntu/Debian)
- macOS: `brew install python3`

### Error: "pip not found"
**Solution**: Install pip
```bash
# Linux
sudo apt install python3-pip

# macOS
brew install python3

# Windows
python -m ensurepip --upgrade
```

### Error installing basemap
**Alternative solutions**:
1. **With conda** (recomended):
   ```bash
   conda install -c conda-forge basemap
   ```

2. **Install system dependencies** (Linux):
   ```bash
   sudo apt install libproj-dev proj-data proj-bin libgeos-dev
   pip install basemap
   ```

### Error: "Permission denied"
**Solution**:
- Use `--user` flag: `pip install --user package_name`
- Use virtual environment: `python -m venv panvita_env && source panvita_env/bin/activate`
- Linux/macOS: Use `sudo` com cuidado: `sudo pip install package_name`

### Connectivity issues
If there are download problems:
```bash
# Use mirror alternativo
pip install -i https://pypi.douban.com/simple/ package_name

# Ou baixe arquivos .whl manualmente de https://pypi.org/
```

## 🧪 Installation Verification

Run the verification test:
```bash
python install_dependencies.py
```

Or test manually:
```python
# Basic test
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import wget

print("✅ Todas as dependências estão funcionando!")
```

## 📊 Memory Usage

| Package | Approximate Size | RAM Usage |
|--------|-------------------|------------|
| pandas | ~25MB | Médio |
| matplotlib | ~40MB | Médio |
| seaborn | ~5MB | Baixo |
| basemap | ~200MB | Alto |

**Approximate total**: ~270MB of space + 2-4GB RAM during execution

## 🐍 Virtual Environments (RECOMENDED)

To avoid dependency conflicts:

```bash
# Create virtual environment
python -m venv panvita_env

# Active (Linux/macOS)
source panvita_env/bin/activate

# Active (Windows)
panvita_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Desactive
deactivate
```

## 📞 Support

If you still have problems:

1. **Check the logs** detailed error reports
2. **Update pip**: `pip install --upgrade pip`
3. **Clear cache**: `pip cache purge`
4. **Report problems** in the project repository

## 🔄 Updates

To update all dependencies:
```bash
pip install --upgrade -r requirements.txt
```

---

**Notice**: This installer has been tested on Python 3.7-3.12 on Windows 10/11, Ubuntu 20.04+, and macOS 10.15+.
