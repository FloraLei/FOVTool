"""验证 matplotlib z-order 是否真的有效"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge
import numpy as np
from PIL import Image

fig, ax = plt.subplots(figsize=(6, 4))
ax.set_facecolor('white')
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)

# Test 1: Wedge first (z=1), Rectangle second (z=100) -- Rectangle should cover
print("=== Test 1: Rectangle with HIGH z-order should cover Wedge ===")
w1 = Wedge((0, 0), 5, -90, 90, facecolor='red', alpha=0.8, zorder=3)
r1 = mpatches.Rectangle((-3, -3), 6, 6, facecolor='black', fill=True, zorder=50)
ax.add_patch(w1)
ax.add_patch(r1)

out1 = r"c:\Fuyue_WorkSpace\FOVTools\test_zorder_1.png"
fig.savefig(out1, dpi=100, facecolor='white')
img1 = np.array(Image.open(out1))
# Check center pixel: should be black (not red) if Rectangle covers Wedge
cy, cx = img1.shape[0]//2, img1.shape[1]//2
p1 = img1[cy, cx, :3]
print(f"Center pixel (should be black): {p1}")
is_black = (p1[0] < 30) and (p1[1] < 30) and (p1[2] < 30)
is_red = (p1[0] > 200) and (p1[1] < 50) and (p1[2] < 50)
print(f"  → {'✅ Black (z-order works!)' if is_black else '❌ Red (z-order FAILED!)' if is_red else '⚠️ Neither'}")

# Test 2: Swap order — Rectangle first, Wedge second (same z values)
fig2, ax2 = plt.subplots(figsize=(6, 4))
ax2.set_facecolor('white')
ax2.set_xlim(-10, 10)
ax2.set_ylim(-10, 10)

print("\n=== Test 2: Rectangle added FIRST, but with HIGH z-order ===")
r2 = mpatches.Rectangle((-3, -3), 6, 6, facecolor='black', fill=True, zorder=50)
w2 = Wedge((0, 0), 5, -90, 90, facecolor='red', alpha=0.8, zorder=3)
ax2.add_patch(r2)
ax2.add_patch(w2)

out2 = r"c:\Fuyue_WorkSpace\FOVTools\test_zorder_2.png"
fig2.savefig(out2, dpi=100, facecolor='white')
img2 = np.array(Image.open(out2))
p2 = img2[cy, cx, :3]
print(f"Center pixel (should be black): {p2}")
is_black2 = (p2[0] < 30) and (p2[1] < 30) and (p2[2] < 30)
is_red2 = (p2[0] > 200) and (p2[1] < 50) and (p2[2] < 50)
print(f"  → {'✅ Black (z-order works!)' if is_black2 else '❌ Red (z-order FAILED!)' if is_red2 else '⚠️ Neither'}")

# Test 3: BOTH at same zorder, Rectangle added second → should be on top
fig3, ax3 = plt.subplots(figsize=(6, 4))
ax3.set_facecolor('white')
ax3.set_xlim(-10, 10)
ax3.set_ylim(-10, 10)

print("\n=== Test 3: Same zorder, Rectangle added AFTER Wedge ===")
w3 = Wedge((0, 0), 5, -90, 90, facecolor='red', alpha=0.8, zorder=1)
r3 = mpatches.Rectangle((-3, -3), 6, 6, facecolor='black', fill=True, zorder=1)
ax3.add_patch(w3)
ax3.add_patch(r3)

out3 = r"c:\Fuyue_WorkSpace\FOVTools\test_zorder_3.png"
fig3.savefig(out3, dpi=100, facecolor='white')
img3 = np.array(Image.open(out3))
p3 = img3[cy, cx, :3]
print(f"Center pixel (should be black): {p3}")
is_black3 = (p3[0] < 30) and (p3[1] < 30) and (p3[2] < 30)
is_red3 = (p3[0] > 200) and (p3[1] < 50) and (p3[2] < 50)
print(f"  → {'✅ Black (insertion order works!)' if is_black3 else '❌ Red (FAILED!)' if is_red3 else '⚠️ Neither'}")

plt.close('all')
print("\nVersion:", matplotlib.__version__)
