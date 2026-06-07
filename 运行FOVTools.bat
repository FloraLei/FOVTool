@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Check if venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境，请先运行：
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Launch FOVTools using the venv Python
start "" ".venv\Scripts\pythonw.exe" fov_tools.py
