#!/usr/bin/env python3
"""
Cross-platform build script for FOVTools
Generates executable packages for Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import json
from datetime import datetime

# Project configuration
PROJECT_NAME = "FOVTools"
PROJECT_VERSION = "1.0.0"
MAIN_SCRIPT = "fov_tools.py"

class CrossPlatformBuilder:
    def __init__(self):
        # 获取项目根目录 (scripts 的父目录)
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.current_platform = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'
        self.current_arch = platform.machine()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log(self, msg: str, level: str = "INFO"):
        """Print formatted log message."""
        colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "ERROR": "\033[91m", "END": "\033[0m"}
        color = colors.get(level, "")
        end = colors["END"]
        print(f"[{level:7s}] {color}{msg}{end}")
    
    def run_command(self, cmd: list, description: str = "") -> bool:
        """Run a command and return success status."""
        if description:
            self.log(description)
        try:
            subprocess.run(cmd, check=True, cwd=str(self.project_root))
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {' '.join(cmd)}", "ERROR")
            return False
    
    def clean_build(self):
        """Clean previous build artifacts."""
        self.log("Cleaning previous builds...")
        for dir_name in ["build", "dist", "__pycache__", "*.pyc"]:
            path = self.project_root / dir_name if not "*" in dir_name else None
            if path and path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        self.log("Clean complete", "SUCCESS")
    
    def generate_pyinstaller_spec(self, platform_name: str) -> str:
        """Generate platform-specific PyInstaller spec file."""
        self.log(f"Generating PyInstaller spec for {platform_name}...")
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for {PROJECT_NAME} - {platform_name}
Generated on {datetime.now().isoformat()}
"""
from PyInstaller.utils.hooks import collect_all

block_cipher = None

numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')
mpl_datas, mpl_binaries, mpl_hiddenimports = collect_all('matplotlib')
mpl_toolkits_datas, mpl_toolkits_binaries, mpl_toolkits_hiddenimports = collect_all('mpl_toolkits')

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=['.'],
    binaries=numpy_binaries + mpl_binaries + mpl_toolkits_binaries,
    datas=numpy_datas + mpl_datas + mpl_toolkits_datas,
    hiddenimports=numpy_hiddenimports + mpl_hiddenimports + mpl_toolkits_hiddenimports + [
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'fitz', 'PIL', 'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={{}},
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
    name='{PROJECT_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
'''
        # Adjust for macOS to create .app bundle
        if platform_name == "macOS":
            spec_content = spec_content.replace(
                "exe = EXE(",
                "app = BUNDLE(\n    exe,\n    name='{}.app',\n)".format(PROJECT_NAME)
            )
        
        spec_file = self.project_root / f"FOVTools_{platform_name}.spec"
        spec_file.write_text(spec_content, encoding='utf-8')
        self.log(f"Spec file generated: {spec_file.name}", "SUCCESS")
        return str(spec_file)
    
    def build_pyinstaller(self, platform_name: str) -> bool:
        """Build executable using PyInstaller."""
        spec_file = self.generate_pyinstaller_spec(platform_name)
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            spec_file
        ]
        
        return self.run_command(cmd, f"Building {platform_name} executable...")
    
    def package_build(self, platform_name: str) -> str:
        """Package the built executable into a compressed archive."""
        self.log(f"Packaging {platform_name} build...")
        
        if platform_name == "Windows":
            exe_dir = self.dist_dir / PROJECT_NAME
            if not exe_dir.exists():
                self.log(f"Executable directory not found: {exe_dir}", "ERROR")
                return ""
            
            # Create package directory
            package_name = f"{PROJECT_NAME}_Windows_v{PROJECT_VERSION}_{self.timestamp}"
            package_dir = self.dist_dir / package_name
            package_dir.mkdir(exist_ok=True)
            
            # Copy executable and resources
            shutil.copytree(exe_dir, package_dir / "app", dirs_exist_ok=True)
            self._copy_resources(package_dir)
            
            # Create batch launcher
            launcher = package_dir / f"Run_{PROJECT_NAME}.bat"
            launcher.write_text(f"@echo off\ncd /d \"%~dp0app\"\n{PROJECT_NAME}.exe\n", encoding='utf-8')
            
            # Create zip archive
            archive_path = self.dist_dir / f"{package_name}.zip"
            shutil.make_archive(str(archive_path.with_suffix('')), 'zip', package_dir.parent, package_name)
            
            return str(archive_path)
        
        elif platform_name == "macOS":
            app_dir = self.dist_dir / f"{PROJECT_NAME}.app"
            if not app_dir.exists():
                self.log(f"App bundle not found: {app_dir}", "ERROR")
                return ""
            
            package_name = f"{PROJECT_NAME}_macOS_v{PROJECT_VERSION}_{self.timestamp}"
            package_dir = self.dist_dir / package_name
            package_dir.mkdir(exist_ok=True)
            
            shutil.copytree(app_dir, package_dir / f"{PROJECT_NAME}.app", dirs_exist_ok=True)
            self._copy_resources(package_dir)
            
            # Create dmg or tar.gz
            archive_path = self.dist_dir / f"{package_name}.tar.gz"
            shutil.make_archive(str(archive_path.with_suffix('')), 'gztar', package_dir.parent, package_name)
            
            return str(archive_path)
        
        elif platform_name == "Linux":
            exe_file = self.dist_dir / PROJECT_NAME / PROJECT_NAME
            if not exe_file.exists():
                self.log(f"Executable not found: {exe_file}", "ERROR")
                return ""
            
            package_name = f"{PROJECT_NAME}_Linux_v{PROJECT_VERSION}_{self.timestamp}"
            package_dir = self.dist_dir / package_name
            package_dir.mkdir(exist_ok=True)
            
            # Copy executable
            exe_dest = package_dir / "bin"
            exe_dest.mkdir(exist_ok=True)
            shutil.copy2(exe_file, exe_dest / PROJECT_NAME)
            os.chmod(exe_dest / PROJECT_NAME, 0o755)
            
            # Create shell launcher
            launcher = package_dir / f"run_{PROJECT_NAME}.sh"
            launcher.write_text(f"#!/bin/bash\ncd \"$(dirname \"$0\")/bin\"\n./{PROJECT_NAME}\n", encoding='utf-8')
            os.chmod(launcher, 0o755)
            
            # Copy supporting libraries
            lib_dest = package_dir / "lib"
            if (self.dist_dir / PROJECT_NAME / "lib").exists():
                shutil.copytree(self.dist_dir / PROJECT_NAME / "lib", lib_dest, dirs_exist_ok=True)
            
            self._copy_resources(package_dir)
            
            # Create tar.gz archive
            archive_path = self.dist_dir / f"{package_name}.tar.gz"
            shutil.make_archive(str(archive_path.with_suffix('')), 'gztar', package_dir.parent, package_name)
            
            return str(archive_path)
        
        return ""
    
    def _copy_resources(self, dest_dir: Path):
        """Copy README and other resources to package."""
        resources = [
            "README.md", "LICENSE", "requirements.txt", "fov_tools_session.json"
        ]
        
        for resource in resources:
            src = self.project_root / resource
            if src.exists():
                shutil.copy2(src, dest_dir / resource)
    
    def build_for_platform(self, platform_name: str) -> bool:
        """Build complete package for a specific platform."""
        self.log(f"\n{'='*60}")
        self.log(f"Building for {platform_name}", "INFO")
        self.log(f"{'='*60}\n")
        
        if not self.build_pyinstaller(platform_name):
            return False
        
        archive_path = self.package_build(platform_name)
        if archive_path:
            self.log(f"Package created: {archive_path}", "SUCCESS")
            return True
        else:
            self.log(f"Failed to package {platform_name} build", "ERROR")
            return False
    
    def build_all_platforms(self):
        """Build for all supported platforms."""
        self.log("\n" + "="*60)
        self.log("FOVTools Cross-Platform Build", "INFO")
        self.log(f"Current Platform: {self.current_platform} ({self.current_arch})")
        self.log(f"Version: {PROJECT_VERSION}")
        self.log("="*60 + "\n")
        
        # Clean previous builds
        self.clean_build()
        
        # Note: You can only build for the current platform with PyInstaller
        # To build for other platforms, run this script on those systems
        platforms_to_build = [self.current_platform]
        
        if self.current_platform == "Windows":
            platforms_to_build = ["Windows"]
        elif self.current_platform == "Darwin":
            platforms_to_build = ["macOS"]
        elif self.current_platform == "Linux":
            platforms_to_build = ["Linux"]
        
        self.log(f"Building for: {', '.join(platforms_to_build)}", "INFO")
        self.log("Note: PyInstaller builds for the current platform only.", "INFO")
        self.log("To build for other platforms, run this script on those systems.\n")
        
        results = {}
        for platform_name in platforms_to_build:
            results[platform_name] = self.build_for_platform(platform_name)
        
        self._print_summary(results)
        return all(results.values())
    
    def _print_summary(self, results: dict):
        """Print build summary."""
        self.log("\n" + "="*60)
        self.log("Build Summary", "INFO")
        self.log("="*60)
        
        for platform_name, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            self.log(f"{platform_name:10s}: {status}", "SUCCESS" if success else "ERROR")
        
        self.log("\nPackages location: " + str(self.dist_dir))
        self.log("="*60 + "\n")


def main():
    builder = CrossPlatformBuilder()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--platform":
            if len(sys.argv) < 3:
                print("Usage: python build_cross_platform.py --platform [Windows|macOS|Linux]")
                sys.exit(1)
            platform_name = sys.argv[2]
            success = builder.build_for_platform(platform_name)
        else:
            print("Usage: python build_cross_platform.py [--platform Windows|macOS|Linux]")
            sys.exit(1)
    else:
        success = builder.build_all_platforms()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
