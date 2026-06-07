# 🚀 FOVTools 快速构建指南

## 一键构建

### Windows
```batch
双击运行: build_windows.bat
```

### macOS
```bash
chmod +x build_macos.sh
./build_macos.sh
```

### Linux (Ubuntu 22.04 / 24.04)
```bash
chmod +x build_linux.sh
./build_linux.sh
```

## 📦 输出文件

构建完成后，在 `dist/` 目录找到：

| 平台 | 文件名格式 | 说明 |
|------|----------|------|
| Windows | `FOVTools_Windows_v*.zip` | Windows可执行包 |
| macOS | `FOVTools_macOS_v*.tar.gz` | macOS应用包 |
| Linux | `FOVTools_Linux_v*.tar.gz` | Linux可执行包 |

## 📋 系统要求

### 构建系统
- **Python 3.9+**
- **pip** (Python包管理器)

### 运行系统
- **Windows**: Windows 7+ (无需Python)
- **macOS**: macOS 10.13+ (无需Python)
- **Linux**: Ubuntu 22.04 / 24.04 或等效系统 (无需Python)

## 🔧 完整流程

### 第一次构建

1. **克隆项目**
   ```bash
   git clone https://github.com/FloraLei/FOVTool.git
   cd FOVTools
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行构建脚本**
   - Windows: 双击 `build_windows.bat`
   - macOS: 运行 `./build_macos.sh`
   - Linux: 运行 `./build_linux.sh`

4. **等待构建完成** (通常需要 5-15 分钟)

### 后续构建

只需重复第3步即可。

## 📚 更多详情

详细的构建文档请参考 [BUILD.md](BUILD.md)

### 包括以下内容：
- 详细的系统要求
- 故障排除指南
- GitHub Actions 自动化构建说明
- 代码签名配置
- 性能优化建议

## 🔄 自动化构建 (GitHub Actions)

本项目已配置自动构建工作流，以下情况会自动生成可执行包：

1. 提交到 `master` 或 `main` 分支
2. 创建新的 Git 标签 (e.g., `v1.0.0`)

所有构建可从 GitHub Actions 页面下载。

## ⚙️ 自定义构建

### 指定平台构建
```bash
# 仅为Windows构建
python build_cross_platform.py --platform Windows

# 仅为macOS构建
python build_cross_platform.py --platform macOS

# 仅为Linux构建
python build_cross_platform.py --platform Linux
```

### 修改构建配置

编辑 `build_cross_platform.py`：
```python
PROJECT_NAME = "FOVTools"      # 应用程序名称
PROJECT_VERSION = "1.0.0"      # 版本号
MAIN_SCRIPT = "fov_tools.py"   # 主脚本
```

## 🚨 常见问题

### ❓ 构建报错 "PyInstaller not found"
**解决**: 
```bash
pip install PyInstaller
# 然后重新运行构建脚本
```

### ❓ Linux 上运行报错 "libGL.so.1"
**解决**:
```bash
sudo apt-get install libgl1-mesa-glx
```

### ❓ macOS 显示 "无法验证开发者"
**解决**:
1. 右键点击应用程序，选择 "打开"
2. 或在终端运行:
   ```bash
   xattr -d com.apple.quarantine FOVTools.app
   ```

### ❓ Windows Defender 报警
这是 PyInstaller 生成的应用常见的误报。可以在 Windows Defender 中添加排除。

## 📊 构建时间参考

- **首次构建**: 10-15 分钟 (需要下载和编译依赖)
- **后续构建**: 5-10 分钟

## 💡 建议

- 构建前更新 Python 包: `pip install --upgrade pip setuptools`
- 使用稳定的网络连接以避免下载中断
- 确保有足够的磁盘空间 (至少 2GB 空闲)

## 📝 版本管理

### 发布新版本

1. 更新版本号
   ```python
   # build_cross_platform.py
   PROJECT_VERSION = "1.1.0"
   ```

2. 提交更改
   ```bash
   git add .
   git commit -m "Release v1.1.0"
   ```

3. 创建标签
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

4. GitHub Actions 会自动为所有平台构建并创建发布版本

## 📞 支持

如遇到问题，请：
1. 检查 [BUILD.md](BUILD.md) 中的常见问题
2. 查看 GitHub Issues
3. 提交新的 Issue 附带详细错误信息

---

**快乐构建! 🎉**
