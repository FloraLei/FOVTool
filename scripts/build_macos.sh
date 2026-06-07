#!/bin/bash

# Build script for macOS
# FOVTools Cross-Platform Build

echo ""
echo "========================================"
echo "  FOVTools Build Script - macOS"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root is the parent directory
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/"
    echo "Or use Homebrew: brew install python3"
    exit 1
fi

echo "[INFO] Python version:"
python3 --version

echo "[INFO] Checking dependencies..."
if ! python3 -m pip show PyInstaller > /dev/null; then
    echo "[INFO] Installing requirements..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install requirements"
        exit 1
    fi
fi

echo ""
echo "[INFO] Starting build process..."
echo ""

python3 scripts/build_cross_platform.py --platform macOS

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  Build completed successfully!"
    echo "========================================"
    echo ""
    echo "Output location: dist/"
    echo ""
else
    echo ""
    echo "========================================"
    echo "  Build failed!"
    echo "========================================"
    echo ""
    exit 1
fi
