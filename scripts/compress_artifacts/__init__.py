"""
Compress artifact directories into archives.

Supports:
- Individual compression of each artifact directory (files at archive root)
- Grouping multiple directories into a single archive (preserves subdirectory structure)
- Configurable compression tool (zip, 7z)
- YAML-based grouping configuration with explicit lists, patterns, and exclusions
"""

from .config import parse_artifact_groups
from .grouping import match_directories, resolve_group_directories
from .compression import (
    resolve_7z_binary,
    get_file_extension,
    get_compression_command,
    compress_ungrouped,
    compress_grouped,
)
from .cli import create_parser, main

__all__ = [
    'parse_artifact_groups',
    'match_directories',
    'resolve_group_directories',
    'resolve_7z_binary',
    'get_file_extension',
    'get_compression_command',
    'compress_ungrouped',
    'compress_grouped',
    'create_parser',
    'main',
]
