# 📚 FOVTools 文档索引

> 🎯 **选择你的使用场景，快速找到对应指南**

---

## 🚀 我想要...

### 🖱️ 直接双击运行（最简单）

**我想构建应用：**
- **Windows**: 双击 `Build_FOVTools.bat`
- **macOS**: 双击 `Build_FOVTools.command`
- **Linux**: 双击 `Build_FOVTools.sh`

👉 **详见**：[GUI 构建指南](README_GUI.md)

### 💻 使用命令行（更多控制）

```bash
python scripts/build_cross_platform.py
```

👉 **详见**：[CLI 使用指南](README_CLI.md)

### ▶️ 运行 FOVTools 应用

- **Windows**: 双击 `运行FOVTools.bat`
- **macOS**: 双击 `Run_FOVTools.command`
- **Linux**: 双击 `Run_FOVTools.sh`

👉 **详见**：[应用运行指南](README_RUN.md)

---

## 📖 文档导航

### 🎯 快速参考

| 需求 | 文档 | 说明 |
|------|------|------|
| 快速构建 | [README_GUI.md](README_GUI.md) | 双击直接使用，无需终端 |
| 命令行构建 | [README_CLI.md](README_CLI.md) | 详细的命令行操作指南 |
| 运行应用 | [README_RUN.md](README_RUN.md) | 如何启动和使用应用 |
| 快速参考 | [QUICK_BUILD.md](QUICK_BUILD.md) | 单页快速查阅 |
| 详细技术 | [BUILD.md](BUILD.md) | 深入的技术细节 |
| 脚本说明 | [scripts/README.md](scripts/README.md) | 脚本文件详解 |

### 📁 文件夹结构

```
FOVTools/
│
├─ 📖 文档
│  ├─ 📖_INDEX.md              ← 你在这里！
│  ├─ README_GUI.md            ← 🖱️ GUI 双击指南
│  ├─ README_CLI.md            ← 💻 命令行指南
│  ├─ README_RUN.md            ← ▶️ 运行应用指南
│  ├─ QUICK_BUILD.md           ← ⚡ 快速参考
│  ├─ BUILD.md                 ← 🔧 详细技术文档
│  └─ scripts/README.md        ← 📄 脚本说明
│
├─ 🖱️ GUI 脚本（双击使用）
│  ├─ Build_FOVTools.bat       ← Windows 构建
│  ├─ Build_FOVTools.command   ← macOS 构建
│  ├─ Build_FOVTools.sh        ← Linux 构建
│  ├─ 运行FOVTools.bat         ← Windows 运行
│  ├─ Run_FOVTools.command     ← macOS 运行
│  └─ Run_FOVTools.sh          ← Linux 运行
│
├─ 💻 CLI 脚本（命令行）
│  ├─ build_windows.bat        ← Windows 便利脚本
│  ├─ build_macos.sh           ← macOS 便利脚本
│  ├─ build_linux.sh           ← Linux 便利脚本
│  ├─ scripts/
│  │  ├─ build_cross_platform.py   ← 核心构建脚本
│  │  ├─ build_windows.bat
│  │  ├─ build_macos.sh
│  │  └─ build_linux.sh
│  └─ Makefile                 ← 统一任务文件
│
├─ 🔧 配置文件
│  ├─ requirements.txt         ← Python 依赖
│  ├─ .venv/                   ← 虚拟环境（自动创建）
│  └─ ...
│
└─ 📦 输出
   └─ dist/                    ← 构建输出目录
      ├─ FOVTools_Windows_v1.0.0_*.zip
      ├─ FOVTools_macOS_v1.0.0_*.tar.gz
      └─ FOVTools_Linux_v1.0.0_*.tar.gz
```

---

## ✨ 按用户类型查找

### 👨‍💻 开发者 / 高级用户

你可能需要：

1. **理解构建系统**
   - 📖 [BUILD.md](BUILD.md) - 深入技术细节
   - 📄 [scripts/README.md](scripts/README.md) - 脚本文件说明

