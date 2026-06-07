"""精确检查：车体/挂车区域的像素是否被擦除"""
import sys
sys.path.insert(0, r"c:\Fuyue_WorkSpace\FOVTools")

import numpy as np
from PIL import Image
from fov_tools import (
    SensorConfig, VehicleConfig, SceneConfig,
    export_diagram_hq, HW30_SENSORS,
)

# === 只用后向传感器，让 FOV 必须穿透车体 ===
v = VehicleConfig(length=4.8, width=2.0, height=1.5,
                  trailer_length=3.0, trailer_width=2.0)

rear_sensors = [
    dict(name="后向摄像头", sensor_type="camera", x=0.0, y=-2.40, z=1.2,
         mount_angle=180, hfov=60, vfov=60, range=110,
         color="#F44336", opacity=0.50),
    dict(name="后向毫米波雷达", sensor_type="radar", x=0.0, y=-2.40, z=0.4,
         mount_angle=180, hfov=120, vfov=10, range=70,
         color="#4CAF50", opacity=0.50),
    # 加几个前向传感器让画面完整
    dict(name="前向双目摄像头", sensor_type="camera", x=0.0, y=2.40, z=1.2,
         mount_angle=0, hfov=60, vfov=40, range=400,
         color="#1565C0", opacity=0.25),
]
sensors = [SensorConfig.from_dict(d) for d in rear_sensors]
cfg = SceneConfig(vehicle=v, sensors=sensors)

out = r"c:\Fuyue_WorkSpace\FOVTools\test_pixel_check.png"
export_diagram_hq(cfg, out, width_px=2000, bg='white',
                  show_legend=True, title='Pixel Check')

# 读取输出，检查车体区域（display x ∈ [-7.8, 0], y ∈ [-1, 1]）
img = Image.open(out)
arr = np.array(img)
h, w = arr.shape[:2]
print(f"Image size: {w}×{h}")

# 计算 DPI 和坐标映射
dpi = 150
# 从 export_diagram_hq 逻辑反推 view bounds
# x-axis: from -bk_max to fwd_max. 前向 camera range=400 at y=2.4 → fwd_max ≈ snap(402.4)=450
# bk_max: 后向 camera range=110 at y=-2.4 → x_min = -2.4 - 110 = -112.4, bk_max = snap(112.4, 25)=125
# vehicle total_length=7.8
x_min = -125
x_max = 450

# y-axis: 后向 camera hfov=60 → sin(150°)=0.5*110=55, max y=55, min y=-55
# 前向 camera: at y=0, no lateral extent
y_max = max(55, 1)
lat_max = 75  # snapped

# Diagram area: 20% legend, 80% diagram
legend_w = 0.20
diagram_w = 0.80
diagram_px_w = int(w * diagram_w)
diagram_x_start = w - diagram_px_w

# x pixel mapping: x_range [x_min, x_max] → [0, diagram_px_w]
def x_to_px(x):
    return int(diagram_x_start + (x - x_min) / (x_max - x_min) * diagram_px_w)

def y_to_px(y):
    return int(h * (1 - (y + lat_max) / (2 * lat_max)))  # flip Y

print(f"\nDiagram area: x=[{x_min},{x_max}], y=[-{lat_max},{lat_max}]")
print(f"Diagram pixels: width={diagram_px_w}, start_x={diagram_x_start}")

# 检查车体区域像素
cab_x0, cab_x1 = x_to_px(-4.8), x_to_px(0)
cab_y0, cab_y1 = y_to_px(-1), y_to_px(1)
print(f"\nCab pixel bounds: x=[{cab_x0},{cab_x1}], y=[{cab_y0},{cab_y1}]")

# 挂车
trailer_x0, trailer_x1 = x_to_px(-7.8), x_to_px(-4.8)
trailer_y0, trailer_y1 = y_to_px(-1), y_to_px(1)
print(f"Trailer pixel bounds: x=[{trailer_x0},{trailer_x1}], y=[{trailer_y0},{trailer_y1}]")

# 检查这几个区域是不是白色（擦除了 FOV）
def check_region(label, x0, x1, y0, y1):
    x0, x1 = max(0, min(x0, x1)), min(w-1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(h-1, max(y0, y1))
    if x1 <= x0 or y1 <= y0:
        print(f"  {label}: invalid range")
        return
    region = arr[y0:y1, x0:x1]
    mean_color = region.mean(axis=(0,1))
    std_color = region.std(axis=(0,1))
    is_white = np.all(mean_color > 240) and np.all(std_color < 20)
    print(f"  {label}: mean=({mean_color[0]:.0f},{mean_color[1]:.0f},{mean_color[2]:.0f}) "
          f"std=({std_color[0]:.0f},{std_color[1]:.0f},{std_color[2]:.0f}) "
          f"-> {'✅ WHITE (erased)' if is_white else '❌ NOT erased!'}")

print("\nRegion checks:")
check_region("Cab body", cab_x0, cab_x1, cab_y0, cab_y1)
check_region("Trailer body", trailer_x0, trailer_x1, trailer_y0, trailer_y1)

# 检查后方盲区（车体后面应该能看到 FOV）
blind_x0 = x_to_px(-20)
blind_x1 = x_to_px(-9)
blind_y0 = y_to_px(-0.5)
blind_y1 = y_to_px(0.5)
check_region("Rear area (should see FOV)", blind_x0, blind_x1, blind_y0, blind_y1)

# 检查前方区域（应该看到 FOV）
front_x0 = x_to_px(3)
front_x1 = x_to_px(10)
front_y0 = y_to_px(-0.5)
front_y1 = y_to_px(0.5)
check_region("Front area (should see FOV)", front_x0, front_x1, front_y0, front_y1)

print("\nDone. Check:", out)
