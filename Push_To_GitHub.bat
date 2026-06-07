@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d c:\Fuyue_WorkSpace\FOVTools

echo.
echo ======================================================================
echo   Push FOVTools to GitHub
echo ======================================================================
echo.

echo [1/4] Checking git status...
git status --short >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not available
    pause
    exit /b 1
)

echo [2/4] Staging all changes...
git add -A
echo.

echo [3/4] Showing recent commits...
git log --oneline -3
echo.

echo [4/4] Pushing to GitHub...
git push -u origin master -v

echo.
echo ======================================================================
echo Success! Changes pushed to GitHub
echo Repository: https://github.com/FloraLei/FOVTool
echo ======================================================================
echo.

pause
