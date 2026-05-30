"""Standalone sample export — no Qt required."""
import math, uuid
from dataclasses import dataclass, field
from typing import List

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge, FancyBboxPatch
from matplotlib.gridspec import GridSpec
import matplotlib.colors as mcolors

# ── minimal data classes ──────────────────────────────────────
@dataclass
class VehicleConfig:
    length: float = 4.8
    width:  float = 2.0

@dataclass
class SensorConfig:
    id:          str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name:        str   = "Sensor"
    sensor_type: str   = "camera"
    x:           float = 0.0
    y:           float = 0.0
    mount_angle: float = 0.0
    hfov:        float = 90.0
    vfov:        float = 60.0
    range:       float = 60.0
    color:       str   = "#4A90D9"
    opacity:     float = 0.30
    enabled:     bool  = True
    disp_hfov:   float = 0.0   # 0 = same as hfov

@dataclass
class SceneConfig:
    vehicle: VehicleConfig       = field(default_factory=VehicleConfig)
    sensors: List[SensorConfig]  = field(default_factory=list)

# ── sample HW30-style sensor layout ──────────────────────────
def make_sample() -> SceneConfig:
    cfg = SceneConfig()
    rows = [
        dict(name="前向双目摄像头", x=0.0,  y=2.4,  mount_angle=0,   hfov=60,  vfov=40, range=400, color="#1565C0", opacity=0.25),
        dict(name="前向广角摄像头", x=0.0,  y=2.4,  mount_angle=0,   hfov=120, vfov=60, range=60,  color="#42A5F5", opacity=0.30),
        dict(name="前向激光雷达",   x=0.0,  y=1.5,  mount_angle=0,   hfov=120, vfov=30, range=250, color="#E8860C", opacity=0.22),
        dict(name="前向毫米波雷达", x=0.0,  y=2.4,  mount_angle=0,   hfov=120, vfov=10, range=210, color="#27AE60", opacity=0.20),
        dict(name="左侧向摄像头",   x=-1.0, y=0.0,  mount_angle=-90, hfov=120, vfov=60, range=60,  color="#7B1FA2", opacity=0.28),
        dict(name="右侧向摄像头",   x=1.0,  y=0.0,  mount_angle=90,  hfov=120, vfov=60, range=60,  color="#9C27B0", opacity=0.28),
        dict(name="后向摄像头",     x=0.0,  y=-2.4, mount_angle=180, hfov=60,  vfov=60, range=110, color="#F44336", opacity=0.28),
        dict(name="后向毫米波雷达", x=0.0,  y=-2.4, mount_angle=180, hfov=120, vfov=10, range=70,  color="#4CAF50", opacity=0.20),
        # demonstrate disp_hfov: radar with 120° physical, showing only 60°
        dict(name="窄角前向雷达(示例)", x=0.0, y=2.4, mount_angle=0, hfov=120, vfov=10, range=350,
             color="#00BCD4", opacity=0.18, disp_hfov=60.0),
    ]
    for r in rows:
        cfg.sensors.append(SensorConfig(**r))
    return cfg

