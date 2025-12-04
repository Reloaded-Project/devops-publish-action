"""
Compression tool invocation and 7z/7zz detection.
"""

import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def resolve_7z_binary() -> str:
    """
    Dynamically detect whether to use '7z' or '7zz'.
    
    On some systems (e.g., certain Linux distributions), the binary is named '7zz'
    instead of '7z'. This function checks which one is available.
    
    Returns:
        The name of the available 7z binary ('7z' or '7zz')
    
    Raises:
        FileNotFoundError: If neither '7z' nor '7zz' is found
    """
    # Check for 7z first (more common)
    if shutil.which('7z'):
        return '7z'
    # Check for 7zz (alternative name on some systems)
    if shutil.which('7zz'):
        return '7zz'
    raise FileNotFoundError("Neither '7z' nor '7zz' found in PATH. Please install p7zip.")


def get_file_extension(tool: str) -> str:
    """Get the appropriate file extension for the compression tool."""
    if tool in ('7z', '7zz'):
        return '.7z'
    return '.zip'


def get_compression_command(tool: str, args: str, archive_path: str, sources: list, cwd: Optional[str] = None) -> list:
    """
    Build the compression command for the specified tool.
    
    Args:
        tool: Compression tool name (zip, 7z, 7zz)
        args: Additional arguments as a string
        archive_path: Output archive path
        sources: List of source paths to compress
        cwd: Working directory for relative paths (unused but kept for API compatibility)
    
    Returns:
        Command as a list of strings
    """
    if tool == 'zip':
        cmd = ['zip', '-r']
        if args:
            cmd.extend(shlex.split(args))
        cmd.append(archive_path)
        cmd.extend(sources)
    elif tool in ('7z', '7zz'):
        # Resolve the actual binary to use
        actual_binary = resolve_7z_binary()
        cmd = [actual_binary, 'a']
        if args:
            cmd.extend(shlex.split(args))
        cmd.append(archive_path)
        cmd.extend(sources)
    else:
        # Generic fallback: tool archive sources...
        cmd = [tool]
        if args:
            cmd.extend(shlex.split(args))
        cmd.append(archive_path)
        cmd.extend(sources)
    
    return cmd


def compress_ungrouped(src_dir: Path, dest_dir: Path, dir_name: str, tool: str, args: str) -> Optional[Path]:
    """
    Compress a single artifact directory with files at archive root.
    
    Args:
        src_dir: Parent directory containing the artifact
        dest_dir: Output directory for the archive
        dir_name: Name of the artifact directory
        tool: Compression tool
        args: Additional compression arguments
    
    Returns:
        Path to the created archive, or None if compression failed
    """
    artifact_dir = src_dir / dir_name
    ext = get_file_extension(tool)
    archive_path = dest_dir / f"{dir_name}{ext}"
    
    # Get list of files/dirs in the artifact directory
    contents = list(artifact_dir.iterdir())
    if not contents:
        print(f"Warning: Empty directory {dir_name}, skipping", file=sys.stderr)
        return None
    
    # Build list of items to compress (relative to artifact_dir)
    items = [item.name for item in contents]
    
    # Run compression from within the artifact directory so files are at root
    cmd = get_compression_command(tool, args, str(archive_path.absolute()), items)
    
    print(f"Compressing {dir_name} -> {archive_path.name}")
    result = subprocess.run(cmd, cwd=str(artifact_dir), capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error compressing {dir_name}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    
    return archive_path


def compress_grouped(src_dir: Path, dest_dir: Path, group_name: str, dir_names: list, tool: str, args: str) -> Optional[Path]:
    """
    Compress multiple directories into a single archive, preserving subdirectory structure.
    
    Args:
        src_dir: Parent directory containing the artifacts
        dest_dir: Output directory for the archive
        group_name: Name for the output archive
        dir_names: List of directory names to include
        tool: Compression tool
        args: Additional compression arguments
    
    Returns:
        Path to the created archive, or None if compression failed
    """
    if not dir_names:
        print(f"Warning: No directories for group {group_name}, skipping", file=sys.stderr)
        return None
    
    ext = get_file_extension(tool)
    archive_path = dest_dir / f"{group_name}{ext}"
    
    # Run compression from the src_dir so subdirectory names are preserved
    cmd = get_compression_command(tool, args, str(archive_path.absolute()), dir_names)
    
    print(f"Compressing group {group_name} ({len(dir_names)} dirs) -> {archive_path.name}")
    result = subprocess.run(cmd, cwd=str(src_dir), capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error compressing group {group_name}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    
    return archive_path
