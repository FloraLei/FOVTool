# 📁 Scripts 文件夹 - FOVTools 构建工具

该文件夹包含 FOVTools 的所有构建脚本和工具。

## 📋 文件说明

### 核心构建脚本

| 文件 | 说明 |
|------|------|
| `build_cross_platform.py` | **核心构建脚本** - 生成所有平台的可执行文件（Python） |

### 平台特定脚本

| 文件 | 说明 |
|------|------|
| `build_windows.bat` | Windows 快速构建脚本（批处理） |
| `build_macos.sh` | macOS 快速构建脚本（Shell） |
| `build_linux.sh` | Linux 快速构建脚本（Shell） |

### 使用说明

详细文档位于项目根目录：
- **GUI 双击版本**：[README_GUI.md](../README_GUI.md)
- **CLI 命令行版本**：[README_CLI.md](../README_CLI.md)
- **快速参考**：[QUICK_BUILD.md](../QUICK_BUILD.md)
- **完整文档**：[BUILD.md](../BUILD.md)

## 🚀 快速开始

### 方式1：GUI 双击运行（推荐）

从项目**根目录**找到：

```
📁 FOVTools (根目录)
  ├─ Build_FOVTools.bat       ← Windows: 双击即可
  ├─ Build_FOVTools.command   ← macOS: 双击即可
  ├─ Build_FOVTools.sh        ← Linux: 双击即可
  └─ scripts/                 ← 本文件夹
```

👉 详见：[README_GUI.md](../README_GUI.md)

### 方式2：从根目录调用脚本

```bash
# Windows
build_windows.bat

# macOS / Linux
./build_macos.sh
./build_linux.sh
```

### 方式3：从 scripts 文件夹直接调用

```bash
# Windows
scripts\build_windows.bat

# macOS / Linux
./scripts/build_macos.sh
./scripts/build_linux.sh
```

### 方式4：直接运行 Python 脚本

```bash
# 当前平台（自动检测）
python scripts/build_cross_platform.py

# 指定特定平台
python scripts/build_cross_platform.py --platform Windows
python scripts/build_cross_platform.py --platform macOS
python scripts/build_cross_platform.py --platform Linux
```

👉 详见：[README_CLI.md](../README_CLI.md)

## 📦 输出位置

所有构建的可执行包都会生成在项目根目录的 `dist/` 文件夹中：

```
dist/
├── FOVTools_Windows_v1.0.0_*.zip        (Windows)
├── FOVTools_macOS_v1.0.0_*.tar.gz       (macOS)
└── FOVTools_Linux_v1.0.0_*.tar.gz       (Linux)
```

## 🔧 完整使用流程

### 1. 首次设置

**GUI 方式**（推荐）：双击 `Build_FOVTools.bat` / `.command` / `.sh`，脚本自动处理所有事情。

**CLI 方式**：
```bash
python -m venv .venv
source .venv/bin/activate  # 或 Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 构建

**GUI 方式**：
```bash
# Windows
Build_FOVTools.bat

# macOS
Build_FOVTools.command

# Linux
Build_FOVTools.sh
```

**CLI 方式**：
```bash
# 从根目录
python scripts/build_cross_platform.py

# 或使用便利脚本
./build_windows.bat
./build_macos.sh
./build_linux.sh

