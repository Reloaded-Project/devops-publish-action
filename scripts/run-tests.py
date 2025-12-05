#!/usr/bin/env python3
"""
Cross-platform test runner for the compress_artifacts module.

This script runs the test suite using pytest.

Usage:
    python run-tests.py [pytest-args...]
    python run-tests.py --no-venv [pytest-args...]

Examples:
    python run-tests.py                    # Run all tests (uses .venv/)
    python run-tests.py -v                 # Run with verbose output
    python run-tests.py --no-venv          # Run directly without venv wrapper
    python run-tests.py -k "ungrouped"     # Run only tests matching "ungrouped"
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


def ensure_venv(venv_dir: Path, requirements_file: Path) -> Path:
    """Ensure venv exists with dependencies. Returns Python path."""
    python_path, pip_path = get_venv_paths(venv_dir)
    
    if not venv_dir.exists():
        print(f"Creating virtual environment at {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        
        # Install dependencies
        print("Installing dependencies...")
        subprocess.run(
            [str(pip_path), "install", "--quiet", "--upgrade", "pip"],
            check=True,
        )
        if requirements_file.exists():
            subprocess.run(
                [str(pip_path), "install", "--quiet", "-r", str(requirements_file)],
                check=True,
            )
    
    if not python_path.exists():
        print(f"Error: Python executable not found at {python_path}")
        sys.exit(1)
    
    return python_path


def run_tests(python_path: Path, tests_dir: Path, extra_args: list[str]) -> int:
    """Run the test suite and return the exit code."""
    print("Running tests...")
    result = subprocess.run(
        [str(python_path), "-m", "pytest", str(tests_dir)] + extra_args,
    )
    return result.returncode


def main() -> int:
    """Main entry point."""
    script_dir = Path(__file__).parent.resolve()
    tests_dir = script_dir / "tests"
    
    # Check for --no-venv flag
    args = sys.argv[1:]
    no_venv = "--no-venv" in args
    if no_venv:
        args = [a for a in args if a != "--no-venv"]
    
    if no_venv:
        # Run directly with current Python
        return run_tests(Path(sys.executable), tests_dir, args)
    else:
        # Use venv (create if needed)
        venv_dir = script_dir / ".venv"
        requirements_file = script_dir / "requirements.txt"
        python_path = ensure_venv(venv_dir, requirements_file)
        return run_tests(python_path, tests_dir, args)


if __name__ == "__main__":
    sys.exit(main())
