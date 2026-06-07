"""极端测试：超大车体 + 后向传感器，车体遮挡必须可见"""
import sys
sys.path.insert(0, r"c:\Fuyue_WorkSpace\FOVTools")

import numpy as np
from PIL import Image
from fov_tools import (
    SensorConfig, VehicleConfig, SceneConfig,
    export_diagram_hq,
)

# 超大车体：长 20m，宽 4m + 挂车 10m，总长 30m
v = VehicleConfig(length=20.0, width=4.0, height=2.0,
                  trailer_length=10.0, trailer_width=4.0)

# 仅一个后向传感器，FOV 必然穿透车体
sensors = [
    SensorConfig.from_dict(dict(
        name="后向雷达", sensor_type="radar",
        x=0.0, y=-5.0, z=0.5,       # 在车体中间位置
        mount_angle=180, hfov=120, vfov=10,
        range=50, color="#FF0000", opacity=0.70  # 高不透明度红色
    )),
    # 加一个前向传感器作参考
    SensorConfig.from_dict(dict(
        name="前向相机", sensor_type="camera",
        x=0.0, y=2.0, z=1.0,
        mount_angle=0, hfov=60, vfov=40,
        range=30, color="#0000FF", opacity=0.50  # 蓝色
    )),
]
cfg = SceneConfig(vehicle=v, sensors=sensors)

out = r"c:\Fuyue_WorkSpace\FOVTools\test_big_vehicle.png"
print("Exporting big vehicle test...")
export_diagram_hq(cfg, out, width_px=2000, bg='white',
                  show_legend=True, title='Big Vehicle Test (30m total, rear sensor at y=-5)')

# 分析输出
img = Image.open(out)
arr = np.array(img)
h, w = arr.shape[:2]
print(f"Image size: {w}×{h}")

# 检查：车体应该占据 display x 从 -30 到 0
# 后向传感器在 display x=-5，FOV 从 x=-5 向左延伸到约 -55
# 车体区域 (x ∈ [-30, 0]) 应该被擦除，纯白

# 由于 bbox_inches='tight'，实际像素映射未知
# 直接扫描：找红色像素（后向雷达 FOV），检查它们在 x < -30 才出现

r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)

# 找红色主导像素 (R > G and R > B and R > 100)
red_mask = (r > g + 20) & (r > b + 20) & (r > 100)
red_rows, red_cols = np.where(red_mask)
n_red = len(red_rows)

# 找蓝色主导像素 (B > R and B > G and B > 100)  
blue_mask = (b > r + 20) & (b > g + 20) & (b > 100)
blue_rows, blue_cols = np.where(blue_mask)
n_blue = len(blue_rows)

print(f"\nRed (rear radar) pixels: {n_red}")
print(f"Blue (front camera) pixels: {n_blue}")

# 报告前后 FOV 的 col 范围
if n_red > 0:
    print(f"Red FOV col range: [{red_cols.min()}, {red_cols.max()}]")
    print(f"Red FOV row range: [{red_rows.min()}, {red_rows.max()}]")
if n_blue > 0:
    print(f"Blue FOV col range: [{blue_cols.min()}, {blue_cols.max()}]")
    print(f"Blue FOV row range: [{blue_rows.min()}, {blue_rows.max()}]")

# 找深色像素（车体轮廓 #999999 / #666666 或 veh_face #F0F0F0 / #2C2C2C）
# 先找所有非白非纯色像素
gray_mask = (np.abs(r - g) < 15) & (np.abs(g - b) < 15) & (np.abs(r - b) < 15)
dark_gray = gray_mask & (r < 180) & (r > 30)
dark_rows, dark_cols = np.where(dark_gray)
n_dark = len(dark_rows)
print(f"\nDark gray (vehicle?) pixels: {n_dark}")
if n_dark > 0:
    print(f"Dark gray col range: [{dark_cols.min()}, {dark_cols.max()}]")
    print(f"Dark gray row range: [{dark_rows.min()}, {dark_rows.max()}]")

# 关键检查：红色 FOV 的最小 col 是否 > 车体左边界
# 如果是，说明车体左边（后方）才有红色 → 遮挡生效
# 如果红色出现在车体内部（较小 col），说明遮挡未生效
if n_red > 0 and n_dark > 0:
    veh_left = dark_cols.min()  # 车体最左端（后方）
    red_before_veh = np.sum(red_cols < veh_left)
    red_in_veh = np.sum((red_cols >= veh_left) & (red_cols <= dark_cols.max()))
    print(f"\n🚗 Vehicle col range (dark gray): [{dark_cols.min()}, {dark_cols.max()}]")
    print(f"🔴 Red FOV pixels BEFORE vehicle (col < {dark_cols.min()}): {red_before_veh}")
    print(f"🔴 Red FOV pixels IN vehicle area ({dark_cols.min()}-{dark_cols.max()}): {red_in_veh}")
    if red_in_veh > 100:
        print("❌ FAIL: Red FOV visible INSIDE vehicle — occlusion NOT working!")
    elif red_before_veh > 100:
        print("✅ PASS: Red FOV only visible BEHIND vehicle — occlusion IS working!")
    else:
        print("⚠️  AMBIGUOUS: Red FOV distribution unclear")

print(f"\nOutput: {out}")
