# FOVTools - 车辆视场角分析工具

## 📦 快速开始

### 方式 1️⃣：直接运行可执行文件（推荐）
```bash
# 直接双击运行
dist/FOV_Tools.exe
```

或在命令行执行：
```bash
c:\Fuyue_WorkSpace\FOVTools\dist\FOV_Tools.exe
```

### 方式 2️⃣：使用 Python 运行（需要环境配置）
```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python fov_tools.py
```

---

## 📋 项目结构

```
FOVTools/
├── FOV_Tools.exe                      ← 💰 最新可执行文件 (6.94 MB)
├── fov_tools.py                       ← 源代码（主程序）
├── FOVTools.spec                      ← PyInstaller 打包配置
├── build_and_cleanup.py               ← 一键打包脚本
├── build_and_cleanup.bat              ← Windows 快捷启动脚本
│
├── 📚 文档/
│   ├── LANE_LINE_GUIDE.md             ← 车道线功能说明
│   ├── QUICK_EDIT_GUIDE.md            ← 快速编辑指南
│   ├── FOV_CLIPPING_GUIDE.md          ← FOV 遮挡切割指南
│   └── FOV_CLIPPING_IMPLEMENTATION.md ← 技术实现文档
│
├── dist/                               ← 可执行文件目录
│   ├── FOV_Tools.exe                  ← ✅ 最新版本
│   ├── FOV_Tools_v9.exe               ← 历史版本
│   └── ...其他资源文件
│
├── build/                              ← PyInstaller 临时构建（可删除）
├── .venv/                              ← Python 虚拟环境
├── requirements.txt                    ← 项目依赖
└── .git/                               ← Git 版本控制
```

---

## 🎯 功能特性

### 1. **传感器管理**
- ✅ 添加/编辑/删除多个传感器
- ✅ 实时预览 FOV（视场角）
- ✅ 支持多种传感器类型（摄像头、激光雷达、雷达）

### 2. **2D 俯视图**
- ✅ 直观显示车辆和传感器布局
- ✅ 传感器 FOV 可视化
- ✅ 支持缩放和平移操作

### 3. **3D 立体视图**
- ✅ 三维 FOV 锥形显示
- ✅ **🆕 FOV 遮挡切割**（车体、挂车自动遮挡处理）
- ✅ 多视角预设（前、后、左、右、俯视）

### 4. **车道线绘制**
- ✅ 支持 4 种车道线类型：
  - 直线车道线
  - 曲线车道线
  - 汇入车道线
  - 汇出车道线
- ✅ **快速编辑面板**（实时修改参数）
- ✅ 导出时可选是否显示车道线

### 5. **导出功能**
- ✅ 高分辨率 PNG 导出
- ✅ 支持自定义标题和背景
- ✅ **选择性导出**（仅显示启用的传感器）
- ✅ **车道线导出控制**（可选是否导出）

---

## 🚀 新增功能说明

### 🆕 FOV 遮挡切割（3D 视图）
在 3D 视图中，后置传感器的 FOV 现在会自动被车体/挂车遮挡。

**使用方法：**
1. 在左侧选择后置传感器
2. 在右侧属性面板找到：
   - ☑️ `被车体遮挡时切割FOV` （默认启用）
   - 📏 `手动切割距离` （0=自动，>0=手动调整）
3. 3D 视图实时更新

**详见：** [FOV_CLIPPING_GUIDE.md](FOV_CLIPPING_GUIDE.md)

### 🆕 车道线功能
支持绘制和管理多条车道线，支持快速编辑和导出控制。

**详见：** [LANE_LINE_GUIDE.md](LANE_LINE_GUIDE.md)

---

## 📝 开发者信息

### 环境要求
- **Python**: 3.11+
- **依赖包**：
  ```
  PyQt5>=5.15
  numpy>=1.21
  matplotlib>=3.5
  pymupdf>=1.21
  PyInstaller>=5.0
  ```

### 安装和运行（开发模式）
```bash
# 克隆项目
git clone https://github.com/FloraLei/FOVTool.git
cd FOVTool

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python fov_tools.py
```

### 重新打包 .exe（修改代码后）
```bash
# 方式 1：使用 Python 脚本
python build_and_cleanup.py

# 方式 2：使用 Windows 批处理脚本（推荐）
build_and_cleanup.bat

# 方式 3：手动使用 PyInstaller
pyinstaller FOVTools.spec
```

---

## 📊 最新版本信息

| 文件 | 版本 | 大小 | 日期 | 说明 |
|------|------|------|------|------|
| FOV_Tools.exe | Latest | 6.94 MB | 2026/6/7 | ✅ 最新版本，含所有功能 |
| FOV_Tools_v9.exe | v9 | - | - | 历史版本 |

---

## 🐛 常见问题

### Q: 无法启动 .exe
**A:** 确保你的 Windows 系统为 Windows 10 或更高版本

### Q: .exe 运行缓慢
**A:** 首次加载会比较慢（加载所有依赖），之后会正常

### Q: 如何更新程序
**A:** 下载最新的 FOV_Tools.exe，覆盖旧版本即可

### Q: 如何修改代码后重新生成 .exe
**A:** 运行 `build_and_cleanup.bat` 一键打包

---

## 📞 技术支持

如有问题或建议，请：
1. 查看对应功能的文档（见📚 文档部分）
2. 检查 GitHub Issues
3. 提交 Pull Request

---

## 📜 许可证

本项目使用 MIT 许可证。详见 LICENSE 文件。

---

## ✨ 感谢

感谢所有贡献者和用户的支持！

---

**最后更新**: 2026-06-07
