@echo off
REM PanVITA - Script de Ativação do Ambiente Virtual (Windows)
REM ==========================================================

echo.
echo Ativando ambiente virtual do PanVITA...
echo.

REM Navega para o diretório pai (onde está o panvita.py)
cd /d "%~dp0\.."

REM Verifica se o ambiente virtual existe
if not exist ".venv" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute primeiro: scripts\install_windows.bat
    pause
    exit /b 1
)

REM Ativa o ambiente virtual
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERRO: Falha ao ativar ambiente virtual.
    pause
    exit /b 1
)

echo Ambiente virtual ativado!
echo Python: %VIRTUAL_ENV%\Scripts\python.exe
echo Pip: %VIRTUAL_ENV%\Scripts\pip.exe
echo.
echo Agora voce pode executar:
echo   python panvita.py [opcoes]
echo.
echo Para desativar o ambiente virtual, digite: deactivate
echo.

REM Inicia um novo prompt de comando para o usuário
cmd /k
