@echo off
REM PanVITA - Virtual Environment Activation Script (Windows)
REM ==========================================================

echo.
echo Activating PanVITA virtual environment...
echo.

REM Navigate to the parent directory (where panvita.py is located)
cd /d "%~dp0\.."

REM Checks if the virtual environment exists
if not exist ".venv" (
    echo ERRO: Virtual environment not found!
    echo Run first: scripts\install_windows.bat
    pause
    exit /b 1
)

REM Activate the virtual environment
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERRO: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Virtual environment activated!
echo Python: %VIRTUAL_ENV%\Scripts\python.exe
echo Pip: %VIRTUAL_ENV%\Scripts\pip.exe
echo.
echo Now you can run:
echo   python panvita.py [options]
echo.
echo To deactivate the virtual environment, type: deactivate
echo.

REM Inicia um novo prompt de comando para o usuário
cmd /k
