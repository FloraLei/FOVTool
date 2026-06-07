# 💻 FOVTools 构建工具 - CLI 命令行使用指南

> 💡 **适合对象**：
> - 希望更多控制和自定义的开发者
> - 需要在 CI/CD 流程中集成的用户
> - 习惯使用命令行的用户

## 📌 概述

本指南展示如何通过命令行构建 FOVTools，提供完整的控制和灵活性。

---

## 🎯 快速开始

### 1. 安装依赖

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 构建当前平台

```bash
# 会自动检测并为当前平台构建
python scripts/build_cross_platform.py
```

### 3. 查看输出

所有构建包都在 `dist/` 文件夹中：

```
dist/
├── FOVTools_Windows_v1.0.0_*.zip
├── FOVTools_macOS_v1.0.0_*.tar.gz
└── FOVTools_Linux_v1.0.0_*.tar.gz
```

---

## 📋 完整使用指南

### 基本命令

#### 1. 激活虚拟环境

**Windows:**
```powershell
# PowerShell
.venv\Scripts\Activate.ps1

# 或 CMD
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

检查是否已安装：
```bash
pip list | grep PyInstaller
```

#### 3. 构建应用

**当前平台（自动检测）:**
```bash
python scripts/build_cross_platform.py
```

**指定特定平台:**
```bash
# Windows
python scripts/build_cross_platform.py --platform Windows

# macOS
python scripts/build_cross_platform.py --platform macOS

# Linux (Ubuntu 22.04/24.04)
python scripts/build_cross_platform.py --platform Linux
```

#### 4. 查看构建日志

完整的构建日志会实时打印到终端。成功时的输出示例：

```
[INFO] ============================================================
[INFO] FOVTools Cross-Platform Build
[INFO] Current Platform: Windows (AMD64)
[INFO] Version: 1.0.0
[INFO] ============================================================

[INFO] Cleaning previous builds...
[INFO] Clean complete
[INFO] Building for Windows
[INFO] ============================================================
[INFO] Generating PyInstaller spec for Windows...
[INFO] Spec file generated: FOVTools_Windows.spec
[INFO] Building Windows executable...
[INFO] Packaging Windows build...
[INFO] Package created: dist/FOVTools_Windows_v1.0.0_20260607_120000.zip

[SUCCESS] ✓ Build Summary
[SUCCESS] Windows    : ✓ SUCCESS
[INFO] Packages location: ...dist
```

---

## 🔧 高级用法

### 1. 使用 Makefile

项目已配置 Makefile，可以快速执行常见任务：

```bash
# 安装依赖
make install

# 构建（当前平台）
make build

# 构建 Windows
make build-windows

# 构建 macOS
make build-macos

# 构建 Linux
make build-linux

# 清理构建产物
make clean

# 运行应用（开发模式）
make run

# 开发模式（监视文件变化）
make dev

# 验证环境
make check
```

### 2. 脚本文件夹内的构建脚本

`scripts/` 文件夹包含平台特定的构建脚本：

**Windows (从项目根目录):**
```powershell
./scripts/build_windows.bat
```

**macOS (从项目根目录):**
```bash
./scripts/build_macos.sh
```

**Linux (从项目根目录):**
```bash
./scripts/build_linux.sh
```

### 3. 根目录的便利脚本

为了向后兼容，根目录也有对应的脚本：

```bash
# Windows
./build_windows.bat

# macOS / Linux
./build_macos.sh
./build_linux.sh
```

---

## 📁 文件结构

```
FOVTools/
├── 🖱️ GUI 双击使用
│   ├── Build_FOVTools.bat          (Windows)
│   ├── Build_FOVTools.command      (macOS)
│   └── Build_FOVTools.sh           (Linux)
│
├── 💻 命令行脚本
│   ├── build_windows.bat           (根目录便利脚本)
│   ├── build_macos.sh              (根目录便利脚本)
│   ├── build_linux.sh              (根目录便利脚本)
│   └── scripts/                    (完整实现)
│       ├── build_cross_platform.py (核心构建脚本)
│       ├── build_windows.bat
│       ├── build_macos.sh
│       ├── build_linux.sh
│       └── README.md
│
├── 📚 文档
│   ├── README_GUI.md               (GUI 双击指南)
│   ├── README_CLI.md               (本文件)
│   ├── BUILD.md                    (详细构建文档)
│   ├── QUICK_BUILD.md              (快速参考)
│   └── scripts/README.md           (脚本说明)
│
├── 🔧 配置
│   ├── Makefile                    (构建任务)
│   ├── requirements.txt            (Python 依赖)
│   ├── FOVTools.spec               (PyInstaller 配置)
│   └── .gitignore
│
└── 📦 输出
    └── dist/                       (所有构建包)
        ├── FOVTools_Windows_v1.0.0_*.zip
        ├── FOVTools_macOS_v1.0.0_*.tar.gz
        └── FOVTools_Linux_v1.0.0_*.tar.gz
