@echo off
REM PanVITA - Installation Script for Windows
REM ==========================================

echo.
echo ============================================================
echo   PanVITA - Dependency Installer (Windows)
echo   Versao: 2.0.0
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.7+ and add it to your PATH.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Navigate to the parent directory (where panvita.py is located)
cd /d "%~dp0\.."

REM Creates virtual environment if it does not exist
if not exist ".venv" (
    echo Creating a Python virtual environment...
    python -m venv .venv
    
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Make sure the venv module is available.
        pause
        exit /b 1
    )
    
    echo Virtual environment created em .venv\
) else (
    echo Virtual environment already exists in .venv\
)

REM Activate the virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Virtual environment activated
echo Python: %VIRTUAL_ENV%\Scripts\python.exe
echo.

REM Update pip in the virtual environment
echo Updating pip in the virtual environment...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo Warning: Failed to update pip, continuing anyway...
)

REM Run the Python installation script
echo Running dependency installer...
echo.
python scripts\install_dependencies.py

if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    echo Try running manually:
    echo   .venv\Scripts\activate.bat
    echo   python scripts\install_dependencies.py
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   INSTALLATION COMPLETED SUCCESSFULLY!
echo ============================================================
echo.
echo To run PanVITA:
echo   .venv\Scripts\activate.bat     REM Activate virtual environment
echo   python panvita.py [opcoes]     REM Run PanVITA
echo.
echo   OR use the activation script:
echo   scripts\activate_env.bat       REM Activate environment
echo.
pause
