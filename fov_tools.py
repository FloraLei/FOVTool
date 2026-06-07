#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOV Tools v1.0  —  传感器视场角可视化工具
Sensor Field-of-View Visualization and Management Tool

Supports: Camera (摄像头) | Millimeter-Wave Radar (毫米波雷达) | LiDAR (激光雷达)

Usage:
    python fov_tools.py
"""

import sys
import os
import warnings
warnings.simplefilter("ignore")

# Robust stream redirection to prevent crashes when stdout/stderr are invalid or closed in non-console mode
if getattr(sys, 'frozen', False):
    stdout_ok = False
    try:
        if sys.stdout is not None:
            sys.stdout.write("")
            sys.stdout.flush()
            stdout_ok = True
    except Exception:
        pass

    if not stdout_ok:
        class SafeStream:
            def write(self, data):
                pass
            def flush(self):
                pass
            def isatty(self):
                return False
            def fileno(self):
                return -1

        try:
            devnull_fd = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull_fd, 1)
            os.dup2(devnull_fd, 2)
        except Exception:
            pass

        sys.stdout = SafeStream()
        sys.stderr = SafeStream()
        sys.__stdout__ = SafeStream()
        sys.__stderr__ = SafeStream()

import json
import math
import uuid
import copy
import re
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict, fields as dc_fields
from typing import List, Optional, Tuple

import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QColorDialog,
    QSlider, QDoubleSpinBox, QCheckBox, QListWidget, QListWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsItemGroup,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsPolygonItem,
    QGraphicsPixmapItem,
    QFileDialog, QMessageBox, QTabWidget, QToolBar, QAction,
    QDialog, QDialogButtonBox, QSpinBox,
    QSizePolicy, QSplitter, QFrame, QGroupBox, QScrollArea,
    QMenu, QStatusBar, QInputDialog, QAbstractItemView,
    QGraphicsSimpleTextItem, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt5.QtCore import (
    Qt, QPointF, QRectF, QRect, QSizeF, pyqtSignal, QObject,
    QLineF, QSize, QTimer,
)
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QFont,
    QTransform, QIcon, QPixmap, QImage, QKeySequence,
    QPolygonF, QCursor, QPainterPathStroker,
)

import matplotlib
matplotlib.use('Qt5Agg')
matplotlib.rcParams['font.sans-serif'] = [
    'Microsoft YaHei', 'SimHei', 'PingFang SC', 'Noto Sans CJK SC', 'DejaVu Sans'
]
matplotlib.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401 – registers 3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches


# ══════════════════════════════════════════════════════════════
#  CONSTANTS & SENSOR METADATA
# ══════════════════════════════════════════════════════════════
APP_NAME = "FOV Tools"
APP_VERSION = "1.0"

SENSOR_META = {
    "camera": dict(zh="摄像头",     color="#4A90D9", hfov=90,  vfov=60,  rng=60,  opacity=0.30),
    "radar":  dict(zh="毫米波雷达", color="#27AE60", hfov=120, vfov=10,  rng=210, opacity=0.22),
    "lidar":  dict(zh="激光雷达",   color="#E8860C", hfov=120, vfov=30,  rng=250, opacity=0.22),
}

# Pre-built HW 3.0 sensor configuration (extracted from reference PDF)
HW30_SENSORS = [
    dict(name="前向双目摄像头", sensor_type="camera", x=0.0,   y=2.40, z=1.2, mount_angle=0,   hfov=60,  vfov=40, range=400, color="#1565C0", opacity=0.25),
    dict(name="前中广角摄像头", sensor_type="camera", x=0.0,   y=2.40, z=1.2, mount_angle=0,   hfov=120, vfov=60, range=60,  color="#42A5F5", opacity=0.32),
    dict(name="前向激光雷达",   sensor_type="lidar",  x=0.0,   y=1.50, z=1.8, mount_angle=0,   hfov=120, vfov=30, range=250, color="#E8860C", opacity=0.22),
    dict(name="前向毫米波雷达", sensor_type="radar",  x=0.0,   y=2.40, z=0.4, mount_angle=0,   hfov=120, vfov=10, range=210, color="#27AE60", opacity=0.20),
    dict(name="左侧向摄像头",   sensor_type="camera", x=-1.0,  y=0.00, z=0.7, mount_angle=-90, hfov=120, vfov=60, range=60,  color="#7B1FA2", opacity=0.30),
    dict(name="右侧向摄像头",   sensor_type="camera", x=1.0,   y=0.00, z=0.7, mount_angle=90,  hfov=120, vfov=60, range=60,  color="#9C27B0", opacity=0.30),
    dict(name="后向摄像头",     sensor_type="camera", x=0.0,   y=-2.40,z=1.2, mount_angle=180, hfov=60,  vfov=60, range=110, color="#F44336", opacity=0.28),
    dict(name="后向毫米波雷达", sensor_type="radar",  x=0.0,   y=-2.40,z=0.4, mount_angle=180, hfov=120, vfov=10, range=70,  color="#4CAF50", opacity=0.20),
]


# ══════════════════════════════════════════════════════════════
#  OCR + SENSOR-LEGEND PARSER
# ══════════════════════════════════════════════════════════════

# PowerShell script that calls the Windows 10+ built-in OCR engine.
# No third-party packages needed — works on every Windows 10/11 system.
_PS_OCR_SCRIPT = r"""
$null = [System.Reflection.Assembly]::LoadWithPartialName('System.Runtime.WindowsRuntime')
$methods = [System.WindowsRuntimeSystemExtensions].GetMethods()
$asTaskG  = ($methods | Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
function Await([object]$task, [type]$T) {
    $net = $asTaskG.MakeGenericMethod($T).Invoke($null, @($task))
    $net.Wait(-1) | Out-Null
    return $net.Result
}
[void][Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
[void][Windows.Media.Ocr.OcrEngine,Windows.Media.Ocr,ContentType=WindowsRuntime]
[void][Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$imgPath = '{IMG}'
$f   = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imgPath)) ([Windows.Storage.StorageFile])
$stm = Await ($f.OpenReadAsync())                                             ([Windows.Storage.Streams.IRandomAccessStream])
$dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stm))   ([Windows.Graphics.Imaging.BitmapDecoder])
$bmp = Await ($dec.GetSoftwareBitmapAsync())                                  ([Windows.Graphics.Imaging.SoftwareBitmap])
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $eng) { Write-Error 'OCR engine unavailable'; exit 1 }
$res = Await ($eng.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
Write-Output $res.Text
"""


def _ocr_image_windows(image_path: str) -> str:
    """Use the built-in Windows OCR engine to read text from an image.

    Requires Windows 10 or later (no extra Python packages).
    Returns the recognized Unicode text.
    """
    abs_path = os.path.abspath(image_path).replace("'", "''")  # escape PS single-quotes
    script = _PS_OCR_SCRIPT.replace('{IMG}', abs_path)
    # Write script to a temp file to avoid command-line length limits
    with tempfile.NamedTemporaryFile('w', suffix='.ps1', delete=False,
                                     encoding='utf-8') as tf:
        tf.write(script)
        ps_path = tf.name
    try:
        res = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive',
             '-ExecutionPolicy', 'Bypass', '-File', ps_path],
            capture_output=True, text=True, timeout=45
        )
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or f"exit code {res.returncode}")
        return res.stdout.strip()
    finally:
        try:
            os.unlink(ps_path)
        except OSError:
            pass


def _parse_sensor_legend(text: str) -> list:
    """Parse OCR text from a sensor-legend image into a list of sensor dicts.

    Expected legend format (one sensor per block):
        <Sensor Name>
        FOV: <range>m/<hfov>°  [optional V:<vfov>°]

    Both English and Chinese text is handled.
    """
    # Normalize: remove stray OCR artifacts, collapse multiple spaces
    lines = []
    for raw in text.splitlines():
        ln = raw.strip()
        # Normalize common OCR mis-reads
        ln = ln.replace('：', ':').replace('／', '/').replace('°', '°')
        if ln:
            lines.append(ln)

    # FOV line pattern:  FOV: [>~≈]?<range>m[/<hfov>°][  &  <range2>m/<hfov2>°]
    _FOV_RE = re.compile(
        r'FOV\s*:\s*[>~≈]?\s*(\d+(?:\.\d+)?)\s*m\s*[/／]\s*(\d+(?:\.\d+)?)\s*°',
        re.IGNORECASE
    )
    # Optional vertical FOV:  @<pct>%  or  V:<deg>°
    _VFOV_RE = re.compile(r'(?:V\s*:\s*|@\s*)(\d+(?:\.\d+)?)[%°]', re.IGNORECASE)

    sensors: list = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # If this line already matches FOV, skip (part of a previous block)
        if _FOV_RE.search(line):
            i += 1
            continue
        # Look ahead for the FOV line (allow one blank/noise line between)
        fov_line = None
        fov_idx  = None
        for j in (i + 1, i + 2):
            if j < len(lines) and _FOV_RE.search(lines[j]):
                fov_line = lines[j]
                fov_idx  = j
                break
        if fov_line is None:
            i += 1
            continue

        m = _FOV_RE.search(fov_line)
        rng  = float(m.group(1))
        hfov = float(m.group(2))

        # Try vfov
        vm = _VFOV_RE.search(fov_line)
        vfov = float(vm.group(1)) if vm else 30.0

        # Infer sensor type from name keywords
        nl = line.lower()
        if any(k in nl for k in ('lidar', '激光', 'laser')):
            stype = 'lidar'
        elif any(k in nl for k in ('radar', '毫米波', 'millimeter', 'mm-wave')):
            stype = 'radar'
        else:
            stype = 'camera'

        meta = SENSOR_META[stype]
        sensors.append(dict(
            name        = line,
            sensor_type = stype,
            range       = rng,
            hfov        = hfov,
            vfov        = vfov,
            color       = meta['color'],
            opacity     = meta['opacity'],
        ))
        i = fov_idx + 1

    return sensors


# ══════════════════════════════════════════════════════════════
#  DATA MODELS
# ══════════════════════════════════════════════════════════════
@dataclass
class SensorConfig:
    id:           str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name:         str   = "Sensor"
    sensor_type:  str   = "camera"
    x:            float = 0.0          # lateral  (right = +)  meters
    y:            float = 0.0          # longitudinal (fwd = +) meters
    z:            float = 0.5          # height meters
    mount_angle:  float = 0.0          # 横摆角 Yaw (degrees); 0=forward, CW positive
    pitch:        float = 0.0          # 俯仰角 Pitch (degrees); 0=horizontal, +up, -down
    roll:         float = 0.0          # 滚转角 Roll (degrees); 0=horizontal, CW positive
    hfov:         float = 90.0         # horizontal FOV degrees
    vfov:         float = 60.0         # vertical FOV degrees
    range:        float = 60.0         # detection range meters
    color:        str   = "#4A90D9"
    opacity:      float = 0.30
    enabled:      bool  = True
    disp_hfov:    float = 0.0          # displayed FOV arc degrees; 0 = same as hfov
    clip_by_vehicle: bool = True       # clip FOV by vehicle occlusion (new)
    clip_range:   float = 0.0          # manual clip distance; 0=auto compute (new)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        valid = {f.name for f in dc_fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})

    @classmethod
    def new(cls, sensor_type="camera", **kw):
        m = SENSOR_META[sensor_type]
        return cls(
            sensor_type=sensor_type,
            color=m["color"],
            hfov=m["hfov"], vfov=m["vfov"],
            range=m["rng"], opacity=m["opacity"],
            **kw,
        )


@dataclass
class LaneParamConfig:
    """参数化车道线配置"""
    lane_width:     float = 3.75       # 中心线到中心线宽度 (m)
    line_width:     float = 0.15       # 车道线自身宽度 (m)
    lateral_offset: float = 0.0        # 相对车辆Y0的偏移 (m)
    curvature_r:    float = 0.0        # 弯道半径 R (m, 0=直)
    left_lines:     int   = 1          # 左侧车道线数量
    right_lines:    int   = 1          # 右侧车道线数量
    length:         float = 1000.0     # 车道线长度 (m)
    color_outer:    str   = "#FFFFFF"  # 外侧边界线颜色 (默认白色)
    color_inner:    str   = "#FFCC00"  # 内侧分界线/中心虚线颜色 (默认黄色)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        valid = {f.name for f in dc_fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class TargetVehicleConfig:
    """目标车辆配置"""
    id:      str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name:    str   = "Target"
    x:       float = 0.0        # 横向坐标 (X, meters)
    y:       float = 20.0       # 纵向坐标 (Y, meters, 车前为正)
    heading: float = 0.0        # 航向角 (degrees, 0 = 同向朝前)
    length:  float = 4.8        # 车长 (meters)
    width:   float = 2.0        # 车宽 (meters)
    color:   str   = "#FF5252"   # 车辆填充颜色 (默认红色)
    enabled: bool  = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        valid = {f.name for f in dc_fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class VehicleConfig:
    length: float = 4.8        # 车头(牵引车)长度
    width:  float = 2.0        # 车头(牵引车)宽度
    height: float = 1.5        # 车头(牵引车)高度
    trailer_length: float = 0.0  # 挂车长度 (0 表示无挂车)
    trailer_width:  float = 0.0  # 挂车宽度 (0 表示与车头同宽)
    name:   str   = "Vehicle"

    def to_dict(self):   return asdict(self)
    @classmethod
    def from_dict(cls, d): return cls(**{k: v for k, v in d.items() if k in {f.name for f in dc_fields(cls)}})

    @property
    def effective_trailer_width(self) -> float:
        """挂车实际宽度 (=trailer_width 或回退到车头宽度)."""
        return self.trailer_width if self.trailer_width > 0 else self.width

    @property
    def total_length(self) -> float:
        """车头 + 挂车整体长度."""
        return self.length + max(0.0, self.trailer_length)

    @property
    def max_width(self) -> float:
        """车头与挂车的最大宽度 (用于视图边界)."""
        return max(self.width, self.effective_trailer_width if self.trailer_length > 0 else 0.0)


@dataclass
class SceneConfig:
    vehicle:         VehicleConfig              = field(default_factory=VehicleConfig)
    sensors:         List[SensorConfig]        = field(default_factory=list)
    lane_params:     LaneParamConfig            = field(default_factory=LaneParamConfig)
    target_vehicles: List[TargetVehicleConfig]  = field(default_factory=list)
    show_grid:       bool                       = True
    show_labels:     bool                       = False
    show_overlap:    bool                       = False

    def to_dict(self):
        return dict(
            vehicle=self.vehicle.to_dict(),
            sensors=[s.to_dict() for s in self.sensors],
            lane_params=self.lane_params.to_dict(),
            target_vehicles=[tv.to_dict() for tv in self.target_vehicles],
            show_grid=self.show_grid,
            show_labels=self.show_labels,
            show_overlap=self.show_overlap,
        )

    @classmethod
    def from_dict(cls, d: dict):
        lp_dict = d.get("lane_params", {})
        if not lp_dict and "lane_lines" in d:
            lp = LaneParamConfig()
        else:
            lp = LaneParamConfig.from_dict(lp_dict)

        return cls(
            vehicle=VehicleConfig.from_dict(d.get("vehicle", {})),
            sensors=[SensorConfig.from_dict(s) for s in d.get("sensors", [])],
            lane_params=lp,
            target_vehicles=[TargetVehicleConfig.from_dict(tv) for tv in d.get("target_vehicles", [])],
            show_grid=d.get("show_grid", True),
            show_labels=d.get("show_labels", True),
            show_overlap=d.get("show_overlap", False),
        )

    @classmethod
    def hw30(cls):
        sensors = []
        for sd in HW30_SENSORS:
            s = SensorConfig.from_dict(dict(
                id=str(uuid.uuid4())[:8],
                enabled=True,
                **sd,
            ))
            sensors.append(s)
        return cls(sensors=sensors)


# ══════════════════════════════════════════════════════════════
#  GEOMETRY UTILITIES
#  World coords: +X = right, +Y = forward, angle 0°=forward CW
#  Scene coords: +X = right, +Y = down  (flip Y from world)
# ══════════════════════════════════════════════════════════════
def w2s(wx: float, wy: float) -> Tuple[float, float]:
    """World → scene (meters, Y-flipped)."""
    return wx, -wy


def s2w(sx: float, sy: float) -> Tuple[float, float]:
    """Scene → world."""
    return sx, -sy


def fov_path(sensor: SensorConfig, n_pts: int = 60) -> QPainterPath:
    """Build a filled FOV arc QPainterPath in scene (meter) coordinates."""
    if sensor.hfov <= 0 or sensor.range <= 0:
        return QPainterPath()

    vis = getattr(sensor, 'disp_hfov', 0.0) or sensor.hfov
    h2 = vis / 2.0
    angles_rad = np.linspace(
        math.radians(sensor.mount_angle - h2),
        math.radians(sensor.mount_angle + h2),
        max(n_pts, int(vis)),
    )

    # Arc points in world offsets from sensor origin
    ax = sensor.range * np.sin(angles_rad)   # world X (right)
    ay = sensor.range * np.cos(angles_rad)   # world Y (forward)

    path = QPainterPath()
    path.moveTo(0.0, 0.0)                     # sensor origin (local)
    # Convert world offsets to scene offsets (flip Y)
    first = QPointF(float(ax[0]), float(-ay[0]))
    path.lineTo(first)
    for i in range(1, len(ax)):
        path.lineTo(float(ax[i]), float(-ay[i]))
    path.closeSubpath()
    return path


def fov_cone_faces(sensor: SensorConfig, n_az: int = 24, n_el: int = 6):
    """Return list of 3-D quad faces [[(x,y,z)×4], …] for the FOV pyramid."""
    if sensor.hfov <= 0 or sensor.range <= 0:
        return []

    az0 = math.radians(sensor.mount_angle)
    h2  = math.radians(sensor.hfov / 2)
    v2  = math.radians(sensor.vfov / 2)

    el0 = math.radians(getattr(sensor, 'pitch', 0.0))
    roll0 = math.radians(getattr(sensor, 'roll', 0.0))
    azs = np.linspace(az0 - h2, az0 + h2, n_az)
    els = np.linspace(el0 - v2, el0 + v2, n_el)
    tip = np.array([sensor.x, sensor.y, sensor.z])

    # If roll is non-zero, calculate optical axis vector for Rodrigues' rotation formula
    if roll0 != 0:
        ux = math.sin(az0) * math.cos(el0)
        uy = math.cos(az0) * math.cos(el0)
        uz = math.sin(el0)
        u = np.array([ux, uy, uz])
        cos_r = math.cos(roll0)
        sin_r = math.sin(roll0)

    def ray(az, el):
        v = np.array([
            math.sin(az) * math.cos(el),   # X right
            math.cos(az) * math.cos(el),   # Y forward
            math.sin(el),                  # Z up
        ])
        if roll0 != 0:
            cross_uv = np.cross(u, v)
            dot_uv = np.dot(u, v)
            v = v * cos_r + cross_uv * sin_r + u * dot_uv * (1.0 - cos_r)
        return tip + sensor.range * v

    faces = []
    for i in range(n_az - 1):
        for j in range(n_el - 1):
            p = [ray(azs[i], els[j]), ray(azs[i+1], els[j]),
                 ray(azs[i+1], els[j+1]), ray(azs[i], els[j+1])]
            faces.append(p)
    # Left triangle fan
    for j in range(n_el - 1):
        faces.append([tip, ray(azs[0], els[j]), ray(azs[0], els[j+1])])
    # Right triangle fan
    for j in range(n_el - 1):
        faces.append([tip, ray(azs[-1], els[j]), ray(azs[-1], els[j+1])])
    # Bottom/top strip
    for i in range(n_az - 1):
        faces.append([tip, ray(azs[i], els[0]),  ray(azs[i+1], els[0])])
        faces.append([tip, ray(azs[i], els[-1]), ray(azs[i+1], els[-1])])
    return faces


# ══════════════════════════════════════════════════════════════
#  APP-WIDE SIGNAL BUS
# ══════════════════════════════════════════════════════════════
class AppSignals(QObject):
    sensor_selected  = pyqtSignal(str)   # sensor id
    sensor_deselected= pyqtSignal()
    sensor_moved     = pyqtSignal(str)   # sensor id
    sensor_changed   = pyqtSignal(str)   # sensor id – property edit
    sensor_added     = pyqtSignal(str)
    sensor_removed   = pyqtSignal(str)
    vehicle_changed  = pyqtSignal()
    scene_rebuilt    = pyqtSignal()      # full rebuild needed
    lane_changed            = pyqtSignal()      # lane parameter edit
    target_vehicle_added    = pyqtSignal(str)   # target vehicle id
    target_vehicle_removed  = pyqtSignal(str)   # target vehicle id
    target_vehicle_changed  = pyqtSignal(str)   # target vehicle id - property edit
    target_vehicle_selected = pyqtSignal(str)   # target vehicle id
    zoom_mode_changed       = pyqtSignal(bool)


# ══════════════════════════════════════════════════════════════
#  CUSTOM GRAPHICS ITEMS
# ══════════════════════════════════════════════════════════════
MARKER_RADIUS = 0.35   # meters – sensor marker circle radius

class SensorGraphicsItem(QGraphicsItemGroup):
    """Compound graphics item: FOV arc + sensor marker + label."""

    def __init__(self, sensor: SensorConfig, signals: AppSignals, scene_cfg: SceneConfig = None, parent=None):
        super().__init__(parent)
        self.sensor  = sensor
        self.signals = signals
        self.scene_cfg = scene_cfg
        self._moving = False

        self.setFlag(QGraphicsItem.ItemIsSelectable,          True)
        self.setFlag(QGraphicsItem.ItemIsMovable,             True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges,  True)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

        # ── FOV arc ──────────────────────────────────────────
        self._fov = QGraphicsPathItem(self)
        self._fov.setZValue(1)

        # ── Sensor marker ────────────────────────────────────
        r = MARKER_RADIUS
        self._marker = QGraphicsEllipseItem(-r, -r, 2*r, 2*r, self)
        self._marker.setZValue(3)

        # ── Direction tick ────────────────────────────────────
        self._tick = QGraphicsLineItem(0, 0, 0, -r * 1.8, self)
        self._tick.setZValue(4)

        # ── Label ─────────────────────────────────────────────
        self._label = QGraphicsSimpleTextItem(self)
        self._label.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._label.setZValue(5)

        # Position group at sensor world coords
        sx, sy = w2s(sensor.x, sensor.y)
        self.setPos(sx, sy)

        self._refresh()

    # ── internal update ───────────────────────────────────────
    def _refresh(self):
        s = self.sensor
        color = QColor(s.color)

        # FOV fill
        fp = fov_path(s) if s.enabled else QPainterPath()
        self._fov.setPath(fp)
        fill = QColor(color)
        fill.setAlphaF(s.opacity if s.enabled else 0.0)
        self._fov.setBrush(QBrush(fill))
        pen_color = QColor(color)
        pen_color.setAlphaF(0.8 if s.enabled else 0.3)
        self._fov.setPen(QPen(pen_color, 0.05))  # 0.05 m stroke

        # Marker
        marker_color = color if s.enabled else QColor("#aaaaaa")
        self._marker.setBrush(QBrush(marker_color))
        self._marker.setPen(QPen(Qt.white, 0.12))

        # Tick (points in forward direction relative to mount angle)
        angle_rad = math.radians(s.mount_angle)
        dx =  math.sin(angle_rad) * MARKER_RADIUS * 1.8
        dy = -math.cos(angle_rad) * MARKER_RADIUS * 1.8   # scene Y flip
        self._tick.setLine(0, 0, dx, dy)
        self._tick.setPen(QPen(Qt.white, 0.10))

        # Label
        self._label.setText(s.name)
        self._label.setBrush(QBrush(marker_color))
        font = QFont("Microsoft YaHei UI", 8)
        self._label.setFont(font)
        # Place label below marker in scene
        br = self._label.boundingRect()
        # Offset in screen pixels relative to scene position (ignores transform)
        self._label.setPos(MARKER_RADIUS + 2, -br.height() / 2)

        # Opacity of whole item
        self.setOpacity(1.0 if s.enabled else 0.5)

    def refresh(self):
        sx, sy = w2s(self.sensor.x, self.sensor.y)
        self.setPos(sx, sy)
        self._refresh()

    def paint(self, painter, option, widget=None):
        """Highlight border when selected."""
        super().paint(painter, option, widget)
        if self.isSelected():
            r = MARKER_RADIUS * 1.6
            painter.setPen(QPen(QColor("#FFD700"), 0.18, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), r, r)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and not self._moving:
            self._moving = True
            sx, sy = value.x(), value.y()
            wx, wy = s2w(sx, sy)
            self.sensor.x = round(wx, 3)
            self.sensor.y = round(wy, 3)
            self.signals.sensor_moved.emit(self.sensor.id)
            self._moving = False
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.signals.sensor_selected.emit(self.sensor.id)
            else:
                self.signals.sensor_deselected.emit()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self.flags() & QGraphicsItem.ItemIsMovable:
            QApplication.setOverrideCursor(Qt.SizeAllCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        act_del  = menu.addAction("删除传感器")
        act_dup  = menu.addAction("复制传感器")
        menu.addSeparator()
        act_tog  = menu.addAction("启用/禁用")
        chosen = menu.exec_(event.screenPos())
        if chosen == act_del:
            self.signals.sensor_removed.emit(self.sensor.id)
        elif chosen == act_dup:
            new_s = copy.deepcopy(self.sensor)
            new_s.id = str(uuid.uuid4())[:8]
            new_s.name += "_副本"
            new_s.x += 0.5
            if self.scene_cfg is not None:
                self.scene_cfg.sensors.append(new_s)
            self.signals.sensor_added.emit(new_s.id)
            # Store data on signal for retrieval
            self._dup_sensor = new_s
        elif chosen == act_tog:
            self.sensor.enabled = not self.sensor.enabled
            self.signals.sensor_changed.emit(self.sensor.id)


class VehicleItem(QGraphicsItem):
    """Top-down view of the vehicle body."""

    def __init__(self, cfg: VehicleConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setZValue(5)

    def boundingRect(self):
        # 车头前保险杠位于场景 (0,0)，车身在场景 Y+ 方向延伸 (世界 -Y = 向后)
        w, l = self.cfg.width, self.cfg.length
        tl = max(0.0, self.cfg.trailer_length)
        tw = self.cfg.effective_trailer_width
        max_w = max(w, tw if tl > 0 else 0.0)
        # 额外预留一些空间给前箭头、“F”标签
        return QRectF(-max_w/2 - 0.5, -0.6, max_w + 1.0, l + tl + 1.2)

    def paint(self, painter, option, widget=None):
        w, l = self.cfg.width, self.cfg.length
        tl = max(0.0, self.cfg.trailer_length)
        tw = self.cfg.effective_trailer_width

        # 车头矩形：场景 y 从 0 (车头前) 到 l (车头后)
        truck_rect = QRectF(-w/2, 0.0, w, l)

        # Truck body fill
        painter.setBrush(QBrush(QColor("#3C4043")))
        painter.setPen(QPen(QColor("#888888"), 0.05))
        painter.drawRoundedRect(truck_rect, 0.3, 0.3)

        # Forward indicator (windshield area) — 靠近车头前部
        front_y = 0.0
        painter.setBrush(QBrush(QColor("#5A7A9A")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(-w/2 + 0.15, front_y + 0.1, w - 0.3, l * 0.28), 0.2, 0.2)

        # Forward arrow (指向场景 -Y，即世界 +Y 前方)
        painter.setPen(QPen(QColor("#AAAAAA"), 0.06))
        painter.drawLine(QPointF(0, 0.2),  QPointF(0, -0.35))
        painter.drawLine(QPointF(0, -0.35), QPointF(-0.12, -0.20))
        painter.drawLine(QPointF(0, -0.35), QPointF( 0.12, -0.20))

        # "F" label
        font = QFont("Arial", 5)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#CCCCCC"))
        painter.drawText(QRectF(-0.25, front_y + 0.12, 0.5, 0.5), Qt.AlignCenter, "F")

        # 挂车矩形：场景 y 从 l 到 l+tl
        if tl > 0:
            trailer_rect = QRectF(-tw/2, l, tw, tl)
            painter.setBrush(QBrush(QColor("#2D3033")))
            painter.setPen(QPen(QColor("#888888"), 0.05))
            painter.drawRoundedRect(trailer_rect, 0.3, 0.3)

            # 车头与挂车连接点 (铰接盘示意)
            painter.setBrush(QBrush(QColor("#888888")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0.0, l), 0.18, 0.18)

            # 挂车中心 "T" 标签
            painter.setFont(font)
            painter.setPen(QColor("#BBBBBB"))
            painter.drawText(QRectF(-0.3, l + tl/2 - 0.25, 0.6, 0.5), Qt.AlignCenter, "T")


class GridItem(QGraphicsItem):
    """Background grid in meter units. Supports dark and light themes."""
    MINOR = 10   # meters
    MAJOR = 50   # meters

    def __init__(self, extent: float = 600, parent=None):
        super().__init__(parent)
        self.extent = extent
        self.setZValue(-10)
        self._dark = True    # toggleable: True=dark bg, False=light bg

    def boundingRect(self):
        e = self.extent
        return QRectF(-e, -e, 2*e, 2*e)

    def paint(self, painter, option, widget=None):
        e   = self.extent
        lv  = option.levelOfDetailFromTransform(painter.worldTransform())

        minor_c = "#333333" if self._dark else "#CCCCCC"
        major_c = "#4A4A4A" if self._dark else "#AAAAAA"
        label_c = "#666666" if self._dark else "#999999"
        axis_c  = "#888888" if self._dark else "#555555"

        # Minor grid (skip if too dense on screen)
        if lv * self.MINOR > 8:
            pen = QPen(QColor(minor_c), 0)
            pen.setCosmetic(True)
            pen.setWidthF(0.5)
            painter.setPen(pen)
            step = self.MINOR
            for v in range(-e, e+1, step):
                painter.drawLine(QPointF(-e, float(v)), QPointF(e, float(v)))
                painter.drawLine(QPointF(float(v), -e), QPointF(float(v), e))

        # Major grid
        pen = QPen(QColor(major_c), 0)
        pen.setCosmetic(True)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        step = self.MAJOR
        for v in range(-e, e+1, step):
            painter.drawLine(QPointF(-e, float(v)), QPointF(e, float(v)))
            painter.drawLine(QPointF(float(v), -e), QPointF(float(v), e))

        # Axis distance labels — adaptive step so labels never overlap
        if lv > 0.002:
            font = QFont("Arial", 8)
            font.setStyleHint(QFont.Monospace)
            painter.setFont(font)
            painter.setPen(QColor(label_c))
            
            fm_step = self.MAJOR
            for candidate in [10, 20, 50, 100, 200, 500, 1000]:
                if lv * candidate >= 65:
                    fm_step = candidate
                    break
            
            orig_transform = painter.worldTransform()
            painter.setWorldTransform(QTransform())
            
            for v in range(-e, e+1, fm_step):
                if v == 0:
                    continue
                # Horizontal labels along X-axis
                pt_h = orig_transform.map(QPointF(float(v), 0.0))
                painter.drawText(pt_h + QPointF(-12, 13), f"{v}m")
                
                # Vertical labels along Y-axis
                pt_v = orig_transform.map(QPointF(0.0, float(-v)))
                painter.drawText(pt_v + QPointF(5, 5), f"{v}m")
                
            painter.setWorldTransform(orig_transform)

        # Axes
        axis_pen = QPen(QColor(axis_c), 0)
        axis_pen.setCosmetic(True)
        axis_pen.setWidthF(1.5)
        painter.setPen(axis_pen)
        painter.drawLine(QPointF(-e, 0), QPointF(e, 0))
        painter.drawLine(QPointF(0, -e), QPointF(0, e))


class ScaleBarItem(QGraphicsItem):
    """A screen-space scale bar (always same pixel size)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setZValue(100)

    def boundingRect(self):
        return QRectF(0, 0, 200, 40)

    def paint(self, painter, option, widget=None):
        # Get current scale from view transform
        t = painter.worldTransform()
        ppm = t.m11()  # pixels per meter (scene unit = 1 m)
        if ppm <= 0:
            return

        # Choose a nice bar length in real-world meters
        bar_px = 120  # target bar length in pixels
        raw_m  = bar_px / ppm
        # Round to nice number
        for nice in [500, 200, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1]:
            if raw_m >= nice:
                bar_m = nice
                break
        else:
            bar_m = 0.1

        bar_px = bar_m * ppm

        painter.setPen(QPen(QColor("#EEEEEE"), 2))
        painter.setBrush(QBrush(QColor("#222222")))
        painter.drawRect(QRectF(0, 10, bar_px, 8))
        painter.setPen(QColor("#EEEEEE"))
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.drawText(QRectF(0, 20, bar_px, 18), Qt.AlignCenter, f"{bar_m:.4g} m")


class LanesItem(QGraphicsItem):
    """Draw parametric lane lines and road surface in Canvas2D."""

    def __init__(self, scene_cfg: SceneConfig, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.setZValue(0)  # Draw below sensor FOVs (Z=1) and vehicle (Z=5)
        self._cache_key = None
        self._cached_road_path = None
        self._cached_left_lines = []   # list of (color, style, line_width, QPainterPath)
        self._cached_right_lines = []  # list of (color, style, line_width, QPainterPath)

    def boundingRect(self):
        return QRectF(-1000, -1000, 2000, 2000)

    def paint(self, painter, option, widget=None):
        lp = self.scene_cfg.lane_params
        if lp.left_lines <= 0 and lp.right_lines <= 0:
            return

        current_key = (
            lp.curvature_r, lp.length, lp.lateral_offset, lp.lane_width,
            lp.left_lines, lp.right_lines, lp.line_width,
            lp.color_outer, lp.color_inner
        )

        if self._cache_key != current_key:
            self._cache_key = current_key
            self._cached_left_lines.clear()
            self._cached_right_lines.clear()

            y_start = -lp.length / 2.0
            y_end = lp.length / 2.0
            num_points = max(20, int(abs(y_end - y_start) / 2))
            s = np.linspace(y_start, y_end, num_points)

            def get_points(x_base):
                R = lp.curvature_r
                if R == 0.0:
                    return np.full_like(s, x_base), s
                phi = s / R
                xs = R - (R - x_base) * np.cos(phi)
                ys_curve = (R - x_base) * np.sin(phi)
                return xs, ys_curve

            # Outermost profiles for road background
            if lp.left_lines > 0:
                x_left_most = lp.lateral_offset - (lp.left_lines - 0.5) * lp.lane_width
            else:
                x_left_most = lp.lateral_offset - 0.5 * lp.lane_width

            if lp.right_lines > 0:
                x_right_most = lp.lateral_offset + (lp.right_lines - 0.5) * lp.lane_width
            else:
                x_right_most = lp.lateral_offset + 0.5 * lp.lane_width

            xs_min, ys_min = get_points(x_left_most)
            xs_max, ys_max = get_points(x_right_most)

            # Rebuild road background path
            road_path = QPainterPath()
            road_path.moveTo(xs_min[0], -ys_min[0])
            for i in range(1, len(s)):
                road_path.lineTo(xs_min[i], -ys_min[i])
            for i in range(len(s) - 1, -1, -1):
                road_path.lineTo(xs_max[i], -ys_max[i])
            road_path.closeSubpath()
            self._cached_road_path = road_path

            # Rebuild left lines
            for idx in range(1, lp.left_lines + 1):
                x_base = lp.lateral_offset - (idx - 0.5) * lp.lane_width
                is_outer = (idx == lp.left_lines)
                color = lp.color_outer if is_outer else lp.color_inner
                style = Qt.SolidLine if is_outer else Qt.DashLine

                path = QPainterPath()
                xs, ys_lane = get_points(x_base)
                path.moveTo(xs[0], -ys_lane[0])
                for i in range(1, len(s)):
                    path.lineTo(xs[i], -ys_lane[i])
                self._cached_left_lines.append((color, style, lp.line_width, path))

            # Rebuild right lines
            for idx in range(1, lp.right_lines + 1):
                x_base = lp.lateral_offset + (idx - 0.5) * lp.lane_width
                is_outer = (idx == lp.right_lines)
                color = lp.color_outer if is_outer else lp.color_inner
                style = Qt.SolidLine if is_outer else Qt.DashLine

                path = QPainterPath()
                xs, ys_lane = get_points(x_base)
                path.moveTo(xs[0], -ys_lane[0])
                for i in range(1, len(s)):
                    path.lineTo(xs[i], -ys_lane[i])
                self._cached_right_lines.append((color, style, lp.line_width, path))

        # ── DRAWING FROM CACHE ──
        # Draw dark road background surface (#21262D)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#21262D")))
        painter.drawPath(self._cached_road_path)

        # Reset brush so lane-line open paths are NOT filled
        painter.setBrush(Qt.NoBrush)

        # Draw left lines from cache
        for color, style, l_width, path in self._cached_left_lines:
            pen = QPen(QColor(color), l_width, style)
            pen.setCapStyle(Qt.RoundCap)
            pen.setCosmetic(False)   # keep world-space width (scales with zoom)
            painter.setPen(pen)
            painter.drawPath(path)

        # Draw right lines from cache
        for color, style, l_width, path in self._cached_right_lines:
            pen = QPen(QColor(color), l_width, style)
            pen.setCapStyle(Qt.RoundCap)
            pen.setCosmetic(False)
            painter.setPen(pen)
            painter.drawPath(path)


class TargetVehicleItem(QGraphicsItem):
    """Top-down view of a target vehicle."""

    def __init__(self, cfg: TargetVehicleConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setZValue(5)  # Layer same as Ego vehicle (above sensors)

    def boundingRect(self):
        w, l = self.cfg.width, self.cfg.length
        # Extra padding for rotation and text bounds
        max_dim = max(w, l) + 2.0
        return QRectF(-max_dim, -max_dim, 2 * max_dim, 2 * max_dim)

    def paint(self, painter, option, widget=None):
        if not self.cfg.enabled:
            return

        w, l = self.cfg.width, self.cfg.length

        painter.save()

        # Target vehicle is positioned at (cfg.x, -cfg.y) in scene coordinates
        # And rotated by cfg.heading
        painter.translate(self.cfg.x, -self.cfg.y)
        painter.rotate(self.cfg.heading)

        # Draw vehicle body (rect centered at (0,0) in rotated local frame)
        # Note: in rotated frame, y is longitudinal (along heading), x is lateral
        # So we draw from -w/2 to w/2 and -l/2 to l/2
        veh_rect = QRectF(-w / 2, -l / 2, w, l)

        # Body fill with custom target color
        color = QColor(self.cfg.color)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor("#888888"), 0.05))
        painter.drawRoundedRect(veh_rect, 0.3, 0.3)

        # Windshield/Forward indicator area
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setOpacity(0.3)
        painter.setPen(Qt.NoPen)
        # Windshield is at front half of vehicle, i.e. local y = -l/2 to -l/4
        painter.drawRoundedRect(QRectF(-w / 2 + 0.15, -l / 2 + 0.1, w - 0.3, l * 0.25), 0.2, 0.2)
        painter.setOpacity(1.0)

        # Central label showing name (e.g. "T1")
        font = QFont("Arial", 6)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(veh_rect, Qt.AlignCenter, self.cfg.name)

        # Small forward arrow pointing in heading direction (local -y)
        painter.setPen(QPen(QColor("#FFFFFF"), 0.06))
        painter.drawLine(QPointF(0, -l/2 + 0.5), QPointF(0, -l/2 - 0.3))
        painter.drawLine(QPointF(0, -l/2 - 0.3), QPointF(-0.12, -l/2 - 0.15))
        painter.drawLine(QPointF(0, -l/2 - 0.3), QPointF(0.12, -l/2 - 0.15))

        painter.restore()


# ══════════════════════════════════════════════════════════════
#  2-D CANVAS
# ══════════════════════════════════════════════════════════════
class Canvas2D(QGraphicsView):

    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals   = signals

        self._sensor_items: dict[str, SensorGraphicsItem] = {}
        self._panning = False
        self._pan_start = QPointF()
        self._view_angle = 0       # cumulative CW rotation (degrees, multiple of 90)
        self._bg_dark = True       # True = dark, False = light
        self._zoom_mode = False
        self._rubber_band = None
        self._fov_locked = False

        # View settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setOptimizationFlags(
            QGraphicsView.DontSavePainterState |
            QGraphicsView.DontAdjustForAntialiasing
        )

        # Scene
        self._scene = QGraphicsScene(self)
        self._scene.setSceneRect(-600, -600, 1200, 1200)  # ±600 m
        self.setScene(self._scene)

        self._bg_item: Optional[QGraphicsPixmapItem] = None  # reference image layer

        # Static items
        self._grid = GridItem(600)
        self._scene.addItem(self._grid)

        self._lanes = LanesItem(scene_cfg)
        self._scene.addItem(self._lanes)

        self._vehicle = VehicleItem(scene_cfg.vehicle)
        self._scene.addItem(self._vehicle)

        self._scale_bar = ScaleBarItem()
        self._scene.addItem(self._scale_bar)
        self._scale_bar.setPos(-580, 560)   # bottom-left in scene meters (ignored transform)

        self._target_vehicle_items: dict[str, TargetVehicleItem] = {}

        # Connect signals
        signals.sensor_changed.connect(self._on_sensor_changed)
        signals.sensor_removed.connect(self._remove_item)
        signals.vehicle_changed.connect(self._on_vehicle_changed)
        signals.scene_rebuilt.connect(self.rebuild)
        signals.lane_changed.connect(self._on_lane_changed)
        signals.target_vehicle_added.connect(self._on_target_vehicle_added)
        signals.target_vehicle_removed.connect(self._on_target_vehicle_removed)
        signals.target_vehicle_changed.connect(self._on_target_vehicle_changed)

        self.rebuild()

        # Initial view: show ±150 m
        QTimer.singleShot(50, self.fit_view)

    # ── build / rebuild ───────────────────────────────────────
    def rebuild(self):
        for item in list(self._sensor_items.values()):
            self._scene.removeItem(item)
        self._sensor_items.clear()

        for sensor in self.scene_cfg.sensors:
            self._add_sensor_item(sensor)

        for item in list(self._target_vehicle_items.values()):
            self._scene.removeItem(item)
        self._target_vehicle_items.clear()

        for tv in self.scene_cfg.target_vehicles:
            self._add_target_vehicle_item(tv)

        self._grid.setVisible(self.scene_cfg.show_grid)
        self._on_lane_changed()

    def _add_sensor_item(self, sensor: SensorConfig):
        item = SensorGraphicsItem(sensor, self.signals, self.scene_cfg)
        self._scene.addItem(item)
        self._sensor_items[sensor.id] = item
        item._label.setVisible(self.scene_cfg.show_labels)
        item.setFlag(QGraphicsItem.ItemIsMovable, not self._fov_locked)

    def add_sensor(self, sensor: SensorConfig):
        self._add_sensor_item(sensor)

    def set_fov_locked(self, locked: bool):
        self._fov_locked = locked
        for item in self._sensor_items.values():
            item.setFlag(QGraphicsItem.ItemIsMovable, not locked)

    def _remove_item(self, sensor_id: str):
        item = self._sensor_items.pop(sensor_id, None)
        if item:
            self._scene.removeItem(item)

    def _on_sensor_changed(self, sensor_id: str):
        item = self._sensor_items.get(sensor_id)
        if item:
            item.refresh()

    def _on_vehicle_changed(self):
        self._vehicle.prepareGeometryChange()
        self._vehicle.update()
        self.viewport().update()

    def _on_lane_changed(self):
        self._lanes.prepareGeometryChange()
        self._lanes.update()
        self.viewport().update()

    def _add_target_vehicle_item(self, tv: TargetVehicleConfig):
        item = TargetVehicleItem(tv)
        self._scene.addItem(item)
        self._target_vehicle_items[tv.id] = item

    def _on_target_vehicle_added(self, tv_id: str):
        for tv in self.scene_cfg.target_vehicles:
            if tv.id == tv_id:
                self._add_target_vehicle_item(tv)
                break
        self.viewport().update()

    def _on_target_vehicle_removed(self, tv_id: str):
        item = self._target_vehicle_items.pop(tv_id, None)
        if item:
            self._scene.removeItem(item)
        self.viewport().update()

    def _on_target_vehicle_changed(self, tv_id: str):
        item = self._target_vehicle_items.get(tv_id)
        if item:
            item.prepareGeometryChange()
            item.update()
        self.viewport().update()

    # ── view control ──────────────────────────────────────────
    def fit_view(self, margin_m: float = 20):
        """Fit view to show vehicle + all sensor FOVs."""
        bounds = self._compute_content_bounds(margin_m)
        self.fitInView(bounds, Qt.KeepAspectRatio)

    def _compute_content_bounds(self, margin: float) -> QRectF:
        r = QRectF()
        for item in self._sensor_items.values():
            s = item.sensor
            if not s.enabled:
                continue
            h2 = s.hfov / 2
            angles = [math.radians(s.mount_angle + da) for da in [-h2, 0, h2]]
            for a in angles:
                fx = s.x + s.range * math.sin(a)
                fy = s.y + s.range * math.cos(a)
                sx, sy = w2s(fx, fy)
                r = r.united(QRectF(sx - 0.5, sy - 0.5, 1, 1))
        v = self.scene_cfg.vehicle
        # 车头前保险杠位于世界 (0,0)，车身向后 (世界 -Y) 延伸
        # 场景坐标 Y 翻转后，车体占场景 y ∈ [0, total_length]
        veh_w = max(v.max_width, v.width)
        r = r.united(QRectF(-veh_w / 2, 0.0, veh_w, v.total_length))
        return r.adjusted(-margin, -margin, margin, margin)

    def select_sensor(self, sensor_id: str):
        item = self._sensor_items.get(sensor_id)
        # Guard: if already selected, do nothing — prevents sensor_selected
        # signal recursion (select_sensor → setSelected → sensor_selected →
        # _on_sensor_selected → select_sensor → …)
        if item and item.isSelected():
            return
        self._scene.clearSelection()
        if item:
            item.setSelected(True)
            self.ensureVisible(item)

    # ── 2D view rotation ─────────────────────────────────────
    def rotate_view(self, delta: int):
        """Rotate the canvas view by delta degrees (±90 or 0 to reset)."""
        self._view_angle = (self._view_angle + delta) % 360
        t = QTransform()
        if self._view_angle != 0:
            t.rotate(float(self._view_angle))
        self.setTransform(t)
        self.fit_view()

    def reset_rotation(self):
        self._view_angle = 0
        self.setTransform(QTransform())
        self.fit_view()

    # ── dark / light background ───────────────────────────────
    def set_dark_bg(self, dark: bool):
        self._bg_dark = dark
        color = QColor("#1E1E1E") if dark else QColor("#F5F5F5")
        self.setBackgroundBrush(QBrush(color))
        self._scene.setBackgroundBrush(QBrush(color))
        self._grid._dark = dark
        self._grid.update()
        self.viewport().update()

    # ── interaction ───────────────────────────────────────────
    def zoom(self, factor):
        self.scale(factor, factor)

    def wheelEvent(self, event):
        factor = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18
        self.zoom(factor)

    def mousePressEvent(self, event):
        if self._zoom_mode and event.button() == Qt.LeftButton:
            self._zoom_start = event.pos()
            from PyQt5.QtWidgets import QRubberBand
            if not self._rubber_band:
                self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self._rubber_band.setGeometry(QRect(self._zoom_start, QSize()))
            self._rubber_band.show()
            event.accept()
            return

        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item is None or isinstance(item, (GridItem, LanesItem)):
                self._panning = True
                self._pan_start = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._zoom_mode and self._rubber_band and (event.buttons() & Qt.LeftButton):
            self._rubber_band.setGeometry(QRect(self._zoom_start, event.pos()).normalized())
            event.accept()
            return

        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._zoom_mode and self._rubber_band:
            self._rubber_band.hide()
            rect = QRect(self._zoom_start, event.pos()).normalized()
            if rect.width() > 5 and rect.height() > 5:
                scene_rect = self.mapToScene(rect).boundingRect()
                self.fitInView(scene_rect, Qt.KeepAspectRatio)
            self._zoom_mode = False
            self.setCursor(Qt.ArrowCursor)
            self.signals.zoom_mode_changed.emit(False)
            event.accept()
            return

        if self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        step = 0.1  # 10 cm nudge
        if event.modifiers() & Qt.ShiftModifier:
            step = 1.0
        moved = False
        selected = [i for i in self._sensor_items.values() if i.isSelected()]
        for item in selected:
            s = item.sensor
            if event.key() == Qt.Key_Left:
                s.x -= step; moved = True
            elif event.key() == Qt.Key_Right:
                s.x += step; moved = True
            elif event.key() == Qt.Key_Up:
                s.y += step; moved = True
            elif event.key() == Qt.Key_Down:
                s.y -= step; moved = True
            elif event.key() == Qt.Key_Delete:
                self.signals.sensor_removed.emit(s.id)
            if moved:
                item.refresh()
                self.signals.sensor_moved.emit(s.id)
        if not moved:
            super().keyPressEvent(event)

    def export_image(self, path: str, width: int = 3000,
                     angle: float = 0.0, bg_color: Optional[QColor] = None,
                     show_legend: bool = True,
                     title: str = '',
                     export_lanes: bool = True,
                     export_ego: bool = True,
                     export_target: bool = True):
        """Render the current scene to a PNG file.

        angle       – clockwise rotation applied after rendering (degrees)
        bg_color    – None = transparent; QColor = fill background
        show_legend – prepend a sensor-legend panel on the left
        title       – optional title for the image
        """
        bounds = self._compute_content_bounds(30)
        h = int(width * bounds.height() / max(bounds.width(), 1))
        scene_img = QImage(width, h, QImage.Format_ARGB32_Premultiplied)
        if bg_color is None:
            scene_img.fill(Qt.transparent)
        else:
            scene_img.fill(bg_color)
        # Temporarily toggle item visibilities based on user export choice
        lanes_old = self._lanes.isVisible()
        ego_old = self._vehicle.isVisible()
        
        self._lanes.setVisible(lanes_old and export_lanes)
        self._vehicle.setVisible(ego_old and export_ego)
        
        target_olds = {}
        for tv_id, tv_item in self._target_vehicle_items.items():
            target_olds[tv_id] = tv_item.isVisible()
            tv_item.setVisible(target_olds[tv_id] and export_target)

        old_bg = self._scene.backgroundBrush()
        self._scene.setBackgroundBrush(
            QBrush(Qt.NoBrush) if bg_color is None else QBrush(bg_color)
        )
        painter = QPainter(scene_img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        self._scene.render(painter, QRectF(scene_img.rect()), bounds)
        painter.end()
        self._scene.setBackgroundBrush(old_bg)
        
        # Restore item visibilities
        self._lanes.setVisible(lanes_old)
        self._vehicle.setVisible(ego_old)
        for tv_id, tv_item in self._target_vehicle_items.items():
            tv_item.setVisible(target_olds[tv_id])

        if show_legend and self.scene_cfg.sensors:
            legend_img = self._render_legend(width, h, bg_color)
            total_w = legend_img.width() + width
            combined = QImage(total_w, h, QImage.Format_ARGB32_Premultiplied)
            combined.fill(Qt.transparent if bg_color is None else bg_color)
            cp = QPainter(combined)
            cp.drawImage(0, 0, legend_img)
            cp.drawImage(legend_img.width(), 0, scene_img)
            cp.end()
            img = combined
        else:
            img = scene_img

        if angle % 360 != 0:
            img = img.transformed(QTransform().rotate(angle),
                                  Qt.SmoothTransformation)
        title = (title or '').strip()
        if title:
            title_h = max(56, int(img.height() * 0.06))
            titled = QImage(img.width(), img.height() + title_h,
                            QImage.Format_ARGB32_Premultiplied)
            titled.fill(Qt.transparent if bg_color is None else bg_color)

            tp = QPainter(titled)
            tp.setRenderHint(QPainter.TextAntialiasing)
            tfont = QFont('Microsoft YaHei')
            tfont.setBold(True)
            tfont.setPointSize(max(18, int(width / 120)))
            tp.setFont(tfont)
            tp.setPen(QColor('#000000'))
            tp.drawText(QRect(0, 0, titled.width(), title_h),
                        Qt.AlignCenter | Qt.AlignVCenter, title)
            tp.drawImage(0, title_h, img)
            tp.end()
            img = titled

        img.save(path)

    def _render_legend(self, scene_w: int, scene_h: int,
                       bg_color: Optional[QColor]) -> QImage:
        """Render a color-coded sensor-legend panel sized to fit scene_h."""
        sensors = [s for s in self.scene_cfg.sensors if s.enabled]
        if not sensors:
            return QImage()
        n = len(sensors)

        # Panel width: ~17% of scene width, bounded by scene height quarter
        lw = max(180, min(scene_w // 6, scene_h // 3))
        margin   = max(10, lw // 18)
        gap      = max(4,  lw // 45)
        border_w = max(3,  lw // 60)
        card_x   = margin
        card_w   = lw - 2 * margin

        # Distribute cards evenly over full height
        usable_h = scene_h - 2 * margin - (n - 1) * gap
        card_h   = max(40, usable_h // n)

        # Font sizes scaled to legend width and adjusted for card height compression
        scale        = lw / 500.0
        h_scale      = min(1.0, card_h / 52.0)
        font_name_pt = max(6,  int(13 * scale * h_scale))
        font_fov_pt  = max(5,  int(9  * scale * h_scale))

        img = QImage(lw, scene_h, QImage.Format_ARGB32_Premultiplied)

        # Panel background
        if bg_color is None or bg_color.alpha() < 10:
            panel_bg = QColor(20, 20, 20, 230)
            img.fill(Qt.transparent)
        elif bg_color.lightness() < 128:
            panel_bg = bg_color.darker(115)
            img.fill(panel_bg)
        else:
            panel_bg = bg_color.darker(108)
            img.fill(panel_bg)

        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.fillRect(img.rect(), panel_bg)

        for i, s in enumerate(sensors):
            card_y = margin + i * (card_h + gap)

            # Card tinted background
            hx = s.color.lstrip('#')
            r, g, b = (int(hx[j:j+2], 16) for j in (0, 2, 4))
            br = min(255, int(r * 0.22 + 18))
            bg_ = min(255, int(g * 0.22 + 18))
            bb  = min(255, int(b * 0.22 + 18))
            card_alpha = 255 if s.enabled else 110
            p.fillRect(card_x, card_y, card_w, card_h,
                       QColor(br, bg_, bb, card_alpha))

            # Left color border
            border_color = QColor(s.color)
            border_color.setAlpha(card_alpha)
            p.fillRect(card_x, card_y, border_w, card_h, border_color)

            txt_x = card_x + border_w + max(4, margin // 2)
            txt_w = card_w - border_w - max(4, margin // 2)
            half  = card_h // 2

            # Sensor name
            nf = QFont("Microsoft YaHei", font_name_pt)
            nf.setBold(True)
            p.setFont(nf)
            nc = QColor(s.color)
            nc.setAlpha(card_alpha)
            p.setPen(nc)
            p.drawText(QRect(txt_x, card_y + gap, txt_w, half - gap),
                       Qt.AlignLeft | Qt.AlignVCenter, s.name)

            # FOV spec
            fov_str = f"FOV: {s.range:.0f}m / {s.hfov:.0f}°"
            if s.mount_angle != 0:
                fov_str += f"  横摆:{s.mount_angle:+.0f}°"
            if s.vfov > 0:
                fov_str += f"  V:{s.vfov:.0f}°"
            if getattr(s, 'pitch', 0.0) != 0:
                fov_str += f"  俯仰:{s.pitch:+.0f}°"
            if getattr(s, 'roll', 0.0) != 0:
                fov_str += f"  滚转:{s.roll:+.0f}°"
            ff = QFont("Microsoft YaHei", font_fov_pt)
            p.setFont(ff)
            fc = QColor(180, 180, 180, card_alpha)
            p.setPen(fc)
            p.drawText(QRect(txt_x, card_y + half, txt_w, half - gap),
                       Qt.AlignLeft | Qt.AlignVCenter, fov_str)

        p.end()
        return img

    # ── background reference image ────────────────────────────
    def load_background(self, path: str, real_w_m: float,
                        rot_deg: int = 0,
                        anchor_x: float = 0.5, anchor_y: float = 0.5,
                        opacity: float = 0.65):
        """Load a reference image scaled to real_w_m meters wide.

        rot_deg   – CW rotation applied to the pixmap before scaling
        anchor_x/y – fraction [0,1] indicating where vehicle origin (0,0)
                     maps within the (rotated) image
        """
        pix = QPixmap(path)
        if pix.isNull():
            raise ValueError(f"无法加载图像: {path}")
        # Apply pre-rotation
        if rot_deg % 360 != 0:
            pix = pix.transformed(QTransform().rotate(rot_deg),
                                  Qt.SmoothTransformation)
        self.clear_background()

        scale    = real_w_m / max(pix.width(), 1)
        real_h_m = pix.height() * scale

        item = QGraphicsPixmapItem(pix)
        item.setTransform(QTransform.fromScale(scale, scale))
        # Position so that (anchor_x, anchor_y) fraction of the image sits at scene (0,0)
        item.setPos(-anchor_x * real_w_m, -anchor_y * real_h_m)
        item.setOpacity(opacity)
        item.setZValue(-20)          # below grid (Z=-10) and all other items
        item.setFlag(QGraphicsItem.ItemIsMovable,   False)
        item.setFlag(QGraphicsItem.ItemIsSelectable, False)

        self._bg_item = item
        self._scene.addItem(item)

    def clear_background(self):
        """Remove the reference image layer."""
        if self._bg_item is not None:
            self._scene.removeItem(self._bg_item)
            self._bg_item = None


# ══════════════════════════════════════════════════════════════
#  3-D CANVAS (matplotlib)
# ══════════════════════════════════════════════════════════════
class Canvas3D(QWidget):

    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals   = signals

        # Persistent view angles (preserved across redraws / user drag)
        self._elev = 25.0
        self._azim = -55.0
        self._hidden_in_3d: set = set()   # sensor IDs hidden only in 3D view

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Viewpoint preset toolbar ──────────────────────────
        vp_bar = QWidget()
        vp_bar.setStyleSheet("background:#2B2B2B;")
        vp_lay = QHBoxLayout(vp_bar)
        vp_lay.setContentsMargins(8, 3, 8, 3)
        vp_lay.setSpacing(4)
        lbl_vp = QLabel("视角预设:")
        lbl_vp.setStyleSheet("color:#AAAAAA; font-size:12px;")
        vp_lay.addWidget(lbl_vp)

        self._vp_presets = [
            ("🔭 等距", 25.0, -55.0, "三维等距视角（再次点击翻转180°）"),
            ("⬆  俯视", 89.0, -90.0, "正上方俯视（再次点击翻转）"),
            ("◀  正视", 0.0,  90.0,  "从车头正前方看（再次点击→后视）"),
            ("↙  侧视", 0.0,   0.0,  "从车辆右侧看（再次点击→左侧视）"),
        ]
        self._vp_buttons: list[QPushButton] = []
        _vp_btn_style = (
            "QPushButton{{background:{bg};border:1px solid {bd};"
            "border-radius:3px;padding:0 8px;font-size:12px;font-weight:bold;}}"
            "QPushButton:hover{{background:#505050;}}"
        )
        for idx, (lbl, e, a, tip) in enumerate(self._vp_presets):
            b = QPushButton(lbl)
            b.setToolTip(tip)
            b.setFixedHeight(26)
            b.setStyleSheet(_vp_btn_style.format(bg="#3A3A3A", bd="#555"))
            b.clicked.connect(lambda _, i=idx: self._set_view_preset(i))
            vp_lay.addWidget(b)
            self._vp_buttons.append(b)
        self._active_preset_idx = -1   # which preset is currently active

        vp_lay.addStretch()
        main_layout.addWidget(vp_bar)

        # ── Splitter: figure (left) + sensor visibility (right) ──
        splitter = QSplitter(Qt.Horizontal)

        fig_widget = QWidget()
        fig_layout = QVBoxLayout(fig_widget)
        fig_layout.setContentsMargins(0, 0, 0, 0)
        fig_layout.setSpacing(0)

        self.fig = Figure(facecolor="#1E1E1E")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self._nav = NavToolbar(self.canvas, self)
        self.canvas.toolbar = self._nav
        self._nav.setStyleSheet("background:#2B2B2B; color:#DDDDDD; qproperty-iconSize: 16px 16px; QToolButton { padding: 2px; border: none; background: transparent; } QToolButton:hover { background: #404040; }")
        fig_layout.addWidget(self._nav)
        fig_layout.addWidget(self.canvas, stretch=1)
        splitter.addWidget(fig_widget)

        # ── Sensor visibility panel ───────────────────────────
        vis_panel = QWidget()
        vis_panel.setStyleSheet("background:#1E1E1E;")
        vis_panel.setMinimumWidth(150)
        vis_panel.setMaximumWidth(200)
        vis_layout = QVBoxLayout(vis_panel)
        vis_layout.setContentsMargins(6, 6, 6, 6)
        vis_layout.setSpacing(6)

        vis_title = QLabel("传感器显示")
        vis_title.setStyleSheet(
            "color:#DDDDDD; font-weight:bold; font-size:13px;"
            "border-bottom:1px solid #444; padding-bottom:4px;")
        vis_layout.addWidget(vis_title)

        self._vis_list = QListWidget()
        self._vis_list.setStyleSheet(
            "QListWidget{background:#2B2B2B; color:#DDDDDD; font-size:12px;"
            "border:1px solid #444; border-radius:3px;}"
            "QListWidget::item{padding:3px 2px;}"
            "QListWidget::item:selected{background:#3A3A3A;}"
        )
        self._vis_list.itemChanged.connect(self._on_vis_changed)
        vis_layout.addWidget(self._vis_list, stretch=1)

        btn_all = QPushButton("全部显示")
        btn_all.setFixedHeight(26)
        btn_all.setStyleSheet(
            "QPushButton{background:#3A3A3A;border:1px solid #555;"
            "border-radius:3px;font-size:12px;color:#DDDDDD;}"
            "QPushButton:hover{background:#505050;}")
        btn_all.clicked.connect(self._show_all_sensors)
        vis_layout.addWidget(btn_all)

        btn_none = QPushButton("全部隐藏")
        btn_none.setFixedHeight(26)
        btn_none.setStyleSheet(
            "QPushButton{background:#3A3A3A;border:1px solid #555;"
            "border-radius:3px;font-size:12px;color:#DDDDDD;}"
            "QPushButton:hover{background:#505050;}")
        btn_none.clicked.connect(self._hide_all_sensors)
        vis_layout.addWidget(btn_none)

        splitter.addWidget(vis_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_layout.addWidget(splitter, stretch=1)

        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor("#1E1E1E")
        self.fig.patch.set_facecolor("#1E1E1E")

        signals.sensor_changed.connect(self._delayed_redraw)
        signals.sensor_moved.connect(self._delayed_redraw)
        signals.sensor_added.connect(self._on_scene_rebuilt)
        signals.sensor_removed.connect(self._on_scene_rebuilt)
        signals.vehicle_changed.connect(self._delayed_redraw)
        signals.scene_rebuilt.connect(self._on_scene_rebuilt)

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.redraw)
        self._timer.start(200)
        QTimer.singleShot(100, self._rebuild_vis_list)

    # ── visibility panel helpers ──────────────────────────────
    def _rebuild_vis_list(self):
        self._vis_list.blockSignals(True)
        self._vis_list.clear()
        for s in self.scene_cfg.sensors:
            item = QListWidgetItem(s.name)
            item.setData(Qt.UserRole, s.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked if s.id in self._hidden_in_3d
                               else Qt.Checked)
            item.setForeground(QColor(s.color))
            self._vis_list.addItem(item)
        self._vis_list.blockSignals(False)

    def _on_vis_changed(self, item: QListWidgetItem):
        sid = item.data(Qt.UserRole)
        if item.checkState() == Qt.Checked:
            self._hidden_in_3d.discard(sid)
        else:
            self._hidden_in_3d.add(sid)
        self._delayed_redraw()

    def _show_all_sensors(self):
        self._hidden_in_3d.clear()
        self._rebuild_vis_list()
        self._delayed_redraw()

    def _hide_all_sensors(self):
        self._hidden_in_3d = {s.id for s in self.scene_cfg.sensors}
        self._rebuild_vis_list()
        self._delayed_redraw()

    def _on_scene_rebuilt(self, *_):
        # Clean up IDs that no longer exist
        current_ids = {s.id for s in self.scene_cfg.sensors}
        self._hidden_in_3d &= current_ids
        self._rebuild_vis_list()
        self._delayed_redraw()

    def _delayed_redraw(self, *_):
        self._timer.start(500)

    # ── viewpoint preset with flip ────────────────────────────
    _VP_BTN_NORMAL  = ("QPushButton{background:#3A3A3A;border:1px solid #555;"
                        "border-radius:3px;padding:0 8px;font-size:12px;font-weight:bold;}"
                        "QPushButton:hover{background:#505050;}")
    _VP_BTN_ACTIVE  = ("QPushButton{background:#4A90D9;border:1px solid #3A7BC8;"
                        "border-radius:3px;padding:0 8px;font-size:12px;font-weight:bold;}"
                        "QPushButton:hover{background:#5AA0E9;}")

    def _clip_fov_by_vehicle(self, faces: list, sensor: SensorConfig) -> list:
        """
        Clip FOV cone faces by vehicle body occlusion.
        Removes faces that are behind the vehicle (for rear-facing sensors).
        """
        v = self.scene_cfg.vehicle
        clip_y = getattr(sensor, 'clip_range', 0.0)
        
        if clip_y > 0:
            # Manual clip distance provided by user
            clip_plane_y = sensor.y - clip_y
        else:
            # Auto-compute: clip at the back of the vehicle/trailer
            clip_plane_y = -v.length - max(0, v.trailer_length)
        
        # Filter faces: keep only faces where at least one point is beyond clip_plane
        clipped_faces = []
        for face in faces:
            keep_face = False
            for pt in face:
                if pt[1] > clip_plane_y:  # Y coordinate > clip plane
                    keep_face = True
                    break
            if keep_face:
                clipped_faces.append(face)
        
        return clipped_faces

    def _set_view_preset(self, idx: int):
        _, elev, azim, _ = self._vp_presets[idx]
        # Same preset clicked again → flip azimuth 180°
        if idx == self._active_preset_idx:
            azim = azim + 180.0
        self._active_preset_idx = idx
        # Update button styles
        for i, b in enumerate(self._vp_buttons):
            b.setStyleSheet(self._VP_BTN_ACTIVE if i == idx else self._VP_BTN_NORMAL)
        self._elev = float(elev)
        self._azim = float(azim)
        self.ax.view_init(elev=self._elev, azim=self._azim)
        self.canvas.draw()

    def _set_view(self, elev: float, azim: float):
        """Direct angle set (used by old callers; clears active preset highlight)."""
        self._active_preset_idx = -1
        for b in self._vp_buttons:
            b.setStyleSheet(self._VP_BTN_NORMAL)
        self._elev = elev
        self._azim = azim
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw()

    def redraw(self):
        try:
            self._redraw_impl()
        except Exception:
            import traceback
            self.ax.cla()
            self.ax.text2D(0.5, 0.5, f'3D\u89c6\u56fe\u9519\u8bef:\n{traceback.format_exc()}',
                           transform=self.ax.transAxes, ha='center', va='center',
                           color='red', fontsize=9, family='monospace')
            self.canvas.draw()

    def _redraw_impl(self):
        # Preserve current view angle (user may have dragged with mouse)
        try:
            self._elev = self.ax.elev
            self._azim = self.ax.azim
        except Exception:
            pass
        self.ax.cla()
        ax = self.ax

        ax.set_facecolor("#1E1E1E")
        ax.tick_params(colors='#AAAAAA', labelsize=11)
        for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
            pane.fill = False
            pane.set_edgecolor('#444444')
        ax.grid(True, color='#333333', linewidth=0.4)
        ax.set_xlabel("X (m)",  color='#AAAAAA', fontsize=12)
        ax.set_ylabel("Y (m)",  color='#AAAAAA', fontsize=12)
        ax.set_zlabel("Z (m)", color='#AAAAAA', fontsize=12)
        ax.set_title("3D FOV 视图", color='#DDDDDD', fontsize=13, pad=6)

        # ── Vehicle box ──────────────────────────────────────
        v   = self.scene_cfg.vehicle
        w2  = v.width / 2
        h   = v.height
        tl  = max(0.0, v.trailer_length)
        tw2 = v.effective_trailer_width / 2

        def _box_faces(x_min, x_max, y_min, y_max, z_min, z_max):
            verts = np.array([
                [x_min, y_min, z_min], [x_max, y_min, z_min],
                [x_max, y_max, z_min], [x_min, y_max, z_min],
                [x_min, y_min, z_max], [x_max, y_min, z_max],
                [x_max, y_max, z_max], [x_min, y_max, z_max],
            ])
            return [
                [verts[0], verts[1], verts[5], verts[4]],
                [verts[1], verts[2], verts[6], verts[5]],
                [verts[2], verts[3], verts[7], verts[6]],
                [verts[3], verts[0], verts[4], verts[7]],
                [verts[0], verts[1], verts[2], verts[3]],
                [verts[4], verts[5], verts[6], verts[7]],
            ]

        # 车头 (牵引车): 车头前保险杠位于世界 (0,0)，Y∈[-length, 0]
        truck_faces = _box_faces(-w2, w2, -v.length, 0.0, 0.0, h)
        ax.add_collection3d(Poly3DCollection(
            truck_faces, alpha=0.25, linewidths=0.5,
            facecolor='#3C4043', edgecolor='#888888'))

        # 挂车 (可选): Y∈[-length-tl, -length]
        if tl > 0:
            trailer_faces = _box_faces(-tw2, tw2, -v.length - tl, -v.length, 0.0, h)
            ax.add_collection3d(Poly3DCollection(
                trailer_faces, alpha=0.25, linewidths=0.5,
                facecolor='#2D3033', edgecolor='#888888'))

        # ── Sensor FOV cones ─────────────────────────────────
        all_pts = [np.array([0, 0, 0])]
        for sensor in self.scene_cfg.sensors:
            if not sensor.enabled:
                continue
            if sensor.id in self._hidden_in_3d:
                continue
            faces = fov_cone_faces(sensor)
            if not faces:
                continue
            
            # Apply FOV clipping by vehicle occlusion
            if getattr(sensor, 'clip_by_vehicle', True):
                faces = self._clip_fov_by_vehicle(faces, sensor)
            
            if not faces:
                continue
            
            hex_c = sensor.color.lstrip('#')
            rgb   = tuple(int(hex_c[i:i+2], 16) / 255 for i in (0, 2, 4))
            poly  = Poly3DCollection(faces, alpha=sensor.opacity * 0.85,
                                     linewidths=0, facecolor=rgb)
            ax.add_collection3d(poly)
            # Collect extent
            for face in faces:
                for pt in face:
                    all_pts.append(np.array(pt))

            # Sensor marker
            ax.scatter([sensor.x], [sensor.y], [sensor.z],
                       color=sensor.color, s=30, zorder=5)
            ax.text(sensor.x, sensor.y, sensor.z + 0.3,
                    sensor.name, color='#FFFFFF', fontsize=8,
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.15',
                              fc='#00000088', ec='none'))

        # ── Auto-scale axes ───────────────────────────────────
        pts = np.array(all_pts)
        margin = 10
        ax.set_xlim(pts[:,0].min() - margin, pts[:,0].max() + margin)
        ax.set_ylim(pts[:,1].min() - margin, pts[:,1].max() + margin)
        ax.set_zlim(0,  max(v.height + 0.5, pts[:,2].max() + 5))

        ax.view_init(elev=self._elev, azim=self._azim)
        self.canvas.draw()


# ══════════════════════════════════════════════════════════════
#  SENSOR LIST PANEL (left dock)
# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
#  PROFILE MANAGER  – in-memory, saved inside JSON as 'profiles'
# ══════════════════════════════════════════════════════════════
class ProfileManager:
    """Holds named sensor configuration profiles for a session.

    Each profile is a snapshot of (sensors, vehicle) stored as plain dicts.
    The *active* profile index determines what is currently displayed.
    Profiles are embedded in the project JSON under key 'profiles'.
    """

    def __init__(self, scene_cfg: 'SceneConfig'):
        self.scene_cfg = scene_cfg
        self._profiles: list[dict] = []   # [{'name': str, 'data': SceneConfig.to_dict()}, …]
        self._active: int = -1            # index into _profiles; -1 = no profile

    # ── query ─────────────────────────────────────────────────
    def names(self) -> list[str]:
        return [p['name'] for p in self._profiles]

    def count(self) -> int:
        return len(self._profiles)

    def active_index(self) -> int:
        return self._active

    # ── mutations ─────────────────────────────────────────────
    def save_current(self, name: str) -> int:
        """Snapshot current scene into a new profile (or update if name exists)."""
        snap = self.scene_cfg.to_dict()
        for i, p in enumerate(self._profiles):
            if p['name'] == name:
                p['data'] = snap
                self._active = i
                return i
        self._profiles.append({'name': name, 'data': snap})
        self._active = len(self._profiles) - 1
        return self._active

    def load(self, index: int):
        """Apply profile[index] data into the live scene_cfg."""
        if not (0 <= index < len(self._profiles)):
            return
        data = self._profiles[index]['data']
        new_cfg = SceneConfig.from_dict(data)
        self.scene_cfg.vehicle         = new_cfg.vehicle
        self.scene_cfg.sensors         = new_cfg.sensors
        self.scene_cfg.lane_params     = new_cfg.lane_params
        self.scene_cfg.target_vehicles = new_cfg.target_vehicles
        self.scene_cfg.show_grid       = new_cfg.show_grid
        self.scene_cfg.show_labels     = new_cfg.show_labels
        self.scene_cfg.show_overlap    = new_cfg.show_overlap
        self._active = index

    def rename(self, index: int, new_name: str):
        if 0 <= index < len(self._profiles):
            self._profiles[index]['name'] = new_name

    def delete(self, index: int):
        if 0 <= index < len(self._profiles):
            self._profiles.pop(index)
            if self._active >= len(self._profiles):
                self._active = len(self._profiles) - 1

    def update_active(self):
        """Overwrite the active profile with the current scene state."""
        if 0 <= self._active < len(self._profiles):
            self._profiles[self._active]['data'] = self.scene_cfg.to_dict()

    # ── serialisation ─────────────────────────────────────────
    def to_list(self) -> list:
        return [{'name': p['name'], 'data': p['data']} for p in self._profiles]

    def from_list(self, lst: list):
        self._profiles = [{'name': p['name'], 'data': p['data']} for p in lst]
        self._active = 0 if self._profiles else -1


class ProfilePanel(QWidget):
    """Dock widget for managing sensor configuration profiles."""

    profile_switched = pyqtSignal()   # emitted after load() so MainWindow can rebuild

    def __init__(self, profile_mgr: 'ProfileManager',
                 signals: AppSignals, parent=None):
        super().__init__(parent)
        self._mgr     = profile_mgr
        self._signals = signals

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        hdr = QLabel("📋 传感器方案")
        f = QFont(); f.setBold(True)
        hdr.setFont(f)
        root.addWidget(hdr)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.itemDoubleClicked.connect(self._on_double_click)
        root.addWidget(self._list)

        # Buttons row 1
        row1 = QHBoxLayout()
        btn_save = QPushButton("💾 另存为方案")
        btn_save.clicked.connect(self._save_current)
        btn_load = QPushButton("▶ 切换到此方案")
        btn_load.clicked.connect(self._load_selected)
        row1.addWidget(btn_save)
        row1.addWidget(btn_load)
        root.addLayout(row1)

        # Buttons row 2
        row2 = QHBoxLayout()
        btn_rename = QPushButton("✏ 重命名")
        btn_rename.clicked.connect(self._rename_selected)
        btn_del = QPushButton("🗑 删除")
        btn_del.clicked.connect(self._delete_selected)
        row2.addWidget(btn_rename)
        row2.addWidget(btn_del)
        root.addLayout(row2)

        hint = QLabel("双击方案名可快速切换")
        hint.setStyleSheet("color:#888;font-size:10px;")
        root.addWidget(hint)

        self._rebuild_list()

    # ── list management ───────────────────────────────────────
    def _rebuild_list(self):
        self._list.clear()
        ai = self._mgr.active_index()
        for i, name in enumerate(self._mgr.names()):
            item = QListWidgetItem(("▶ " if i == ai else "   ") + name)
            item.setData(Qt.UserRole, i)
            if i == ai:
                f = item.font(); f.setBold(True); item.setFont(f)
            self._list.addItem(item)

    def _selected_index(self) -> int:
        items = self._list.selectedItems()
        if not items:
            return -1
        return items[0].data(Qt.UserRole)

    # ── actions ───────────────────────────────────────────────
    def _save_current(self):
        name, ok = QInputDialog.getText(self, "另存为方案", "方案名称:",
                                        text=f"方案 {self._mgr.count() + 1}")
        if not ok or not name.strip():
            return
        self._mgr.save_current(name.strip())
        self._rebuild_list()
        self._signals.sensor_changed.emit('')   # trigger modified flag

    def _load_selected(self):
        idx = self._selected_index()
        if idx < 0:
            QMessageBox.information(self, "提示", "请先选择一个方案")
            return
        self._mgr.load(idx)
        self._rebuild_list()
        self.profile_switched.emit()

    def _on_double_click(self, item):
        idx = item.data(Qt.UserRole)
        self._mgr.load(idx)
        self._rebuild_list()
        self.profile_switched.emit()

    def _rename_selected(self):
        idx = self._selected_index()
        if idx < 0:
            return
        old = self._mgr.names()[idx]
        name, ok = QInputDialog.getText(self, "重命名方案", "新名称:", text=old)
        if ok and name.strip():
            self._mgr.rename(idx, name.strip())
            self._rebuild_list()

    def _delete_selected(self):
        idx = self._selected_index()
        if idx < 0:
            return
        ans = QMessageBox.question(self, "删除方案",
                                   f"确定删除方案「{self._mgr.names()[idx]}」？",
                                   QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            self._mgr.delete(idx)
            self._rebuild_list()

    def refresh(self):
        """Call after external profile changes (e.g. file load)."""
        self._rebuild_list()


class SensorListPanel(QWidget):
    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals   = signals
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Add controls ─────────────────────────────────────
        add_row = QHBoxLayout()
        self._type_combo = QComboBox()
        for k, v in SENSOR_META.items():
            self._type_combo.addItem(v["zh"], k)
        add_row.addWidget(self._type_combo)
        btn_add = QPushButton("+ 添加")
        btn_add.clicked.connect(self._add_sensor)
        btn_add.setFixedWidth(70)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        # ── List widget ───────────────────────────────────────
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.itemSelectionChanged.connect(self._on_list_selection)
        self._list.itemDoubleClicked.connect(self._rename_selected_item)
        layout.addWidget(self._list)

        # ── Bottom buttons ────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_del = QPushButton("🗑 删除")
        btn_del.clicked.connect(self._delete_selected)
        btn_dup = QPushButton("⧉ 复制")
        btn_dup.clicked.connect(self._duplicate_selected)
        btn_tog = QPushButton("◎ 切换")
        btn_tog.clicked.connect(self._toggle_selected)
        btn_ren = QPushButton("✏ 重命名")
        btn_ren.clicked.connect(self._rename_selected)
        for b in (btn_del, btn_dup, btn_tog, btn_ren):
            b.setFixedHeight(28)
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        # Preset buttons
        preset_row = QHBoxLayout()
        btn_hw30 = QPushButton("载入 HW 3.0 预设")
        btn_hw30.clicked.connect(self._load_hw30)
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self._clear_all)
        for b in (btn_hw30, btn_clear):
            b.setFixedHeight(28)
            preset_row.addWidget(b)
        layout.addLayout(preset_row)

        signals.sensor_added.connect(self._rebuild_list)
        signals.sensor_removed.connect(self._rebuild_list)
        signals.sensor_changed.connect(self._refresh_item)
        signals.sensor_selected.connect(self._sync_selection)
        signals.scene_rebuilt.connect(self._rebuild_list)

        self._rebuild_list()

    # ── list management ───────────────────────────────────────
    def _rebuild_list(self, *_):
        self._updating = True
        self._list.clear()
        for s in self.scene_cfg.sensors:
            self._list.addItem(self._make_item(s))
        self._updating = False

    def _make_item(self, sensor: SensorConfig) -> QListWidgetItem:
        meta = SENSOR_META[sensor.sensor_type]
        icon_text = {"camera": "📷", "radar": "📡", "lidar": "🔴"}.get(sensor.sensor_type, "●")
        item = QListWidgetItem(f"{icon_text} {sensor.name}")
        item.setData(Qt.UserRole, sensor.id)
        color = QColor(sensor.color)
        if not sensor.enabled:
            color.setAlphaF(0.4)
        item.setForeground(QBrush(color))
        return item

    def _refresh_item(self, sensor_id: str):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.UserRole) == sensor_id:
                sensor = next((s for s in self.scene_cfg.sensors if s.id == sensor_id), None)
                if sensor:
                    item.setText(f"{'📷' if sensor.sensor_type=='camera' else '📡' if sensor.sensor_type=='radar' else '🔴'} {sensor.name}")
                    color = QColor(sensor.color)
                    item.setForeground(QBrush(color))
                break

    def _on_list_selection(self):
        if self._updating:
            return
        items = self._list.selectedItems()
        if items:
            sensor_id = items[0].data(Qt.UserRole)
            self.signals.sensor_selected.emit(sensor_id)

    def _sync_selection(self, sensor_id: str):
        self._updating = True
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setSelected(item.data(Qt.UserRole) == sensor_id)
        self._updating = False

    # ── actions ───────────────────────────────────────────────
    def _add_sensor(self):
        stype = self._type_combo.currentData()
        meta  = SENSOR_META[stype]
        name, ok = QInputDialog.getText(self, "添加传感器", "传感器名称:",
                                         text=f"新{meta['zh']}")
        if not ok or not name.strip():
            return
        sensor = SensorConfig.new(stype, name=name.strip())
        self.scene_cfg.sensors.append(sensor)
        self._rebuild_list()
        self.signals.sensor_added.emit(sensor.id)

    def _delete_selected(self):
        sid = self._selected_id()
        if not sid:
            return
        self.scene_cfg.sensors = [s for s in self.scene_cfg.sensors if s.id != sid]
        self.signals.sensor_removed.emit(sid)

    def _duplicate_selected(self):
        sid = self._selected_id()
        if not sid:
            return
        original = next((s for s in self.scene_cfg.sensors if s.id == sid), None)
        if original:
            new_s = copy.deepcopy(original)
            new_s.id   = str(uuid.uuid4())[:8]
            new_s.name += "_副本"
            new_s.x   += 0.5
            self.scene_cfg.sensors.append(new_s)
            self._rebuild_list()
            self.signals.sensor_added.emit(new_s.id)

    def _toggle_selected(self):
        sid = self._selected_id()
        if not sid:
            return
        sensor = next((s for s in self.scene_cfg.sensors if s.id == sid), None)
        if sensor:
            sensor.enabled = not sensor.enabled
            self.signals.sensor_changed.emit(sid)
            self._refresh_item(sid)

    def _rename_selected(self):
        sid = self._selected_id()
        if not sid:
            return
        sensor = next((s for s in self.scene_cfg.sensors if s.id == sid), None)
        if sensor:
            name, ok = QInputDialog.getText(self, "重命名传感器", "新传感器名称:",
                                             text=sensor.name)
            if ok and name.strip():
                sensor.name = name.strip()
                self._refresh_item(sid)
                self.signals.sensor_changed.emit(sid)

    def _rename_selected_item(self, item):
        sid = item.data(Qt.UserRole)
        sensor = next((s for s in self.scene_cfg.sensors if s.id == sid), None)
        if sensor:
            name, ok = QInputDialog.getText(self, "重命名传感器", "新传感器名称:",
                                             text=sensor.name)
            if ok and name.strip():
                sensor.name = name.strip()
                self._refresh_item(sid)
                self.signals.sensor_changed.emit(sid)

    def _load_hw30(self):
        if self.scene_cfg.sensors:
            ans = QMessageBox.question(self, "载入预设",
                                       "是否清除当前所有传感器并载入 HW 3.0 预设？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ans != QMessageBox.Yes:
                return
        self.scene_cfg.sensors.clear()
        hw30 = SceneConfig.hw30()
        self.scene_cfg.sensors.extend(hw30.sensors)
        self.signals.scene_rebuilt.emit()

    def _clear_all(self):
        ans = QMessageBox.question(self, "清空", "确定清除所有传感器？",
                                   QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.scene_cfg.sensors.clear()
            self.signals.scene_rebuilt.emit()

    def _selected_id(self) -> Optional[str]:
        items = self._list.selectedItems()
        return items[0].data(Qt.UserRole) if items else None


# ══════════════════════════════════════════════════════════════
#  SENSOR PROPERTIES PANEL (right dock)
# ══════════════════════════════════════════════════════════════
class SensorPropertiesPanel(QWidget):
    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg   = scene_cfg
        self.signals     = signals
        self._sensor     = None
        self._updating   = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Title
        self._title = QLabel("— 未选择传感器 —")
        self._title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self._title.setFont(font)
        layout.addWidget(self._title)

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(6)

        self._name   = QLineEdit()
        self._name.editingFinished.connect(self._on_name)

        self._type   = QComboBox()
        for k, v in SENSOR_META.items():
            self._type.addItem(v["zh"], k)
        self._type.currentIndexChanged.connect(self._on_type)

        def spin(lo, hi, dec=1, suffix=""):
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setDecimals(dec)
            s.setSuffix(suffix)
            s.setSingleStep(0.1 if dec >= 1 else 1)
            return s

        self._x    = spin(-50,  50, 2, " m")
        self._y    = spin(-50,  50, 2, " m")
        self._z    = spin(  0,  10, 2, " m")
        self._ang  = spin(-180, 180, 1, "°")
        self._pitch= spin( -90,  90, 1, "°")
        self._roll = spin(-180, 180, 1, "°")
        self._hfov = spin(  1, 360, 1, "°")
        self._vfov = spin(  1, 180, 1, "°")
        self._rng  = spin(  1, 800, 0, " m")
        self._opa  = spin(  0,   1, 2, "")
        self._dhfov= spin(  0, 360, 1, "°")  # disp_hfov

        for w in (self._x, self._y, self._z, self._ang, self._pitch, self._roll,
                  self._hfov, self._vfov, self._rng, self._opa, self._dhfov):
            w.valueChanged.connect(self._on_spinbox)

        self._color_btn = QPushButton()
        self._color_btn.setFixedHeight(28)
        self._color_btn.clicked.connect(self._pick_color)

        self._enabled = QCheckBox("启用")
        self._enabled.stateChanged.connect(self._on_enabled)

        # New: FOV clipping parameters
        self._clip_by_vehicle = QCheckBox("被车体遮挡时切割FOV")
        self._clip_by_vehicle.stateChanged.connect(self._on_clip_changed)
        
        self._clip_range = spin(0, 200, 1, " m")
        self._clip_range.valueChanged.connect(self._on_clip_changed)

        form.addRow("名称:",     self._name)
        form.addRow("类型:",     self._type)
        form.addRow("X 横向:",   self._x)
        form.addRow("Y 纵向:",   self._y)
        form.addRow("Z 高度:",   self._z)
        form.addRow("横摆角:",   self._ang)
        form.addRow("俯仰角:",   self._pitch)
        form.addRow("滚转角:",   self._roll)
        form.addRow("水平FOV:",  self._hfov)
        form.addRow("垂直FOV:",  self._vfov)
        form.addRow("探测距离:", self._rng)
        form.addRow("透明度:",   self._opa)
        form.addRow("颜色:",     self._color_btn)
        form.addRow("显示FOV:",  self._dhfov)  # 0 = same as hfov
        form.addRow("",          self._enabled)
        form.addRow("",          self._clip_by_vehicle)
        form.addRow("手动切割距离:", self._clip_range)

        layout.addLayout(form)
        layout.addStretch()

        # Coverage label
        self._cov_label = QLabel()
        self._cov_label.setWordWrap(True)
        self._cov_label.setStyleSheet("color:#aaaaaa;font-size:10px;")
        layout.addWidget(self._cov_label)

        # Mirror button
        btn_mirror = QPushButton("↔ 添加镜像传感器")
        btn_mirror.clicked.connect(self._add_mirror)
        layout.addWidget(btn_mirror)

        self._set_editable(False)

        signals.sensor_selected.connect(self._load_sensor)
        signals.sensor_deselected.connect(self._clear)
        signals.sensor_moved.connect(self._on_moved)

    # ── load / clear ──────────────────────────────────────────
    def _load_sensor(self, sensor_id: str):
        sensor = next((s for s in self.scene_cfg.sensors if s.id == sensor_id), None)
        if not sensor:
            self._clear()
            return
        self._sensor = sensor
        self._updating = True

        self._title.setText(f"📐 {sensor.name}")
        self._name.setText(sensor.name)
        idx = self._type.findData(sensor.sensor_type)
        self._type.setCurrentIndex(idx)
        self._x.setValue(sensor.x)
        self._y.setValue(sensor.y)
        self._z.setValue(sensor.z)
        self._ang.setValue(sensor.mount_angle)
        self._pitch.setValue(getattr(sensor, 'pitch', 0.0))
        self._roll.setValue(getattr(sensor, 'roll', 0.0))
        self._hfov.setValue(sensor.hfov)
        self._vfov.setValue(sensor.vfov)
        self._rng.setValue(sensor.range)
        self._opa.setValue(sensor.opacity)
        self._dhfov.setValue(getattr(sensor, 'disp_hfov', 0.0))
        self._enabled.setChecked(sensor.enabled)
        self._clip_by_vehicle.setChecked(getattr(sensor, 'clip_by_vehicle', True))
        self._clip_range.setValue(getattr(sensor, 'clip_range', 0.0))
        self._update_color_btn(sensor.color)

        self._updating = False
        self._set_editable(True)
        self._update_cov_label()

    def _clear(self):
        self._sensor = None
        self._title.setText("— 未选择传感器 —")
        self._set_editable(False)
        self._cov_label.clear()

    def _set_editable(self, on: bool):
        for w in (self._name, self._type, self._x, self._y, self._z,
                  self._ang, self._pitch, self._roll, self._hfov, self._vfov, self._rng,
                  self._opa, self._dhfov, self._color_btn, self._enabled,
                  self._clip_by_vehicle, self._clip_range):
            w.setEnabled(on)

    def _on_moved(self, sensor_id: str):
        if self._sensor and self._sensor.id == sensor_id:
            self._updating = True
            self._x.setValue(self._sensor.x)
            self._y.setValue(self._sensor.y)
            self._updating = False
            self._update_cov_label()

    # ── change handlers ───────────────────────────────────────
    def _on_name(self):
        if self._sensor and not self._updating:
            self._sensor.name = self._name.text()
            self._title.setText(f"📐 {self._sensor.name}")
            self.signals.sensor_changed.emit(self._sensor.id)

    def _on_type(self):
        if self._sensor and not self._updating:
            self._sensor.sensor_type = self._type.currentData()
            self.signals.sensor_changed.emit(self._sensor.id)

    def _on_spinbox(self):
        if not self._sensor or self._updating:
            return
        self._sensor.x           = self._x.value()
        self._sensor.y           = self._y.value()
        self._sensor.z           = self._z.value()
        self._sensor.mount_angle = self._ang.value()
        self._sensor.pitch       = self._pitch.value()
        self._sensor.roll        = self._roll.value()
        self._sensor.hfov        = self._hfov.value()
        self._sensor.vfov        = self._vfov.value()
        self._sensor.range       = self._rng.value()
        self._sensor.opacity     = self._opa.value()
        self._sensor.disp_hfov  = self._dhfov.value()
        self.signals.sensor_changed.emit(self._sensor.id)
        self._update_cov_label()

    def _on_enabled(self):
        if self._sensor and not self._updating:
            self._sensor.enabled = self._enabled.isChecked()
            self.signals.sensor_changed.emit(self._sensor.id)

    def _pick_color(self):
        if not self._sensor:
            return
        c = QColorDialog.getColor(QColor(self._sensor.color), self, "选择颜色")
        if c.isValid():
            self._sensor.color = c.name()
            self._update_color_btn(self._sensor.color)
            self.signals.sensor_changed.emit(self._sensor.id)

    def _on_clip_changed(self):
        if self._sensor and not self._updating:
            self._sensor.clip_by_vehicle = self._clip_by_vehicle.isChecked()
            self._sensor.clip_range = self._clip_range.value()
            self.signals.sensor_changed.emit(self._sensor.id)

    def _update_color_btn(self, hex_color: str):
        self._color_btn.setStyleSheet(
            f"background-color:{hex_color}; border-radius:4px; border:1px solid #666;"
        )
        self._color_btn.setText(hex_color)

    def _update_cov_label(self):
        if not self._sensor:
            return
        # Simple coverage area estimate (sector area)
        r = self._sensor.range
        h = self._sensor.hfov
        area = math.pi * r**2 * (h / 360.0)
        self._cov_label.setText(
            f"覆盖面积约 {area:.0f} m²  |  "
            f"最远 {r:.0f} m  |  "
            f"角度 {h:.0f}°"
        )

    def _add_mirror(self):
        if not self._sensor:
            return
        new_s = copy.deepcopy(self._sensor)
        new_s.id    = str(uuid.uuid4())[:8]
        new_s.name += "_镜像"
        new_s.x     = -self._sensor.x
        new_s.mount_angle = -self._sensor.mount_angle
        new_s.roll = -getattr(self._sensor, 'roll', 0.0)
        self.scene_cfg.sensors.append(new_s)
        self.signals.sensor_added.emit(new_s.id)


class VehiclePropertiesPanel(QWidget):
    """Vehicle dimensions panel (length/width)."""

    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals = signals
        self._updating = False

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title = QLabel("🚗 车辆参数")
        tf = QFont()
        tf.setBold(True)
        title.setFont(tf)
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(6)

        self._len = QDoubleSpinBox()
        self._len.setRange(1.0, 30.0)
        self._len.setDecimals(2)
        self._len.setSingleStep(0.1)
        self._len.setSuffix(" m")

        self._wid = QDoubleSpinBox()
        self._wid.setRange(0.8, 8.0)
        self._wid.setDecimals(2)
        self._wid.setSingleStep(0.1)
        self._wid.setSuffix(" m")

        self._tlen = QDoubleSpinBox()
        self._tlen.setRange(0.0, 30.0)
        self._tlen.setDecimals(2)
        self._tlen.setSingleStep(0.1)
        self._tlen.setSuffix(" m")
        self._tlen.setToolTip("挂车长度 (0 表示无挂车)")

        self._twid = QDoubleSpinBox()
        self._twid.setRange(0.0, 8.0)
        self._twid.setDecimals(2)
        self._twid.setSingleStep(0.1)
        self._twid.setSuffix(" m")
        self._twid.setToolTip("挂车宽度 (0 表示与车头同宽)")

        self._len.valueChanged.connect(self._on_changed)
        self._wid.valueChanged.connect(self._on_changed)
        self._tlen.valueChanged.connect(self._on_changed)
        self._twid.valueChanged.connect(self._on_changed)

        form.addRow("车头长:", self._len)
        form.addRow("车头宽:", self._wid)
        form.addRow("挂车长:", self._tlen)
        form.addRow("挂车宽:", self._twid)
        root.addLayout(form)

        hint = QLabel("车头前保险杠位于 (0, 0)，车身向后延伸。\n修改后会实时刷新 2D/3D/侧视图。")
        hint.setStyleSheet("color:#aaaaaa;font-size:10px;")
        root.addWidget(hint)
        root.addStretch()

        self._load()
        signals.scene_rebuilt.connect(self._load)

    def _load(self, *_):
        self._updating = True
        v = self.scene_cfg.vehicle
        self._len.setValue(v.length)
        self._wid.setValue(v.width)
        self._tlen.setValue(v.trailer_length)
        self._twid.setValue(v.trailer_width)
        self._updating = False

    def _on_changed(self):
        if self._updating:
            return
        v = self.scene_cfg.vehicle
        v.length = self._len.value()
        v.width = self._wid.value()
        v.trailer_length = self._tlen.value()
        v.trailer_width  = self._twid.value()
        self.signals.vehicle_changed.emit()


class LaneConfigPanel(QWidget):
    """Parametric lane line configuration panel."""

    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals = signals
        self._updating = False

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title = QLabel("🛣️ 车道线参数")
        tf = QFont()
        tf.setBold(True)
        title.setFont(tf)
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(6)

        self._lane_width = QDoubleSpinBox()
        self._lane_width.setRange(1.0, 15.0)
        self._lane_width.setDecimals(2)
        self._lane_width.setSingleStep(0.25)
        self._lane_width.setSuffix(" m")

        self._line_width = QDoubleSpinBox()
        self._line_width.setRange(0.01, 2.0)
        self._line_width.setDecimals(2)
        self._line_width.setSingleStep(0.05)
        self._line_width.setSuffix(" m")

        self._lateral_offset = QDoubleSpinBox()
        self._lateral_offset.setRange(-50.0, 50.0)
        self._lateral_offset.setDecimals(2)
        self._lateral_offset.setSingleStep(0.5)
        self._lateral_offset.setSuffix(" m")

        self._curvature_r = QDoubleSpinBox()
        self._curvature_r.setRange(-10000.0, 10000.0)
        self._curvature_r.setDecimals(1)
        self._curvature_r.setSingleStep(50.0)
        self._curvature_r.setSuffix(" m")
        self._curvature_r.setToolTip("弯道半径 R (0=直道)")

        self._left_lines = QSpinBox()
        self._left_lines.setRange(0, 10)

        self._right_lines = QSpinBox()
        self._right_lines.setRange(0, 10)

        self._length = QDoubleSpinBox()
        self._length.setRange(10.0, 1000.0)
        self._length.setDecimals(1)
        self._length.setSingleStep(10.0)
        self._length.setSuffix(" m")

        form.addRow("车道中到中宽:", self._lane_width)
        form.addRow("车道线自身宽:", self._line_width)
        form.addRow("横向Y0面偏移:", self._lateral_offset)
        form.addRow("曲率半径 R:", self._curvature_r)
        form.addRow("左侧车道线数:", self._left_lines)
        form.addRow("右侧车道线数:", self._right_lines)
        form.addRow("车道线长度:", self._length)

        root.addLayout(form)

        colors_layout = QHBoxLayout()
        self._btn_outer = QPushButton("外侧边界颜色")
        self._btn_inner = QPushButton("内侧分界颜色")
        colors_layout.addWidget(self._btn_outer)
        colors_layout.addWidget(self._btn_inner)
        root.addLayout(colors_layout)

        root.addStretch()

        self._lane_width.valueChanged.connect(self._on_changed)
        self._line_width.valueChanged.connect(self._on_changed)
        self._lateral_offset.valueChanged.connect(self._on_changed)
        self._curvature_r.valueChanged.connect(self._on_changed)
        self._left_lines.valueChanged.connect(self._on_changed)
        self._right_lines.valueChanged.connect(self._on_changed)
        self._length.valueChanged.connect(self._on_changed)

        self._btn_outer.clicked.connect(self._choose_color_outer)
        self._btn_inner.clicked.connect(self._choose_color_inner)

        self._load()
        signals.scene_rebuilt.connect(self._load)

    def _load(self, *_):
        self._updating = True
        lp = self.scene_cfg.lane_params
        self._lane_width.setValue(lp.lane_width)
        self._line_width.setValue(lp.line_width)
        self._lateral_offset.setValue(lp.lateral_offset)
        self._curvature_r.setValue(lp.curvature_r)
        self._left_lines.setValue(lp.left_lines)
        self._right_lines.setValue(lp.right_lines)
        self._length.setValue(lp.length)

        self._btn_outer.setStyleSheet(f"background-color: {lp.color_outer}; color: {'#000000' if QColor(lp.color_outer).lightness() > 128 else '#ffffff'};")
        self._btn_inner.setStyleSheet(f"background-color: {lp.color_inner}; color: {'#000000' if QColor(lp.color_inner).lightness() > 128 else '#ffffff'};")

        self._updating = False

    def _on_changed(self):
        if self._updating:
            return
        lp = self.scene_cfg.lane_params
        lp.lane_width = self._lane_width.value()
        lp.line_width = self._line_width.value()
        lp.lateral_offset = self._lateral_offset.value()
        lp.curvature_r = self._curvature_r.value()
        lp.left_lines = self._left_lines.value()
        lp.right_lines = self._right_lines.value()
        lp.length = self._length.value()

        self.signals.lane_changed.emit()

    def _choose_color_outer(self):
        lp = self.scene_cfg.lane_params
        col = QColorDialog.getColor(QColor(lp.color_outer), self, "选择外侧边界线颜色")
        if col.isValid():
            lp.color_outer = col.name()
            self._load()
            self.signals.lane_changed.emit()

    def _choose_color_inner(self):
        lp = self.scene_cfg.lane_params
        col = QColorDialog.getColor(QColor(lp.color_inner), self, "选择内侧分界线颜色")
        if col.isValid():
            lp.color_inner = col.name()
            self._load()
            self.signals.lane_changed.emit()


class TargetVehiclePanel(QWidget):
    """Target vehicles management panel."""

    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals = signals
        self._updating = False

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title = QLabel("🚘 目标车配置")
        tf = QFont()
        tf.setBold(True)
        title.setFont(tf)
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        self._list_widget = QListWidget()
        self._list_widget.setMaximumHeight(120)
        root.addWidget(self._list_widget)

        btn_layout = QHBoxLayout()
        self._btn_add = QPushButton("添加目标车")
        self._btn_del = QPushButton("删除选中")
        btn_layout.addWidget(self._btn_add)
        btn_layout.addWidget(self._btn_del)
        root.addLayout(btn_layout)

        self._prop_group = QGroupBox("目标车属性")
        form = QFormLayout(self._prop_group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(6)

        self._name = QLineEdit()
        self._x = QDoubleSpinBox()
        self._x.setRange(-100.0, 100.0)
        self._x.setDecimals(2)
        self._x.setSingleStep(0.5)
        self._x.setSuffix(" m")

        self._y = QDoubleSpinBox()
        self._y.setRange(-200.0, 500.0)
        self._y.setDecimals(2)
        self._y.setSingleStep(1.0)
        self._y.setSuffix(" m")

        self._heading = QDoubleSpinBox()
        self._heading.setRange(-180.0, 180.0)
        self._heading.setDecimals(1)
        self._heading.setSingleStep(5.0)
        self._heading.setSuffix(" °")

        self._len = QDoubleSpinBox()
        self._len.setRange(0.5, 30.0)
        self._len.setDecimals(2)
        self._len.setSingleStep(0.1)
        self._len.setSuffix(" m")

        self._wid = QDoubleSpinBox()
        self._wid.setRange(0.5, 8.0)
        self._wid.setDecimals(2)
        self._wid.setSingleStep(0.1)
        self._wid.setSuffix(" m")

        self._btn_color = QPushButton("选择车身颜色")
        self._enabled = QCheckBox("启用渲染")

        form.addRow("名称:", self._name)
        form.addRow("横向 X (Y0偏移):", self._x)
        form.addRow("纵向 Y (车前):", self._y)
        form.addRow("航向角 Heading:", self._heading)
        form.addRow("车身长度:", self._len)
        form.addRow("车身宽度:", self._wid)
        form.addRow("车身颜色:", self._btn_color)
        form.addRow("", self._enabled)

        root.addWidget(self._prop_group)
        root.addStretch()

        self._list_widget.currentRowChanged.connect(self._on_selection_changed)
        self._btn_add.clicked.connect(self._add_target_vehicle)
        self._btn_del.clicked.connect(self._del_target_vehicle)

        self._name.textChanged.connect(self._on_changed)
        self._x.valueChanged.connect(self._on_changed)
        self._y.valueChanged.connect(self._on_changed)
        self._heading.valueChanged.connect(self._on_changed)
        self._len.valueChanged.connect(self._on_changed)
        self._wid.valueChanged.connect(self._on_changed)
        self._enabled.toggled.connect(self._on_changed)
        self._btn_color.clicked.connect(self._choose_color)

        self._sync_list()
        self._update_prop_enables()

        signals.scene_rebuilt.connect(self._on_scene_rebuilt)

    def _on_scene_rebuilt(self):
        self._sync_list()

    def _sync_list(self):
        self._updating = True
        self._list_widget.clear()
        for tv in self.scene_cfg.target_vehicles:
            item = QListWidgetItem(f"{tv.name} (X:{tv.x:.1f}, Y:{tv.y:.1f})")
            item.setData(Qt.UserRole, tv.id)
            self._list_widget.addItem(item)
        self._updating = False

        if self.scene_cfg.target_vehicles:
            self._list_widget.setCurrentRow(0)
        else:
            self._update_prop_enables()

    def _selected_tv(self) -> Optional[TargetVehicleConfig]:
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self.scene_cfg.target_vehicles):
            return None
        tv_id = self._list_widget.item(row).data(Qt.UserRole)
        for tv in self.scene_cfg.target_vehicles:
            if tv.id == tv_id:
                return tv
        return None

    def _on_selection_changed(self, row):
        if self._updating:
            return
        tv = self._selected_tv()
        if not tv:
            self._update_prop_enables()
            return

        self._updating = True
        self._name.setText(tv.name)
        self._x.setValue(tv.x)
        self._y.setValue(tv.y)
        self._heading.setValue(tv.heading)
        self._len.setValue(tv.length)
        self._wid.setValue(tv.width)
        self._enabled.setChecked(tv.enabled)
        self._btn_color.setStyleSheet(f"background-color: {tv.color}; color: {'#000000' if QColor(tv.color).lightness() > 128 else '#ffffff'};")
        self._updating = False

        self._update_prop_enables()
        self.signals.target_vehicle_selected.emit(tv.id)

    def _update_prop_enables(self):
        has_sel = (self._selected_tv() is not None)
        self._prop_group.setEnabled(has_sel)

    def _add_target_vehicle(self):
        idx = len(self.scene_cfg.target_vehicles) + 1
        x_default = 3.75
        if self.scene_cfg.lane_params.left_lines > 0:
            x_default = -self.scene_cfg.lane_params.lane_width
        elif self.scene_cfg.lane_params.right_lines > 0:
            x_default = self.scene_cfg.lane_params.lane_width

        tv = TargetVehicleConfig(
            name=f"T{idx}",
            x=x_default,
            y=20.0 + idx * 5.0,
            heading=0.0,
            length=4.8,
            width=2.0,
            color="#FF5252",
            enabled=True
        )
        self.scene_cfg.target_vehicles.append(tv)
        self._sync_list()
        for i in range(self._list_widget.count()):
            if self._list_widget.item(i).data(Qt.UserRole) == tv.id:
                self._list_widget.setCurrentRow(i)
                break
        self.signals.target_vehicle_added.emit(tv.id)

    def _del_target_vehicle(self):
        tv = self._selected_tv()
        if not tv:
            return
        self.scene_cfg.target_vehicles.remove(tv)
        self._sync_list()
        self.signals.target_vehicle_removed.emit(tv.id)

    def _choose_color(self):
        tv = self._selected_tv()
        if not tv:
            return
        col = QColorDialog.getColor(QColor(tv.color), self, "选择车身颜色")
        if col.isValid():
            tv.color = col.name()
            self._btn_color.setStyleSheet(f"background-color: {tv.color}; color: {'#000000' if QColor(tv.color).lightness() > 128 else '#ffffff'};")
            self.signals.target_vehicle_changed.emit(tv.id)

    def _on_changed(self):
        if self._updating:
            return
        tv = self._selected_tv()
        if not tv:
            return
        tv.name = self._name.text()
        tv.x = self._x.value()
        tv.y = self._y.value()
        tv.heading = self._heading.value()
        tv.length = self._len.value()
        tv.width = self._wid.value()
        tv.enabled = self._enabled.isChecked()

        row = self._list_widget.currentRow()
        if row >= 0:
            self._updating = True
            self._list_widget.item(row).setText(f"{tv.name} (X:{tv.x:.1f}, Y:{tv.y:.1f})")
            self._updating = False

        self.signals.target_vehicle_changed.emit(tv.id)


# ═════════════════════════════════════════════════════════════
#  SENSOR GROUND-INTERSECTION TABLE
# ═════════════════════════════════════════════════════════════
def compute_ground_intersections(s: 'SensorConfig'):
    """计算传感器 FOV 与地面 (z=0) 的交点水平地面距离。

    所有距离都是从传感器所在地面投影点 (s.x, s.y) 到地面交点
    的 X-Y 平面直线距离 x = z / tan(|el|) = √(t² - z²)。

    返回 dict：
        lower   : 下沿射线交地水平距 (m)，None 表示不交
        upper   : 上沿射线交地水平距 (m)
        center  : 中心线交地水平距 (m)
        range_  : 探测圆弧交地水平距 (m)
        nearest : 最近地面点水平距 (m)
        ground_y: 最近地面点世界 Y 坐标 (m)
    """
    empty = dict(lower=None, upper=None, center=None, range_=None,
                 nearest=None, ground_y=None)
    if s.z <= 0.05:
        return empty

    pitch  = math.radians(getattr(s, 'pitch', 0.0))
    v2     = math.radians(s.vfov / 2.0)
    az     = math.radians(s.mount_angle)
    rng    = float(s.range)

    # 返回水平距离 x = z / tan(|el|)；仅当射线朝下且斜距 <= range
    def _hit(el):
        sin_el = math.sin(el)
        if sin_el >= -1e-9:
            return None
        t = s.z / (-sin_el)          # 斜距
        if t > rng + 1e-6:
            return None
        # 水平距离 = √(t² - z²)
        return math.sqrt(max(t * t - s.z * s.z, 0.0))

    lower = _hit(pitch - v2)
    upper = _hit(pitch + v2)
    cent  = _hit(pitch)

    # 探测圆弧交地：sin(el) = -z/range，需在 vfov 范围内
    range_hit = None
    if s.z < rng:
        sin_arc = -s.z / rng
        if -1.0 < sin_arc < -1e-9:
            el_arc = math.asin(sin_arc)
            if pitch - v2 <= el_arc <= pitch + v2:
                # 斜距 = range，水平距 = √(range² - z²)
                range_hit = math.sqrt(max(rng * rng - s.z * s.z, 0.0))

    candidates = [c for c in (lower, upper, cent, range_hit) if c is not None]
    if not candidates:
        return dict(lower=lower, upper=upper, center=cent, range_=range_hit,
                    nearest=None, ground_y=None)

    nearest = min(candidates)
    ground_y = s.y + nearest * math.cos(az)
    return dict(lower=lower, upper=upper, center=cent, range_=range_hit,
                nearest=nearest, ground_y=ground_y)


class SensorGroundTablePanel(QWidget):
    """传感器地面落点距离表。

    列：品牌色 / 名称 / 启用 / X / Y / Z / 横摆角 / 俯仰角 / 滚转角 / vFOV / range
           / 下沿落地 / 中心落地 / 上沿落地 / 探测圆弧落地 / 最近点 / 最近点 Y
    跟随传感器位置/参数变化实时更新。
    """

    COLUMNS = [
        "", "名称", "启用",
        "X(m)", "Y(m)", "Z(m)",
        "横摆角°", "俯仰角°", "滚转角°", "vFOV°", "range(m)",
        "下沿地距(m)", "中心地距(m)",
        "上沿地距(m)", "圆弧地距(m)",
        "最近点(m)", "最近点 Y(m)",
    ]

    def __init__(self, scene_cfg: 'SceneConfig', signals: 'AppSignals', parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals = signals

        self._needs_rebuild = True
        self._updated_sensor_ids = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 顶部提示
        hint = QLabel(
            "传感器 FOV 下/中/上沿与地面 z=0 交点的水平距离 x = z / tan(|仰角|)。"
            "表格随传感器位置/姿态变动自动更新；"
            "“—” 表示该射线不交地面；本表计算暂不考虑滚转角。"
        )
        hint.setStyleSheet("color:#9DB1C0; font-size:10px; padding:2px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.setStyleSheet(
            "QTableWidget { background:#1E1E1E; color:#DDDDDD; gridline-color:#333; }"
            "QHeaderView::section { background:#2B2B2B; color:#CCCCCC;"
            " padding:3px; border:1px solid #3A3A3A; }"
            "QTableWidget::item:selected { background:#3F567A; }"
        )
        self._table.itemSelectionChanged.connect(self._on_row_selected)
        layout.addWidget(self._table)

        # 延迟刷新
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.refresh)

        # 结构变化信号 -> 触发全表重建
        for sig in (signals.sensor_added, signals.sensor_removed,
                    signals.vehicle_changed, signals.scene_rebuilt):
            sig.connect(self._on_structure_changed)

        # 单个传感器数值/位置变化 -> 仅刷新对应行
        for sig in (signals.sensor_changed, signals.sensor_moved):
            sig.connect(self._on_sensor_updated)

        signals.sensor_selected.connect(self._on_external_select)

        QTimer.singleShot(200, self.refresh)

    def _on_structure_changed(self, *_):
        self._needs_rebuild = True
        self._timer.start(120)

    def _on_sensor_updated(self, sid: str, *_):
        if not self._needs_rebuild:
            self._updated_sensor_ids.add(sid)
        self._timer.start(120)

    @staticmethod
    def _fmt(v, prec=1, suffix=""):
        if v is None:
            return "—"
        return f"{v:.{prec}f}{suffix}"

    def refresh(self):
        if self._needs_rebuild:
            self._rebuild_table()
            self._needs_rebuild = False
            self._updated_sensor_ids.clear()
        elif self._updated_sensor_ids:
            for sid in list(self._updated_sensor_ids):
                self._refresh_sensor_row(sid)
            self._updated_sensor_ids.clear()

    def _rebuild_table(self):
        sensors = list(self.scene_cfg.sensors)
        # 记住当前选中传感器，刷新后重新选上
        sel_id = None
        items = self._table.selectedItems()
        if items:
            row = items[0].row()
            sel_id = self._table.item(row, 1).data(Qt.UserRole) if self._table.item(row, 1) else None

        self._table.blockSignals(True)
        self._table.setRowCount(len(sensors))
        for r, s in enumerate(sensors):
            self._populate_row(r, s)

        # 恢复选中行
        if sel_id is not None:
            for r in range(self._table.rowCount()):
                it = self._table.item(r, 1)
                if it and it.data(Qt.UserRole) == sel_id:
                    self._table.selectRow(r)
                    break
        self._table.blockSignals(False)
        self._table.resizeColumnsToContents()
        self._table.setColumnWidth(0, 18)

    def _refresh_sensor_row(self, sid: str):
        s = next((x for x in self.scene_cfg.sensors if x.id == sid), None)
        if not s:
            return
        r = self._find_row_by_id(sid)
        if r < 0:
            return
        self._table.blockSignals(True)
        self._populate_row(r, s)
        self._table.blockSignals(False)

    def _find_row_by_id(self, sid: str) -> int:
        for r in range(self._table.rowCount()):
            name_item = self._table.item(r, 1)
            if name_item and name_item.data(Qt.UserRole) == sid:
                return r
        return -1

    def _populate_row(self, r: int, s: SensorConfig):
        info = compute_ground_intersections(s)

        # 0: 颜色色块
        color_item = QTableWidgetItem("")
        color_item.setBackground(QColor(s.color))
        color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(r, 0, color_item)

        def _mk(text, align=Qt.AlignCenter, tip=None):
            it = QTableWidgetItem(text)
            it.setTextAlignment(align)
            if tip:
                it.setToolTip(tip)
            if not s.enabled:
                it.setForeground(QBrush(QColor("#666666")))
            return it

        name_item = _mk(s.name, Qt.AlignLeft | Qt.AlignVCenter)
        name_item.setData(Qt.UserRole, s.id)
        self._table.setItem(r, 1, name_item)
        self._table.setItem(r, 2, _mk("✓" if s.enabled else "✗"))
        self._table.setItem(r, 3, _mk(self._fmt(s.x, 2)))
        self._table.setItem(r, 4, _mk(self._fmt(s.y, 2)))
        self._table.setItem(r, 5, _mk(self._fmt(s.z, 2)))
        self._table.setItem(r, 6, _mk(self._fmt(s.mount_angle, 1)))
        self._table.setItem(r, 7, _mk(self._fmt(s.pitch, 1)))
        self._table.setItem(r, 8, _mk(self._fmt(s.roll, 1)))
        self._table.setItem(r, 9, _mk(self._fmt(s.vfov, 1)))
        self._table.setItem(r, 10, _mk(self._fmt(s.range, 1)))
        self._table.setItem(r, 11, _mk(self._fmt(info['lower'], 1),
                                      tip="FOV 下沿射线交地点的水平距离 x = z/tan|下沿仰角|"))
        self._table.setItem(r, 12, _mk(self._fmt(info['center'], 1),
                                      tip="FOV 中心线交地点的水平距离 x = z/tan|pitch|"))
        self._table.setItem(r, 13, _mk(self._fmt(info['upper'], 1),
                                      tip="FOV 上沿射线交地点的水平距离"))
        self._table.setItem(r, 14, _mk(self._fmt(info['range_'], 1),
                                      tip="探测圆弧交地点的水平距离 √(range² − z²)"))
        nearest_item = _mk(self._fmt(info['nearest'], 1))
        nearest_item.setForeground(QBrush(QColor("#FFD54F"))
                                   if (info['nearest'] is not None and s.enabled)
                                   else QBrush(QColor("#666666")))
        self._table.setItem(r, 15, nearest_item)
        self._table.setItem(r, 16, _mk(self._fmt(info['ground_y'], 1)))

    def _on_row_selected(self):
        items = self._table.selectedItems()
        if not items:
            return
        row = items[0].row()
        name_item = self._table.item(row, 1)
        if name_item:
            sid = name_item.data(Qt.UserRole)
            if sid:
                self.signals.sensor_selected.emit(sid)

    def _on_external_select(self, sid: str):
        for r in range(self._table.rowCount()):
            it = self._table.item(r, 1)
            if it and it.data(Qt.UserRole) == sid:
                if not self._table.selectionModel().isRowSelected(r, self._table.rootIndex()):
                    self._table.blockSignals(True)
                    self._table.selectRow(r)
                    self._table.blockSignals(False)
                break


# ══════════════════════════════════════════════════════════════
#  COVERAGE ANALYSIS  (lightweight raster)
# ══════════════════════════════════════════════════════════════
def compute_coverage_grid(sensors: List[SensorConfig],
                          x_range=(-200, 400), y_range=(-200, 200),
                          resolution: float = 2.0):
    """Return (X_grid, Y_grid, count_grid) where count = number of sensors covering each cell."""
    xs = np.arange(x_range[0], x_range[1], resolution)
    ys = np.arange(y_range[0], y_range[1], resolution)
    X, Y = np.meshgrid(xs, ys)
    C    = np.zeros_like(X, dtype=int)

    for s in sensors:
        if not s.enabled:
            continue
        # Vector from sensor to each point
        dx = X - s.x
        dy = Y - s.y
        dist = np.sqrt(dx**2 + dy**2)
        # Angle from sensor to each point (world: 0=forward=+Y, CW)
        angle_to = np.degrees(np.arctan2(dx, dy))  # arctan2(x,y) gives angle from +Y
        # Angle difference from mount_angle
        diff = (angle_to - s.mount_angle + 180) % 360 - 180
        in_fov = (np.abs(diff) <= s.hfov / 2) & (dist <= s.range) & (dist > 0.1)
        C[in_fov] += 1

    return X, Y, C


class CoverageDialog(QWidget):
    def __init__(self, scene_cfg: SceneConfig, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("覆盖率分析")
        self.resize(800, 600)
        self.scene_cfg = scene_cfg

        layout = QVBoxLayout(self)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("分辨率:"))
        self._res_spin = QDoubleSpinBox()
        self._res_spin.setRange(0.5, 10)
        self._res_spin.setValue(2.0)
        self._res_spin.setSuffix(" m")
        ctrl.addWidget(self._res_spin)
        btn_calc = QPushButton("计算覆盖率")
        btn_calc.clicked.connect(self._calculate)
        ctrl.addWidget(btn_calc)
        self._stats_label = QLabel()
        ctrl.addWidget(self._stats_label)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # 提示：暂不考虑滚转角
        disclaimer = QLabel("注：本覆盖率分析仅计算2D水平面投影，暂未计算滚转角(Roll)影响。")
        disclaimer.setStyleSheet("color: #888888; font-size: 10px; margin-left: 2px;")
        layout.addWidget(disclaimer)

        self.fig = Figure(facecolor="#1E1E1E")
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

    def _calculate(self):
        res = self._res_spin.value()
        X, Y, C = compute_coverage_grid(self.scene_cfg.sensors, resolution=res)
        total   = C.size
        covered = np.sum(C >= 1)
        multi   = np.sum(C >= 2)
        pct     = 100 * covered / total if total > 0 else 0
        self._stats_label.setText(
            f"覆盖 {pct:.1f}%  |  冗余(≥2) {100*multi/total:.1f}%  |  盲区 {100*(1-covered/total):.1f}%"
        )

        self.fig.clf()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#1E1E1E")
        cmap_data = [(0,   '#1E1E1E'),
                     (0.01,'#1a3a1a'),
                     (0.33,'#27AE60'),
                     (0.66,'#F39C12'),
                     (1.0, '#E74C3C')]
        colors_cmap = [c for _, c in cmap_data]
        cmap = mcolors.LinearSegmentedColormap.from_list("coverage", colors_cmap, N=256)
        im = ax.pcolormesh(X, Y, C, cmap=cmap, vmin=0, vmax=max(3, C.max()))
        self.fig.colorbar(im, ax=ax, label="传感器覆盖数量")
        ax.set_xlabel("X (m)", color='white')
        ax.set_ylabel("Y (m)", color='white')
        ax.set_title("传感器覆盖热力图", color='white')
        ax.tick_params(colors='white')
        ax.set_aspect('equal')

        # Vehicle outline (车头前保险杠位于世界 (0,0)，车身向 -Y 后延伸)
        v = self.scene_cfg.vehicle
        ax.add_patch(mpatches.Rectangle(
            (-v.width / 2, -v.length), v.width, v.length,
            linewidth=1.5, edgecolor='white', facecolor='#3C4043'
        ))
        if v.trailer_length > 0:
            tw = v.effective_trailer_width
            ax.add_patch(mpatches.Rectangle(
                (-tw / 2, -v.length - v.trailer_length), tw, v.trailer_length,
                linewidth=1.2, edgecolor='white', facecolor='#2D3033'
            ))

        self.canvas.draw()


# ══════════════════════════════════════════════════════════════
#  SIDE ELEVATION VIEW  (Y-Z cross-section with blind zones)
# ══════════════════════════════════════════════════════════════
class CanvasSideView(QWidget):
    """Y-Z cross-section view: sensor elevation FOV arcs + blind zone analysis."""

    Y_MIN, Y_MAX = -120.0, 450.0
    Z_MIN, Z_MAX =   -2.0,  50.0

    def __init__(self, scene_cfg: "SceneConfig", signals: "AppSignals", parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals   = signals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Control bar ────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(6, 4, 6, 4)

        ctrl.addWidget(QLabel("  分辨率:"))
        self._res = QDoubleSpinBox()
        self._res.setRange(0.2, 5.0)
        self._res.setValue(1.0)
        self._res.setSuffix(" m")
        self._res.setFixedWidth(80)
        self._res.setToolTip("覆盖网格分辨率（越小越精细，越慢）")
        self._res.valueChanged.connect(self._delayed_redraw)
        ctrl.addWidget(self._res)

        ctrl.addSpacing(16)
        ctrl.addWidget(QLabel("截面X位置:"))
        self._cx = QDoubleSpinBox()
        self._cx.setRange(-30.0, 30.0)
        self._cx.setValue(0.0)
        self._cx.setSuffix(" m")
        self._cx.setFixedWidth(84)
        self._cx.setToolTip("沿横向X轴的侧视截面位置")
        self._cx.valueChanged.connect(self._delayed_redraw)
        ctrl.addWidget(self._cx)

        self._stats_lbl = QLabel("")
        self._stats_lbl.setStyleSheet("color:#AAAAAA; font-size:10px; margin-left:14px;")
        ctrl.addWidget(self._stats_lbl)
        ctrl.addStretch()

        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl)
        ctrl_widget.setStyleSheet("background:#2B2B2B;")
        layout.addWidget(ctrl_widget)

        # ── Matplotlib canvas ─────────────────────────────────
        self._fig = Figure(facecolor="#1E1E1E")
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setFocusPolicy(Qt.StrongFocus)
        self._nav = NavToolbar(self._canvas, self)
        self._canvas.toolbar = self._nav
        self._nav.setStyleSheet("background:#2B2B2B; border:none; qproperty-iconSize: 16px 16px; QToolButton { padding: 2px; border: none; background: transparent; } QToolButton:hover { background: #404040; }")
        layout.addWidget(self._nav)
        layout.addWidget(self._canvas, stretch=1)

        # ── Delay timer ───────────────────────────────────────
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.redraw)

        for sig in (signals.sensor_changed, signals.sensor_moved,
                signals.sensor_added,   signals.sensor_removed,
                signals.vehicle_changed,
                    signals.scene_rebuilt):
            sig.connect(self._delayed_redraw)

        QTimer.singleShot(800, self.redraw)

    # ──────────────────────────────────────────────────────────
    def _delayed_redraw(self, *_):
        self._timer.start(500)

    # ──────────────────────────────────────────────────────────
    def redraw(self):
        """Compute Y-Z coverage grid and render side-elevation view."""
        try:
            self._redraw_impl()
        except Exception:
            import traceback
            self._fig.clf()
            ax = self._fig.add_subplot(111)
            ax.set_facecolor("#0D1117")
            self._fig.patch.set_facecolor("#1E1E1E")
            ax.text(0.5, 0.5, f'侧视图渲染错误:\n{traceback.format_exc()}',
                    transform=ax.transAxes, ha='center', va='center',
                    color='#FF6666', fontsize=7, family='monospace')
            self._canvas.draw()

    def _redraw_impl(self):
        """Internal: actual rendering logic."""
        res = self._res.value()
        cx  = self._cx.value()

        ys = np.arange(self.Y_MIN, self.Y_MAX + res, res)
        zs = np.arange(self.Z_MIN, self.Z_MAX + res, res)
        Y, Z = np.meshgrid(ys, zs)          # shape (nz, ny)
        C    = np.zeros_like(Y, dtype=np.float32)

        for s in self.scene_cfg.sensors:
            if not s.enabled:
                continue
            pitch = getattr(s, 'pitch', 0.0)
            dx = float(cx) - s.x
            dy = Y - s.y
            dz = Z - s.z
            dist    = np.sqrt(dx**2 + dy**2 + dz**2)
            dist_xy = np.sqrt(dx**2 + dy**2)

            # azimuth: 0=+Y forward, CW positive (matches mount_angle convention)
            az_deg = np.degrees(np.arctan2(float(dx), dy))
            el_deg = np.degrees(np.arctan2(dz, dist_xy))

            az_diff = (az_deg - s.mount_angle + 180.0) % 360.0 - 180.0
            el_diff = el_deg - pitch

            mask = (
                (np.abs(az_diff) <= s.hfov / 2.0) &
                (np.abs(el_diff) <= s.vfov / 2.0) &
                (dist <= s.range) & (dist > 0.05)
            )
            C[mask] += 1.0

        # ── Statistics ─────────────────────────────────────────
        above_gnd     = Z >= 0.0
        total_cells   = int(np.sum(above_gnd))
        blind_cells   = int(np.sum((C < 0.5) & above_gnd))
        covered_cells = total_cells - blind_cells
        blind_pct     = 100.0 * blind_cells   / max(total_cells, 1)
        covered_pct   = 100.0 * covered_cells / max(total_cells, 1)
        self._stats_lbl.setText(
            f"  覆盖 {covered_pct:.1f}%   |   盲区 {blind_pct:.1f}%   "
            f"|   分辨率 {res:.1f} m  (注: 暂不考虑滚转角)  "
        )

        # ── Draw ───────────────────────────────────────────────
        self._fig.clf()
        ax = self._fig.add_subplot(111)
        ax.set_facecolor("#0D1117")
        self._fig.patch.set_facecolor("#1E1E1E")

        vmax = max(float(C.max()), 1.0)

        # Coverage heatmap (above ground only)
        cmap_cov = mcolors.LinearSegmentedColormap.from_list(
            "cov",
            [(0.0,  "#0D2010"),
             (0.3,  "#1a5c2a"),
             (0.7,  "#27AE60"),
             (1.0,  "#76ECA0")],
            N=256
        )
        cov_display = np.where(above_gnd & (C >= 0.5), C, np.nan)
        ax.pcolormesh(ys, zs, cov_display,
                      cmap=cmap_cov, vmin=0.5, vmax=vmax,
                      alpha=0.70, shading='auto', zorder=1)

        # Blind zone overlay (above ground, uncovered)
        blind_mask = (C < 0.5) & above_gnd
        blind_display = np.where(blind_mask, 1.0, np.nan)
        cmap_blind = mcolors.LinearSegmentedColormap.from_list(
            "blind", [(0, "#CC2222"), (1, "#CC2222")], N=2
        )
        ax.pcolormesh(ys, zs, blind_display,
                      cmap=cmap_blind, vmin=0.5, vmax=1.5,
                      alpha=0.50, shading='auto', zorder=2)

        # Below-ground shading
        ax.axhspan(self.Z_MIN, 0.0, color='#2A1E12', alpha=0.6, zorder=0)
        ax.axhline(0.0, color='#888888', linewidth=1.2,
                   linestyle='--', alpha=0.8, zorder=3)

        # Vehicle silhouette (车头前保险杠位于 Y=0，车身向 -Y 延伸)
        v = self.scene_cfg.vehicle
        ax.add_patch(mpatches.Rectangle(
            (-v.length, 0), v.length, v.height,
            lw=1.5, edgecolor='#DDDDDD',
            facecolor='#3C4043', zorder=4))
        ax.text(-v.length / 2, v.height * 0.5, '车头', color='#DDDDDD', fontsize=7,
                ha='center', va='center', zorder=5)
        if v.trailer_length > 0:
            ax.add_patch(mpatches.Rectangle(
                (-v.length - v.trailer_length, 0), v.trailer_length, v.height,
                lw=1.2, edgecolor='#DDDDDD',
                facecolor='#2D3033', zorder=4))
            ax.text(-v.length - v.trailer_length / 2, v.height * 0.5, '挂车',
                    color='#DDDDDD', fontsize=7, ha='center', va='center', zorder=5)

        # ── Sensor arcs ────────────────────────────────────────
        for s in self.scene_cfg.sensors:
            if not s.enabled:
                continue
            pitch  = getattr(s, 'pitch', 0.0)
            v2_rad = math.radians(s.vfov / 2.0)
            p_rad  = math.radians(pitch)
            az_rad = math.radians(s.mount_angle)

            # Parse hex color
            hex_c = s.color.lstrip('#')
            rgb   = tuple(int(hex_c[i:i+2], 16) / 255.0 for i in (0, 2, 4))

            # Sensor position marker
            ax.scatter([s.y], [s.z], color=s.color, s=55, zorder=9,
                       edgecolors='white', linewidths=0.8)

            y_proj = math.cos(az_rad)   # component along +Y axis
            sign   = 1.0 if y_proj >= 0 else -1.0

            if abs(y_proj) > 0.08:
                # Draw filled elevation arc
                n_arc = 72
                els   = np.linspace(p_rad - v2_rad, p_rad + v2_rad, n_arc)
                arc_y = s.y + sign * s.range * np.cos(els) * abs(y_proj)
                arc_z = s.z + s.range * np.sin(els)

                poly_y = np.concatenate([[s.y], arc_y, [s.y]])
                poly_z = np.concatenate([[s.z], arc_z, [s.z]])
                ax.fill(poly_y, poly_z, color=rgb,
                        alpha=min(s.opacity * 2.5, 0.70), zorder=6)
                ax.plot(arc_y, arc_z, color=s.color,
                        linewidth=1.0, alpha=0.9, zorder=7)
                ax.plot([s.y, arc_y[0]],  [s.z, arc_z[0]],
                        color=s.color, linewidth=0.8, alpha=0.7, zorder=7)
                ax.plot([s.y, arc_y[-1]], [s.z, arc_z[-1]],
                        color=s.color, linewidth=0.8, alpha=0.7, zorder=7)

                # Center-line arrow
                c_y = s.y + sign * s.range * math.cos(p_rad) * abs(y_proj)
                c_z = s.z + s.range * math.sin(p_rad)
                ax.annotate("",
                            xy=(c_y, c_z), xytext=(s.y, s.z),
                            arrowprops=dict(arrowstyle="-|>", color=s.color,
                                            lw=0.8, mutation_scale=8),
                            zorder=8)

                # ── Ground intersection distances ───────────────
                # For each FOV boundary ray (and range-arc boundary) that
                # reaches Z=0, draw a dotted line sensor→ground and label
                # the HORIZONTAL ground distance (X-Y plane) from sensor.
                if s.z > 0.05:
                    gnd_pts = []   # (y_hit, horizontal_dist)
                    for el_b in (p_rad - v2_rad, p_rad + v2_rad):
                        sin_b = math.sin(el_b)
                        if sin_b < -1e-6:              # ray points downward
                            t = s.z / (-sin_b)
                            if 0.05 < t <= s.range:
                                horiz = t * math.cos(el_b)   # 水平距离 (X-Y 平面)
                                gnd_pts.append((
                                    s.y + sign * horiz * abs(y_proj),
                                    horiz
                                ))
                    # Range-arc boundary at Z=0
                    if s.z < s.range:
                        sin_arc = -s.z / s.range
                        if -1.0 < sin_arc < -1e-6:
                            el_arc = math.asin(sin_arc)
                            if p_rad - v2_rad <= el_arc <= p_rad + v2_rad:
                                horiz = math.sqrt(
                                    max(s.range * s.range - s.z * s.z, 0.0))
                                gnd_pts.append((
                                    s.y + sign * horiz * abs(y_proj),
                                    horiz
                                ))
                    # Sort by horizontal distance; remove near-duplicates (< 0.5 m apart)
                    gnd_pts.sort(key=lambda p: p[1])
                    deduped: list = []
                    for pt in gnd_pts:
                        if not deduped or abs(pt[1] - deduped[-1][1]) > 0.5:
                            deduped.append(pt)
                    for y_hit, horiz in deduped:
                        # Downward-triangle marker on ground line
                        ax.plot([y_hit], [0.0], marker='v', markersize=5,
                                color=s.color, markeredgecolor='white',
                                markeredgewidth=0.4, clip_on=True, zorder=12)
                        # Dotted line: sensor → ground intersection
                        ax.plot([s.y, y_hit], [s.z, 0.0],
                                color=s.color, linewidth=0.9,
                                linestyle=':', alpha=0.65, zorder=11)
                        # Horizontal-distance label at midpoint of the line
                        ax.text((s.y + y_hit) / 2, s.z / 2,
                                f"{horiz:.1f} m",
                                color=s.color, fontsize=6,
                                ha='center', va='center',
                                bbox=dict(boxstyle='round,pad=0.2',
                                          fc='#0D1117', ec='none', alpha=0.80),
                                zorder=13)
            else:
                # Sideways sensor: vertical elevation bar at Y position
                z_lo = s.z + s.range * math.sin(p_rad - v2_rad)
                z_hi = s.z + s.range * math.sin(p_rad + v2_rad)
                ax.plot([s.y, s.y], [z_lo, z_hi],
                        color=s.color, linewidth=3, alpha=0.65, zorder=7)

            ax.annotate(
                s.name, xy=(s.y, s.z + 0.35),
                color='#000000', fontsize=10, fontweight='bold',
                ha='center', va='bottom', zorder=15,
                bbox=dict(boxstyle='round,pad=0.25',
                          fc='white', ec=s.color,
                          linewidth=1.4, alpha=0.92)
            )

        # ── Legend & axes ─────────────────────────────────────
        ax.legend(
            handles=[
                mpatches.Patch(facecolor=(0.80, 0.13, 0.13), alpha=0.55, label='盲区（无覆盖）'),
                mpatches.Patch(facecolor='#27AE60',           alpha=0.60, label='已覆盖区域'),
                mpatches.Patch(facecolor='#2A1E12',           alpha=0.70, label='地面以下'),
            ],
            loc='upper right', facecolor='#2B2B2B', edgecolor='#555555',
            labelcolor='#CCCCCC', fontsize=8
        )
        ax.set_xlabel("Y – 纵向距离 (m)", color='#CCCCCC', fontsize=9)
        ax.set_ylabel("Z – 高度 (m)",     color='#CCCCCC', fontsize=9)
        ax.set_title(
            f"侧视截面  X = {cx:.1f} m  ·  绿色 = 覆盖  红色 = 盲区",
            color='#DDDDDD', fontsize=9
        )
        ax.tick_params(colors='#777777', labelsize=7)
        ax.set_xlim(self.Y_MIN, self.Y_MAX)
        ax.set_ylim(self.Z_MIN, self.Z_MAX)
        ax.grid(True, color='#2A2A2A', linewidth=0.4)
        for sp in ax.spines.values():
            sp.set_edgecolor('#444444')

        self._fig.tight_layout(pad=0.8)
        self._canvas.draw()


# ══════════════════════════════════════════════════════════════
#  SENSOR LEGEND WIDGET
# ══════════════════════════════════════════════════════════════
class SensorLegendWidget(QWidget):
    """Color-coded card list showing every sensor's name and FOV spec.
    Click a card (or its 👁 button) to toggle sensor enabled/disabled.
    """

    def __init__(self, scene_cfg: SceneConfig, signals: AppSignals, parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self._signals  = signals

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setContentsMargins(2, 2, 2, 2)
        self._vbox.setSpacing(4)
        self._vbox.addStretch()

        scroll.setWidget(self._container)
        root.addWidget(scroll)

        for sig in (signals.sensor_added, signals.sensor_removed,
                    signals.sensor_changed, signals.scene_rebuilt):
            sig.connect(self._rebuild)

        self._rebuild()

    # ── rebuild ───────────────────────────────────────────────
    def _rebuild(self, *_):
        # Remove all card widgets (keep the trailing stretch)
        while self._vbox.count() > 1:
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for s in self.scene_cfg.sensors:
            self._vbox.insertWidget(self._vbox.count() - 1, self._make_card(s))

    def _make_card(self, s: SensorConfig) -> QFrame:
        frame = QFrame()
        frame.setObjectName("LegendCard")

        # Derive a dark tinted background from sensor color
        hx = s.color.lstrip('#')
        r, g, b = (int(hx[i:i+2], 16) for i in (0, 2, 4))
        br, bg, bb = int(r * 0.22 + 18), int(g * 0.22 + 18), int(b * 0.22 + 18)

        frame.setStyleSheet(f"""
            QFrame#LegendCard {{
                background-color: rgb({br},{bg},{bb});
                border-left: 4px solid {s.color};
                border-radius: 4px;
            }}
        """)

        lay = QHBoxLayout(frame)
        lay.setContentsMargins(8, 5, 4, 5)
        lay.setSpacing(4)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        # Sensor name
        name_lbl = QLabel(s.name)
        nf = QFont()
        nf.setBold(True)
        nf.setPointSize(9)
        name_lbl.setFont(nf)
        opacity = "ff" if s.enabled else "80"
        name_lbl.setStyleSheet(
            f"color: {s.color}{opacity}; background: transparent; border: none;")
        text_col.addWidget(name_lbl)

        # FOV spec
        fov_str = f"FOV: {s.range:.0f}m / {s.hfov:.0f}°"
        d = getattr(s, 'disp_hfov', 0.0)
        if d > 0:
            fov_str += f" (显示:{d:.0f}°)"
        if s.vfov > 0:
            fov_str += f"  V:{s.vfov:.0f}°"
        if s.pitch != 0:
            fov_str += f"  俯仰:{s.pitch:+.0f}°"
        if getattr(s, 'roll', 0.0) != 0:
            fov_str += f"  滚转:{s.roll:+.0f}°"
        fov_lbl = QLabel(fov_str)
        fov_lbl.setStyleSheet(
            "color: #aaaaaa; background: transparent; border: none; font-size: 8pt;")
        text_col.addWidget(fov_lbl)

        lay.addLayout(text_col, stretch=1)

        # Visibility toggle button
        eye_btn = QPushButton("👁" if s.enabled else "🚫")
        eye_btn.setFixedSize(26, 26)
        eye_btn.setFlat(True)
        eye_btn.setToolTip("点击切换显示/隐藏")
        eye_btn.setStyleSheet(
            "QPushButton { font-size: 14px; border: none; background: transparent; }"
            "QPushButton:hover { background: rgba(255,255,255,15); border-radius: 4px; }"
        )
        sid = s.id
        def _toggle(checked, _s=s, _b=eye_btn):
            _s.enabled = not _s.enabled
            _b.setText("👁" if _s.enabled else "🚫")
            self._signals.sensor_changed.emit(_s.id)
        eye_btn.clicked.connect(_toggle)
        lay.addWidget(eye_btn, alignment=Qt.AlignVCenter)

        return frame


# ══════════════════════════════════════════════════════════════
#  IMPORT SENSORS FROM IMAGE DIALOG
# ══════════════════════════════════════════════════════════════
class ImportSensorsFromImageDialog(QDialog):
    """Load a FOV-legend image, OCR it, parse sensor specs, confirm, then import."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("从图片识别传感器")
        self.setMinimumSize(760, 560)
        self._parsed: list = []

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # ── File row ──────────────────────────────────────────
        file_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText("选择含有传感器图例的图像文件…")
        browse_btn = QPushButton("浏览…")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self._path_edit)
        file_row.addWidget(browse_btn)
        root.addLayout(file_row)

        # ── Preview | OCR text ────────────────────────────────
        mid = QHBoxLayout()
        mid.setSpacing(10)

        # Left: image preview
        self._preview = QLabel("图像预览")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setMinimumSize(280, 200)
        self._preview.setStyleSheet(
            "border: 1px solid #555; background: #181818; color: #666;")
        mid.addWidget(self._preview, 3)

        # Right: OCR text + buttons
        right_col = QVBoxLayout()
        right_col.setSpacing(4)

        ocr_hdr = QHBoxLayout()
        ocr_hdr.addWidget(QLabel("识别 / 粘贴文字:"))
        ocr_hdr.addStretch()
        self._ocr_btn = QPushButton("🔍 OCR 自动识别")
        self._ocr_btn.setEnabled(False)
        self._ocr_btn.setToolTip(
            "调用 Windows 内置 OCR 引擎识别图像中的文字（需要 Windows 10+）")
        self._ocr_btn.clicked.connect(self._run_ocr)
        self._parse_btn = QPushButton("⚙ 解析传感器")
        self._parse_btn.setEnabled(False)
        self._parse_btn.setToolTip(
            "从上方文字中提取传感器名称和 FOV 参数")
        self._parse_btn.clicked.connect(self._run_parse)
        ocr_hdr.addWidget(self._ocr_btn)
        ocr_hdr.addWidget(self._parse_btn)
        right_col.addLayout(ocr_hdr)

        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText(
            "点击「OCR 自动识别」提取图像文字，\n"
            "或直接在此粘贴从图例中复制的文字。\n\n"
            "格式示例：\n"
            "Front Stereo Camera\n"
            "FOV: 400m/60°\n"
            "Front LiDAR\n"
            "FOV: 250m/120°"
        )
        self._text_edit.setMinimumHeight(160)
        self._text_edit.textChanged.connect(self._on_text_changed)
        right_col.addWidget(self._text_edit)

        mid.addLayout(right_col, 4)
        root.addLayout(mid)

        # ── Parsed sensor list ────────────────────────────────
        root.addWidget(QLabel("解析结果（可在属性面板中修改颜色/位置）:"))
        self._list = QListWidget()
        self._list.setMaximumHeight(160)
        self._list.setSelectionMode(QAbstractItemView.NoSelection)
        root.addWidget(self._list)

        # ── Dialog buttons ────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._import_btn = QPushButton("✅ 导入传感器")
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._import_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    # ── internal helpers ──────────────────────────────────────
    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图像", "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)")
        if not path:
            return
        self._path_edit.setText(path)
        pix = QPixmap(path)
        if not pix.isNull():
            self._preview.setPixmap(
                pix.scaled(280, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self._ocr_btn.setEnabled(True)

    def _on_text_changed(self):
        has_text = bool(self._text_edit.toPlainText().strip())
        self._parse_btn.setEnabled(has_text)

    def _run_ocr(self):
        path = self._path_edit.text()
        if not path:
            return
        self._ocr_btn.setEnabled(False)
        self._ocr_btn.setText("识别中…")
        QApplication.processEvents()
        try:
            text = _ocr_image_windows(path)
            if text:
                self._text_edit.setPlainText(text)
            else:
                QMessageBox.information(self, "提示", "OCR 未能识别到文字，请手动粘贴。")
        except Exception as e:
            QMessageBox.warning(
                self, "OCR 失败",
                f"Windows OCR 识别失败：\n{e}\n\n请手动在文本框中粘贴图例文字。")
        finally:
            self._ocr_btn.setEnabled(True)
            self._ocr_btn.setText("🔍 OCR 自动识别")

    def _run_parse(self):
        text = self._text_edit.toPlainText()
        self._parsed = _parse_sensor_legend(text)
        self._list.clear()
        if not self._parsed:
            item = QListWidgetItem("⚠ 未识别到传感器，请检查文本格式（需含 FOV: XXm/XX° 行）")
            item.setForeground(QColor("#FF9800"))
            self._list.addItem(item)
            self._import_btn.setEnabled(False)
            return
        type_zh = {"camera": "摄像头", "radar": "毫米波雷达", "lidar": "激光雷达"}
        for s in self._parsed:
            lbl = (f"[{type_zh.get(s['sensor_type'], s['sensor_type'])}]  "
                   f"{s['name']}  —  FOV: {s['range']:.0f}m / {s['hfov']:.0f}°"
                   f"  V:{s['vfov']:.0f}°")
            item = QListWidgetItem(lbl)
            item.setForeground(QColor(s['color']))
            self._list.addItem(item)
        self._import_btn.setEnabled(True)

    # ── public ────────────────────────────────────────────────
    def sensors(self) -> list:
        return self._parsed


# ══════════════════════════════════════════════════════════════
#  EXPORT DIALOG
# ══════════════════════════════════════════════════════════════
class ExportDialog(QDialog):
    """PNG export options: resolution, rotation, background, render mode."""

    _PRESET_ANGLES = [0, 90, 180, 270]
    _BG_LABELS     = ["白色", "透明 (PNG)", "黑色", "深色 #1E1E1E"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出 PNG 选项")
        self.setMinimumWidth(340)
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Render mode ───────────────────────────────────────
        self._mode_combo = QComboBox()
        self._mode_combo.addItems([
            "🎨 高质量 (Matplotlib) — 推荐",
            "🖥 标准 (实时画布) — 所见即所得",
        ])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        layout.addRow("渲染模式:", self._mode_combo)

        self._width = QSpinBox()
        self._width.setRange(500, 12000)
        self._width.setValue(4000)
        self._width.setSingleStep(500)
        self._width.setSuffix(" px  (宽)")
        layout.addRow("分辨率:", self._width)

        self._rot_combo = QComboBox()
        for lbl in ["0° (不旋转)", "90° 顺时针", "180°", "270° 顺时针", "自定义…"]:
            self._rot_combo.addItem(lbl)
        layout.addRow("旋转导出:", self._rot_combo)

        self._custom_spin = QDoubleSpinBox()
        self._custom_spin.setRange(-360, 360)
        self._custom_spin.setValue(0)
        self._custom_spin.setSuffix("°")
        self._custom_spin.setEnabled(False)
        layout.addRow("自定义角度:", self._custom_spin)
        self._rot_combo.currentIndexChanged.connect(
            lambda i: self._custom_spin.setEnabled(i == 4)
        )

        self._bg_combo = QComboBox()
        self._bg_combo.addItems(self._BG_LABELS)
        layout.addRow("背景颜色:", self._bg_combo)

        self._legend_cb = QCheckBox("在左侧附加传感器图例")
        self._legend_cb.setChecked(True)
        layout.addRow("图例:", self._legend_cb)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("可选：输入导出抬头，不填则不显示")
        layout.addRow("抬头:", self._title_edit)

        # Optional elements checkboxes
        self._export_lanes_cb = QCheckBox("包含车道线和路面")
        self._export_lanes_cb.setChecked(True)
        layout.addRow("导出车道线:", self._export_lanes_cb)

        self._export_ego_cb = QCheckBox("包含主车 (Ego)")
        self._export_ego_cb.setChecked(True)
        layout.addRow("导出主车:", self._export_ego_cb)

        self._export_target_cb = QCheckBox("包含目标车辆 (Target)")
        self._export_target_cb.setChecked(True)
        layout.addRow("导出目标车:", self._export_target_cb)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("导出")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _on_mode_changed(self, idx: int):
        # Rotation is only meaningful for the standard canvas export
        hq = (idx == 0)
        self._rot_combo.setEnabled(not hq)
        self._custom_spin.setEnabled(False)

    def params(self):
        """Return (width_px, angle_deg, bg_str_or_QColor, show_legend, hq_mode, title)."""
        idx   = self._rot_combo.currentIndex()
        angle = (self._custom_spin.value() if idx == 4
                 else self._PRESET_ANGLES[idx])
        # bg: string for HQ matplotlib mode; QColor for standard mode
        bg_str_map   = ['white', None, 'black', '#1E1E1E']
        bg_qcol_map  = [QColor(Qt.white), None, QColor(Qt.black), QColor('#1E1E1E')]
        bi = self._bg_combo.currentIndex()
        hq = (self._mode_combo.currentIndex() == 0)
        bg = bg_str_map[bi] if hq else bg_qcol_map[bi]
        return (self._width.value(), angle, bg,
            self._legend_cb.isChecked(), hq,
            self._title_edit.text().strip(),
            self._export_lanes_cb.isChecked(),
            self._export_ego_cb.isChecked(),
            self._export_target_cb.isChecked())


# ══════════════════════════════════════════════════════════════
#  IMPORT BACKGROUND IMAGE DIALOG
# ══════════════════════════════════════════════════════════════
class ImportBgDialog(QDialog):
    """Configure a reference image to use as 2D-view background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入背景参考图")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── File picker ───────────────────────────────────────
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("选择图像文件…")
        self._path_edit.setReadOnly(True)
        browse_btn = QPushButton("浏览…")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self._path_edit)
        path_row.addWidget(browse_btn)
        layout.addRow("图像文件:", path_row)

        # ── Preview ───────────────────────────────────────────
        self._preview = QLabel("（无预览）")
        self._preview.setFixedSize(240, 130)
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet("border:1px solid #555; background:#111; color:#888;")
        layout.addRow("预览:", self._preview)

        # ── Pre-rotation ──────────────────────────────────────
        self._rot_combo = QComboBox()
        self._rot_combo.addItems(["0° (不旋转)", "90° 顺时针", "180°", "270° 顺时针"])
        self._rot_combo.currentIndexChanged.connect(self._update_preview)
        layout.addRow("旋转图像:", self._rot_combo)

        # ── Real-world scale ──────────────────────────────────
        self._real_w = QDoubleSpinBox()
        self._real_w.setRange(0.5, 2000)
        self._real_w.setValue(6.0)
        self._real_w.setSuffix(" m  (旋转后图像宽度对应实际米数)")
        self._real_w.setDecimals(1)
        layout.addRow("实际宽度:", self._real_w)

        # ── Vehicle anchor in image ───────────────────────────
        hint = QLabel("车辆中心在图像中的位置（百分比，旋转后坐标）")
        hint.setStyleSheet("color:#888; font-size:11px;")
        layout.addRow("", hint)

        self._anchor_x = QDoubleSpinBox()
        self._anchor_x.setRange(0, 100)
        self._anchor_x.setValue(50.0)
        self._anchor_x.setSuffix(" %  (从左)")
        layout.addRow("横向位置:", self._anchor_x)

        self._anchor_y = QDoubleSpinBox()
        self._anchor_y.setRange(0, 100)
        self._anchor_y.setValue(50.0)
        self._anchor_y.setSuffix(" %  (从上)")
        layout.addRow("纵向位置:", self._anchor_y)

        # ── Opacity ───────────────────────────────────────────
        self._opacity = QDoubleSpinBox()
        self._opacity.setRange(10, 100)
        self._opacity.setValue(65.0)
        self._opacity.setSuffix(" %")
        layout.addRow("不透明度:", self._opacity)

        # ── Buttons ───────────────────────────────────────────
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("导入")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

        self._raw_pix = None   # original QPixmap before rotation

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景参考图", "",
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)"
        )
        if path:
            self._path_edit.setText(path)
            self._raw_pix = QPixmap(path)
            self._update_preview()

    def _update_preview(self):
        if not self._raw_pix or self._raw_pix.isNull():
            return
        pix = self._rotated_pix()
        self._preview.setPixmap(
            pix.scaled(240, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _rotated_pix(self):
        if not self._raw_pix or self._raw_pix.isNull():
            return QPixmap()
        angles = [0, 90, 180, 270]
        deg = angles[self._rot_combo.currentIndex()]
        if deg == 0:
            return self._raw_pix
        return self._raw_pix.transformed(QTransform().rotate(deg),
                                          Qt.SmoothTransformation)

    def params(self):
        return {
            'path':     self._path_edit.text(),
            'rot_deg':  [0, 90, 180, 270][self._rot_combo.currentIndex()],
            'real_w':   self._real_w.value(),
            'anchor_x': self._anchor_x.value() / 100.0,
            'anchor_y': self._anchor_y.value() / 100.0,
            'opacity':  self._opacity.value() / 100.0,
        }


# ══════════════════════════════════════════════════════════════
#  TOP-DOWN BLIND ZONE VIEW (X-Y plane @ given z height)
# ═════════════════════════════════════════════════════════════
class CanvasBlindZoneView(QWidget):
    """俯视盲区分析视图：在指定高度 z 的 X-Y 平面上计算传感器覆盖/盲区。

    Display: 世界 +Y (前方) → 屏幕向上; 世界 +X (右) → 屏幕向右。
    车头前保险杠位于 (0, 0)，车身占 Y ∈ [-total_length, 0]。
    """

    DEFAULT_X_HALF   = 15.0   # 侧向 ±X
    DEFAULT_Y_FRONT  = 30.0   # 车头前方
    DEFAULT_Y_BACK   = 8.0    # 车尾后额外范围

    def __init__(self, scene_cfg: "SceneConfig", signals: "AppSignals", parent=None):
        super().__init__(parent)
        self.scene_cfg = scene_cfg
        self.signals = signals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 控制栏
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(6, 4, 6, 4)

        ctrl.addWidget(QLabel("  分析高度 Z:"))
        self._z = QDoubleSpinBox()
        self._z.setRange(-2.0, 10.0)
        self._z.setValue(1.0)
        self._z.setSingleStep(0.1)
        self._z.setSuffix(" m")
        self._z.setFixedWidth(80)
        self._z.setToolTip("平面模式：分析高度。立柱模式：目标顶部高度。")
        self._z.valueChanged.connect(self._delayed_redraw)
        ctrl.addWidget(self._z)

        ctrl.addSpacing(8)
        ctrl.addWidget(QLabel("模式:"))
        self._mode = QComboBox()
        self._mode.addItems([
            "目标立柱 (0∼Z 任一高度被视=覆盖)",
            "单平面切片 (z=Z 处覆盖)",
        ])
        self._mode.setCurrentIndex(0)
        self._mode.setToolTip(
            "目标立柱模式：以 0~Z 为高的立柱作为目标，"
            "只要立柱任一高度被传感器看到即算覆盖。\n"
            "单平面模式：只检查 z=Z 这一个水平切面。"
        )
        self._mode.setFixedWidth(220)
        self._mode.currentIndexChanged.connect(self._delayed_redraw)
        ctrl.addWidget(self._mode)

        ctrl.addSpacing(8)
        ctrl.addWidget(QLabel("分辨率:"))
        self._res = QDoubleSpinBox()
        self._res.setRange(0.05, 2.0)
        self._res.setValue(0.25)
        self._res.setSingleStep(0.05)
        self._res.setSuffix(" m")
        self._res.setFixedWidth(80)
        self._res.setToolTip("网格分辨率（越小越精细越慢）")
        self._res.valueChanged.connect(self._delayed_redraw)
        ctrl.addWidget(self._res)

        ctrl.addSpacing(12)
        ctrl.addWidget(QLabel("范围:"))
        self._range_combo = QComboBox()
        self._range_combo.addItems(["近前盲区 (±15m × 30m)",
                                    "车周近区 (±25m × 50m)",
                                    "中距离 (±50m × 100m)"])
        self._range_combo.setCurrentIndex(0)
        self._range_combo.currentIndexChanged.connect(self._delayed_redraw)
        ctrl.addWidget(self._range_combo)

        ctrl.addSpacing(12)
        self._show_fov = QCheckBox("叠加FOV轮廓")
        self._show_fov.setChecked(True)
        self._show_fov.toggled.connect(self._delayed_redraw)
        ctrl.addWidget(self._show_fov)

        ctrl.addSpacing(8)
        self._show_blind_outline = QCheckBox("盲区轮廓线")
        self._show_blind_outline.setChecked(True)
        self._show_blind_outline.setToolTip("用黄色粗线勾勒出盲区边界")
        self._show_blind_outline.toggled.connect(self._delayed_redraw)
        ctrl.addWidget(self._show_blind_outline)

        ctrl.addSpacing(8)
        self._show_blind_fill = QCheckBox("盲区色块")
        self._show_blind_fill.setChecked(True)
        self._show_blind_fill.setToolTip("红色半透明填充盲区")
        self._show_blind_fill.toggled.connect(self._delayed_redraw)
        ctrl.addWidget(self._show_blind_fill)

        ctrl.addSpacing(8)
        self._show_blind_dims = QCheckBox("标注盲区尺寸")
        self._show_blind_dims.setChecked(True)
        self._show_blind_dims.setToolTip("用箭头线标注每个盲区地块的宽度和深度")
        self._show_blind_dims.toggled.connect(self._delayed_redraw)
        ctrl.addWidget(self._show_blind_dims)

        self._stats_lbl = QLabel("")
        self._stats_lbl.setStyleSheet("color:#AAAAAA; font-size:10px; margin-left:14px;")
        ctrl.addWidget(self._stats_lbl)
        ctrl.addStretch()

        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl)
        ctrl_widget.setStyleSheet("background:#2B2B2B;")
        layout.addWidget(ctrl_widget)

        self._fig = Figure(facecolor="#1E1E1E")
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setFocusPolicy(Qt.StrongFocus)
        self._nav = NavToolbar(self._canvas, self)
        self._canvas.toolbar = self._nav
        self._nav.setStyleSheet("background:#2B2B2B; border:none; qproperty-iconSize: 16px 16px; QToolButton { padding: 2px; border: none; background: transparent; } QToolButton:hover { background: #404040; }")
        layout.addWidget(self._nav)
        layout.addWidget(self._canvas, stretch=1)   # stretch=1 → canvas takes all spare space

        # 右键点击查询覆盖详情
        self._fig.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        # 保存最新一次渲染的覆盖数据，供点击查询用
        self._last_cover = None   # (C, X, Y, xs, ys, analyze_mask, z_levels)

        # 延迟重绘
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.redraw)

        for sig in (signals.sensor_changed, signals.sensor_moved,
                    signals.sensor_added,   signals.sensor_removed,
                    signals.vehicle_changed, signals.scene_rebuilt):
            sig.connect(self._delayed_redraw)

        QTimer.singleShot(900, self.redraw)

    def _delayed_redraw(self, *_):
        self._timer.start(450)

    def _on_canvas_click(self, event):
        """右键点击盲区图：弹窗显示该点的覆盖详情。"""
        if event.button != 3:   # 仅响应右键 (matplotlib: 1=左, 2=中, 3=右)
            return
        if self._last_cover is None or event.xdata is None or event.ydata is None:
            return

        C, X, Y, xs, ys, analyze_mask, z_levels, mode_idx = self._last_cover
        px, py = float(event.xdata), float(event.ydata)

        # 找到最近网格点
        ix = np.argmin(np.abs(xs - px))
        iy = np.argmin(np.abs(ys - py))
        cx_val = int(C[iy, ix])
        in_veh  = not bool(analyze_mask[iy, ix])

        # 生成报告
        lines = [f"测试点  X={px:.3f}  Y={py:.3f}"]
        if in_veh:
            lines.append("位于车体内部（不计入盲区分析）")
        else:
            lines.append(f"覆盖传感器数: {cx_val}")
            if cx_val == 0:
                lines.append("❌ 盲区 — 所有高度层均无传感器覆盖")
            else:
                lines.append(f"✅ 已覆盖 — 最多 {cx_val} 个传感器在立柱高度内看到该点")
        lines.append(f"分析模式: {'立柱 0~{z_levels[-1]:.2f}m' if mode_idx == 0 else f'平面 z={z_levels[0]:.2f}m'}")

        msg = "\n".join(lines)
        QMessageBox.information(self, "盲区测试点查询", msg)

    def _current_bounds(self):
        idx = self._range_combo.currentIndex()
        if idx == 0:
            return self.DEFAULT_X_HALF, self.DEFAULT_Y_FRONT, self.DEFAULT_Y_BACK
        if idx == 1:
            return 25.0, 50.0, 12.0
        return 50.0, 100.0, 20.0

    def _draw_blind_zone_dimensions(self, ax, blind_bin, xs, ys, v):
        """在盲区地块上绘制尺寸标注箭头。

        对每个连续盲区地块（由相邻盲区Y行合并）：
        - 在宽度最大的连续段处画水平尺寸线 + 标注该段宽度
        - 左侧画纵向尺寸箭头 + 标注深度
        - 标注距车头距离

        宽度取连续盲区段（不含FOV覆盖"洞"）的最大值，而非整行跨度。
        """
        if not blind_bin.any():
            return

        ny, nx = blind_bin.shape
        res_y = (ys[-1] - ys[0]) / max(ny - 1, 1)

        def _contiguous_segments(row):
            """返回该行所有连续 True 段的 (col_start, col_end, xs_left, xs_right, width) 列表"""
            cols = np.where(row)[0]
            if len(cols) == 0:
                return []
            segs = []
            start = cols[0]
            for i in range(1, len(cols)):
                if cols[i] != cols[i-1] + 1:
                    segs.append((start, cols[i-1],
                                 xs[start], xs[cols[i-1]],
                                 xs[cols[i-1]] - xs[start]))
                    start = cols[i]
            segs.append((start, cols[-1],
                         xs[start], xs[cols[-1]],
                         xs[cols[-1]] - xs[start]))
            return segs

        # 按 Y 行收集每行最宽连续段
        row_best = []   # (y, x_left, x_right, width) or None
        for ri in range(ny):
            segs = _contiguous_segments(blind_bin[ri, :])
            if not segs:
                row_best.append(None)
                continue
            best_seg = max(segs, key=lambda s: s[4])  # widest segment
            row_best.append((ys[ri], best_seg[2], best_seg[3], best_seg[4]))

        # 按连续 Y 行分割成不同地块
        chunks = []
        chunk_start = None
        for ri in range(ny):
            if row_best[ri] is not None:
                if chunk_start is None:
                    chunk_start = ri
            else:
                if chunk_start is not None:
                    chunks.append((chunk_start, ri - 1))
                    chunk_start = None
        if chunk_start is not None:
            chunks.append((chunk_start, ny - 1))

        # 过滤太小的地块（<3 行）
        min_rows = 3
        chunks = [(a, b) for a, b in chunks if b - a + 1 >= min_rows]

        dim_color  = '#FF7043'   # 橙色标注线
        text_color = '#FFAB91'

        for y_start, y_end in chunks:
            # 地块范围内找宽度最大的最宽连续段
            max_w = 0.0
            best_ri = y_start
            for ri in range(y_start, y_end + 1):
                *_, w = row_best[ri]
                if w > max_w:
                    max_w = w
                    best_ri = ri

            best = row_best[best_ri]
            yc, xl, xr, bw = best

            y_top = ys[y_start]
            y_bot = ys[y_end]

            # 用地块内所有最宽段的极值左右边界（而非整行跨度）
            x_left_all = [row_best[ri][1] for ri in range(y_start, y_end + 1)]
            x_right_all = [row_best[ri][2] for ri in range(y_start, y_end + 1)]
            real_xl = min(x_left_all)
            real_xr = max(x_right_all)

            # ── 水平尺寸线（最宽连续段处） ──
            h_offset = 0.5
            ax.annotate(
                "", xy=(real_xl, yc + h_offset),
                xytext=(real_xr, yc + h_offset),
                arrowprops=dict(arrowstyle="<->", color=dim_color,
                                lw=1.8, shrinkA=0, shrinkB=0),
                zorder=20)
            ax.text((real_xl + real_xr) / 2, yc + h_offset + 0.25,
                    f"{bw:.1f} m",
                    color=text_color, fontsize=6.5, fontweight='bold',
                    ha='center', va='bottom', zorder=21,
                    bbox=dict(boxstyle='round,pad=0.15',
                              fc='#1E1E1E', ec=dim_color, alpha=0.85))

            # ── 纵向尺寸线（左侧外） ──
            depth = y_bot - y_top
            x_ann = real_xl - 1.8
            if x_ann >= xs[0] + 0.5 and depth > res_y:
                ax.annotate(
                    "", xy=(x_ann, y_bot), xytext=(x_ann, y_top),
                    arrowprops=dict(arrowstyle="<->", color=dim_color,
                                    lw=1.8, shrinkA=0, shrinkB=0),
                    zorder=20)
                ax.text(x_ann - 0.15, (y_top + y_bot) / 2,
                        f"{depth:.1f} m",
                        color=text_color, fontsize=6.5, fontweight='bold',
                        ha='right', va='center', rotation=90, zorder=21,
                        bbox=dict(boxstyle='round,pad=0.15',
                                  fc='#1E1E1E', ec=dim_color, alpha=0.85))

            # ── 距车头距离 ──
            dist_from_veh = y_top if y_top >= 0 else abs(y_bot)
            ax.text(x_ann + 0.3, y_bot - 0.35,
                    f"距车头 {dist_from_veh:.1f} m",
                    color='#B0BEC5', fontsize=5.5, ha='left', va='bottom',
                    zorder=21,
                    bbox=dict(boxstyle='round,pad=0.12',
                              fc='#1E1E1E', ec='#555555', alpha=0.8))

    def redraw(self):
        try:
            self._redraw_impl()
        except Exception:
            import traceback
            self._fig.clf()
            ax = self._fig.add_subplot(111)
            ax.set_facecolor("#0D1117")
            self._fig.patch.set_facecolor("#1E1E1E")
            ax.text(0.5, 0.5, f'俯视盲区图渲染错误:\n{traceback.format_exc()}',
                    transform=ax.transAxes, ha='center', va='center',
                    color='#FF6666', fontsize=7, family='monospace')
            self._canvas.draw()

    def _redraw_impl(self):
        z_plane = float(self._z.value())
        res     = float(self._res.value())
        x_half, y_front, y_back_extra = self._current_bounds()
        mode_idx = self._mode.currentIndex()   # 0 = 立柱, 1 = 平面

        v = self.scene_cfg.vehicle
        y_min = -(v.total_length + y_back_extra)
        y_max =  y_front
        x_min = -x_half
        x_max =  x_half

        xs = np.arange(x_min, x_max + res, res)
        ys = np.arange(y_min, y_max + res, res)
        X, Y = np.meshgrid(xs, ys)

        # 采样高度列表
        if mode_idx == 0:
            # 目标立柱：0.05 → z_plane 均匀采样 6 层
            top = max(z_plane, 0.1)
            z_levels = np.linspace(0.05, top, 6).tolist()
        else:
            z_levels = [z_plane]

        # 该点被任何传感器看到的最高层数（越多越亮）
        C = np.zeros_like(X, dtype=np.int16)
        for z_layer in z_levels:
            covered_layer = np.zeros_like(X, dtype=bool)
            for s in self.scene_cfg.sensors:
                if not s.enabled:
                    continue
                pitch = getattr(s, 'pitch', 0.0)
                dx = X - s.x
                dy = Y - s.y
                dz = z_layer - s.z
                dist_xy = np.sqrt(dx**2 + dy**2)
                dist    = np.sqrt(dist_xy**2 + dz**2)

                az_deg = np.degrees(np.arctan2(dx, dy))
                with np.errstate(divide='ignore', invalid='ignore'):
                    el_deg = np.degrees(np.arctan2(dz, np.maximum(dist_xy, 1e-6)))

                az_diff = (az_deg - s.mount_angle + 180.0) % 360.0 - 180.0
                el_diff = el_deg - pitch

                mask = (
                    (np.abs(az_diff) <= s.hfov / 2.0) &
                    (np.abs(el_diff) <= s.vfov / 2.0) &
                    (dist <= s.range) & (dist > 0.05)
                )
                covered_layer |= mask
            C[covered_layer] += 1

        # 车体占据区不计入盲区统计
        veh_mask = (
            (X >= -v.width / 2) & (X <= v.width / 2) &
            (Y >= -v.length) & (Y <= 0.0)
        )
        if v.trailer_length > 0:
            tw = v.effective_trailer_width
            veh_mask |= (
                (X >= -tw / 2) & (X <= tw / 2) &
                (Y >= -v.length - v.trailer_length) & (Y <= -v.length)
            )
        analyze_mask = ~veh_mask

        total_cells   = int(np.sum(analyze_mask))
        blind_cells   = int(np.sum((C < 1) & analyze_mask))
        covered_cells = total_cells - blind_cells
        blind_pct     = 100.0 * blind_cells   / max(total_cells, 1)
        covered_pct   = 100.0 * covered_cells / max(total_cells, 1)

        # 近前10m区专项统计
        front_w = max(v.width, v.effective_trailer_width if v.trailer_length > 0 else v.width)
        front_mask = (
            (X >= -front_w / 2 - 1.0) & (X <= front_w / 2 + 1.0) &
            (Y >= 0.0) & (Y <= 10.0)
        )
        front_total = int(np.sum(front_mask))
        front_blind = int(np.sum((C < 1) & front_mask))
        front_blind_pct = 100.0 * front_blind / max(front_total, 1)

        mode_lbl = f"立柱 0∼{z_plane:.2f}m" if mode_idx == 0 else f"平面 z={z_plane:.2f}m"
        self._stats_lbl.setText(
            f"  覆盖 {covered_pct:.1f}%   |   盲区 {blind_pct:.1f}%   "
            f"|   近前10m盲区 {front_blind_pct:.1f}%   "
            f"|   {mode_lbl}  "
        )

        # 绘制
        self._fig.clf()
        ax = self._fig.add_subplot(111)
        ax.set_facecolor("#0D1117")
        self._fig.patch.set_facecolor("#1E1E1E")

        vmax = max(float(C.max()), 1.0)
        cmap_cov = mcolors.LinearSegmentedColormap.from_list(
            "cov_top",
            [(0.0, "#0D2010"), (0.3, "#1a5c2a"),
             (0.7, "#27AE60"), (1.0, "#76ECA0")],
            N=256
        )
        cov_disp = np.where(analyze_mask & (C >= 1), C, np.nan)
        ax.pcolormesh(xs, ys, cov_disp,
                      cmap=cmap_cov, vmin=0.5, vmax=vmax,
                      alpha=0.65, shading='auto', zorder=1)

        blind_disp = np.where(analyze_mask & (C < 1), 1.0, np.nan)
        cmap_blind = mcolors.LinearSegmentedColormap.from_list(
            "blind_top", [(0, "#CC2222"), (1, "#CC2222")], N=2
        )
        if self._show_blind_fill.isChecked():
            ax.pcolormesh(xs, ys, blind_disp,
                          cmap=cmap_blind, vmin=0.5, vmax=1.5,
                          alpha=0.55, shading='auto', zorder=2)

        # 盲区二值掩膜（轮廓线 & 尺寸标注共用）
        need_blind_bin = (self._show_blind_outline.isChecked() or
                          self._show_blind_dims.isChecked())
        blind_bin = None
        if need_blind_bin:
            blind_bin = (analyze_mask & (C < 1)).astype(np.float32)

        # 盲区轮廓线
        if self._show_blind_outline.isChecked():
            if blind_bin is not None and blind_bin.any() and (~blind_bin.astype(bool)).any():
                # 外阈：黑色描边提高可读性
                ax.contour(xs, ys, blind_bin, levels=[0.5],
                           colors=['#000000'], linewidths=3.2,
                           alpha=0.85, zorder=11)
                # 主轮廓：高对比黄色
                ax.contour(xs, ys, blind_bin, levels=[0.5],
                           colors=['#FFEB3B'], linewidths=1.6,
                           zorder=12)

        # ── 盲区尺寸标注 ───────────────────────────────────
        if self._show_blind_dims.isChecked() and blind_bin is not None:
            self._draw_blind_zone_dimensions(ax, blind_bin.astype(bool), xs, ys, v)

        # 近前10m区高亮虚线框
        ax.add_patch(mpatches.Rectangle(
            (-front_w / 2 - 1.0, 0.0), front_w + 2.0, 10.0,
            fill=False, edgecolor='#FFD54F', linestyle='--',
            linewidth=1.2, zorder=8))
        ax.text(0, 10.0 + 0.4, '近前盲区区 (10m)',
                color='#FFD54F', fontsize=7,
                ha='center', va='bottom', zorder=9)

        # 车辆轮廓
        ax.add_patch(mpatches.Rectangle(
            (-v.width / 2, -v.length), v.width, v.length,
            linewidth=1.5, edgecolor='#DDDDDD',
            facecolor='#3C4043', zorder=5))
        ax.text(0, -v.length / 2, '车头',
                color='#DDDDDD', fontsize=7, fontweight='bold',
                ha='center', va='center', zorder=6)
        if v.trailer_length > 0:
            tw = v.effective_trailer_width
            ax.add_patch(mpatches.Rectangle(
                (-tw / 2, -v.length - v.trailer_length),
                tw, v.trailer_length,
                linewidth=1.2, edgecolor='#DDDDDD',
                facecolor='#2D3033', zorder=5))
            ax.text(0, -v.length - v.trailer_length / 2, '挂车',
                    color='#DDDDDD', fontsize=7,
                    ha='center', va='center', zorder=6)

        # FOV 轮廓 — 真实地面交线（非全圆）
        if self._show_fov.isChecked():
            for s in self.scene_cfg.sensors:
                if not s.enabled:
                    continue
                hex_c = s.color.lstrip('#')
                rgb = tuple(int(hex_c[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                h2 = s.hfov / 2.0
                azs = np.radians(np.linspace(s.mount_angle - h2,
                                             s.mount_angle + h2, 60))
                pitch_rad = math.radians(getattr(s, 'pitch', 0.0))
                v2_rad = math.radians(s.vfov / 2.0)
                sz = max(float(s.z), 0.05)
                rng = float(s.range)

                # — 下沿落地水平距离 —
                el_lo = pitch_rad - v2_rad
                if math.sin(el_lo) < -1e-6:
                    t_lo = sz / (-math.sin(el_lo))
                    near_xy = math.sqrt(max(t_lo * t_lo - sz * sz, 0.0))
                    near_xy = min(near_xy, rng)
                else:
                    near_xy = 0.0

                # — 上沿 / range 弧 —
                el_hi = pitch_rad + v2_rad
                if math.sin(el_hi) < -1e-6:
                    t_hi = sz / (-math.sin(el_hi))
                    far_xy = math.sqrt(max(t_hi * t_hi - sz * sz, 0.0))
                    far_xy = min(far_xy, rng)
                else:
                    far_xy = math.sqrt(max(rng * rng - sz * sz, 0.0))

                near_x = s.x + near_xy * np.sin(azs)
                near_y = s.y + near_xy * np.cos(azs)
                far_x  = s.x + far_xy  * np.sin(azs)
                far_y  = s.y + far_xy  * np.cos(azs)

                # 填充地面交线扇形
                poly_x = np.concatenate([near_x, far_x[::-1]])
                poly_y = np.concatenate([near_y, far_y[::-1]])
                ax.fill(poly_x, poly_y, color=rgb,
                        alpha=min(s.opacity * 0.9, 0.14), zorder=3)
                # 下沿弧
                ax.plot(near_x, near_y, color=s.color,
                        linewidth=0.6, alpha=0.5, zorder=4)
                # 上沿/range 弧
                ax.plot(far_x, far_y, color=s.color,
                        linewidth=0.8, alpha=0.6, zorder=4)
                # 两侧边线
                ax.plot([near_x[0], far_x[0]], [near_y[0], far_y[0]],
                        color=s.color, linewidth=0.5, alpha=0.4, zorder=4)
                ax.plot([near_x[-1], far_x[-1]], [near_y[-1], far_y[-1]],
                        color=s.color, linewidth=0.5, alpha=0.4, zorder=4)
                # 传感器位置
                ax.scatter([s.x], [s.y], color=s.color, s=22, zorder=7,
                           edgecolors='white', linewidths=0.6)

                # 最近地面落点标注
                info = compute_ground_intersections(s)
                nd = info['nearest']
                gy = info['ground_y']
                if nd is not None and gy is not None:
                    nx = s.x + nd * math.sin(math.radians(s.mount_angle))
                    # 菱形标记
                    ax.scatter([nx], [gy], marker='D', s=36,
                               color=s.color, edgecolors='white',
                               linewidths=0.7, zorder=15, alpha=0.9)
                    # 距离标签
                    ax.text(nx, gy + 0.45, f"{nd:.1f} m",
                            color=s.color, fontsize=6, fontweight='bold',
                            ha='center', va='bottom', zorder=16,
                            bbox=dict(boxstyle='round,pad=0.15',
                                      fc='#0D1117', ec=s.color, alpha=0.85))

        # 原点标记 (车头前保险杠)
        ax.axhline(0.0, color='#888888', linewidth=0.6,
                   linestyle=':', alpha=0.5, zorder=2)
        ax.axvline(0.0, color='#888888', linewidth=0.6,
                   linestyle=':', alpha=0.5, zorder=2)
        ax.scatter([0], [0], color='#FFEB3B', s=32, marker='+',
                   linewidths=1.2, zorder=10)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect('equal')
        ax.set_xlabel('X / 侧向 (m)', color='#BBBBBB', fontsize=8)
        ax.set_ylabel('Y / 前后 (m)', color='#BBBBBB', fontsize=8)
        if mode_idx == 0:
            title = f'俯视盲区分析  (目标立柱 0∼{z_plane:.2f} m，{len(z_levels)} 层采样)'
        else:
            title = f'俯视盲区分析  (z = {z_plane:.2f} m 单平面)'
        ax.set_title(title, color='#DDDDDD', fontsize=10, pad=6)
        ax.tick_params(colors='#888888', labelsize=7)
        for sp in ax.spines.values():
            sp.set_color('#444444')
        ax.grid(True, color='#222222', linewidth=0.4, alpha=0.5)

        self._fig.tight_layout(pad=0.8)
        self._fig.subplots_adjust(left=0.07, right=0.99, top=0.95, bottom=0.07)

        # 保存覆盖数据，供点击查询用
        self._last_cover = (C, X, Y, xs, ys, analyze_mask, z_levels, mode_idx)

        self._canvas.draw()


#  HIGH-QUALITY MATPLOTLIB DIAGRAM EXPORT
# ══════════════════════════════════════════════════════════════
def export_diagram_hq(scene_cfg: 'SceneConfig', path: str,
                      width_px: int = 4000,
                      bg: str = 'white',
                      show_legend: bool = True,
                      title: str = '',
                      export_lanes: bool = True,
                      export_ego: bool = True,
                      export_target: bool = True) -> None:
    """Render a publication-quality 2-D FOV diagram using matplotlib.

    Layout  : forward direction → right (landscape orientation)
    Axes    : display-X = world-Y (forward/back), display-Y = world-X (lateral)
    Legend  : colour-coded sensor cards on the left, readable at export resolution
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Wedge, FancyBboxPatch
    from matplotlib.gridspec import GridSpec
    import matplotlib.colors as mcolors

    sensors   = scene_cfg.sensors
    enabled   = [s for s in sensors if s.enabled]
    draw_list = enabled or sensors

    # ── World-space view bounds ───────────────────────────────
    # world-X = lateral, world-Y = forward
    # 车头前保险杠位于世界 (0,0)，车身向 -Y 后延伸
    if draw_list:
        veh_total_l = scene_cfg.vehicle.total_length
        veh_max_w   = max(scene_cfg.vehicle.width,
                          scene_cfg.vehicle.effective_trailer_width if scene_cfg.vehicle.trailer_length > 0 else 0.0)
        # display X = world Y (forward) ∈ [-total_length, 0]
        x_min = -veh_total_l
        x_max = 0.0
        # display Y = world X (lateral)
        y_min = -veh_max_w / 2
        y_max =  veh_max_w / 2

        for s in draw_list:
            cx, cy = s.y, s.x  # display coordinates
            vis_h = (s.disp_hfov if getattr(s, 'disp_hfov', 0.0) > 0 else s.hfov)
            a1 = math.radians(s.mount_angle - vis_h / 2.0)
            a2 = math.radians(s.mount_angle + vis_h / 2.0)
            a_samples = np.linspace(a1, a2, max(18, int(vis_h / 2) + 2))
            rr = s.range * 1.02  # include soft glow radius

            xs = cx + rr * np.cos(a_samples)
            ys = cy + rr * np.sin(a_samples)

            x_min = min(x_min, cx, float(np.min(xs)))
            x_max = max(x_max, cx, float(np.max(xs)))
            y_min = min(y_min, cy, float(np.min(ys)))
            y_max = max(y_max, cy, float(np.max(ys)))

        lat_max = max(abs(y_min), abs(y_max))
        fwd_max = max(0.0, x_max)
        bk_max = max(0.0, -x_min)
    else:
        lat_max = 150
        fwd_max = 250
        bk_max = 0

    def snap(v, step=50):
        return max(step, math.ceil(v / step) * step)
    lat_max = snap(lat_max)
    fwd_max = snap(fwd_max)
    bk_max  = snap(bk_max, 25) if bk_max > 0 else 0

    # Display extents: X-axis = forward, Y-axis = lateral
    disp_x_span = fwd_max + bk_max   # horizontal span (forward direction)
    disp_y_span = lat_max * 2        # vertical span (lateral direction)
    grid_step   = 50 if max(disp_x_span, disp_y_span) > 250 else 25

    # ── Figure sizing ─────────────────────────────────────────
    dpi = 150
    # Allocate: 20% for legend, 80% for diagram (min 3 in legend, min 8 in diagram)
    total_budget_in = width_px / dpi
    legend_in  = max(3.0, total_budget_in * 0.20) if (show_legend and sensors) else 0.0
    diagram_in = max(8.0, total_budget_in - legend_in)
    total_w_in = diagram_in + legend_in
    # Diagram height follows the display aspect ratio
    diagram_h_in = diagram_in * (disp_y_span / disp_x_span)
    total_h_in   = diagram_h_in

    is_dark    = bg not in ('white', '#FFFFFF', '#ffffff')
    fg_color   = '#BBBBBB' if is_dark else '#444444'
    grid_color = '#3A4A5A' if is_dark else '#BDD7EE'
    spine_color= '#555555' if is_dark else '#CCCCCC'
    veh_face   = '#2C2C2C' if is_dark else '#F0F0F0'
    veh_edge   = '#999999' if is_dark else '#666666'

    title = (title or '').strip()
    title_h_in = 0.55 if title else 0.0
    fig = plt.figure(figsize=(total_w_in, total_h_in + title_h_in), facecolor=bg, dpi=dpi)
    top = 0.94 if title else 0.975

    if title:
        fig.text(
            0.5, 0.985, title,
            ha='center', va='top',
            fontsize=max(16, min(30, total_budget_in * 1.15)),
            fontweight='bold', color='#000000'
        )

    if show_legend and sensors:
        gs = GridSpec(
            1, 2, figure=fig,
            width_ratios=[legend_in, diagram_in],
            left=0.005, right=0.995, top=top, bottom=0.065,
            wspace=0.015,
        )
        ax_leg = fig.add_subplot(gs[0])
        ax     = fig.add_subplot(gs[1])
    else:
        ax     = fig.add_axes([0.055, 0.065, 0.930, 0.900])
        ax_leg = None

    # ── Diagram: forward = +X (right), lateral = +Y (up) ─────
    ax.set_facecolor(bg)
    ax.set_xlim(-bk_max, fwd_max)     # forward axis (horizontal)
    ax.set_ylim(-lat_max, lat_max)    # lateral axis (vertical)
    ax.set_aspect('equal', adjustable='box')

    # Grid removed as requested.

    # ── Sensor wedges ─────────────────────────────────────────
    # Coordinate rotation: display_x = world_y (fwd), display_y = world_x (lateral)
    # → sensor centre in display = (s.y, s.x)
    # Angle: mount_angle=0 → forward → right in display → mpl 0°
    #         mount_angle=90 → world+X → up in display → mpl 90°
    # → mpl_centre = mount_angle  (CW-from-north maps to CCW-from-east in rotated frame)
    for s in sorted(draw_list, key=lambda s: -s.range):
        cx, cy  = s.y, s.x            # rotated centre
        mpl_mid = s.mount_angle       # see derivation above
        vis_h   = (s.disp_hfov if getattr(s, 'disp_hfov', 0.0) > 0 else s.hfov)
        t1 = mpl_mid - vis_h / 2.0
        t2 = mpl_mid + vis_h / 2.0

        # Soft outer glow
        ax.add_patch(Wedge((cx, cy), s.range * 1.02, t1, t2,
                           facecolor=s.color,
                           alpha=min(0.12, s.opacity * 0.35),
                           edgecolor='none', zorder=2))
        # Main filled wedge
        ax.add_patch(Wedge((cx, cy), s.range, t1, t2,
                           facecolor=s.color, alpha=s.opacity,
                           edgecolor=s.color, linewidth=0.8, zorder=3))
        # If display FOV is narrower, show physical FOV as dashed boundary
        if 0 < getattr(s, 'disp_hfov', 0.0) < s.hfov:
            ax.add_patch(Wedge(
                (cx, cy), s.range,
                mpl_mid - s.hfov / 2.0,
                mpl_mid + s.hfov / 2.0,
                facecolor='none', edgecolor=s.color,
                linewidth=0.7, linestyle='--', alpha=0.35,
                zorder=2
            ))
        # Centre direction line
        mr = math.radians(mpl_mid)
        ir = min(s.range * 0.07, 2.5)
        ax.plot(
            [cx + ir * math.cos(mr), cx + s.range * 0.90 * math.cos(mr)],
            [cy + ir * math.sin(mr), cy + s.range * 0.90 * math.sin(mr)],
            color=s.color, linewidth=0.7, alpha=0.5, zorder=4
        )
        # Mount dot
        ax.plot(cx, cy, 'o', color=s.color, markersize=3.5,
                markeredgecolor='white', markeredgewidth=0.6, zorder=5)

    # ── Lane Lines and Road Surface ──
    if export_lanes:
        lp = scene_cfg.lane_params
        if lp.left_lines > 0 or lp.right_lines > 0:
            y_start = -lp.length / 2.0
            y_end = lp.length / 2.0
            s = np.linspace(y_start, y_end, 100)

            def get_points(x_base):
                R = lp.curvature_r
                if R == 0.0:
                    return np.full_like(s, x_base), s
                phi = s / R
                xs = R - (R - x_base) * np.cos(phi)
                ys_curve = (R - x_base) * np.sin(phi)
                return xs, ys_curve

            if lp.left_lines > 0:
                x_left_most = lp.lateral_offset - (lp.left_lines - 0.5) * lp.lane_width
            else:
                x_left_most = lp.lateral_offset - 0.5 * lp.lane_width

            if lp.right_lines > 0:
                x_right_most = lp.lateral_offset + (lp.right_lines - 0.5) * lp.lane_width
            else:
                x_right_most = lp.lateral_offset + 0.5 * lp.lane_width

            xs_min, ys_min = get_points(x_left_most)
            xs_max, ys_max = get_points(x_right_most)

            # Draw road background surface
            poly_x = np.concatenate([ys_min, ys_max[::-1]])
            poly_y = np.concatenate([xs_min, xs_max[::-1]])
            ax.fill(poly_x, poly_y, color="#21262D", zorder=1)

            # Draw left lines
            for idx in range(1, lp.left_lines + 1):
                x_base = lp.lateral_offset - (idx - 0.5) * lp.lane_width
                xs, ys_lane = get_points(x_base)
                is_outer = (idx == lp.left_lines)
                color = lp.color_outer if is_outer else lp.color_inner
                style = 'solid' if is_outer else 'dashed'
                ax.plot(ys_lane, xs, color=color, linestyle=style, linewidth=1.5, zorder=2)

            # Draw right lines
            for idx in range(1, lp.right_lines + 1):
                x_base = lp.lateral_offset + (idx - 0.5) * lp.lane_width
                xs, ys_lane = get_points(x_base)
                is_outer = (idx == lp.right_lines)
                color = lp.color_outer if is_outer else lp.color_inner
                style = 'solid' if is_outer else 'dashed'
                ax.plot(ys_lane, xs, color=color, linestyle=style, linewidth=1.5, zorder=2)

    # ── Target Vehicles ──
    if export_target:
        for tv in scene_cfg.target_vehicles:
            if not tv.enabled:
                continue
            cx, cy = tv.y, tv.x
            w, l = tv.width, tv.length
            beta = math.radians(tv.heading)
            cos_b, sin_b = math.cos(beta), math.sin(beta)

            local_corners = [
                (l/2, -w/2),
                (l/2, w/2),
                (-l/2, w/2),
                (-l/2, -w/2)
            ]

            corners = []
            for lx, ly in local_corners:
                rx = lx * cos_b - ly * sin_b
                ry = lx * sin_b + ly * cos_b
                corners.append((cx + rx, cy + ry))

            poly = mpatches.Polygon(corners, closed=True, facecolor=tv.color, edgecolor='#888888', linewidth=0.8, zorder=6)
            ax.add_patch(poly)

            ws_corners = []
            local_ws = [
                (l/2 - 0.1, -w/2 + 0.15),
                (l/2 - 0.1, w/2 - 0.15),
                (l/4, w/2 - 0.15),
                (l/4, -w/2 + 0.15)
            ]
            for lx, ly in local_ws:
                rx = lx * cos_b - ly * sin_b
                ry = lx * sin_b + ly * cos_b
                ws_corners.append((cx + rx, cy + ry))
            ws_poly = mpatches.Polygon(ws_corners, closed=True, facecolor='#FFFFFF', alpha=0.3, edgecolor='none', zorder=7)
            ax.add_patch(ws_poly)

            ax.text(cx, cy, tv.name, color='#FFFFFF', fontsize=7, fontweight='bold', ha='center', va='center', zorder=8)

    # ── Vehicle (车头前保险杠位于 display (0,0)，车身向 -X 后延伸) ──
    if export_ego:
        v = scene_cfg.vehicle
        # 车头矩形
        ax.add_patch(FancyBboxPatch(
            (-v.length, -v.width / 2), v.length, v.width,
            boxstyle='round,pad=0.15',
            facecolor=veh_face, edgecolor=veh_edge,
            linewidth=1.5, zorder=6
        ))
        # 挂车矩形 (可选)
        if v.trailer_length > 0:
            tw = v.effective_trailer_width
            ax.add_patch(FancyBboxPatch(
                (-v.length - v.trailer_length, -tw / 2), v.trailer_length, tw,
                boxstyle='round,pad=0.10',
                facecolor=veh_face, edgecolor=veh_edge,
                linewidth=1.2, zorder=6
            ))
        # 前进方向指示 (F) —— 位于车头前保险杠右侧
        ax.text(0.6, 0, 'F',
                ha='left', va='center', fontsize=8,
                fontweight='bold', color=veh_edge, zorder=7)

    # ── Axis ticks & labels ───────────────────────────────────
    tick_fs = max(8.0, min(12.0, diagram_in * 0.65))
    ax.set_xticks(list(range(-bk_max, fwd_max + 1, grid_step)))
    ax.set_yticks(list(range(-lat_max, lat_max + 1, grid_step)))
    ax.set_xticklabels(
        [f'{abs(x)}m' for x in range(-bk_max, fwd_max + 1, grid_step)],
        fontsize=tick_fs, color=fg_color, fontweight='bold')
    ax.set_yticklabels(
        [f'{abs(y)}m' for y in range(-lat_max, lat_max + 1, grid_step)],
        fontsize=tick_fs, color=fg_color, fontweight='bold')
    for sp in ax.spines.values():
        sp.set_color(spine_color); sp.set_linewidth(0.7)
    ax.tick_params(length=3.5, width=0.7, color=spine_color, pad=2.5)

    # ── Legend panel ──────────────────────────────────────────
    if ax_leg is not None:
        ax_leg.set_facecolor(bg)
        ax_leg.set_xlim(0, 1)
        ax_leg.set_ylim(0, 1)
        ax_leg.axis('off')

        legend_sensors = [s for s in sensors if s.enabled]
        n = len(legend_sensors)
        if n:
            gap    = 0.012
            card_h = (1.0 - (n + 1) * gap) / n
            card_h_in = total_h_in * card_h
            h_scale   = min(1.0, card_h_in / 0.72)
            name_fs   = max(6.5, min(18.0, card_h_in * 72 * 0.34 * h_scale))
            fov_fs    = max(5.5, min(14.0, card_h_in * 72 * 0.26 * h_scale))

            for i, s in enumerate(legend_sensors):
                y_top = 1.0 - (i * (card_h + gap) + gap)
                y_bot = y_top - card_h

                r, g, b    = mcolors.to_rgb(s.color)
                card_bg    = ((r*0.12+0.84, g*0.12+0.84, b*0.12+0.84) if not is_dark
                              else (r*0.20+0.05, g*0.20+0.05, b*0.20+0.05))
                alpha_card = 1.0 if s.enabled else 0.38

                # Card background
                ax_leg.add_patch(FancyBboxPatch(
                    (0.03, y_bot + 0.004), 0.94, card_h - 0.008,
                    boxstyle='round,pad=0.01',
                    facecolor=card_bg, edgecolor='none',
                    transform=ax_leg.transAxes, zorder=1,
                    alpha=alpha_card,
                ))
                # Left colour accent bar
                ax_leg.add_patch(mpatches.Rectangle(
                    (0.03, y_bot + 0.004), 0.048, card_h - 0.008,
                    facecolor=s.color, edgecolor='none',
                    transform=ax_leg.transAxes, zorder=2,
                    alpha=alpha_card,
                ))

                y_mid = (y_top + y_bot) / 2
                # Sensor name (bold, black)
                ax_leg.text(
                    0.12, y_mid + card_h * 0.15,
                    s.name,
                    transform=ax_leg.transAxes,
                    fontsize=name_fs, fontweight='bold',
                    color='#000000', va='center', ha='left',
                    alpha=alpha_card, clip_on=True,
                )
                # FOV spec (bold, black)
                fov_str = f"FOV: {s.range:.0f}m / {s.hfov:.0f}°"
                if getattr(s, 'disp_hfov', 0.0) > 0:
                    fov_str += f" (显示:{s.disp_hfov:.0f}°)"
                if s.mount_angle != 0:
                    fov_str += f"  横摆:{s.mount_angle:+.0f}°"
                if s.vfov > 0:
                    fov_str += f"  V:{s.vfov:.0f}°"
                if getattr(s, 'pitch', 0.0) != 0:
                    fov_str += f"  俯仰:{s.pitch:+.0f}°"
                if getattr(s, 'roll', 0.0) != 0:
                    fov_str += f"  滚转:{s.roll:+.0f}°"
                ax_leg.text(
                    0.12, y_mid - card_h * 0.15,
                    fov_str,
                    transform=ax_leg.transAxes,
                    fontsize=fov_fs, fontweight='bold',
                    color='#000000',
                    va='center', ha='left',
                    alpha=alpha_card, clip_on=True,
                )

    plt.savefig(path, dpi=dpi, bbox_inches='tight',
                facecolor=bg, edgecolor='none')
    plt.close(fig)


def get_session_file_path():
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "fov_tools_session.json")
        # Try writing to verify access
        test_path = os.path.join(base_dir, ".test_write")
        with open(test_path, 'w') as f:
            f.write("1")
        os.remove(test_path)
        return path
    except Exception:
        return os.path.expanduser("~/fov_tools_session.json")


# ══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1400, 860)

        # Attempt to load autosaved session configuration
        session_path = get_session_file_path()
        self._loaded_session = False
        self._scene_cfg = None
        self._file_path = None

        if os.path.exists(session_path):
            try:
                with open(session_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._scene_cfg = SceneConfig.from_dict(data)
                self._profile_mgr = ProfileManager(self._scene_cfg)
                if 'profiles' in data and isinstance(data['profiles'], list):
                    self._profile_mgr.from_list(data['profiles'])
                self._file_path = data.get('last_file_path')
                self._loaded_session = True
                # Automatically upgrade old short lane length to 1000m to cover zoomed-out sensor views
                if self._scene_cfg.lane_params and self._scene_cfg.lane_params.length < 1000.0:
                    self._scene_cfg.lane_params.length = 1000.0
            except Exception as e:
                print(f"Failed to load autosaved session: {e}")

        if not self._scene_cfg:
            self._scene_cfg = SceneConfig.hw30()
            self._profile_mgr = ProfileManager(self._scene_cfg)

        self._signals    = AppSignals()
        self._modified   = False
        self._coverage_dlg = None

        # ── Central tab widget ────────────────────────────────
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._canvas2d   = Canvas2D(self._scene_cfg, self._signals)
        self._canvas3d   = Canvas3D(self._scene_cfg, self._signals)
        self._canvas_side = CanvasSideView(self._scene_cfg, self._signals)
        self._canvas_blind = CanvasBlindZoneView(self._scene_cfg, self._signals)

        # ── 2D canvas wrapper with rotation + bg toolbar ──────
        _wrap2d = QWidget()
        _wrap2d_lay = QVBoxLayout(_wrap2d)
        _wrap2d_lay.setContentsMargins(0, 0, 0, 0)
        _wrap2d_lay.setSpacing(0)

        _ctrl2d = QWidget()
        _ctrl2d.setStyleSheet("background:#2B2B2B;")
        _ctrl2d_lay = QHBoxLayout(_ctrl2d)
        _ctrl2d_lay.setContentsMargins(8, 3, 8, 3)
        _ctrl2d_lay.setSpacing(4)

        _sep_lbl = QLabel("旋转:")
        _sep_lbl.setStyleSheet("color:#AAAAAA; font-size:13px;")
        _ctrl2d_lay.addWidget(_sep_lbl)

        def _mb(text, tip, fn, checkable=False):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setFixedHeight(28)
            b.setCheckable(checkable)
            b.setStyleSheet(
                "QPushButton{background:#3A3A3A;border:1px solid #555;"
                "border-radius:3px;padding:0 10px;font-size:13px;}"
                "QPushButton:hover{background:#505050;}"
                "QPushButton:pressed,QPushButton:checked{background:#4A90D9;border-color:#4A90D9;}"
            )
            b.clicked.connect(fn)
            return b

        _ctrl2d_lay.addWidget(_mb("↺ 逆时针90°", "视图逆时针旋转90度",
                                  lambda: self._canvas2d.rotate_view(-90)))
        _ctrl2d_lay.addWidget(_mb("↻ 顺时针90°", "视图顺时针旋转90度",
                                  lambda: self._canvas2d.rotate_view(90)))
        _ctrl2d_lay.addWidget(_mb("⟳ 复位", "还原旋转",
                                  self._canvas2d.reset_rotation))
        _ctrl2d_lay.addSpacing(16)

        _zoom_lbl = QLabel("缩放:")
        _zoom_lbl.setStyleSheet("color:#AAAAAA; font-size:13px;")
        _ctrl2d_lay.addWidget(_zoom_lbl)
        _ctrl2d_lay.addWidget(_mb("➕ 放大", "放大视图",
                                  lambda: self._canvas2d.zoom(1.2)))
        _ctrl2d_lay.addWidget(_mb("➖ 缩小", "缩小视图",
                                  lambda: self._canvas2d.zoom(1.2 ** -1)))
        _ctrl2d_lay.addWidget(_mb("🔍 适中", "自适应视野大小",
                                  self._canvas2d.fit_view))
        self._zoom_rect_btn = _mb("🔎 框选放大", "拉框进行局部放大",
                                  self._toggle_zoom_mode, checkable=True)
        _ctrl2d_lay.addWidget(self._zoom_rect_btn)
        _ctrl2d_lay.addSpacing(16)

        _bg_lbl = QLabel("背景:")
        _bg_lbl.setStyleSheet("color:#AAAAAA; font-size:13px;")
        _ctrl2d_lay.addWidget(_bg_lbl)

        self._bg_light_btn = _mb("☀ 白色背景", "切换为白色/浅色背景（适合打印导出）",
                                  self._on_bg_toggle, checkable=True)
        _ctrl2d_lay.addWidget(self._bg_light_btn)
        _ctrl2d_lay.addSpacing(16)

        self._lock_btn = _mb("🔓 视角解锁", "锁定后防止鼠标不小心拖动传感器位置",
                              self._on_lock_toggle, checkable=True)
        _ctrl2d_lay.addWidget(self._lock_btn)

        _ctrl2d_lay.addStretch()
        _wrap2d_lay.addWidget(_ctrl2d)
        _wrap2d_lay.addWidget(self._canvas2d, stretch=1)

        self._tabs.addTab(_wrap2d,               "🗺  2D 俯视图")
        self._tabs.addTab(self._canvas3d,        "🧊  3D 视图")
        self._tabs.addTab(self._canvas_side,     "📐  侧视图 / 盲区")
        self._tabs.addTab(self._canvas_blind,    "🎯  俯视盲区")

        # ── Dock: sensor list ─────────────────────────────────
        self._list_panel = SensorListPanel(self._scene_cfg, self._signals)
        dock_list = QDockWidget("传感器列表", self)
        dock_list.setWidget(self._list_panel)
        dock_list.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_list.setMinimumWidth(220)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_list)

        # ── Dock: profile panel ───────────────────────────────
        self._profile_panel = ProfilePanel(self._profile_mgr, self._signals)
        self._profile_panel.profile_switched.connect(self._on_profile_switched)
        dock_profile = QDockWidget("方案管理", self)
        dock_profile.setWidget(self._profile_panel)
        dock_profile.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_profile.setMinimumWidth(220)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_profile)

        # ── Dock: properties ──────────────────────────────────
        self._prop_panel = SensorPropertiesPanel(self._scene_cfg, self._signals)
        self._vehicle_panel = VehiclePropertiesPanel(self._scene_cfg, self._signals)
        self._lane_panel = LaneConfigPanel(self._scene_cfg, self._signals)
        self._target_vehicle_panel = TargetVehiclePanel(self._scene_cfg, self._signals)
        self._prop_tabs = QTabWidget()
        self._prop_tabs.addTab(self._prop_panel, "传感器")
        self._prop_tabs.addTab(self._vehicle_panel, "车辆")
        self._prop_tabs.addTab(self._lane_panel, "车道线")
        self._prop_tabs.addTab(self._target_vehicle_panel, "目标车")
        dock_prop = QDockWidget("参数配置", self)
        dock_prop.setWidget(self._prop_tabs)
        dock_prop.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_prop.setMinimumWidth(240)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_prop)

        # ── Dock: legend ──────────────────────────────────────
        self._legend_panel = SensorLegendWidget(self._scene_cfg, self._signals)
        dock_legend = QDockWidget("传感器图例", self)
        dock_legend.setWidget(self._legend_panel)
        dock_legend.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock_legend.setMinimumWidth(200)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_legend)
        self.tabifyDockWidget(dock_prop, dock_legend)
        dock_prop.raise_()   # keep properties tab in front by default

        # Dock: ground intersection table (bottom)
        self._ground_table = SensorGroundTablePanel(self._scene_cfg, self._signals)
        dock_ground = QDockWidget("传感器地面落点表", self)
        dock_ground.setWidget(self._ground_table)
        dock_ground.setAllowedAreas(
            Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        dock_ground.setMinimumHeight(140)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_ground)

        # ── Toolbar ───────────────────────────────────────────
        tb = QToolBar("主工具栏")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        def act(text, shortcut=None, tip=None, cb=None):
            a = QAction(text, self)
            if shortcut: a.setShortcut(QKeySequence(shortcut))
            if tip:      a.setToolTip(tip)
            if cb:       a.triggered.connect(cb)
            tb.addAction(a)
            return a

        act("📂 打开",     "Ctrl+O", "打开配置文件", self._file_open)
        act("💾 保存",     "Ctrl+S", "保存配置文件", self._file_save)
        act("💾 另存为",   "Ctrl+Shift+S", "另存为", self._file_save_as)
        tb.addSeparator()
        act("🔍 适应视图", "Ctrl+0", "适应窗口", self._fit_view)
        act("📏 网格",     "Ctrl+G", "显示/隐藏网格", self._toggle_grid)
        act("🏷 标签",     "Ctrl+L", "显示/隐藏标签", self._toggle_labels)
        tb.addSeparator()
        act("📊 覆盖分析", "Ctrl+M", "显示覆盖热力图", self._show_coverage)
        tb.addSeparator()
        act("🖼 导入背景图", "Ctrl+I", "导入参考图像为背景", self._import_bg)
        act("🗑 清除背景图", "",      "移除背景参考图",     self._clear_bg)
        act("🤖 识别导入",  "Ctrl+R", "从图片OCR识别传感器并导入", self._import_sensors_from_image)
        tb.addSeparator()
        act("📷 导出PNG",  "Ctrl+E", "导出2D图像为PNG", self._export_png)

        # ── Menu bar ──────────────────────────────────────────
        mb = self.menuBar()
        fm = mb.addMenu("文件(&F)")
        fm.addAction("新建",   self._file_new,      QKeySequence.New)
        fm.addAction("打开…",  self._file_open,     QKeySequence.Open)
        fm.addAction("保存",   self._file_save,     QKeySequence.Save)
        fm.addAction("另存为…",self._file_save_as,  QKeySequence("Ctrl+Shift+S"))
        fm.addSeparator()
        fm.addAction("导出 PNG…",  self._export_png)
        fm.addSeparator()
        fm.addAction("从图片识别传感器…", self._import_sensors_from_image, QKeySequence("Ctrl+R"))
        fm.addSeparator()
        fm.addAction("导入背景参考图…", self._import_bg, QKeySequence("Ctrl+I"))
        fm.addAction("清除背景图",      self._clear_bg)
        fm.addSeparator()
        fm.addAction("退出",   self.close, QKeySequence.Quit)

        vm = mb.addMenu("视图(&V)")
        vm.addAction("适应窗口", self._fit_view, QKeySequence("Ctrl+0"))
        vm.addAction("显示/隐藏网格", self._toggle_grid, QKeySequence("Ctrl+G"))
        vm.addAction("显示/隐藏标签", self._toggle_labels, QKeySequence("Ctrl+L"))
        vm.addAction("显示/隐藏图例", lambda: dock_legend.setVisible(not dock_legend.isVisible()), QKeySequence("Ctrl+J"))

        am = mb.addMenu("分析(&A)")
        am.addAction("覆盖率热力图…", self._show_coverage, QKeySequence("Ctrl+M"))

        hm = mb.addMenu("帮助(&H)")
        hm.addAction("关于", self._about)

        # ── Status bar ────────────────────────────────────────
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        if self._loaded_session:
            self._status.showMessage(f"已恢复上次的会话状态 — {len(self._scene_cfg.sensors)} 个传感器")
            self._update_title()
        else:
            self._status.showMessage(f"已载入 HW 3.0 预设 — {len(self._scene_cfg.sensors)} 个传感器")

        # Connect signals for status
        self._signals.sensor_added.connect(self._on_modified)
        self._signals.sensor_removed.connect(self._on_modified)
        self._signals.sensor_changed.connect(self._on_modified)
        self._signals.sensor_moved.connect(self._on_modified)
        self._signals.vehicle_changed.connect(self._on_modified)
        self._signals.lane_changed.connect(self._on_modified)
        self._signals.target_vehicle_added.connect(self._on_modified)
        self._signals.target_vehicle_removed.connect(self._on_modified)
        self._signals.target_vehicle_changed.connect(self._on_modified)
        self._signals.sensor_selected.connect(self._on_sensor_selected)
        self._signals.sensor_deselected.connect(lambda: self._status.showMessage(""))
        self._signals.zoom_mode_changed.connect(self._zoom_rect_btn.setChecked)

        # Also connect canvas2d sensor add from context-menu duplication
        self._signals.sensor_added.connect(self._on_sensor_added_rebuild)

    # ── slot: sensor added externally (e.g. mirror / duplicate) ──
    def _on_sensor_added_rebuild(self, sensor_id: str):
        sensor = next((s for s in self._scene_cfg.sensors if s.id == sensor_id), None)
        if sensor:
            self._canvas2d.add_sensor(sensor)
            self._update_title()

    # ── slot: profile switched ────────────────────────────────
    def _on_profile_switched(self):
        self._signals.scene_rebuilt.emit()
        QTimer.singleShot(100, self._canvas2d.fit_view)
        n = len(self._scene_cfg.sensors)
        ai = self._profile_mgr.active_index()
        names = self._profile_mgr.names()
        name = names[ai] if 0 <= ai < len(names) else "—"
        self._status.showMessage(f"已切换到方案「{name}」— {n} 个传感器", 4000)
        self._modified = True
        self._update_title()
        self._auto_save()

    # ── slot: 2D background toggle ────────────────────────────
    def _on_bg_toggle(self):
        light = self._bg_light_btn.isChecked()
        self._canvas2d.set_dark_bg(not light)
        self._bg_light_btn.setText("🌙 暗色背景" if light else "☀ 白色背景")

    def _on_lock_toggle(self):
        locked = self._lock_btn.isChecked()
        self._canvas2d.set_fov_locked(locked)
        if locked:
            self._lock_btn.setText("🔒 视角锁定")
            self._lock_btn.setToolTip("当前已锁定传感器位置，再次点击解锁")
        else:
            self._lock_btn.setText("🔓 视角解锁")
            self._lock_btn.setToolTip("锁定后防止鼠标不小心拖动传感器位置")

    def _auto_save(self):
        try:
            path = get_session_file_path()
            data = self._scene_cfg.to_dict()
            profiles_list = self._profile_mgr.to_list()
            if profiles_list:
                data['profiles'] = profiles_list
            if self._file_path:
                data['last_file_path'] = self._file_path
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Auto-save failed: {e}")

    def _on_modified(self, *_):
        self._modified = True
        self._update_title()
        n = len(self._scene_cfg.sensors)
        self._status.showMessage(f"{n} 个传感器")
        self._auto_save()

    def _on_sensor_selected(self, sensor_id: str):
        sensor = next((s for s in self._scene_cfg.sensors if s.id == sensor_id), None)
        if sensor:
            self._canvas2d.select_sensor(sensor_id)
            self._status.showMessage(
                f"已选: {sensor.name}  |  位置 ({sensor.x:.2f}, {sensor.y:.2f}) m  "
                f"|  HFOV {sensor.hfov:.0f}°  |  距离 {sensor.range:.0f} m"
            )

    def _update_title(self):
        n    = len(self._scene_cfg.sensors)
        name = os.path.basename(self._file_path) if self._file_path else "未保存"
        mod  = " *" if self._modified else ""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}  —  {name}{mod}  [{n} 传感器]")

    # ── file operations ───────────────────────────────────────
    def _file_new(self):
        if self._modified:
            ans = QMessageBox.question(self, "新建", "当前修改未保存，是否继续？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ans != QMessageBox.Yes:
                return
        self._scene_cfg.sensors.clear()
        self._file_path = None
        self._modified  = False
        self._signals.scene_rebuilt.emit()
        self._update_title()
        self._auto_save()

    def _file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开配置", "",
                                               "JSON 文件 (*.json);;所有文件 (*)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            new_cfg = SceneConfig.from_dict(data)
            self._scene_cfg.vehicle         = new_cfg.vehicle
            self._scene_cfg.sensors         = new_cfg.sensors
            self._scene_cfg.lane_params     = new_cfg.lane_params
            self._scene_cfg.target_vehicles = new_cfg.target_vehicles
            self._scene_cfg.show_grid       = new_cfg.show_grid
            self._scene_cfg.show_labels     = new_cfg.show_labels
            self._scene_cfg.show_overlap    = new_cfg.show_overlap
            # Restore profiles if present
            if 'profiles' in data and isinstance(data['profiles'], list):
                self._profile_mgr.from_list(data['profiles'])
            else:
                self._profile_mgr._profiles.clear()
                self._profile_mgr._active = -1
            self._profile_panel.refresh()
            self._file_path = path
            self._modified  = False
            self._signals.scene_rebuilt.emit()
            self._update_title()
            self._auto_save()
            QTimer.singleShot(100, self._canvas2d.fit_view)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开失败:\n{e}")

    def _file_save(self):
        if self._file_path:
            self._do_save(self._file_path)
        else:
            self._file_save_as()

    def _file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "另存为", "",
                                               "JSON 文件 (*.json)")
        if path:
            if not path.endswith('.json'):
                path += '.json'
            self._do_save(path)

    def _do_save(self, path: str):
        try:
            data = self._scene_cfg.to_dict()
            # Save profiles
            profiles_list = self._profile_mgr.to_list()
            if profiles_list:
                data['profiles'] = profiles_list
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._file_path = path
            self._modified  = False
            self._update_title()
            self._status.showMessage(f"已保存: {path}", 3000)
            self._auto_save()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{e}")

    # ── view controls ─────────────────────────────────────────
    def _fit_view(self):
        self._canvas2d.fit_view()

    def _toggle_zoom_mode(self):
        is_active = self._zoom_rect_btn.isChecked()
        self._canvas2d._zoom_mode = is_active
        if is_active:
            self._canvas2d.setCursor(Qt.CrossCursor)
        else:
            self._canvas2d.setCursor(Qt.ArrowCursor)

    def _toggle_grid(self):
        self._scene_cfg.show_grid = not self._scene_cfg.show_grid
        self._canvas2d.rebuild()

    def _toggle_labels(self):
        self._scene_cfg.show_labels = not self._scene_cfg.show_labels
        # Toggle label visibility on all sensor items
        for item in self._canvas2d._sensor_items.values():
            item._label.setVisible(self._scene_cfg.show_labels)

    # ── export ────────────────────────────────────────────────

    # ── import sensors from image ─────────────────────────────
    def _import_sensors_from_image(self):
        dlg = ImportSensorsFromImageDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        sensor_dicts = dlg.sensors()
        if not sensor_dicts:
            return
        count = 0
        for sd in sensor_dicts:
            s = SensorConfig(
                name        = sd['name'],
                sensor_type = sd['sensor_type'],
                range       = sd['range'],
                hfov        = sd['hfov'],
                vfov        = sd['vfov'],
                color       = sd['color'],
                opacity     = sd['opacity'],
            )
            self._scene_cfg.sensors.append(s)
            self._canvas2d.add_sensor(s)
            self._signals.sensor_added.emit(s.id)
            count += 1
        self._modified = True
        self._update_title()
        self._status.showMessage(f"已从图片导入 {count} 个传感器", 5000)
    def _export_png(self):
        dlg = ExportDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        width, angle, bg, show_legend, hq_mode, title, export_lanes, export_ego, export_target = dlg.params()
        path, _ = QFileDialog.getSaveFileName(self, "导出 PNG", "fov_diagram.png",
                                               "PNG 图像 (*.png)")
        if not path:
            return
        try:
            if hq_mode:
                # Matplotlib high-quality export (bg is a colour string)
                export_diagram_hq(
                    self._scene_cfg, path,
                    width_px=width,
                    bg=bg or 'white',
                    show_legend=show_legend,
                    title=title,
                    export_lanes=export_lanes,
                    export_ego=export_ego,
                    export_target=export_target
                )
            else:
                # Standard QGraphicsScene export (bg is a QColor or None)
                self._canvas2d.export_image(
                    path, width=width, angle=angle,
                    bg_color=bg,
                    show_legend=show_legend,
                    title=title,
                    export_lanes=export_lanes,
                    export_ego=export_ego,
                    export_target=export_target
                )
            self._status.showMessage(f"已导出: {path}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

    # ── background image ──────────────────────────────────────
    def _import_bg(self):
        dlg = ImportBgDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        p = dlg.params()
        if not p['path']:
            QMessageBox.warning(self, "提示", "请先选择图像文件。")
            return
        try:
            self._canvas2d.load_background(
                path     = p['path'],
                real_w_m = p['real_w'],
                rot_deg  = p['rot_deg'],
                anchor_x = p['anchor_x'],
                anchor_y = p['anchor_y'],
                opacity  = p['opacity'],
            )
            self._status.showMessage("背景参考图已加载。可在图像上添加传感器以生成可编辑版本。", 5000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败:\n{e}")

    def _clear_bg(self):
        self._canvas2d.clear_background()
        self._status.showMessage("背景图已清除", 2000)

    # ── analysis ──────────────────────────────────────────────
    def _show_coverage(self):
        if self._coverage_dlg is None:
            self._coverage_dlg = CoverageDialog(self._scene_cfg, self)
        self._coverage_dlg.show()
        self._coverage_dlg.raise_()
        self._coverage_dlg._calculate()

    # ── about ─────────────────────────────────────────────────
    def _about(self):
        QMessageBox.about(self, f"关于 {APP_NAME}",
            f"<b>{APP_NAME} v{APP_VERSION}</b><br><br>"
            "传感器视场角可视化与管理工具<br>"
            "支持摄像头、毫米波雷达、激光雷达<br><br>"
            "<b>操作说明:</b><br>"
            "• 鼠标滚轮: 缩放视图<br>"
            "• 中键拖拽: 平移视图<br>"
            "• 左键拖拽传感器: 移动位置<br>"
            "• 方向键: 微调位置 (Shift=1m步进)<br>"
            "• Delete 键: 删除选中传感器<br>"
            "• Ctrl+0: 适应视图<br>"
        )

    def closeEvent(self, event):
        if self._modified:
            ans = QMessageBox.question(self, "退出",
                                       "当前修改未保存，是否退出？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ans != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
def main():
    import traceback
    def crash_handler(etype, value, tb):
        try:
            with open("app_crash.txt", "w", encoding="utf-8") as f:
                traceback.print_exception(etype, value, tb, file=f)
        except Exception:
            pass
        sys.__excepthook__(etype, value, tb)
    sys.excepthook = crash_handler

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Dark palette
    palette = app.palette()
    from PyQt5.QtGui import QPalette
    palette.setColor(QPalette.Window,          QColor("#2B2B2B"))
    palette.setColor(QPalette.WindowText,      QColor("#DDDDDD"))
    palette.setColor(QPalette.Base,            QColor("#1E1E1E"))
    palette.setColor(QPalette.AlternateBase,   QColor("#2B2B2B"))
    palette.setColor(QPalette.ToolTipBase,     QColor("#1E1E1E"))
    palette.setColor(QPalette.ToolTipText,     QColor("#DDDDDD"))
    palette.setColor(QPalette.Text,            QColor("#DDDDDD"))
    palette.setColor(QPalette.Button,          QColor("#353535"))
    palette.setColor(QPalette.ButtonText,      QColor("#DDDDDD"))
    palette.setColor(QPalette.BrightText,      Qt.red)
    palette.setColor(QPalette.Link,            QColor("#4A90D9"))
    palette.setColor(QPalette.Highlight,       QColor("#4A90D9"))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    app.setStyleSheet("""
        QDockWidget::title {
            background: #353535;
            padding: 4px;
            font-weight: bold;
        }
        QToolBar {
            background: #2B2B2B;
            border-bottom: 1px solid #444;
            spacing: 4px;
            padding: 2px;
        }
        QToolButton {
            padding: 4px 8px;
            border-radius: 3px;
        }
        QToolButton:hover { background: #404040; }
        QPushButton {
            background: #404040;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 4px 8px;
            color: #DDDDDD;
        }
        QPushButton:hover  { background: #505050; }
        QPushButton:pressed{ background: #303030; }
        QListWidget { background: #1E1E1E; border: 1px solid #444; }
        QListWidget::item:selected { background: #2C5280; }
        QComboBox    { background: #353535; border: 1px solid #555; padding: 3px; border-radius:3px;}
        QDoubleSpinBox,QLineEdit { background: #1E1E1E; border: 1px solid #555; padding:3px; border-radius:3px;}
        QTabWidget::pane { border: 1px solid #444; }
        QTabBar::tab { background:#2B2B2B; padding:6px 14px; border:1px solid #444; }
        QTabBar::tab:selected { background:#353535; border-bottom:2px solid #4A90D9; }
        QMenuBar { background:#2B2B2B; color:#DDDDDD; }
        QMenuBar::item:selected { background:#4A90D9; }
        QMenu { background:#2B2B2B; color:#DDDDDD; border:1px solid #555; }
        QMenu::item:selected { background:#4A90D9; }
        QStatusBar { background:#2B2B2B; color:#AAAAAA; }
    """)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
