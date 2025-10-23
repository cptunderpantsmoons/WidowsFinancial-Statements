import sys
import subprocess
import os

def main():
    """Entry point for the application."""
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    app_path = os.path.join(project_root, "src", "app.py")
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

if __name__ == "__main__":
    main()
