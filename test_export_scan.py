"""扫描导出图：找出所有非背景像素的位置"""
import sys
sys.path.insert(0, r"c:\Fuyue_WorkSpace\FOVTools")

import numpy as np
from PIL import Image
from fov_tools import (
    SensorConfig, VehicleConfig, SceneConfig,
    export_diagram_hq, HW30_SENSORS,
)

v = VehicleConfig(length=4.8, width=2.0, height=1.5,
                  trailer_length=3.0, trailer_width=2.0)
sensors = [SensorConfig.from_dict(d) for d in HW30_SENSORS]
cfg = SceneConfig(vehicle=v, sensors=sensors)

out = r"c:\Fuyue_WorkSpace\FOVTools\test_export_scan.png"
export_diagram_hq(cfg, out, width_px=2000, bg='white',
                  show_legend=True, title='Scan Test')

img = Image.open(out)
arr = np.array(img)
h, w = arr.shape[:2]
print(f"Image size: {w}×{h}")

# 分类每个像素
# (255,255,255) = 纯白背景
# (~240,~240,~240) = 接近白
# 其他 = 有内容
r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
is_white = (r > 250) & (g > 250) & (b > 250)
is_bg = (r > 240) & (g > 240) & (b > 240)

content_mask = ~is_bg
n_content = int(np.sum(content_mask))
n_white = int(np.sum(is_white))
n_near_white = int(np.sum(is_bg)) - n_white
print(f"White pixels: {n_white:,} ({100*n_white/(w*h):.1f}%)")
print(f"Near-white pixels: {n_near_white:,} ({100*n_near_white/(w*h):.1f}%)")  
print(f"Content pixels: {n_content:,} ({100*n_content/(w*h):.1f}%)")

# 找出内容分布
if n_content > 0:
    rows, cols = np.where(content_mask)
    r_min, r_max = rows.min(), rows.max()
    c_min, c_max = cols.min(), cols.max()
    print(f"\nContent bounding box: rows [{r_min},{r_max}], cols [{c_min},{c_max}]")

    # 采样一些内容像素的颜色
    sample_idx = np.random.choice(len(rows), min(20, len(rows)), replace=False)
    print("\nSample content colors:")
    for i in sample_idx[:10]:
        ri, ci = rows[i], cols[i]
        print(f"  [{ri:4d},{ci:4d}] = ({r[ri,ci]},{g[ri,ci]},{b[ri,ci]})")

    # 找车体：应该有一块区域颜色接近 veh_face (#F0F0F0 = 240,240,240)
    # 但 veh_face 是 near-white，会被 is_bg 过滤掉
    # 所以应该检查 veh_edge (#666666) 或 veh 内非 bg 区域
    
    # 检查中间行（大约 y=0 附近）
    mid_row = h // 2
    row_vals = arr[mid_row, :, :]
    non_white_in_row = np.where(~(row_vals[:,0] > 250))[0]
    if len(non_white_in_row) > 0:
        c_left = non_white_in_row[0]
        c_right = non_white_in_row[-1]
        print(f"\nMid row ({mid_row}): non-white from col {c_left} to {c_right}")
        # Show colors at quartiles
        for frac in [0, 0.25, 0.5, 0.75, 1.0]:
            ci = int(c_left + frac * (c_right - c_left))
            if 0 <= ci < w:
                print(f"  col {ci}: ({r[mid_row,ci]},{g[mid_row,ci]},{b[mid_row,ci]})")
else:
    print("\n⚠️ No content found! All pixels are near-white.")

# Also check: what color IS (156, 160, 105) that we found earlier?
c1, c2 = 723, 736
r1, r2 = 678, 697
sample = arr[r1:r2, c1:c2]
print(f"\nPrevious test region [{r1}:{r2}, {c1}:{c2}]:")
print(f"  mean=({sample[:,:,0].mean():.0f},{sample[:,:,1].mean():.0f},{sample[:,:,2].mean():.0f})")
print(f"  unique colors: {len(np.unique(sample.reshape(-1, 3), axis=0))}")
if len(sample) > 0:
    print(f"  first pixel: ({sample[0,0,0]},{sample[0,0,1]},{sample[0,0,2]})")
