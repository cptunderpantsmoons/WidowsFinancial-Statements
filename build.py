"""
Build script to create a Windows .exe executable using PyInstaller.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_executable():
    """Build the Windows executable."""
    
    project_root = Path(__file__).parent
    dist_path = project_root / "dist"
    build_path = project_root / "build"
    
    if dist_path.exists():
        shutil.rmtree(dist_path)
        print(f"Removed existing dist directory")
    
    if build_path.exists():
        shutil.rmtree(build_path)
        print(f"Removed existing build directory")
    
    print("Building executable with PyInstaller...")
    
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
        str(project_root / "src" / "main.py"),
    ]
    
    cmd = [c for c in cmd if c]
    
    result = subprocess.run(cmd, cwd=str(project_root))
    
    if result.returncode == 0:
        exe_path = dist_path / "FinancialStatementGenerator.exe"
        if exe_path.exists():
            print(f"\n✓ Executable created successfully: {exe_path}")
            print(f"  File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
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
