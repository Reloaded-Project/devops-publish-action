#!/usr/bin/env python3
"""
Thin wrapper for the compress_artifacts module.

This script maintains backwards compatibility with action.yml.
The module can also be run directly as: python -m compress_artifacts
"""

import sys
from pathlib import Path

# Add the scripts directory to the path so we can import the module
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from compress_artifacts.cli import main

if __name__ == '__main__':
    sys.exit(main())
