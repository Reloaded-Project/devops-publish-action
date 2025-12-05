"""
CLI argument parsing and main entry point.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import parse_artifact_groups
from .grouping import resolve_group_directories
from .compression import compress_ungrouped, compress_grouped
from .transforms import prepare_group_staging


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the compression script."""
    parser = argparse.ArgumentParser(
        description='Compress artifact directories into archives',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Compress all artifacts individually
  %(prog)s --artifacts-dir artifacts --output-dir compressed

  # Use 7z with maximum compression
  %(prog)s --artifacts-dir artifacts --output-dir compressed --tool 7z --args "-mx=9"

  # Group artifacts with YAML config
  %(prog)s --artifacts-dir artifacts --output-dir compressed --groups '
    c-library:
      - c-library-linux-x64
      - c-library-windows-x64
    symbols:
      patterns: "*-symbols"
  '
'''
    )
    
    parser.add_argument(
        '--artifacts-dir', '-a',
        required=True,
        help='Path to directory containing artifact subdirectories'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        required=True,
        help='Path to output directory for compressed archives'
    )
    
    parser.add_argument(
        '--groups', '-g',
        default='',
        help="YAML grouping configuration (inline or @filename). "
             "Supports explicit directory lists or 'patterns:' for glob matching."
    )
    
    parser.add_argument(
        '--tool', '-t',
        default='zip',
        help="Compression tool: 'zip' (default), '7z', or any command-line archiver. "
             "For 7z, auto-detects '7z' or '7zz' binary."
    )
    
    parser.add_argument(
        '--args',
        default='',
        help="Additional arguments passed to the compression tool. "
             "Examples: '-mx=9' for 7z max compression, '-9' for zip max compression."
    )
    
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the compression script.
    
    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Validate paths
    artifacts_dir = Path(args.artifacts_dir)
    if not artifacts_dir.exists():
        print(f"Artifacts directory does not exist: {artifacts_dir}")
        print("No artifacts to compress.")
        return 0
    
    if not artifacts_dir.is_dir():
        print(f"Error: Not a directory: {artifacts_dir}", file=sys.stderr)
        return 1
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse grouping configuration
    groups_yaml = args.groups
    if groups_yaml.startswith('@'):
        # Load from file
        groups_file = Path(groups_yaml[1:])
        if groups_file.exists():
            groups_yaml = groups_file.read_text()
        else:
            print(f"Warning: Groups file not found: {groups_file}", file=sys.stderr)
            groups_yaml = ''
    
    groups = parse_artifact_groups(groups_yaml)
    
    # Find all artifact directories
    all_dirs = set()
    for entry in artifacts_dir.iterdir():
        if entry.is_dir():
            all_dirs.add(entry.name)
    
    if not all_dirs:
        print("No artifact directories found.")
        return 0
    
    # Track which directories have been grouped
    grouped_dirs = set()
    
    # Process groups first
    for group_name, group_config in groups.items():
        dir_names, flattens_patterns = resolve_group_directories(artifacts_dir, group_config)
        if dir_names:
            if flattens_patterns:
                # Transform path: staging -> compress staged
                staging_path, staging_handle = prepare_group_staging(
                    artifacts_dir, group_name, dir_names, flattens_patterns
                )
                try:
                    archive = compress_grouped(
                        staging_path, output_dir, group_name,
                        args.tool, args.args
                    )
                finally:
                    staging_handle.cleanup()
            else:
                # Direct path: compress original dirs (no staging needed)
                archive = compress_grouped(
                    artifacts_dir, output_dir, group_name,
                    args.tool, args.args, dir_names=dir_names
                )
            if archive:
                grouped_dirs.update(dir_names)
    
    # Compress remaining ungrouped directories individually
    ungrouped = sorted(all_dirs - grouped_dirs)
    for dir_name in ungrouped:
        compress_ungrouped(artifacts_dir, output_dir, dir_name, args.tool, args.args)
    
    # List created archives
    print("\nCreated archives:")
    for archive in sorted(output_dir.iterdir()):
        if archive.is_file():
            size = archive.stat().st_size
            print(f"  {archive.name} ({size:,} bytes)")
    
    return 0
