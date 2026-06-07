#!/bin/bash

# Build script for FOVTools - Linux GUI Version
# 双击直接使用版本

cd "$(dirname "$0")"

echo ""
echo "========================================"
echo "  FOVTools 构建工具 - Linux"
echo "========================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "❌ 错误：未检测到 Python 3"
    echo ""
    echo "请使用包管理器安装 Python 3:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt-get install python3 python3-pip python3-venv"
    echo ""
    echo "Fedora/RHEL/CentOS:"
    echo "  sudo dnf install python3 python3-pip"
    echo ""
    echo "Arch Linux:"
    echo "  sudo pacman -S python"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "[信息] 正在创建虚拟环境..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 虚拟环境创建失败"
        echo ""
        echo "按任意键退出..."
        read -n 1
        exit 1
    fi
fi

# Activate venv
source .venv/bin/activate

# Check for system dependencies (graphics libraries)
echo "[信息] 检查系统依赖..."
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    dpkg -l | grep -i libgl1 > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "[信息] 安装图形库依赖..."
        sudo apt-get update
        sudo apt-get install -y libgl1 libxkbcommon-x11-0 libdbus-1-3
    fi
elif [ -f /etc/redhat-release ]; then
    # Fedora/RHEL/CentOS
    rpm -q libglvnd > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "[信息] 安装图形库依赖..."
        sudo dnf install -y libglvnd libxkbcommon libdbus
    fi
fi

# Check and install Python dependencies
echo "[信息] 检查 Python 依赖..."
pip list | grep -i "PyInstaller" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[信息] 安装依赖... （首次可能需要 5-10 分钟）"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 依赖安装失败"
        echo ""
        echo "按任意键退出..."
        read -n 1
        exit 1
    fi
fi

echo ""
echo "[信息] 开始构建过程..."
echo "[信息] 这可能需要 5-15 分钟，请稍候..."
echo ""

python3 scripts/build_cross_platform.py --platform Linux

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  ✅ 构建成功！"
    echo "========================================"
    echo ""
    echo "📦 输出位置: dist/"
    echo ""
    echo "应用包已准备就绪，可以分发给他人使用。"
    echo ""
else
    echo ""
    echo "❌ 构建失败！"
    echo ""
fi

echo "按任意键退出..."
read -n 1
