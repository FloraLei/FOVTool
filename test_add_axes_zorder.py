"""测试: add_axes vs add_subplot(GridSpec) z-order"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge, FancyBboxPatch
import numpy as np
from PIL import Image

def test(name, create_func):
    fig = plt.figure(figsize=(12, 8), facecolor='white', dpi=100)
    ax = create_func(fig)
    
    ax.set_facecolor('white')
    ax.set_xlim(-60, 40)
    ax.set_ylim(-30, 30)
    ax.set_aspect('equal', adjustable='box')
    
    w = Wedge((-5, 0), 50, 120, 240, facecolor='red', alpha=0.7, zorder=3)
    ax.add_patch(w)
    r = mpatches.Rectangle((-20, -2), 20, 4, facecolor='black', fill=True, zorder=50)
    ax.add_patch(r)
    
    out = rf"c:\Fuyue_WorkSpace\FOVTools\test_zorder_{name}.png"
    fig.savefig(out, dpi=100, facecolor='white', bbox_inches='tight')
    plt.close(fig)
    
    img = np.array(Image.open(out))
    h, w = img.shape[:2]
    rr, gg, bb = img[:,:,0].astype(float), img[:,:,1].astype(float), img[:,:,2].astype(float)
    black = int(np.sum((rr<30)&(gg<30)&(bb<30)))
    red = int(np.sum((rr>gg+30)&(rr>bb+30)&(rr>100)))
    
    # 找到黑色区域，检查内部红色
    if black > 0:
        rows, cols = np.where((rr<30)&(gg<30)&(bb<30))
        r0,r1,c0,c1 = rows.min(),rows.max(),cols.min(),cols.max()
        red_in = int(np.sum((rr[r0:r1+1,c0:c1+1]>gg[r0:r1+1,c0:c1+1]+30)&
                            (rr[r0:r1+1,c0:c1+1]>bb[r0:r1+1,c0:c1+1]+30)&
                            (rr[r0:r1+1,c0:c1+1]>100)))
        status = "✅ WORKS" if red_in < 100 else f"❌ FAILS ({red_in} red in black)"
    else:
        status = "⚠️ No black rendered"
    
    print(f"  {name}: black={black}, red={red}, red_in_black={red_in if black>0 else 'N/A'} → {status}")

# Test 1: plain subplots
print("Testing z-order with different axes creation methods:")
test("subplots", lambda fig: plt.subplots(figsize=(12,8))[1].set_position([0.3,0.1,0.65,0.85]) or plt.subplots()[1])

# Test 2: add_axes (no GridSpec)
def create_add_axes(fig):
    ax = fig.add_axes([0.30, 0.10, 0.65, 0.85])
    return ax
test("add_axes", create_add_axes)

# Test 3: add_subplot with GridSpec  
from matplotlib.gridspec import GridSpec
def create_gridspec(fig):
    gs = GridSpec(1, 2, figure=fig, width_ratios=[3,9])
    return fig.add_subplot(gs[1])
test("add_subplot_gs", create_gridspec)

# Test 4: add_subplot without GridSpec
def create_plain_subplot(fig):
    return fig.add_subplot(1, 2, 2)
test("add_subplot_plain", create_plain_subplot)

print("\nDone. Check the output images.")
