@echo off
REM PanVITA - Script de Instalação para Windows
REM ==========================================

echo.
echo ============================================================
echo   PanVITA - Instalador de Dependencias (Windows)
echo   Versao: 2.0.0
echo ============================================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale Python 3.7+ e adicione ao PATH.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python encontrado:
python --version
echo.

REM Navega para o diretório pai (onde está o panvita.py)
cd /d "%~dp0\.."

REM Cria ambiente virtual se não existir
if not exist ".venv" (
    echo Criando ambiente virtual Python...
    python -m venv .venv
    
    if errorlevel 1 (
        echo ERRO: Falha ao criar ambiente virtual.
        echo Certifique-se de que o modulo venv esta disponivel.
        pause
        exit /b 1
    )
    
    echo Ambiente virtual criado em .venv\
) else (
    echo Ambiente virtual ja existe em .venv\
)

REM Ativa o ambiente virtual
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERRO: Falha ao ativar ambiente virtual.
    pause
    exit /b 1
)

echo Ambiente virtual ativado
echo Python: %VIRTUAL_ENV%\Scripts\python.exe
echo.

REM Atualiza pip no ambiente virtual
echo Atualizando pip no ambiente virtual...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo Aviso: Falha ao atualizar pip, continuando mesmo assim...
)

REM Executa o script de instalação Python
echo Executando instalador de dependencias...
echo.
python scripts\install_dependencies.py

if errorlevel 1 (
    echo.
    echo ERRO: Falha na instalacao das dependencias.
    echo Tente executar manualmente:
    echo   .venv\Scripts\activate.bat
    echo   python scripts\install_dependencies.py
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo ============================================================
echo.
echo Para executar o PanVITA:
echo   .venv\Scripts\activate.bat     REM Ativar ambiente virtual
echo   python panvita.py [opcoes]     REM Executar PanVITA
echo.
echo   OU use o script de ativacao:
echo   scripts\activate_env.bat       REM Ativar ambiente
echo.
pause
