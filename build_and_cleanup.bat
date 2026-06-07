@echo off
REM FOVTools 一键打包脚本
REM 生成最新 .exe 并清理临时文件

echo.
echo ================================================================
echo FOVTools 一键打包工具
echo ================================================================
echo.

cd /d c:\Fuyue_WorkSpace\FOVTools

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ 错误: 未找到 Python
    echo 请确保 Python 已安装并添加到环境变量
    pause
    exit /b 1
)

echo 正在执行打包脚本...
echo.

REM 运行 Python 脚本
python build_and_cleanup.py

if errorlevel 1 (
    echo.
    echo ✗ 打包失败
    pause
    exit /b 1
) else (
    echo.
    echo ✓ 打包完成！
    echo.
    echo 可执行文件位置: dist\FOV_Tools.exe
    echo.
    pause
    exit /b 0
)