2. **自定义构建**
   ```bash
   python scripts/build_cross_platform.py --platform Windows
   ```
   - 📖 [README_CLI.md](README_CLI.md) - 完整命令行指南

3. **在 CI/CD 中使用**
   - 查看 `.github/workflows/build.yml` - GitHub Actions 配置
   - 📖 [README_CLI.md](README_CLI.md) - CI/CD 集成部分

### 👤 一般用户 / 非技术用户

你可能只需要：

1. **第一次构建**
   - 按照 [README_GUI.md](README_GUI.md) 操作
   - 只需双击，其他都自动处理

2. **运行应用**
   - 按照 [README_RUN.md](README_RUN.md) 操作
   - 双击 `运行FOVTools.bat` 等

3. **重新构建**
   - 再次双击 `Build_FOVTools.bat` 等
   - 通常比第一次快得多

### 🏢 团队主管 / 项目经理

你可能关心：

1. **构建流程概览**
   - 📖 [QUICK_BUILD.md](QUICK_BUILD.md) - 单页概览

2. **CI/CD 自动化**
   - 查看 `.github/workflows/build.yml`
   - 了解自动构建流程

3. **分发指南**
   - 📖 [README_GUI.md](README_GUI.md) - 最后一章"分发应用"

---

## 🎯 常见任务速查

### 我想...

| 任务 | 快速命令 | 详见 |
|------|---------|------|
| **双击构建应用** | 就是双击啦！ | [GUI](README_GUI.md) |
| **命令行构建** | `python scripts/build_cross_platform.py` | [CLI](README_CLI.md) |
| **快速重建** | `make build` | [Makefile](Makefile) |
| **运行应用** | 双击 `运行FOVTools.bat` | [RUN](README_RUN.md) |
| **查看所有 Make 任务** | `make help` | [Makefile](Makefile) |
| **清除构建缓存** | `make clean` | [CLI](README_CLI.md) |
| **为特定平台构建** | `python scripts/build_cross_platform.py --platform macOS` | [CLI](README_CLI.md) |
| **在 CI/CD 中使用** | 参考 `.github/workflows/build.yml` | [BUILD](BUILD.md) |

---

## 🌐 平台指南