# 或从 scripts 文件夹
./scripts/build_windows.bat
./scripts/build_macos.sh
./scripts/build_linux.sh
```

### 3. 验证输出

```bash
ls dist/  # 或在 Windows 上查看 dist 文件夹
```

应该看到 `.zip` (Windows) 或 `.tar.gz` (macOS/Linux) 文件。

## 💡 使用建议

- **首次构建** 可能需要 10-15 分钟（需要下载依赖）
- **后续构建** 通常需要 5-10 分钟（虚拟环境已存在）
- 确保有足够的磁盘空间（至少 2GB）
- 使用稳定的网络连接以避免下载中断
- 不要删除虚拟环境 `.venv` 文件夹（除非遇到问题）

## 🔄 脚本工作流

### build_windows.bat

```
1. 检测 Python 是否已安装
2. 检查虚拟环境是否存在
3. 创建虚拟环境（如需要）
4. 检查 PyInstaller 是否已安装
5. 安装依赖（如需要）
6. 调用 build_cross_platform.py
7. 显示完成状态和输出位置
```

### build_macos.sh & build_linux.sh

```
1. 检测 Python3 是否已安装
2. 检查虚拟环境是否存在
3. 创建虚拟环境（如需要）
4. 检查系统依赖
5. 安装系统包（如需要）
6. 检查 PyInstaller 是否已安装
7. 安装依赖（如需要）
8. 调用 build_cross_platform.py
9. 显示完成状态和输出位置
```

### build_cross_platform.py

```
1. 检测当前平台
2. 清理之前的构建产物
3. 生成 PyInstaller spec 文件
4. 运行 PyInstaller 编译
5. 打包成压缩文件
6. 复制资源文件
7. 显示构建统计
```

## 📝 日志和调试

构建过程中会生成以下临时文件：

- `build/` - PyInstaller 构建中间文件
- `FOVTools_*.spec` - PyInstaller 配置文件
- `dist/` - 最终的可执行包

构建失败时查看这些文件可以帮助诊断问题。

## 🎯 平台特定说明

### Windows (.bat 脚本)
- 使用 `@echo off` 抑制输出
- 自动创建虚拨环境（`.venv`）
- 自动安装依赖
- 生成 `.zip` 压缩包
- 包含 `.exe` 可执行文件和 `Run_FOVTools.bat` 启动脚本
- 输出为 `FOVTools_Windows_v1.0.0_*.zip`

### macOS (.sh 脚本)
- 使用 bash shell
- 自动创建虚拨环境
- 自动安装依赖
- 生成 `.tar.gz` 压缩包
- 包含 `.app` 应用包
- 输出为 `FOVTools_macOS_v1.0.0_*.tar.gz`

### Linux (.sh 脚本)
- 支持 Ubuntu 22.04 和 24.04
- 自动检测 Linux 发行版
- 自动安装系统图形库依赖
- 生成 `.tar.gz` 压缩包
- 包含可执行文件和启动脚本
- 输出为 `FOVTools_Linux_v1.0.0_*.tar.gz`

## ⚙️ 自定义构建

若要自定义构建参数，编辑 `build_cross_platform.py` 中的配置：

```python
PROJECT_NAME = "FOVTools"      # 应用程序名称
PROJECT_VERSION = "1.0.0"      # 版本号
MAIN_SCRIPT = "fov_tools.py"   # 主程序文件
```

## 🔗 相关文件

### 项目根目录

| 文件 | 说明 |
|------|------|
| `Build_FOVTools.bat` | 🖱️ Windows GUI 双击构建脚本 |
| `Build_FOVTools.command` | 🖱️ macOS GUI 双击构建脚本 |
| `Build_FOVTools.sh` | 🖱️ Linux GUI 双击构建脚本 |
| `build_windows.bat` | 💻 Windows 便利脚本 |
| `build_macos.sh` | 💻 macOS 便利脚本 |
| `build_linux.sh` | 💻 Linux 便利脚本 |
| `Makefile` | 📋 统一任务文件（make install/build/clean 等） |
| `requirements.txt` | 📦 Python 依赖列表 |

### 文档

| 文件 | 说明 |
|------|------|
| `README_INDEX.md` | 📚 文档索引（从这里开始！） |
| `README_GUI.md` | 🖱️ GUI 双击使用指南 |
| `README_CLI.md` | 💻 命令行使用指南 |
| `README_RUN.md` | ▶️ 运行应用指南 |
| `QUICK_BUILD.md` | ⚡ 快速参考 |
| `BUILD.md` | 🔧 详细技术文档 |

## 🚨 故障排除

| 问题 | 解决方案 |
|------|---------|
| 脚本无法执行（Linux/macOS） | 运行 `chmod +x Build_FOVTools.sh` |
| Python 未找到 | 安装 Python 3.9+ 并将其添加到 PATH |
| PyInstaller 缺失 | 运行 `pip install -r requirements.txt` |
| 磁盘空间不足 | 清除 `build/` 和 `dist/` 文件夹 |
| 构建中断 | 安全的，下次运行会继续，或 `make clean` 后重试 |

## ✅ 检查清单

构建前确认：

- [ ] Python 3.9+ 已安装
- [ ] 进入项目根目录
- [ ] 有稳定的网络连接
- [ ] 有至少 2GB 的磁盘空间
- [ ] `requirements.txt` 文件完整

## 📞 需要帮助？

- 🖱️ **GUI 双击方式**：[README_GUI.md](../README_GUI.md)
- 💻 **命令行方式**：[README_CLI.md](../README_CLI.md)
- ⚡ **快速参考**：[QUICK_BUILD.md](../QUICK_BUILD.md)
- 🔧 **技术细节**：[BUILD.md](../BUILD.md)
- 📚 **文档索引**：[README_INDEX.md](../README_INDEX.md)

---

**开心构建！🚀**
MAIN_SCRIPT = "fov_tools.py"   # 主脚本
```

## 🆘 常见问题

### ❓ 脚本无法执行
**解决**：确保脚本有执行权限
```bash
chmod +x scripts/build_*.sh    # Linux/macOS
```

### ❓ PyInstaller 未找到
**解决**：安装依赖
```bash
pip install -r requirements.txt
```

### ❓ 磁盘空间不足
**解决**：清理旧的构建
```bash
# Windows
rmdir /s build dist

# Linux/macOS
rm -rf build dist
```

## 📞 更多帮助

详细文档请参考：
- [BUILD.md](../BUILD.md) - 完整构建指南
- [QUICK_BUILD.md](../QUICK_BUILD.md) - 快速开始指南
- [Makefile](../Makefile) - Make 命令参考

---

**所有构建脚本都已集中在 `scripts/` 文件夹中，便于管理和维护。** ✨
