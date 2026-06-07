"""验证 plt.subplots(1,2) 的 z-order"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge
import numpy as np
from PIL import Image

fig, (ax_leg, ax) = plt.subplots(1, 2, figsize=(12, 8),
                                   gridspec_kw={'width_ratios': [3, 9]})

ax.set_facecolor('white')
ax.set_xlim(-60, 40)
ax.set_ylim(-30, 30)
ax.set_aspect('equal', adjustable='box')
ax_leg.axis('off')

w = Wedge((-5, 0), 50, 120, 240, facecolor='red', alpha=0.7, zorder=3)
ax.add_patch(w)
r = mpatches.Rectangle((-20, -2), 20, 4, facecolor='black', fill=True, zorder=50)
ax.add_patch(r)

out = r"c:\Fuyue_WorkSpace\FOVTools\test_subplots2.png"
fig.savefig(out, dpi=100, facecolor='white', bbox_inches='tight')
plt.close(fig)

img = np.array(Image.open(out))
rr, gg, bb = img[:,:,0].astype(float), img[:,:,1].astype(float), img[:,:,2].astype(float)
black = int(np.sum((rr<30)&(gg<30)&(bb<30)))
red = int(np.sum((rr>gg+30)&(rr>bb+30)&(rr>100)))

if black > 0:
    rows, cols = np.where((rr<30)&(gg<30)&(bb<30))
    r0,r1,c0,c1 = rows.min(),rows.max(),cols.min(),cols.max()
    red_in = int(np.sum((rr[r0:r1+1,c0:c1+1]>gg[r0:r1+1,c0:c1+1]+30)&
                        (rr[r0:r1+1,c0:c1+1]>bb[r0:r1+1,c0:c1+1]+30)&
                        (rr[r0:r1+1,c0:c1+1]>100)))
    print(f"Black: {black}, Red: {red}, Red in black: {red_in}")
    if red_in < 100:
        print("✅ plt.subplots(1,2) z-order WORKS!")
    else:
        print(f"❌ Still fails: {red_in} red in black")
else:
    print("⚠️ No black pixels")

# Second test: fig.add_subplot with plt.figure 
fig2 = plt.figure(figsize=(12, 8))
ax2 = fig2.add_subplot(1, 2, 2)
ax2.set_facecolor('white')
ax2.set_xlim(-60, 40)
ax2.set_ylim(-30, 30)
ax2.set_aspect('equal', adjustable='box')
w2 = Wedge((-5, 0), 50, 120, 240, facecolor='red', alpha=0.7, zorder=3)
ax2.add_patch(w2)
r2 = mpatches.Rectangle((-20, -2), 20, 4, facecolor='black', fill=True, zorder=50)
ax2.add_patch(r2)
out2 = r"c:\Fuyue_WorkSpace\FOVTools\test_figure_add_subplot.png"
fig2.savefig(out2, dpi=100, facecolor='white', bbox_inches='tight')
plt.close(fig2)

img2 = np.array(Image.open(out2))
rr2, gg2, bb2 = img2[:,:,0].astype(float), img2[:,:,1].astype(float), img2[:,:,2].astype(float)
black2 = int(np.sum((rr2<30)&(gg2<30)&(bb2<30)))
red2 = int(np.sum((rr2>gg2+30)&(rr2>bb2+30)&(rr2>100)))
if black2 > 0:
    rows2, cols2 = np.where((rr2<30)&(gg2<30)&(bb2<30))
    r02,r12,c02,c12 = rows2.min(),rows2.max(),cols2.min(),cols2.max()
    red_in2 = int(np.sum((rr2[r02:r12+1,c02:c12+1]>gg2[r02:r12+1,c02:c12+1]+30)&
                         (rr2[r02:r12+1,c02:c12+1]>bb2[r02:r12+1,c02:c12+1]+30)&
                         (rr2[r02:r12+1,c02:c12+1]>100)))
    print(f"\nplt.figure + add_subplot: Black={black2}, Red={red2}, RedInBlack={red_in2}")
    print("✅ Works" if red_in2 < 100 else f"❌ Fails ({red_in2})")
