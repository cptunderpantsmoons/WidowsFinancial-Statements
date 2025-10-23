"""
Build script to create an executable using PyInstaller.
Supports Windows, Linux, and macOS platforms.
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def build_executable():
    """Build the executable for the current platform."""
    
    project_root = Path(__file__).parent
    dist_path = project_root / "dist"
    build_path = project_root / "build"
    
    if dist_path.exists():
        shutil.rmtree(dist_path)
        print("Removed existing dist directory")
    
    if build_path.exists():
        shutil.rmtree(build_path)
        print("Removed existing build directory")
    
    print(f"Building executable for {platform.system()}...")
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        "FinancialStatementGenerator",
        "--icon=icon.ico" if (project_root / "icon.ico").exists() else "",
        "--hidden-import=streamlit",
        "--hidden-import=fitz",
        "--hidden-import=pymupdf",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=requests",
        "--collect-all=streamlit",
        "--add-data=Finance Knowledge:Finance Knowledge",
        "--add-data=config:config",
        str(project_root / "src" / "main.py"),
    ]
    
    cmd = [c for c in cmd if c]
    
    result = subprocess.run(cmd, cwd=str(project_root))
    
    if result.returncode == 0:
        exe_extensions = {
            "Windows": ".exe",
            "Linux": "",
            "Darwin": ".app"
        }
        exe_ext = exe_extensions.get(platform.system(), "")
        exe_name = f"FinancialStatementGenerator{exe_ext}"
        
        exe_path = dist_path / exe_name if exe_ext else dist_path / "FinancialStatementGenerator"
        
        if exe_path.exists():
            file_size_mb = exe_path.stat().st_size / (1024*1024) if exe_path.is_file() else "N/A"
            print(f"\n✓ Executable created successfully: {exe_path}")
            if isinstance(file_size_mb, float):
                print(f"  File size: {file_size_mb:.1f} MB")
            return True
        else:
            print("✗ Executable not found after build")
            return False
    else:
        print("✗ Build failed")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
