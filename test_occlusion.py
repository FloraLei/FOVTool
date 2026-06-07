"""快速测试遮挡效果：导出 HW30 默认配置，并放大显示车体周围"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import fov_tools as ft

# 加载 HW30 默认场景（直接调用工厂函数）
scene = ft.SceneConfig.hw30()
print(f"Vehicle: width={scene.vehicle.width}, length={scene.vehicle.length}")
print(f"Trailer: length={scene.vehicle.trailer_length}, width={scene.vehicle.effective_trailer_width}")
print(f"Sensors: {len(scene.sensors)}")
for s in scene.sensors:
    if s.enabled:
        print(f"  {s.name:8s} pos=({s.x:+.2f},{s.y:+.2f}) ang={s.mount_angle:+.0f} hfov={s.hfov:.0f} range={s.range:.0f}")

out = os.path.join(os.path.dirname(__file__), "test_occlusion_full.png")
ft.export_diagram_hq(scene, out)
print(f"\nWrote: {out}")
print(f"File size: {os.path.getsize(out)} bytes")
