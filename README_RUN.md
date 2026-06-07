# 🚀 FOVTools 应用 - 使用指南

> ⭐ **快速开始**：
> - **Windows**：双击 `运行FOVTools.bat`
> - **macOS**：双击 `Run_FOVTools.command`
> - **Linux**：双击 `Run_FOVTools.sh`

---

## 🖥️ Windows 用户

### 方式1：GUI 双击运行（推荐）

1. 找到项目根目录中的 `运行FOVTools.bat`
2. **双击** 该文件即可启动应用

```
📁 FOVTools
  ├─ 运行FOVTools.bat  ← 双击启动
  ├─ fov_tools.py
  └─ ...
```

### 方式2：命令行运行

```powershell
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 运行应用
python fov_tools.py
```

### 常见问题

**Q: 双击没有反应？**
- A: 检查虚拟环境是否存在（`.venv` 文件夹）
- 如果不存在，请先运行依赖安装

**Q: 提示 "未找到虚拟环境"？**
- A: 需要安装依赖。打开 CMD，运行：
  ```bash
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
  ```

---

## 🍎 macOS 用户

### 前置步骤

首次运行需要创建虚拟环境和安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 方式1：GUI 双击运行（推荐）

1. 找到项目根目录中的 `Run_FOVTools.command`
2. **双击** 该文件即可启动应用

```
📁 FOVTools
  ├─ Run_FOVTools.command  ← 双击启动
  ├─ fov_tools.py
  └─ ...
```

> 💡 如果显示"无法打开"，先赋予执行权限：
> ```bash
> chmod +x Run_FOVTools.command
> ```

### 方式2：命令行运行

```bash
source .venv/bin/activate
python3 fov_tools.py
```

### 常见问题

**Q: 双击显示 "无法验证开发者"？**
- A: 右键选择"打开"，然后点击"打开"确认

**Q: 显示 "Permission denied"？**
- A: 赋予执行权限：
  ```bash
  chmod +x Run_FOVTools.command
  ```

---

## 🐧 Linux 用户

### 前置步骤

首次运行需要创建虚拟环境和安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 方式1：GUI 双击运行（推荐）

1. 打开文件管理器进入项目根目录
2. 找到 `Run_FOVTools.sh` 文件
3. **双击** 该文件

```
📁 FOVTools
  ├─ Run_FOVTools.sh  ← 双击启动
  ├─ fov_tools.py
  └─ ...
```

> 💡 如果文件管理器无法执行，先赋予权限：
> ```bash
> chmod +x Run_FOVTools.sh
> ```

### 方式2：命令行运行

```bash
source .venv/bin/activate
python3 fov_tools.py
```

### 方式3：使用 Makefile

```bash
make run
```

### 常见问题

**Q: 双击无反应或显示权限错误？**
- A: 在终端中运行：
  ```bash
  bash Run_FOVTools.sh
  ```

**Q: 提示缺少图形库？**
- A: 安装依赖：
  - Ubuntu/Debian: `sudo apt-get install libgl1 libxkbcommon-x11-0`
  - Fedora: `sudo dnf install libglvnd libxkbcommon`

---

## 📖 应用功能说明

启动 FOVTools 后，你可以：

### 传感器配置
- 📡 添加/删除传感器
- 🔧 配置传感器参数（分辨率、FOV 等）
- 💾 保存/加载配置

### FOV 可视化
- 📊 2D 俯视图展示 FOV
- 🎯 3D 效果展示
- 📐 自定义 FOV 角度范围

### 数据导出
- 📤 导出为 PDF
- 📸 保存为图片
- 💾 导出配置文件

---

## ⌨️ 快捷键

（待补充，根据应用实际功能）

---

## 🎨 界面说明

### 主窗口
- **传感器列表**：左侧显示已配置的传感器
- **参数编辑**：中间编辑传感器参数
- **预览窗口**：右侧实时预览 FOV 效果

### 工具栏
- **新建**：创建新传感器
- **删除**：移除选中传感器
- **保存**：保存当前配置
- **导出**：导出为文件

---

## 🔄 工作流程示例

### 示例1：创建完整的车辆 FOV 配置

1. 启动应用
2. 添加前向摄像头
3. 添加侧向摄像头
4. 添加后向摄像头
5. 调整参数直到满意
6. 导出为 PDF 或图片

### 示例2：修改现有配置

1. 启动应用
2. 加载已保存的配置
3. 修改特定传感器参数
4. 查看实时预览
5. 保存修改

---

## 💾 数据保存位置

- **配置文件**：`fov_tools_session.json`（项目根目录）
- **导出文件**：用户自定义的输出目录

---

## 🛠️ 故障排除

| 问题 | 解决方案 |
|------|---------|
| 应用无法启动 | 检查依赖是否安装：`pip list \| grep PyQt5` |
| 显示界面不完整 | 尝试调整窗口大小 |
| 导出失败 | 检查输出目录权限 |
| 配置无法保存 | 确保对项目目录有写入权限 |

---

## 📞 需要帮助？

- 🖱️ **构建应用**：查看 [GUI 构建指南](README_GUI.md)
- 💻 **命令行方式**：查看 [CLI 指南](README_CLI.md)
- 📚 **详细文档**：查看 [BUILD.md](BUILD.md)

---

## 快速参考

```bash
# Windows
运行FOVTools.bat

# macOS
./Run_FOVTools.command

# Linux
bash Run_FOVTools.sh

# 或使用 Python 直接运行
python3 fov_tools.py
```

享受使用 FOVTools！🎯
