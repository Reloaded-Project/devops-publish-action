#!/usr/bin/env python3
"""
Create and configure a virtual environment for the compress_artifacts module.

This script:
- Creates a virtual environment at scripts/.venv/
- Installs dependencies from requirements.txt

Run this once before running tests or using VSCode debugging.

Usage:
    python setup-venv.py
"""

import subprocess
import sys
import venv
from pathlib import Path


def get_venv_paths(venv_dir: Path) -> tuple[Path, Path]:
    """Get the Python and pip executable paths for the virtual environment."""
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        python_path = venv_dir / "bin" / "python"
        pip_path = venv_dir / "bin" / "pip"
    return python_path, pip_path


def create_venv(venv_dir: Path) -> bool:
    """Create a virtual environment. Returns True if created, False if already exists."""
    if venv_dir.exists():
        print(f"Virtual environment already exists at {venv_dir}")
        return False
    print(f"Creating virtual environment at {venv_dir}...")
    venv.create(venv_dir, with_pip=True)
    return True


def install_dependencies(pip_path: Path, requirements_file: Path) -> None:
    """Install dependencies from requirements.txt."""
    print("Installing dependencies...")
    
    # Upgrade pip first
    subprocess.run(
        [str(pip_path), "install", "--quiet", "--upgrade", "pip"],
        check=True,
    )
    
    # Install requirements
    if requirements_file.exists():
        subprocess.run(
            [str(pip_path), "install", "--quiet", "-r", str(requirements_file)],
            check=True,
        )


def main() -> int:
    """Main entry point."""
    script_dir = Path(__file__).parent.resolve()
    venv_dir = script_dir / ".venv"
    requirements_file = script_dir / "requirements.txt"
    
    # Create virtual environment
    created = create_venv(venv_dir)
    
    # Get venv executable paths
    python_path, pip_path = get_venv_paths(venv_dir)
    
    # Verify the venv was created correctly
    if not python_path.exists():
        print(f"Error: Python executable not found at {python_path}")
        return 1
    
    # Install dependencies
    install_dependencies(pip_path, requirements_file)
    
    if created:
        print(f"\nVirtual environment ready at: {venv_dir}")
    print(f"Python: {python_path}")
    print("\nTo activate manually:")
    if sys.platform == "win32":
        print(f"  {venv_dir}\\Scripts\\activate")
    else:
        print(f"  source {venv_dir}/bin/activate")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
