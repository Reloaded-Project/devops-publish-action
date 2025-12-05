"""
Entry point for running as a module: python -m compress_artifacts
"""

import sys
from .cli import main

if __name__ == '__main__':
    sys.exit(main())