# ── export function (self-contained copy) ─────────────────────
def export_diagram_hq(scene_cfg, path, width_px=3200, bg='white', show_legend=True):
    sensors   = scene_cfg.sensors
    draw_list = [s for s in sensors if s.enabled] or sensors

    if draw_list:
        lat_max = max(abs(s.x) + s.range for s in draw_list)
        fwd_max = max(s.y + s.range       for s in draw_list)
        bk_max  = max(max(0, -(s.y - s.range)) for s in draw_list)
    else:
        lat_max = 150; fwd_max = 250; bk_max = 50

    def snap(v, step=50): return max(step, math.ceil(v / step) * step)
    lat_max = snap(lat_max); fwd_max = snap(fwd_max); bk_max = snap(max(bk_max, 25), 25)
    disp_x  = fwd_max + bk_max; disp_y = lat_max * 2
    grid_step = 50 if max(disp_x, disp_y) > 250 else 25

    dpi = 150
    total_budget = width_px / dpi
    legend_in  = max(3.0, total_budget * 0.20) if (show_legend and sensors) else 0.0
    diagram_in = max(8.0, total_budget - legend_in)
    total_w = diagram_in + legend_in
    total_h = diagram_in * (disp_y / disp_x)

    is_dark    = bg not in ('white', '#FFFFFF', '#ffffff')
    fg         = '#BBBBBB' if is_dark else '#444444'
    grid_c     = '#3A4A5A' if is_dark else '#BDD7EE'
    spine_c    = '#555555' if is_dark else '#CCCCCC'
    veh_face   = '#2C2C2C' if is_dark else '#F0F0F0'
    veh_edge   = '#999999' if is_dark else '#666666'

    fig = plt.figure(figsize=(total_w, total_h), facecolor=bg, dpi=dpi)
    if show_legend and sensors:
        gs = GridSpec(1, 2, figure=fig, width_ratios=[legend_in, diagram_in],
                      left=0.005, right=0.995, top=0.975, bottom=0.065, wspace=0.015)
        ax_leg = fig.add_subplot(gs[0]); ax = fig.add_subplot(gs[1])
    else:
        ax = fig.add_axes([0.055, 0.065, 0.930, 0.900]); ax_leg = None

    ax.set_facecolor(bg)
    ax.set_xlim(-bk_max, fwd_max); ax.set_ylim(-lat_max, lat_max)
    ax.set_aspect('equal', adjustable='box')

    for gx in range(-bk_max, fwd_max+1, grid_step): ax.axvline(gx, color=grid_c, lw=0.55, zorder=0)
    for gy in range(-lat_max, lat_max+1, grid_step): ax.axhline(gy, color=grid_c, lw=0.55, zorder=0)
    ax.axvline(0, color=spine_c, lw=1.0, zorder=1); ax.axhline(0, color=spine_c, lw=1.0, zorder=1)

    for s in sorted(draw_list, key=lambda s: -s.range):
        cx, cy  = s.y, s.x
        mid     = s.mount_angle
        vis_h   = s.disp_hfov if s.disp_hfov > 0 else s.hfov
        t1, t2  = mid - vis_h/2, mid + vis_h/2
        ax.add_patch(Wedge((cx,cy), s.range*1.02, t1, t2,
                           facecolor=s.color, alpha=min(0.12, s.opacity*0.35), edgecolor='none', zorder=2))
        ax.add_patch(Wedge((cx,cy), s.range, t1, t2,
                           facecolor=s.color, alpha=s.opacity,
                           edgecolor=s.color, linewidth=0.8, zorder=3))
        # If disp_hfov < hfov, show the full physical FOV as a dashed outline
        if 0 < s.disp_hfov < s.hfov:
            ax.add_patch(Wedge((cx,cy), s.range, mid-s.hfov/2, mid+s.hfov/2,
                               facecolor='none', edgecolor=s.color,
                               linewidth=0.7, linestyle='--', alpha=0.35, zorder=2))
        mr = math.radians(mid); ir = min(s.range*0.07, 2.5)
        ax.plot([cx+ir*math.cos(mr), cx+s.range*0.9*math.cos(mr)],
                [cy+ir*math.sin(mr), cy+s.range*0.9*math.sin(mr)],
                color=s.color, lw=0.7, alpha=0.5, zorder=4)
        ax.plot(cx, cy, 'o', color=s.color, ms=3.5, mec='white', mew=0.6, zorder=5)

    v = scene_cfg.vehicle
    ax.add_patch(FancyBboxPatch((-v.length/2, -v.width/2), v.length, v.width,
                                boxstyle='round,pad=0.15',
                                facecolor=veh_face, edgecolor=veh_edge, lw=1.5, zorder=6))
    ax.text(v.length/2+0.6, 0, 'F', ha='left', va='center', fontsize=8, fontweight='bold',
            color=veh_edge, zorder=7)

    tick_fs = max(6.5, min(9.5, diagram_in*0.55))
    ax.set_xticks(list(range(-bk_max, fwd_max+1, grid_step)))
    ax.set_yticks(list(range(-lat_max, lat_max+1, grid_step)))
    ax.set_xticklabels([f'{abs(x)}m' if x!=0 else '' for x in range(-bk_max, fwd_max+1, grid_step)],
                       fontsize=tick_fs, color=fg)
    ax.set_yticklabels([f'{abs(y)}m' if y!=0 else '' for y in range(-lat_max, lat_max+1, grid_step)],
                       fontsize=tick_fs, color=fg)
    for sp in ax.spines.values(): sp.set_color(spine_c); sp.set_linewidth(0.7)
    ax.tick_params(length=3.5, width=0.7, color=spine_c, pad=2.5)

    if ax_leg is not None:
        ax_leg.set_facecolor(bg); ax_leg.set_xlim(0,1); ax_leg.set_ylim(0,1); ax_leg.axis('off')
        n = len(sensors)
        if n:
            gap = 0.012; card_h = (1-(n+1)*gap)/n
            card_h_in = total_h * card_h
            name_fs = max(9.0, min(15.0, card_h_in*72*0.28))
            fov_fs  = max(7.0, min(11.0, card_h_in*72*0.20))
            for i, s in enumerate(sensors):
                y_top = 1-(i*(card_h+gap)+gap); y_bot = y_top-card_h
                r,g,b = mcolors.to_rgb(s.color)
                card_bg = (r*.12+.84, g*.12+.84, b*.12+.84) if not is_dark else (r*.20+.05, g*.20+.05, b*.20+.05)
                alpha_c = 1.0 if s.enabled else 0.38
                ax_leg.add_patch(FancyBboxPatch((0.03, y_bot+0.004), 0.94, card_h-0.008,
                    boxstyle='round,pad=0.01', facecolor=card_bg, edgecolor='none',
                    transform=ax_leg.transAxes, zorder=1, alpha=alpha_c))
                ax_leg.add_patch(mpatches.Rectangle((0.03, y_bot+0.004), 0.048, card_h-0.008,
                    facecolor=s.color, edgecolor='none',
                    transform=ax_leg.transAxes, zorder=2, alpha=alpha_c))
                y_mid = (y_top+y_bot)/2
                ax_leg.text(0.12, y_mid+card_h*0.15, s.name,
                    transform=ax_leg.transAxes, fontsize=name_fs, fontweight='bold',
                    color=s.color, va='center', ha='left', alpha=alpha_c, clip_on=True)
                fov_str = f"FOV: {s.range:.0f}m / {s.hfov:.0f}°"
                if s.disp_hfov > 0: fov_str += f" (显示:{s.disp_hfov:.0f}°)"
                if s.vfov > 0: fov_str += f"  V:{s.vfov:.0f}°"
                ax_leg.text(0.12, y_mid-card_h*0.15, fov_str,
                    transform=ax_leg.transAxes, fontsize=fov_fs,
                    color='#555555' if not is_dark else '#AAAAAA',
                    va='center', ha='left', alpha=alpha_c, clip_on=True)

    plt.savefig(path, dpi=dpi, bbox_inches='tight', facecolor=bg, edgecolor='none')
    plt.close(fig)
    print(f"  Saved → {path}")


if __name__ == '__main__':
    cfg = make_sample()
    out = r'c:\Fuyue_WorkSpace\FOVTools\sample_output.png'
    print(f"Generating sample diagram …")
    export_diagram_hq(cfg, out, width_px=3200)
    print("Done.")