### 🪟 Windows
1. **构建**：[README_GUI.md#-windows-用户](README_GUI.md#-windows-用户)
2. **运行**：[README_RUN.md#-windows-用户](README_RUN.md#-windows-用户)
3. **命令行**：[README_CLI.md](README_CLI.md)

### 🍎 macOS
1. **构建**：[README_GUI.md#-macos-用户](README_GUI.md#-macos-用户)
2. **运行**：[README_RUN.md#-macos-用户](README_RUN.md#-macos-用户)
3. **命令行**：[README_CLI.md](README_CLI.md)

### 🐧 Linux
1. **构建**：[README_GUI.md#-linux-用户](README_GUI.md#-linux-用户)
2. **运行**：[README_RUN.md#-linux-用户](README_RUN.md#-linux-用户)
3. **命令行**：[README_CLI.md](README_CLI.md)

---

## 📊 文档特点对比

| 特性 | GUI 指南 | CLI 指南 | BUILD | QUICK |
|------|---------|---------|-------|-------|
| **易用度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **详细程度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **适合初学者** | ✅ | ⚠️ | ❌ | ✅ |
| **适合开发者** | ⚠️ | ✅ | ✅ | ✅ |
| **参考用** | ✅ | ✅ | ✅ | ✅ |
| **可打印** | ⚠️ | ✅ | ✅ | ✅ |

---

## 💡 学习路径建议

### 第一次使用？

1. **5 分钟快速了解**：这个文件
2. **30 分钟全面学习**：[README_GUI.md](README_GUI.md)
3. **实际操作**：按照指南步骤操作
4. **遇到问题**：查看对应文档的"常见问题"部分

### 需要自定义？

1. **了解结构**：[scripts/README.md](scripts/README.md)
2. **学习命令**：[README_CLI.md](README_CLI.md)
3. **深入研究**：[BUILD.md](BUILD.md)
4. **查看代码**：`scripts/build_cross_platform.py`

### 想要自动化？

1. **理解 Makefile**：[Makefile](Makefile)
2. **学习 CI/CD**：`.github/workflows/build.yml`
3. **阅读相关部分**：[BUILD.md](BUILD.md) 的 CI/CD 章节
4. **集成到你的流程**：修改工作流文件

---

## ❓ 常见问题速查

| 问题 | 答案位置 |
|------|---------|
| 如何双击构建？ | [GUI 指南](README_GUI.md) |
| 命令行怎么用？ | [CLI 指南](README_CLI.md) |
| 构建失败了？ | [BUILD.md - 故障排除](BUILD.md) |
| Python 没安装？ | [GUI 指南 - 常见问题](README_GUI.md#常见问题) |
| 如何分发应用？ | [GUI 指南 - 后续步骤](README_GUI.md#-后续步骤) |
| Makefile 怎么用？ | [CLI 指南 - 使用 Makefile](README_CLI.md#1-使用-makefile) |
| 虚拟环境是什么？ | [CLI 指南 - 虚拟环境](README_CLI.md#虚拟环境venv) |
| 要装系统包吗？ | [CLI 指南 - 系统依赖](README_CLI.md#系统依赖linux-用户特别注意) |

---

## 🔗 快速链接

### 📖 文档
- [README_GUI.md](README_GUI.md) - 🖱️ GUI 双击指南
- [README_CLI.md](README_CLI.md) - 💻 命令行指南  
- [README_RUN.md](README_RUN.md) - ▶️ 运行应用指南
- [QUICK_BUILD.md](QUICK_BUILD.md) - ⚡ 快速参考
- [BUILD.md](BUILD.md) - 🔧 详细技术文档
- [scripts/README.md](scripts/README.md) - 📄 脚本说明

### 🔧 文件
- [Makefile](Makefile) - 统一任务文件
- [requirements.txt](requirements.txt) - Python 依赖
- [.github/workflows/build.yml](.github/workflows/build.yml) - CI/CD 配置

### 📝 脚本
- **GUI 脚本**
  - [Build_FOVTools.bat](Build_FOVTools.bat)
  - [Build_FOVTools.command](Build_FOVTools.command)
  - [Build_FOVTools.sh](Build_FOVTools.sh)

- **CLI 脚本**
  - [build_windows.bat](build_windows.bat)
  - [build_macos.sh](build_macos.sh)
  - [build_linux.sh](build_linux.sh)
  - [scripts/build_cross_platform.py](scripts/build_cross_platform.py)

---

## 🎓 学习资源

### 入门级
- ✅ [README_GUI.md](README_GUI.md) - 最简单的方式
- ✅ [QUICK_BUILD.md](QUICK_BUILD.md) - 快速查阅

### 中级
- 📖 [README_CLI.md](README_CLI.md) - 命令行深入
- 📖 [scripts/README.md](scripts/README.md) - 脚本理解

### 高级
- 🔧 [BUILD.md](BUILD.md) - 技术细节
- 🔧 [Makefile](Makefile) - 任务自动化
- 🔧 `.github/workflows/build.yml` - CI/CD 流程

---

## ✅ 检查清单

使用前，确保你：

- [ ] 理解 GUI 和 CLI 的区别
- [ ] 知道你的操作系统（Windows/macOS/Linux）
- [ ] 安装了 Python 3.9+
- [ ] 有项目访问权限

---

## 🚀 开始使用

### 🖱️ 最简单的方式（推荐新手）
双击对应的 `Build_FOVTools.*` 文件 → 等待完成

👉 **[进入 GUI 指南](README_GUI.md)**

### 💻 更多控制（推荐开发者）
运行 `python scripts/build_cross_platform.py`

👉 **[进入 CLI 指南](README_CLI.md)**

### ⚡ 快速查阅（推荐查询）
寻找单个命令或快速参考

👉 **[进入快速参考](QUICK_BUILD.md)**

---

**需要帮助？**
- 查看你的操作系统对应的文档
- 阅读"常见问题"部分
- 查看 [BUILD.md](BUILD.md) 的故障排除部分

祝你构建顺利！🎉
