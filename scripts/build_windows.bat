@echo off
REM Build script for Windows
REM FOVTools Cross-Platform Build

echo.
echo ========================================
echo   FOVTools Build Script - Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Change to project root (scripts directory is one level up)
cd /d "%~dp0.."

echo [INFO] Checking dependencies...
pip list | find "PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing requirements...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Starting build process...
echo.

python scripts/build_cross_platform.py --platform Windows

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Build completed successfully!
    echo ========================================
    echo.
    echo Output location: dist\
    echo.
) else (
    echo.
    echo ========================================
    echo   Build failed!
    echo ========================================
    echo.
)

pause
