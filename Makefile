.PHONY: help build clean install deps build-windows build-macos build-linux build-all run dev

PROJECT_NAME := FOVTools
PYTHON := python3
PIP := pip3
DIST_DIR := dist
BUILD_DIR := build

# 默认目标
help:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║  $(PROJECT_NAME) - Build System                           ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "  make help           - Show this help message"
	@echo "  make install        - Install dependencies"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make build          - Build for current platform"
	@echo "  make build-windows  - Build Windows executable"
	@echo "  make build-macos    - Build macOS application"
	@echo "  make build-linux    - Build Linux executable"
	@echo "  make build-all      - Build for all platforms (GitHub Actions)"
	@echo "  make run            - Run the application from source"
	@echo "  make dev            - Install in development mode"
	@echo "  make deps           - Show dependency information"
	@echo ""

# 安装依赖
install:
	@echo "[INFO] Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "[SUCCESS] Dependencies installed"

# 开发模式安装
dev: install
	@echo "[INFO] Setting up development environment..."
	$(PIP) install pytest pytest-cov black flake8
	@echo "[SUCCESS] Development environment ready"

# 显示依赖信息
deps:
	@echo "Required packages:"
	@$(PYTHON) -m pip show PyQt5 numpy matplotlib pymupdf PyInstaller || true

# 清理构建文件
clean:
	@echo "[INFO] Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(DIST_DIR) __pycache__ *.pyc *.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "[SUCCESS] Clean complete"

# 当前平台构建
build: install
	@echo "[INFO] Building for current platform..."
	@$(PYTHON) build_cross_platform.py
	@echo "[SUCCESS] Build complete"

# Windows 构建
build-windows: install
	@echo "[INFO] Building Windows executable..."
	@$(PYTHON) build_cross_platform.py --platform Windows
	@echo "[SUCCESS] Windows build complete"

# macOS 构建
build-macos: install
	@echo "[INFO] Building macOS application..."
	@$(PYTHON) build_cross_platform.py --platform macOS
	@echo "[SUCCESS] macOS build complete"

# Linux 构建
build-linux: install
	@echo "[INFO] Building Linux executable..."
	@$(PYTHON) build_cross_platform.py --platform Linux
	@echo "[SUCCESS] Linux build complete"

# 全平台构建 (仅在有 GitHub Actions 时使用)
build-all: install
	@echo "[WARNING] Build-all is for CI/CD environments"
	@echo "[INFO] Building for current platform only..."
	@$(PYTHON) build_cross_platform.py

# 从源代码直接运行
run:
	@echo "[INFO] Running from source..."
	@$(PYTHON) fov_tools.py

# 快速检查
check:
	@echo "[INFO] Checking Python version..."
	@$(PYTHON) --version
	@echo ""
	@echo "[INFO] Checking installed packages..."
	@$(PYTHON) -m pip list | grep -E "PyQt5|numpy|matplotlib|pymupdf|PyInstaller"
	@echo ""
	@echo "[INFO] Checking main script..."
	@test -f fov_tools.py && echo "✓ fov_tools.py found" || echo "✗ fov_tools.py not found"
	@test -f requirements.txt && echo "✓ requirements.txt found" || echo "✗ requirements.txt not found"
	@test -f build_cross_platform.py && echo "✓ build_cross_platform.py found" || echo "✗ build_cross_platform.py not found"

# 验证
verify: check
	@echo ""
	@echo "[INFO] Verifying build configuration..."
	@$(PYTHON) build_cross_platform.py --help 2>/dev/null || $(PYTHON) -c "import sys; sys.path.insert(0, '.'); import build_cross_platform; print('[SUCCESS] Build system ready')"

# 输出文件位置
dist-info:
	@echo "Distribution files location: $(DIST_DIR)/"
	@ls -lah $(DIST_DIR)/ 2>/dev/null || echo "No distributions built yet. Run 'make build' first."

# 完整重建
rebuild: clean build
	@echo "[SUCCESS] Rebuild complete"

# Windows 特定命令 (如果在Windows上)
ifeq ($(OS),Windows_NT)
PYTHON := python
PIP := pip

build-windows-bat:
	@echo Building Windows batch wrapper...
	@cmd /c build_windows.bat

endif

# 帮助信息
.PHONY: .DEFAULT
.DEFAULT:
	@echo "Target '$@' not found. Run 'make help' for available targets."
