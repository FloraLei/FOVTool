#!/bin/bash

# Run FOVTools - macOS GUI Version
# 双击直接运行版本

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo ""
    echo "❌ 错误：未找到虚拟环境"
    echo ""
    echo "首次使用需要安装依赖，请运行："
    echo ""
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    echo "或者双击 Build_FOVTools.command 自动构建"
    echo ""
    echo "按任意键退出..."
    read -n 1
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Launch FOVTools
python3 fov_tools.py &

# Exit (allow the app to run in background)
exit 0
