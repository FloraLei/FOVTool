"""把车体周围放大，看看遮挡是否生效"""
from PIL import Image
import os

src = r"C:\Fuyue_WorkSpace\FOVTools\test_occlusion_full.png"
img = Image.open(src)
W, H = img.size
print(f"image size: {W}x{H}")

# 车体大约在中心，width=2 length=4.8 + sensor 范围 ~12m。中心位置约 (W*0.6, H*0.5)
cx, cy = 975, 1390
half = 350
crop = img.crop((cx - half, cy - half, cx + half, cy + half))
out = r"C:\Fuyue_WorkSpace\FOVTools\test_occlusion_zoom.png"
crop.save(out)
print(f"zoomed: {out}")
