# FOVTools 车道线功能使用指南

## 概述
FOVTools 现已支持绘制和管理车道线。你可以添加三种类型的车道线：
1. **直线车道线** - 标准直线车道线
2. **曲线车道线** - 基于二次曲率的弯曲车道线  
3. **汇入车道线** - 从侧面汇入到主道路的车道线
4. **汇出车道线** - 从主道路汇出到侧面的车道线

## 工作流程

### 添加车道线
1. 在 FOVTools 左侧栏点击"车道线列表"选项卡（在"传感器列表"旁边）
2. 选择要添加的车道线类型（直线/曲线/汇入/汇出）
3. 点击"+ 添加"按钮
4. 输入车道线的名称
5. 新的车道线将显示在列表中

### 编辑车道线
在右侧属性面板中可以编辑车道线参数（后续版本会完善UI）：
- `name` - 车道线名称
- `line_type` - 车道线类型
- `x_start` - 横向位置（负数=左侧，正数=右侧）
- `y_start` - 纵向起点（负数=车后，正数=车前）
- `y_end` - 纵向终点
- `curvature` - 曲率参数（仅对曲线和汇入/汇出有效）
- `width` - 线条宽度
- `color` - 线条颜色
- `enabled` - 是否显示

### 管理车道线
- **删除** - 选中车道线后点击"🗑 删除"
- **复制** - 点击"⧉ 复制"创建副本
- **切换显示** - 点击"◎ 切换"显示/隐藏车道线

## 坐标系说明
- **X轴**（横向）：负数=左侧，0=中心，正数=右侧
- **Y轴**（纵向）：负数=车后，0=车头保险杠，正数=车前方

示例：
- 直线车道线：x_start=-1.0, y_start=-50.0, y_end=50.0 → 左侧50米长直线
- 曲线车道线：curvature=0.01 → 缓和曲线
- 汇入车道线：x_start=2.0, curvature=0.5 → 从右侧汇入

## 导出功能
车道线会自动包含在导出的图像中：
- **2D导出**：车道线以配置的颜色和宽度显示
- **高质量导出**（Matplotlib）：支持更好的视觉效果

## 保存和加载
车道线配置会与其他场景信息一起保存到JSON文件中：
```json
{
  "lane_lines": [
    {
      "id": "abc12345",
      "name": "左侧车道",
      "line_type": "straight",
      "x_start": -1.0,
      "y_start": -50.0,
      "y_end": 50.0,
      "curvature": 0.0,
      "width": 0.15,
      "color": "#FFFFFF",
      "enabled": true
    }
  ]
}
```

## 常见用例

### 场景1：标准双向四车道
```python
# 左侧两条线
LaneLineConfig(name="左分界线", x_start=-1.0, ...)
LaneLineConfig(name="左中线", x_start=-2.0, ...)
# 右侧两条线  
LaneLineConfig(name="右中线", x_start=1.0, ...)
LaneLineConfig(name="右分界线", x_start=2.0, ...)
```

### 场景2：弯曲道路
```python
LaneLineConfig(
    name="左弯道",
    line_type="curved",
    x_start=-1.0,
    y_start=-50.0,
    y_end=50.0,
    curvature=0.01  # 控制曲率大小
)
```

### 场景3：交汇区域
```python
# 主道路
LaneLineConfig(name="主线", line_type="straight", x_start=0.0, ...)
# 汇入线
LaneLineConfig(name="汇入", line_type="merge_in", x_start=2.0, ...)
```

## 技术细节

### 数据结构
```python
@dataclass
class LaneLineConfig:
    id: str           # 唯一标识符
    name: str         # 显示名称
    line_type: str    # 类型：straight/curved/merge_in/merge_out
    x_start: float    # 横向起始位置
    y_start: float    # 纵向起始位置
    y_end: float      # 纵向结束位置
    curvature: float  # 曲率系数
    width: float      # 线宽
    color: str        # 颜色（#RRGGBB）
    enabled: bool     # 是否启用
```

### 渲染实现
- **2D视图**：使用 QGraphicsItem 绘制
- **导出图像**：使用 Matplotlib 绘制，支持同时显示多条线

## 后续改进方向
- [ ] 在属性面板中支持车道线参数直接编辑
- [ ] 在画布上直接拖动编辑车道线
- [ ] 支持复杂的车道线几何形状
- [ ] 3D视图中的车道线显示
