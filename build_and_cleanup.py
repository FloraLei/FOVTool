#!/usr/bin/env python3
"""
FOVTools Build and Cleanup Script
生成最新的 .exe 文件并清理临时文件
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 项目路径
PROJECT_DIR = Path(r'c:\Fuyue_WorkSpace\FOVTools')
SPEC_FILE = PROJECT_DIR / 'FOVTools.spec'
DIST_DIR = PROJECT_DIR / 'dist'
BUILD_DIR = PROJECT_DIR / 'build'

# 需要删除的临时文件模式
CLEANUP_PATTERNS = [
    # 日志文件
    '*.txt',  # app_err.txt, crash_log.txt, err.txt 等
    'custom_crash.txt',
    
    # 测试文件
    'test_*.py',
    'test_*.png',
    'demo_*.py',
    'demo_*.png',
    
    # 示例输出
    'sample_*.png',
    'reference_*.png',
    'zoom_*.py',
    
    # 调试文件
    'debug_*.png',
    '*_debug.spec',
    '*_v9*.spec',
    
    # 会话文件
    '*_session.json',
    
    # 缓存
    '__pycache__',
    '*.pyc',
]

# 始终保留的重要文件
KEEP_FILES = {
    'fov_tools.py',
    'FOVTools.spec',
    'requirements.txt',
    'make_demo.py',
    '.gitignore',
    '.git',
    '.venv',
    'build',
    'dist',
    # 指南文档
    'LANE_LINE_GUIDE.md',
    'QUICK_EDIT_GUIDE.md',
    'FOV_CLIPPING_GUIDE.md',
    'FOV_CLIPPING_IMPLEMENTATION.md',
    # 参考资料
    'HW 3.0 Sensor Layout Reference.pdf',
}

def update_spec_file():
    """更新 spec 文件使用最新代码"""
    print("[1] 更新 FOVTools.spec...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FOVTools
生成最新版本的 .exe 文件
"""

block_cipher = None

a = Analysis(
    ['c:\\\\Fuyue_WorkSpace\\\\FOVTools\\\\fov_tools.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tcl', 'tk', '_tkinter', 'tkinter', '__future__'],
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
'''
    
    with open(SPEC_FILE, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("  ✓ FOVTools.spec 已更新")

def cleanup_files():
    """清理临时和测试文件"""
    print("\n[2] 清理临时文件...")
    
    cleaned_count = 0
    
    for pattern in CLEANUP_PATTERNS:
        if pattern.endswith('/'):
            # 目录
            dir_path = PROJECT_DIR / pattern.rstrip('/')
            if dir_path.exists() and dir_path.name not in KEEP_FILES:
                try:
                    shutil.rmtree(dir_path)
                    print(f"  ✓ 删除目录: {pattern}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"  ✗ 无法删除 {pattern}: {e}")
        else:
            # 文件（支持通配符）
            if '*' in pattern:
                import glob
                for file_path in glob.glob(str(PROJECT_DIR / pattern)):
                    file_name = os.path.basename(file_path)
                    if file_name not in KEEP_FILES:
                        try:
                            if os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                            else:
                                os.remove(file_path)
                            print(f"  ✓ 删除: {file_name}")
                            cleaned_count += 1
                        except Exception as e:
                            print(f"  ✗ 无法删除 {file_name}: {e}")
    
    print(f"\n  总计删除 {cleaned_count} 个项目")

def build_exe():
    """使用 PyInstaller 生成 .exe"""
    print("\n[3] 生成 .exe 文件...")
    
    try:
        # 检查 PyInstaller 是否已安装
        result = subprocess.run(
            ['pyinstaller', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"  ✓ PyInstaller 版本: {result.stdout.strip()}")
        else:
            print("  ✗ PyInstaller 未安装，尝试安装...")
            subprocess.run(
                ['pip', 'install', 'pyinstaller'],
                check=True,
                capture_output=True
            )
            print("  ✓ PyInstaller 已安装")
        
        # 生成 .exe
        print("\n  正在编译... (这可能需要 1-2 分钟)")
        result = subprocess.run(
            ['pyinstaller', str(SPEC_FILE)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            exe_path = DIST_DIR / 'FOV_Tools.exe'
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"\n  ✅ 成功生成 .exe 文件!")
                print(f"     路径: {exe_path}")
                print(f"     大小: {size_mb:.1f} MB")
                return True
            else:
                print(f"  ✗ .exe 文件未找到")
                return False
        else:
            print(f"  ✗ 编译失败:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("  ✗ 编译超时（超过 5 分钟）")
        return False
    except FileNotFoundError:
        print("  ✗ PyInstaller 未找到，请确保已安装")
        return False
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False

def summary():
    """生成总结信息"""
    print("\n" + "=" * 70)
    print("📦 打包总结")
    print("=" * 70)
    
    exe_path = DIST_DIR / 'FOV_Tools.exe'
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ .exe 文件已生成")
        print(f"   位置: dist\\FOV_Tools.exe")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"\n📝 使用方法:")
        print(f"   1. 双击 FOV_Tools.exe 运行应用")
        print(f"   2. 或在命令行执行: .\\dist\\FOV_Tools.exe")
    else:
        print(f"❌ .exe 文件未生成")
    
    print(f"\n📂 项目结构:")
    print(f"   主程序: fov_tools.py")
    print(f"   打包配置: FOVTools.spec")
    print(f"   输出目录: dist\\")
    print(f"   临时构建: build\\ (可安全删除)")
    
    print(f"\n📚 文档:")
    print(f"   - LANE_LINE_GUIDE.md (车道线功能指南)")
    print(f"   - QUICK_EDIT_GUIDE.md (快速编辑指南)")
    print(f"   - FOV_CLIPPING_GUIDE.md (FOV 切割指南)")
    print(f"   - FOV_CLIPPING_IMPLEMENTATION.md (技术文档)")
    
    print(f"\n🗑️  旧版本 .exe 已保存到 dist\\:")
    for exe in DIST_DIR.glob('FOV_Tools_*.exe'):
        print(f"   - {exe.name}")

def main():
    """主流程"""
    print("=" * 70)
    print("FOVTools 打包和清理工具")
    print("=" * 70)
    
    # 确保在项目目录
    if not SPEC_FILE.exists():
        print(f"✗ 错误: 未找到 {SPEC_FILE}")
        sys.exit(1)
    
    try:
        # 1. 更新 spec 文件
        update_spec_file()
        
        # 2. 清理临时文件
        cleanup_files()
        
        # 3. 生成 .exe
        success = build_exe()
        
        # 4. 显示总结
        summary()
        
        if success:
            print("\n✅ 打包完成!")
            sys.exit(0)
        else:
            print("\n❌ 打包失败，请查看上方错误信息")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
