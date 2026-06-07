"""用 GridSpec 布局测试 z-order —— 模拟 export_diagram_hq"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge, FancyBboxPatch
from matplotlib.gridspec import GridSpec
import numpy as np
from PIL import Image

# 模拟真实的导出参数
bg = 'white'
veh_length = 20.0
veh_width = 4.0
trailer_length = 10.0
trailer_width = 4.0

# 用 GridSpec: 20% legend, 80% diagram
fig = plt.figure(figsize=(12, 8), facecolor=bg, dpi=100)
gs = GridSpec(1, 2, figure=fig, width_ratios=[3, 9],
              left=0.005, right=0.995, top=0.975, bottom=0.065, wspace=0.015)
ax_leg = fig.add_subplot(gs[0])
ax = fig.add_subplot(gs[1])

ax.set_facecolor(bg)
ax.set_xlim(-60, 40)
ax.set_ylim(-30, 30)
ax.set_aspect('equal', adjustable='box')

# Draw wedge (rear radar) 
w = Wedge((-5, 0), 50, 120, 240, facecolor='red', alpha=0.7,
          edgecolor='red', linewidth=0.5, zorder=3)
ax.add_patch(w)

# Draw wedge (front camera)
w2 = Wedge((2, 0), 30, -30, 30, facecolor='blue', alpha=0.5,
           edgecolor='blue', linewidth=0.5, zorder=3)
ax.add_patch(w2)

# Erase rectangles (BLACK for visibility)
print("Adding BLACK erase rectangles at z=50...")
ax.add_patch(mpatches.Rectangle(
    (-veh_length, -veh_width/2), veh_length, veh_width,
    facecolor='black', edgecolor='none', fill=True, zorder=50))
ax.add_patch(mpatches.Rectangle(
    (-veh_length - trailer_length, -trailer_width/2),
    trailer_length, trailer_width,
    facecolor='black', edgecolor='none', fill=True, zorder=50))

# Vehicle outline (on top of erase)
veh_face = '#F0F0F0'
veh_edge = '#666666'
ax.add_patch(FancyBboxPatch(
    (-veh_length, -veh_width/2), veh_length, veh_width,
    boxstyle='round,pad=0.15',
    facecolor=veh_face, edgecolor=veh_edge, linewidth=1.5, zorder=51))
ax.add_patch(FancyBboxPatch(
    (-veh_length - trailer_length, -trailer_width/2),
    trailer_length, trailer_width,
    boxstyle='round,pad=0.10',
    facecolor=veh_face, edgecolor=veh_edge, linewidth=1.2, zorder=51))

out = r"c:\Fuyue_WorkSpace\FOVTools\test_gridspec_zorder.png"
fig.savefig(out, dpi=100, bbox_inches='tight', facecolor=bg)
plt.close(fig)

# Analyze
img = np.array(Image.open(out))
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

r, g, b = img[:,:,0].astype(float), img[:,:,1].astype(float), img[:,:,2].astype(float)

black = (r < 30) & (g < 30) & (b < 30)
red = (r > g + 30) & (r > b + 30) & (r > 100)

print(f"Black pixels: {int(np.sum(black))}")
print(f"Red pixels: {int(np.sum(red))}")

if np.sum(black) > 0:
    rows, cols = np.where(black)
    r0, r1, c0, c1 = rows.min(), rows.max(), cols.min(), cols.max()
    # Check red inside black region
    red_in_black = int(np.sum(red[r0:r1+1, c0:c1+1]))
    print(f"Black region: [{r0},{r1}] x [{c0},{c1}]")
    print(f"Red IN black: {red_in_black}")
    if red_in_black > 100:
        print("❌ GridSpec breaks z-order! Red visible through black.")
    else:
        print("✅ GridSpec z-order works. Issue is elsewhere.")
else:
    print("❌ No black pixels — erase not rendered in GridSpec!")