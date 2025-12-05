"""
Compression tool invocation and 7z/7zz detection.
"""

import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


# Default compression arguments for maximum compression
DEFAULT_COMPRESSION_ARGS = {
    '7z': '-mx=9',
    '7zz': '-mx=9',
    'zip': '-9',
}


def get_default_args(tool: str) -> str:
    """
    Get default compression arguments for a tool.
    
    Args:
        tool: Compression tool name (zip, 7z, 7zz)
    
    Returns:
        Default arguments string for maximum compression, or empty string
    """
    return DEFAULT_COMPRESSION_ARGS.get(tool, '')


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
        args: Additional arguments as a string (if empty, uses max compression defaults)
        archive_path: Output archive path
        sources: List of source paths to compress
        cwd: Working directory for relative paths (unused but kept for API compatibility)
    
    Returns:
        Command as a list of strings
    """
    # Use default args if none specified
    effective_args = args if args else get_default_args(tool)
    
    if tool == 'zip':
        cmd = ['zip', '-r']
        if effective_args:
            cmd.extend(shlex.split(effective_args))
        cmd.append(archive_path)
        cmd.extend(sources)
    elif tool in ('7z', '7zz'):
        # Resolve the actual binary to use
        actual_binary = resolve_7z_binary()
        cmd = [actual_binary, 'a']
        if effective_args:
            cmd.extend(shlex.split(effective_args))
        cmd.append(archive_path)
        cmd.extend(sources)
    else:
        # Generic fallback: tool archive sources...
        cmd = [tool]
        if effective_args:
            cmd.extend(shlex.split(effective_args))
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


def compress_grouped(src_dir: Path, dest_dir: Path, group_name: str,
                     tool: str, args: str,
                     dir_names: Optional[List[str]] = None) -> Optional[Path]:
    """
    Compress directories into a grouped archive.
    
    Args:
        src_dir: Source directory (staging dir or artifacts dir)
        dest_dir: Output directory for archive
        group_name: Name for the archive
        tool: Compression tool (zip, 7z, etc.)
        args: Extra compression arguments
        dir_names: If provided, compress these specific subdirs.
                   If None, compress all contents of src_dir.
    
    Returns:
        Path to the created archive, or None if compression failed
    """
    if dir_names is not None:
        # Compress specific subdirs
        if not dir_names:
            print(f"Warning: No directories for group {group_name}, skipping", file=sys.stderr)
            return None
        sources = dir_names
        log_msg = f"Compressing group {group_name} ({len(dir_names)} dirs) -> "
    else:
        # Compress all contents of src_dir
        sources = [item.name for item in src_dir.iterdir()]
        if not sources:
            print(f"Warning: Staging directory empty for group {group_name}, skipping", file=sys.stderr)
            return None
        log_msg = f"Compressing group {group_name} -> "
    
    ext = get_file_extension(tool)
    archive_path = dest_dir / f"{group_name}{ext}"
    
    cmd = get_compression_command(tool, args, str(archive_path.absolute()), sources)
    print(f"{log_msg}{archive_path.name}")
    result = subprocess.run(cmd, cwd=str(src_dir), capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error compressing group {group_name}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    
    return archive_path
