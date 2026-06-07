# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FOVTools
生成最新版本的 .exe 文件
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# 强制收集 numpy 和 matplotlib 的所有文件（包括编译扩展）
numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')
mpl_datas, mpl_binaries, mpl_hiddenimports = collect_all('matplotlib')
mpl_toolkits_datas, mpl_toolkits_binaries, mpl_toolkits_hiddenimports = collect_all('mpl_toolkits')

a = Analysis(
    ['c:\\Fuyue_WorkSpace\\FOVTools\\fov_tools.py'],
    pathex=['c:\\Fuyue_WorkSpace\\FOVTools'],
    binaries=numpy_binaries + mpl_binaries + mpl_toolkits_binaries,
    datas=numpy_datas + mpl_datas + mpl_toolkits_datas,
    hiddenimports=numpy_hiddenimports + mpl_hiddenimports + mpl_toolkits_hiddenimports + [
        # PyQt5 核心模块
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        # 其他库
        'fitz',  # pymupdf
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tcl', 'tk', '_tkinter', 'tkinter', 'test', 'tests'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FOV_Tools',  # 输出文件名: FOV_Tools.exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口（GUI模式）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
