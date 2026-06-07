"""Debug: 对比导出图中有/无车体擦除的差异"""
import sys
sys.path.insert(0, r"c:\Fuyue_WorkSpace\FOVTools")

import numpy as np
from fov_tools import (
    SensorConfig, VehicleConfig, SceneConfig,
    export_diagram_hq, HW30_SENSORS,
)

v = VehicleConfig(length=4.8, width=2.0, height=1.5,
                  trailer_length=3.0, trailer_width=2.0)
sensors = [SensorConfig.from_dict(d) for d in HW30_SENSORS]
cfg = SceneConfig(vehicle=v, sensors=sensors)

# 导出两份：有擦除 vs 无擦除（去掉 zorder=50 擦除矩形）
out1 = r"c:\Fuyue_WorkSpace\FOVTools\test_export_with_erase.png"
out2 = r"c:\Fuyue_WorkSpace\FOVTools\test_export_no_erase.png"

print("Exporting with erase...")
export_diagram_hq(cfg, out1, width_px=2000, bg='white',
                  show_legend=True, title='With Erase (z=50)')
print("Done 1")

print("Exporting without erase (patched)...")
# Monkey-patch to skip erase rectangles
import matplotlib.patches as mpatches
_orig_rect = mpatches.Rectangle
class NoEraseRect(_orig_rect):
    def __init__(self, *args, **kw):
        if kw.get('zorder') == 50:
            kw['alpha'] = 0.0  # make invisible
        super().__init__(*args, **kw)
mpatches.Rectangle = NoEraseRect

export_diagram_hq(cfg, out2, width_px=2000, bg='white',
                  show_legend=True, title='No Erase (z=50 hidden)')
mpatches.Rectangle = _orig_rect  # restore
print("Done 2")

# Pixel comparison
from PIL import Image
img1 = np.array(Image.open(out1))
img2 = np.array(Image.open(out2))
diff = np.abs(img1.astype(int) - img2.astype(int))

# Vehicle body area in display coords: x ∈ [0, 7.8]m → need to map to pixels
# Since the export has legend on left, vehicle is roughly in left-center of diagram area
# Let's just check if there ARE differences (meaning erase is working)
total_pixels = img1.size
diff_pixels = int(np.sum(diff > 10))
print(f"\nTotal pixels: {total_pixels:,}")
print(f"Different pixels (diff>10): {diff_pixels:,} ({100*diff_pixels/total_pixels:.2f}%)")
if diff_pixels > 0:
    print("✅ Erase rectangles ARE changing the output (they're working)")
    # Find the region with most differences
    diff_gray = np.max(diff, axis=2)
    rows_with_diff = np.any(diff_gray > 10, axis=1)
    cols_with_diff = np.any(diff_gray > 10, axis=0)
    if rows_with_diff.any() and cols_with_diff.any():
        r_min, r_max = np.where(rows_with_diff)[0][[0, -1]]
        c_min, c_max = np.where(cols_with_diff)[0][[0, -1]]
        print(f"Difference region: rows [{r_min}-{r_max}], cols [{c_min}-{c_max}]")
else:
    print("❌ Erase rectangles have NO effect — BUG!")
