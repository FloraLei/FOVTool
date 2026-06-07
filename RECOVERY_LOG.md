# 传感器配置文件恢复记录

## 📋 恢复总结
**日期**: 2026年6月7日  
**状态**: ✅ 完全恢复

## 🔍 问题背景
在commit `f73f036` (build: Generate FOV_Tools.exe and cleanup temporary files) 中，`fov_tools_session.json` 文件被删除了。

**原始配置文件信息**:
- 大小: ~4 KB
- 包含: 8个完整传感器配置 + 车道参数
- 传感器列表:
  1. 前向双目摄像头 (Camera)
  2. 前中广角摄像头 (Camera)
  3. 前向激光雷达 (LiDAR)
  4. 前向毫米波雷达 (Radar)
  5. 左侧向摄像头 (Camera)
  6. 右侧向摄像头 (Camera)
  7. 后向摄像头 (Camera)
  8. 后向毫米波雷达 (Radar)

## ✅ 恢复步骤

### 1. 定位被删除的文件
```bash
git log --diff-filter=D --summary -- dist/*.json
git show f73f036 --stat | grep "fov_tools_session.json"
```

### 2. 从Git历史恢复
```bash
# 从f73f036之前的提交恢复
git show f73f036^:fov_tools_session.json > fov_tools_session.json
```

### 3. 验证数据完整性
✓ JSON 文件有效  
✓ 8个传感器完整  
✓ 所有属性正确  

### 4. 创建备份
- **主备份**: `c:\Fuyue_WorkSpace\FOVTools\fov_tools_session.json` (3.99 KB)
- **副本**: `c:\Fuyue_WorkSpace\FOVTools\dist\fov_tools_session.json` (3.99 KB)

## 🛡️ 预防措施

### 修改 1: build_and_cleanup.py
**状态**: ✅ 已更新

**变更内容**:
1. **移除** `'*_session.json'` 从 CLEANUP_PATTERNS
2. **添加** `'fov_tools_session.json'` 到 KEEP_FILES

**效果**: 清理脚本将不再删除传感器配置文件

### 修改 2: .gitignore 建议
虽然dist/目录被忽略（这是合理的），但应该考虑：
- 在版本控制中保留一个模板或参考配置
- 或者使用 Git LFS 管理大型二进制配置

## 📌 使用说明

### 在应用中加载配置
应用启动时会自动从以下位置搜索并加载配置（按优先级）:
```
1. ./fov_tools_session.json (项目根目录)
2. ./dist/fov_tools_session.json (dist目录)
3. ~/fov_tools_session.json (用户主目录)
```

### 手动加载配置
在FOVTools GUI中:
1. 点击 "打开配置" 按钮
2. 选择 `fov_tools_session.json` 文件
3. 应用将加载所有传感器配置

## 🔄 未来建议

### 短期
- 定期备份 fov_tools_session.json 到云存储或额外位置
- 在README.md中记录配置文件位置

### 中期
- 考虑在版本控制中跟踪一个 `.sensors-config-template.json`
- 实现自动备份机制

### 长期
- 支持多个配置文件存储
- 配置版本管理系统
- 用户配置同步功能

## 📝 更新记录
- **v1.0.1 (2026-06-07)**: 恢复所有传感器配置，更新清理脚本保护措施
