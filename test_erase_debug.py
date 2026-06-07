"""Debug: 把擦除矩形画成黑色，确认是否渲染"""
import sys
sys.path.insert(0, r"c:\Fuyue_WorkSpace\FOVTools")

# 直接复制 export_diagram_hq 的核心逻辑，但把擦除矩形改成黑色
import math
import numpy as np
from dataclasses import dataclass, field, asdict, fields as dc_fields
from typing import List

@dataclass
class SC:
    name: str = ""; sensor_type: str = ""; x: float = 0; y: float = 0; z: float = 0
    mount_angle: float = 0; hfov: float = 60; vfov: float = 40; range: float = 60
    color: str = "#FF0000"; opacity: float = 0.5; enabled: bool = True
    id: str = "test"; disp_hfov: float = 0; pitch: float = 0

@dataclass
class VC:
    length: float = 20.0; width: float = 4.0; height: float = 2.0
    trailer_length: float = 10.0; trailer_width: float = 4.0
    @property
    def effective_trailer_width(self): return self.trailer_width or self.width
    @property
    def total_length(self): return self.length + max(0.0, self.trailer_length)
    @property
    def max_width(self): return max(self.width, self.effective_trailer_width if self.trailer_length > 0 else 0.0)

@dataclass
class CFG:
    vehicle: VC = field(default_factory=VC)
    sensors: List[SC] = field(default_factory=list)
    show_grid: bool = True
    show_labels: bool = False
    show_overlap: bool = False

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge, FancyBboxPatch

v = VC()
s = SC(name="后向雷达", x=0.0, y=-5.0, z=0.5, mount_angle=180, hfov=120, vfov=10, range=50, color="#FF0000", opacity=0.70)
s2 = SC(name="前向相机", x=0.0, y=2.0, z=1.0, mount_angle=0, hfov=60, vfov=40, range=30, color="#0000FF", opacity=0.50)
cfg = CFG(vehicle=v, sensors=[s, s2])

# 最小化重现
bg = 'white'
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_facecolor(bg)
ax.set_xlim(-60, 40)
ax.set_ylim(-30, 30)
ax.set_aspect('equal')

# Draw wedges
for sensor in cfg.sensors:
    cx, cy = sensor.y, sensor.x
    mpl_mid = sensor.mount_angle
    t1 = mpl_mid - sensor.hfov / 2.0
    t2 = mpl_mid + sensor.hfov / 2.0
    ax.add_patch(Wedge((cx, cy), sensor.range, t1, t2,
                       facecolor=sensor.color, alpha=sensor.opacity,
                       edgecolor=sensor.color, linewidth=0.5, zorder=3))

# Erase rectangles — 改成 BLACK 来验证渲染
print("Drawing erase rectangles in BLACK for visibility...")
ax.add_patch(mpatches.Rectangle(
    (-v.length, -v.width / 2), v.length, v.width,
    facecolor='black', edgecolor='none', fill=True, zorder=50))
if v.trailer_length > 0:
    tw = v.effective_trailer_width
    ax.add_patch(mpatches.Rectangle(
        (-v.length - v.trailer_length, -tw / 2), v.trailer_length, tw,
        facecolor='black', edgecolor='none', fill=True, zorder=50))

out = r"c:\Fuyue_WorkSpace\FOVTools\test_erase_black.png"
fig.savefig(out, dpi=100, bbox_inches='tight', facecolor=bg)
plt.close(fig)
print(f"Saved: {out}")

# 分析
from PIL import Image
img = np.array(Image.open(out))
h, w = img.shape[:2]
print(f"Image size: {w}x{h}")

# 找黑色像素
r, g, b = img[:,:,0].astype(float), img[:,:,1].astype(float), img[:,:,2].astype(float)
black_mask = (r < 30) & (g < 30) & (b < 30)
n_black = int(np.sum(black_mask))
red_mask = (r > g + 20) & (r > b + 20) & (r > 100)
n_red = int(np.sum(red_mask))

print(f"Black (erase) pixels: {n_black}")
print(f"Red (rear FOV) pixels: {n_red}")

if n_black > 0:
    rows, cols = np.where(black_mask)
    print(f"Black region: rows [{rows.min()},{rows.max()}], cols [{cols.min()},{cols.max()}]")
    
    # 检查车体区域：黑色区域内是否还有红色？
    black_in_region = black_mask[rows.min():rows.max()+1, cols.min():cols.max()+1]
    red_in_black_region = red_mask[rows.min():rows.max()+1, cols.min():cols.max()+1]
    n_red_in_black = int(np.sum(red_in_black_region))
    print(f"Red pixels INSIDE black region: {n_red_in_black}")
    if n_red_in_black > 0:
        print("❌ FAIL: Red FOV visible through black erase! z-order ISSUE!")
    else:
        print("✅ PASS: Black erase covers red FOV — z-order works")
else:
    print("❌ CRITICAL: Black erase rectangles not rendered at all!")
