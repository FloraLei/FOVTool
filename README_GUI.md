# 🖱️ FOVTools 构建工具 - GUI双击使用指南

> ⭐ **推荐方式**：直接双击，无需打开终端！

## 📌 概述

本指南适用于以下用户：
- 🪟 **Windows** 用户
- 🍎 **macOS** 用户  
- 🐧 **Linux** 用户（包括 Ubuntu 22.04/24.04）

所有用户都可以通过 **直接双击** 脚本文件来构建 FOVTools 应用程序包。

---

## 🖥️ Windows 用户

### 前提条件

1. **安装 Python 3.9+**
   - 从 [python.org](https://www.python.org/) 下载
   - ⚠️ **重要**：安装时必须勾选 "Add Python to PATH"
   - 验证安装：打开 CMD，输入 `python --version`

### 构建步骤

**第1步**：找到项目根目录中的 `Build_FOVTools.bat` 文件

![image-placeholder]

**第2步**：双击 `Build_FOVTools.bat`

```
┌─────────────────────────────────────┐
│  📁 FOVTools                        │
│    ├─ Build_FOVTools.bat  ←─ 双击   │
│    ├─ fov_tools.py                 │
│    └─ ...                          │
└─────────────────────────────────────┘
```

**第3步**：等待构建完成

- 首次构建需要 10-15 分钟（需要下载依赖）
- 后续构建通常需要 5-10 分钟
- 窗口会显示构建进度

**第4步**：查看输出

构建完成后，应用包将在 `dist/` 文件夹中：

```
dist/
└── FOVTools_Windows_v1.0.0_20260607_120000.zip
```

✅ **构建成功！** 可以将 `.zip` 文件分发给他人使用。

### 常见问题

**Q: 双击没有反应？**
- A: 检查 Python 是否正确安装。打开 CMD，输入 `python --version`

**Q: 出现 "找不到 Python" 错误？**
- A: 重新安装 Python，**必须** 勾选 "Add Python to PATH"

**Q: 构建过程中出现错误？**
- A: 检查 `requirements.txt` 是否完整，或尝试手动安装依赖：
  ```bash
  python -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```

---

## 🍎 macOS 用户

### 前提条件

1. **安装 Python 3.9+**
   - 使用 Homebrew（推荐）：
     ```bash
     brew install python3
     ```
   - 或从 [python.org](https://www.python.org/) 下载
   - 验证安装：打开终端，输入 `python3 --version`

### 构建步骤

**第1步**：找到项目根目录中的 `Build_FOVTools.command` 文件

**第2步**：双击 `Build_FOVTools.command`

```
┌─────────────────────────────────────┐
│  📁 FOVTools                        │
│    ├─ Build_FOVTools.command ← 双击 │
│    ├─ fov_tools.py                 │
│    └─ ...                          │
└─────────────────────────────────────┘
```

> 💡 **第一次双击可能需要允许权限**：
> - 右键点击 `Build_FOVTools.command`
> - 选择"打开"
> - 点击"打开"确认

**第3步**：等待构建完成

- 首次构建需要 10-15 分钟
- 后续构建通常需要 5-10 分钟
- 终端窗口会显示进度

**第4步**：查看输出

构建完成后，应用包将在 `dist/` 文件夹中：

```
dist/
└── FOVTools_macOS_v1.0.0_20260607_120000.tar.gz
```

✅ **构建成功！** 可以将 `.tar.gz` 文件分发给他人使用。

### 常见问题

**Q: 双击显示 "无法打开"？**
- A: 需要赋予执行权限：
  ```bash
  chmod +x Build_FOVTools.command
  ```

**Q: 显示 "无法验证开发者" 警告？**
- A: 这是 macOS 安全功能。右键选择"打开"，然后点击"打开"即可。

**Q: Python 未找到？**
- A: 检查 Python 是否安装：`python3 --version`

---

## 🐧 Linux 用户

### 前提条件

1. **安装 Python 3.9+ 和依赖**

   **Ubuntu / Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-venv
   sudo apt-get install libgl1 libxkbcommon-x11-0 libdbus-1-3
   ```

   **Fedora / RHEL / CentOS:**
   ```bash
   sudo dnf install python3 python3-pip
   sudo dnf install libglvnd libxkbcommon libdbus
   ```

   **Arch Linux:**
   ```bash
   sudo pacman -S python python-pip
   sudo pacman -S libglvnd libxkbcommon dbus
   ```

2. 验证安装：`python3 --version`

### 构建步骤

**第1步**：打开文件管理器，进入项目根目录

**第2步**：找到 `Build_FOVTools.sh` 文件

```
┌─────────────────────────────────────┐
│  📁 FOVTools                        │
│    ├─ Build_FOVTools.sh  ← 双击    │
│    ├─ fov_tools.py                 │
│    └─ ...                          │
└─────────────────────────────────────┘
```

**第3步**：双击 `Build_FOVTools.sh`

> 💡 **如果文件管理器询问是否执行**，选择"在终端中执行"或"执行"

**第4步**：等待构建完成

- 首次构建需要 10-15 分钟
- 可能会要求输入密码（用于安装系统依赖）
- 终端会显示进度

**第5步**：查看输出

构建完成后，应用包将在 `dist/` 文件夹中：

```
dist/
└── FOVTools_Linux_v1.0.0_20260607_120000.tar.gz
```

✅ **构建成功！** 可以将 `.tar.gz` 文件分发给他人使用。

### 常见问题

**Q: 双击没有反应？**
- A: 赋予执行权限：
  ```bash
  chmod +x Build_FOVTools.sh
  ```

**Q: 文件管理器无法执行？**
- A: 在终端中运行：
  ```bash
  bash Build_FOVTools.sh
  ```

**Q: 提示 "Python 未找到"？**
- A: 按提示安装 Python3 和依赖

**Q: 要求输入密码？**
- A: 这是正常的，需要安装系统图形库。输入你的 Linux 账户密码即可。

---

## 📦 输出说明

### Windows
- **格式**：`.zip` 压缩包
- **包含**：`FOVTools.exe` 可执行文件 + 依赖库
- **使用**：解压后运行 `FOVTools.exe` 或点击 `Run_FOVTools.bat`

### macOS
- **格式**：`.tar.gz` 压缩包
- **包含**：`FOVTools.app` 应用包 + 依赖
- **使用**：解压后双击 `run_FOVTools.sh` 或直接运行二进制文件

### Linux
- **格式**：`.tar.gz` 压缩包
- **包含**：`FOVTools` 可执行文件 + 库
- **使用**：解压后运行 `./run_FOVTools.sh` 或 `./bin/FOVTools`

---

## ✅ 检查清单

- [ ] Python 3.9+ 已安装
- [ ] Python 已添加到系统 PATH（Windows）
- [ ] 进入项目根目录
- [ ] 找到对应平台的 `Build_FOVTools.*` 文件
- [ ] 双击该文件
- [ ] 等待构建完成
- [ ] 在 `dist/` 文件夹中找到输出包

---

## 🚀 后续步骤

### 分发应用

构建完成后，将 `dist/` 中的压缩包分发给其他用户：

1. **Windows**: 用户下载 `.zip`，解压，运行 `FOVTools.exe`
2. **macOS**: 用户下载 `.tar.gz`，解压，双击 `run_FOVTools.sh`
3. **Linux**: 用户下载 `.tar.gz`，解压，运行 `./run_FOVTools.sh`

### 再次构建

无需重新安装依赖，直接双击 `Build_FOVTools.*` 即可快速重新构建。

---

## 💡 提示

- 第一次构建会较慢（需要下载和编译依赖）
- 后续构建会快得多（虚拟环境已存在）
- 构建过程中可以安全中断（按 Ctrl+C），不会损害项目
- 所有输出都保存在 `dist/` 文件夹，不会影响项目源代码

---

## 📞 需要帮助？

如果遇到问题，请查看对应平台的"常见问题"部分，或查看 [CLI 命令行使用指南](README_CLI.md)。
