"""
Cross-platform build script that can create Windows .exe on Linux using Wine or PyInstaller's cross-compilation.
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def check_pyinstaller_cross_support():
    """Check if system can do cross-platform builds."""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller not found")
        return False

def build_for_windows_on_linux():
    """Attempt to build Windows executable on Linux using PyInstaller."""
    print("Attempting Windows build on Linux...")
    print("Note: PyInstaller requires the target platform to create native executables.")
    print("\nOptions:")
    print("1. GitHub Actions (Recommended): Automatic builds on Windows runners")
    print("2. Docker: Windows container with Python")
    print("3. Wine: Windows compatibility layer on Linux")
    print("4. Cross-compile attempt: May not work reliably")
    return False

def build_executable(target_os=None):
    """Build the executable for specified or current platform."""
    
    project_root = Path(__file__).parent
    dist_path = project_root / "dist"
    build_path = project_root / "build"
    
    if dist_path.exists():
        shutil.rmtree(dist_path)
        print("Removed existing dist directory")
    
    if build_path.exists():
        shutil.rmtree(build_path)
        print("Removed existing build directory")
    
    current_os = platform.system()
    build_os = target_os or current_os
    
    print(f"Building for: {build_os}")
    print(f"Building on: {current_os}")
    
    if build_os == "Windows" and current_os != "Windows":
        print("\n⚠ Warning: Cannot create native Windows .exe on non-Windows system")
        print("Use one of these solutions:")
        print("  1. GitHub Actions workflow (automated)")
        print("  2. Docker with Windows image")
        print("  3. Wine compatibility layer")
        print("  4. Native Windows machine")
        return False
    
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
            "Darwin": ""
        }
        exe_ext = exe_extensions.get(build_os, "")
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
    if len(sys.argv) > 1 and sys.argv[1] == "--target-windows":
        if platform.system() == "Windows":
            success = build_executable("Windows")
        else:
            print("Cannot build Windows .exe on non-Windows system.")
            print("Please use GitHub Actions or Docker.")
            build_for_windows_on_linux()
            success = False
    else:
        success = build_executable()
    
    sys.exit(0 if success else 1)
