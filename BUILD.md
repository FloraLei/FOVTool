# FOVTools 跨平台构建指南

## 📦 快速开始

### Windows
```batch
# 方法1：直接运行 (已安装Python)
python build_cross_platform.py

# 方法2：使用批处理脚本
build_windows.bat
```

### macOS
```bash
# 安装依赖
brew install python3
python3 -m pip install -r requirements.txt

# 构建
python3 build_cross_platform.py
```

### Linux (Ubuntu 22.04/24.04)
```bash
# 安装依赖
sudo apt-get update
sudo apt-get install python3-pip python3-dev
pip3 install -r requirements.txt

# 构建
python3 build_cross_platform.py
```

## 🔨 构建脚本说明

### `build_cross_platform.py`

**功能**：为当前平台生成可执行文件和压缩包

**使用方法**：

```bash
# 构建当前平台
python build_cross_platform.py

# 指定平台构建 (必须在该平台上运行)
python build_cross_platform.py --platform Windows
python build_cross_platform.py --platform macOS
python build_cross_platform.py --platform Linux
```

**输出**：
- `dist/FOVTools_Windows_v1.0.0_*.zip` - Windows压缩包
- `dist/FOVTools_macOS_v1.0.0_*.tar.gz` - macOS压缩包
- `dist/FOVTools_Linux_v1.0.0_*.tar.gz` - Linux压缩包

### 生成的包结构

#### Windows
```
FOVTools_Windows_v1.0.0_*.zip
├── Run_FOVTools.bat          # 启动脚本
├── app/                       # 应用程序文件
│   ├── FOVTools.exe
│   ├── PyQt5/
│   ├── numpy/
│   └── ...
├── README.md
├── LICENSE
└── fov_tools_session.json
```

#### macOS
```
FOVTools_macOS_v1.0.0_*.tar.gz
├── FOVTools.app/               # macOS应用包
│   ├── Contents/
│   │   ├── MacOS/
│   │   ├── Frameworks/
│   │   └── Info.plist
├── README.md
├── LICENSE
└── fov_tools_session.json
```

#### Linux
```
FOVTools_Linux_v1.0.0_*.tar.gz
├── run_FOVTools.sh             # 启动脚本
├── bin/                        # 可执行文件
│   └── FOVTools
├── lib/                        # 库文件
├── README.md
├── LICENSE
└── fov_tools_session.json
```

## 📋 系统要求

### Windows
- Windows 7 SP1 或更新版本
- 无需安装Python

### macOS
- macOS 10.13 或更新版本
- Intel 或 Apple Silicon

### Linux
- Ubuntu 22.04 LTS 或 24.04 LTS
- Debian 11/12
- 其他基于Linux的系统 (需要相同的库)

## 🚀 运行可执行程序

### Windows
解压 `FOVTools_Windows_*.zip`，双击 `Run_FOVTools.bat` 或 `app/FOVTools.exe`

### macOS
解压 `.tar.gz` 文件后，双击 `FOVTools.app` 或在终端运行：
```bash
./FOVTools.app/Contents/MacOS/FOVTools
```

### Linux
解压 `.tar.gz` 文件后，运行：
```bash
./run_FOVTools.sh
# 或直接运行
./bin/FOVTools
```

## 🔄 自动化构建 (使用GitHub Actions)

该项目配置了GitHub Actions工作流，可在以下情况自动构建：

1. **推送到 master/main 分支**
2. **创建标签** (如 v1.0.0)
3. **手动触发** (Workflow dispatch)

### 构建流程

1. GitHub Actions 在三个平台上并行构建：
   - Windows (windows-latest)
   - macOS (macos-latest)
   - Linux Ubuntu 22.04 (ubuntu-22.04)
   - Linux Ubuntu 24.04 (ubuntu-24.04)

2. 所有构建完成后，生成发布版本 (如果是标签推送)

3. 可从 Actions 标签页面下载构建产物

### 查看构建状态
访问：`https://github.com/YOUR_USERNAME/FOVTools/actions`

## 📥 本地构建要求

### 所有平台通用
```bash
pip install -r requirements.txt
```

### Windows 额外要求
- Visual C++ Build Tools (用于编译部分扩展)

### macOS 额外要求
```bash
xcode-select --install
brew install openblas
```

### Linux 额外要求
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev libopenblas-dev

# Fedora
sudo dnf install python3-devel openblas-devel
```

## 🛠️ 开发和贡献

### 本地开发运行
```bash
# 安装开发依赖
pip install -r requirements.txt

# 直接运行源代码
python fov_tools.py
```

### 构建新版本发布

1. 更新版本号
   ```python
   # 在 build_cross_platform.py 中修改
   PROJECT_VERSION = "1.0.1"
   ```

2. 提交更改
   ```bash
   git add .
   git commit -m "Release v1.0.1"
   ```

3. 创建标签
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

4. 等待GitHub Actions构建完成

5. 在 Releases 页面下载构建的压缩包

## 📊 构建配置详情

### PyInstaller 配置
- **模式**：单文件或单目录 (dir模式以减少启动时间)
- **压缩**：启用 UPX 压缩
- **控制台**：禁用 (GUI应用)
- **依赖**：自动收集 numpy, matplotlib, PyQt5 及其所有子模块

### 包含的依赖
- PyQt5 (>= 5.15) - GUI框架
- numpy (>= 1.21) - 数值计算
- matplotlib (>= 3.5) - 2D/3D绘图
- pymupdf (>= 1.21) - PDF处理
- Pillow - 图像处理

## 🐛 常见问题

### Q: 在Linux上运行报错 "libGL.so.1 not found"
A: 安装缺失的OpenGL库：
```bash
sudo apt-get install libgl1-mesa-glx
```

### Q: macOS显示"无法验证开发者"
A: 右键点击应用 -> 打开，或在终端运行：
```bash
xattr -d com.apple.quarantine FOVTools.app
```

### Q: Windows Defender 报警
A: 这是误报。可以向Microsoft报告或在Windows Defender中添加排除。

### Q: 如何在不同架构的Windows上构建
A: PyInstaller 会自动为当前系统架构构建 (x86/x64/ARM64)

## 📝 构建日志

所有构建都会生成详细日志，存放在：
- `build/` - 构建中间文件
- `.spec` 文件 - PyInstaller配置

## 🔐 代码签名 (可选)

### macOS代码签名
```bash
codesign -s - dist/FOVTools.app
```

### Windows代码签名
需要 Authenticode 证书，在 `build_cross_platform.py` 中配置

## 📦 打包大小参考

- Windows: ~150-200 MB
- macOS: ~180-220 MB  
- Linux: ~160-200 MB

## 🚀 性能优化提示

- PyInstaller 一次可执行文件启动时间通常为 2-5 秒
- 首次运行后会建立缓存，后续启动更快
- 可通过 `UPX` 压缩进一步减小包大小 (~30-50%)

---

**最后更新**: 2024年
**维护者**: FOVTools 团队