```

---

## 🛠️ 环境配置详解

### 虚拟环境（venv）

为了避免与系统 Python 包冲突，使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# 验证激活成功（命令行前缀会显示 (.venv)）
# (.venv) $ 

# 停止使用虚拟环境
deactivate
```

### 依赖安装

```bash
# 安装 requirements.txt 中的所有依赖
pip install -r requirements.txt

# 查看已安装的包
pip list

# 检查特定包
pip show PyInstaller

# 升级特定包
pip install --upgrade PyInstaller
```

### 系统依赖（Linux 用户特别注意）

构建过程需要图形库，某些 Linux 系统需要手动安装：

**Ubuntu / Debian:**
```bash
sudo apt-get update
sudo apt-get install libgl1 libxkbcommon-x11-0 libdbus-1-3
```

**Fedora / RHEL:**
```bash
sudo dnf install libglvnd libxkbcommon libdbus
```

---

## 🔍 常见问题

### Q: 如何清除缓存并重新构建？

```bash
# 清除构建产物
make clean

# 或手动删除
rm -rf build/ dist/ *.spec

# 重新构建
python scripts/build_cross_platform.py
```

### Q: 如何只构建，不打包成压缩文件？

编辑 `scripts/build_cross_platform.py`，注释掉 `package_build()` 的调用。输出会在 `dist/FOVTools/` 中。

### Q: 构建失败怎么办？

1. **检查依赖**：
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **查看详细错误**：
   - 错误信息通常会显示在终端
   - 保存输出到文件：`python scripts/build_cross_platform.py > build.log 2>&1`

3. **清除缓存重试**：
   ```bash
   make clean
   python scripts/build_cross_platform.py
   ```

### Q: 如何为不同平台构建？

```bash
# 在 Windows 上只能为 Windows 构建
python scripts/build_cross_platform.py --platform Windows

# 在 macOS 上只能为 macOS 构建
python scripts/build_cross_platform.py --platform macOS

# 在 Linux 上只能为 Linux 构建
python scripts/build_cross_platform.py --platform Linux
```

要为多平台构建，需要在对应的操作系统上运行。

### Q: 如何加快构建速度？

1. **第一次构建最慢**（需要编译依赖）
2. **后续构建快得多**（已缓存）
3. **避免清除虚拟环境**（除非有问题）

### Q: 如何在 CI/CD 中使用？

参考 `.github/workflows/build.yml` 的 GitHub Actions 配置：

```yaml
- name: Build FOVTools
  run: python scripts/build_cross_platform.py --platform ${{ matrix.platform }}
```

---

## 📊 构建时间估算

| 步骤 | 首次 | 后续 |
|------|------|------|
| 虚拟环境创建 | 1-2 分钟 | - |
| 依赖安装 | 5-10 分钟 | - |
| PyInstaller 构建 | 5-10 分钟 | 3-5 分钟 |
| 打包 | 1-2 分钟 | 1-2 分钟 |
| **总计** | **10-15 分钟** | **5-10 分钟** |

---

## 🔐 安全与最佳实践

1. **不要删除虚拟环境**（`.venv` 文件夹）
2. **不要在虚拟环境外运行构建**
3. **定期更新依赖**：`pip install --upgrade -r requirements.txt`
4. **版本号管理**：编辑 `scripts/build_cross_platform.py` 中的 `PROJECT_VERSION`

---

## 📞 需要帮助？

| 问题类型 | 查看 |
|---------|------|
| 🖱️ 双击构建有问题 | [GUI 使用指南](README_GUI.md) |
| 📦 构建产物说明 | [快速参考](QUICK_BUILD.md) |
| 🔧 详细技术信息 | [BUILD.md](BUILD.md) |
| 📄 脚本文件说明 | [scripts/README.md](scripts/README.md) |

---

## ✅ 快速参考

```bash
# 完整流程
python -m venv .venv
source .venv/bin/activate    # macOS/Linux: 或 .venv\Scripts\activate (Windows)
pip install -r requirements.txt
python scripts/build_cross_platform.py

# 快速构建（激活后）
python scripts/build_cross_platform.py

# 使用 Makefile
make install
make build

# 只构建 Windows
python scripts/build_cross_platform.py --platform Windows
```

享受构建过程！🚀
