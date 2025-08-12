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
# Torne o script executável e execute (cria ambiente virtual automaticamente)
chmod +x scripts/install_linux.sh
./scripts/install_linux.sh
```

### Instalação Manual com Ambiente Virtual
```bash
# 1. Crie um ambiente virtual
python3 -m venv .venv

# 2. Ative o ambiente virtual
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate.bat

# 3. Execute o script de instalação
python scripts/install_dependencies.py
```

## 🔧 Uso após Instalação

### Ativação do Ambiente Virtual

**Scripts de Ativação Automática:**
```bash
# Linux/macOS
./scripts/activate_env.sh

# Windows
scripts\activate_env.bat
```

**Ativação Manual:**
```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate.bat
```

### Execução do PanVITA
```bash
# Com ambiente virtual ativo
python panvita.py [opções]

# Para desativar o ambiente virtual
deactivate
```

## 📦 Dependências Incluídas

### Pacotes Obrigatórios
- **pandas** (>=1.3.0): Manipulação e análise de dados
- **matplotlib** (>=3.3.0): Criação de gráficos
- **seaborn** (>=0.11.0): Visualização estatística
- **wget** (>=3.2): Download de arquivos
- **numpy** (>=1.19.0): Computação numérica
- **scipy** (>=1.6.0): Algoritmos científicos

### Pacotes Opcionais
- **basemap** (>=1.3.0): Visualização de mapas geográficos (pode falhar em algumas instalações)

## 🛠️ Instalação Manual por Pacote

Se a instalação automática falhar, você pode instalar cada pacote individualmente no ambiente virtual:

```bash
# Ative o ambiente virtual primeiro
source .venv/bin/activate  # Linux/macOS
# OU
.venv\Scripts\activate.bat  # Windows

# Instale os pacotes
pip install pandas>=1.3.0
pip install matplotlib>=3.3.0
pip install seaborn>=0.11.0
pip install wget>=3.2
pip install basemap basemap-data
```

### Usando requirements.txt
```bash
pip install -r requirements.txt
```

## 🔧 Solução de Problemas

### Erro: "Python não encontrado"
**Solução**: Instale Python 3.7+ e adicione ao PATH do sistema
- Windows: https://www.python.org/downloads/
- Linux: `sudo apt install python3 python3-pip` (Ubuntu/Debian)
- macOS: `brew install python3`

### Erro: "pip não encontrado"
**Solução**: Instale pip
```bash
# Linux
sudo apt install python3-pip

# macOS
brew install python3

# Windows
python -m ensurepip --upgrade
```

### Erro na instalação do basemap
**Soluções alternativas**:
1. **Com conda** (recomendado):
   ```bash
   conda install -c conda-forge basemap
   ```

2. **Instalar dependências do sistema** (Linux):
   ```bash
   sudo apt install libproj-dev proj-data proj-bin libgeos-dev
   pip install basemap
   ```

### Erro: "Permission denied"
**Soluções**:
- Use `--user` flag: `pip install --user package_name`
- Use ambiente virtual: `python -m venv panvita_env && source panvita_env/bin/activate`
- Linux/macOS: Use `sudo` com cuidado: `sudo pip install package_name`

### Problemas de conectividade
Se houver problemas de download:
```bash
# Use mirror alternativo
pip install -i https://pypi.douban.com/simple/ package_name

# Ou baixe arquivos .whl manualmente de https://pypi.org/
```

## 🧪 Verificação da Instalação

Execute o teste de verificação:
```bash
python install_dependencies.py
```

Ou teste manualmente:
```python
# Teste básico
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import wget

print("✅ Todas as dependências estão funcionando!")
```

## 📊 Uso de Memória

| Pacote | Tamanho Aproximado | Uso de RAM |
|--------|-------------------|------------|
| pandas | ~25MB | Médio |
| matplotlib | ~40MB | Médio |
| seaborn | ~5MB | Baixo |
| basemap | ~200MB | Alto |

**Total aproximado**: ~270MB de espaço + 2-4GB RAM durante execução

## 🐍 Ambientes Virtuais (Recomendado)

Para evitar conflitos de dependências:

```bash
# Criar ambiente virtual
python -m venv panvita_env

# Ativar (Linux/macOS)
source panvita_env/bin/activate

# Ativar (Windows)
panvita_env\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Desativar
deactivate
```

## 📞 Suporte

Se ainda tiver problemas:

1. **Verifique os logs** de erro detalhados
2. **Atualize pip**: `pip install --upgrade pip`
3. **Limpe cache**: `pip cache purge`
4. **Reporte problemas** no repositório do projeto

## 🔄 Atualizações

Para atualizar todas as dependências:
```bash
pip install --upgrade -r requirements.txt
```

---

**Nota**: Este instalador foi testado em Python 3.7-3.12 em Windows 10/11, Ubuntu 20.04+, e macOS 10.15+.
