"""车体周围 30m 直接测试，更直观显示遮挡效果"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Rectangle
import fov_tools as ft


# 准备一个能演示遮挡的场景:
# 车: width=2, length=4.8
# sensor 1: 在车顶中心 (0, -2.0) 朝向 0° (前方), 360 度环视
# sensor 2: 在车后保险杠后 (0, -6.0) 朝向 0° (前方) — 这个 sensor 看车头方向, 应被车挡住
veh = ft.VehicleConfig(width=2.0, length=4.8, trailer_length=8.0, trailer_width=2.4)

s_top = ft.SensorConfig(name="车顶环视", x=0.0, y=-2.0, mount_angle=0,
                        hfov=360, vfov=30, range=30, color="#FF6B6B", opacity=0.3)
s_back = ft.SensorConfig(name="车后看前", x=0.0, y=-15.0, mount_angle=0,
                         hfov=120, vfov=30, range=30, color="#4ECDC4", opacity=0.4)

fig, axes = plt.subplots(1, 2, figsize=(14, 7), facecolor="white")

for ax, sensor, title in [(axes[0], s_top, "车头顶环视 360° (背后挂车遵从遮挡)"),
                          (axes[1], s_back, "挂车后看前 (两节车体都遮挡)")]:
    # 计算 visible 多边形 (world)
    vis_world = ft.compute_visible_fov_world(sensor, veh, n_samples=361)
    print(f"{title}: {len(vis_world)} pts")
    print(f"  first 3: {vis_world[:3]}")

    # 画多边形
    if len(vis_world) >= 3:
        poly = MplPolygon(vis_world, closed=True, facecolor=sensor.color,
                          alpha=sensor.opacity, edgecolor=sensor.color, linewidth=1)
        ax.add_patch(poly)

    # 画车头
    ax.add_patch(Rectangle((-veh.width/2, -veh.length), veh.width, veh.length,
                            facecolor="#3C4043", edgecolor="white", linewidth=2,
                            zorder=10))
    # 画挂车
    if veh.trailer_length > 0:
        tw = veh.effective_trailer_width
        ax.add_patch(Rectangle((-tw/2, -veh.length-veh.trailer_length),
                                tw, veh.trailer_length,
                                facecolor="#2D3033", edgecolor="white",
                                linewidth=2, zorder=10))

    # sensor 位置
    ax.plot(sensor.x, sensor.y, 'o', color="white", markeredgecolor="black",
            markersize=10, zorder=20)

    ax.set_xlim(-20, 20); ax.set_ylim(-20, 20)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.set_title(title)
    ax.set_xlabel("X (m, lateral)")
    ax.set_ylabel("Y (m, forward)")

plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "demo_occlusion.png"),
            dpi=120, facecolor="white")
print("\nWrote demo_occlusion.png")
