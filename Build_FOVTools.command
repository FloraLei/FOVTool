#!/bin/bash

# Build script for FOVTools - macOS GUI Version
# 双击直接使用版本

cd "$(dirname "$0")"

echo ""
echo "========================================"
echo "  FOVTools 构建工具 - macOS"
echo "========================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "❌ 错误：未检测到 Python 3"
    echo ""
    echo "请通过以下方式之一安装 Python 3:"
    echo ""
    echo "1. 使用 Homebrew:"
    echo "   brew install python3"
    echo ""
    echo "2. 从官网下载:"
    echo "   https://www.python.org/"
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

# Check and install dependencies
echo "[信息] 检查依赖..."
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

python3 scripts/build_cross_platform.py --platform macOS

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
