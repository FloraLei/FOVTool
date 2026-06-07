@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Build script for FOVTools - Windows GUI Version
REM 双击直接使用版本

cd /d "%~dp0"

echo.
echo ========================================
echo   FOVTools 构建工具 - Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 错误：未检测到 Python
    echo.
    echo 请从以下地址下载并安装 Python 3.9+:
    echo https://www.python.org/
    echo.
    echo 安装时请勾选"Add Python to PATH"选项
    echo.
    pause
    exit /b 1
)

REM Check if venv exists, create if not
if not exist ".venv" (
    echo [信息] 正在创建虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo.
        echo ❌ 虚拟环境创建失败
        echo.
        pause
        exit /b 1
    )
)

REM Activate venv and install/check dependencies
echo [信息] 检查依赖...
call .venv\Scripts\activate.bat
pip list | find "PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 安装依赖... （首次可能需要 5-10 分钟）
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo ❌ 依赖安装失败
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [信息] 开始构建过程...
echo [信息] 这可能需要 5-15 分钟，请稍候...
echo.

python scripts/build_cross_platform.py --platform Windows

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ 构建成功！
    echo ========================================
    echo.
    echo 📦 输出位置: dist\
    echo.
    echo 应用包已准备就绪，可以分发给他人使用。
    echo.
) else (
    echo.
    echo ❌ 构建失败！
    echo.
)

pause
