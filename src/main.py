import sys
import subprocess
import os
from pathlib import Path


def initialize_directories():
    """Create necessary directories on startup."""
    project_root = Path(__file__).parent.parent

    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    env_file = project_root / ".env"
    if not env_file.exists():
        example_env = project_root / ".env.example"
        if example_env.exists():
            example_env_content = example_env.read_text()
        else:
            example_env_content = "OPENROUTER_API_KEY=\nLOG_LEVEL=INFO\nMAX_FILE_SIZE_MB=100\n# API_TIMEOUT_SECONDS=60  # Optional: Remove or comment out for unlimited timeout\n"

        env_file.write_text(example_env_content)


def main():
    """Entry point for the application."""

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    initialize_directories()

    app_path = os.path.join(project_root, "src", "app.py")

    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])


if __name__ == "__main__":
    main()
