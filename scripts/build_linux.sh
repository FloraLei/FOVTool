#!/bin/bash

# Build script for Linux
# FOVTools Cross-Platform Build

echo ""
echo "========================================"
echo "  FOVTools Build Script - Linux"
echo "========================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root is the parent directory
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
    OS_VERSION=$VERSION_ID
else
    OS_NAME="Unknown Linux"
    OS_VERSION="Unknown"
fi

echo "[INFO] Detected: $OS_NAME $OS_VERSION"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-dev"
    echo "  Fedora: sudo dnf install python3 python3-pip python3-devel"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

echo "[INFO] Python version:"
python3 --version

# Check for required system dependencies
echo "[INFO] Checking system dependencies..."

# Check for development tools
if [[ "$OS_NAME" == *"Ubuntu"* ]] || [[ "$OS_NAME" == *"Debian"* ]]; then
    echo "[INFO] Installing Ubuntu/Debian dependencies..."
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-dev
    
    # Optional: Install additional graphics libraries
    sudo apt-get install -y libgl1-mesa-glx libxkbcommon-x11-0
    
elif [[ "$OS_NAME" == *"Fedora"* ]]; then
    echo "[INFO] Installing Fedora dependencies..."
    sudo dnf install -y python3 python3-pip python3-devel
    
elif [[ "$OS_NAME" == *"Arch"* ]]; then
    echo "[INFO] Installing Arch Linux dependencies..."
    sudo pacman -S --noconfirm python python-pip base-devel
fi

echo "[INFO] Checking Python packages..."
if ! python3 -m pip show PyInstaller > /dev/null; then
    echo "[INFO] Installing requirements..."
    python3 -m pip install --upgrade pip setuptools wheel
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install requirements"
        exit 1
    fi
fi

echo ""
echo "[INFO] Starting build process..."
echo ""

# Detect if this is Ubuntu 22.04 or 24.04
if [ "$OS_VERSION" == "22.04" ]; then
    PLATFORM="Linux-Ubuntu22.04"
elif [ "$OS_VERSION" == "24.04" ]; then
    PLATFORM="Linux-Ubuntu24.04"
else
    PLATFORM="Linux"
fi

python3 scripts/build_cross_platform.py --platform $PLATFORM

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  Build completed successfully!"
    echo "========================================"
    echo ""
    echo "Output location: dist/"
    echo ""
    echo "To run the application:"
    echo "  cd dist/FOVTools_Linux_*/
    echo "  ./run_FOVTools.sh"
    echo ""
else
    echo ""
    echo "========================================"
    echo "  Build failed!"
    echo "========================================"
    echo ""
    exit 1
fi
