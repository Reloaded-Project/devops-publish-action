"""
Transformation pipeline for artifact staging.

This module handles all file transformations (flatten, rename, etc.) by creating
a staging directory with the transformed structure before compression.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .grouping import matches_any_pattern


def prepare_group_staging(
    src_dir: Path,
    group_name: str,
    dir_names: List[str],
    flattens_patterns: Optional[List[str]] = None,
    renames_config: Optional[List[Dict[str, str]]] = None
) -> Tuple[Path, tempfile.TemporaryDirectory]:
    """
    Prepare a staging directory with transformed files ready for compression.
    
    Creates a temporary directory containing the transformed file structure.
    The caller is responsible for keeping the returned temp_handle alive until
    compression is complete, then calling temp_handle.cleanup().
    
    Args:
        src_dir: Parent directory containing the artifacts
        group_name: Name of the group (for error messages)
        dir_names: List of directory names to include
        flattens_patterns: Optional list of glob patterns for directories to flatten
        renames_config: Optional list of single-key dicts [{"search": "replace"}, ...]
                        for renaming top-level directories
    
    Returns:
        Tuple of (staging_path, temp_handle). The staging_path is ready for compression.
        Keep temp_handle alive until done, then call temp_handle.cleanup().
    
    Raises:
        SystemExit: If file path conflicts are detected
    """
    temp_handle = tempfile.TemporaryDirectory()
    staging = Path(temp_handle.name)
    
    # Apply transformations
    dest_paths = _apply_flatten_transform(
        src_dir, staging, dir_names, flattens_patterns or []
    )
    
    # === TRANSFORMATION 2: Rename ===
    _apply_rename_transform(staging, renames_config or [], group_name)
    
    # Detect and report conflicts
    _detect_conflicts(dest_paths, group_name)
    
    return staging, temp_handle


def _apply_flatten_transform(
    src_dir: Path,
    staging: Path,
    dir_names: List[str],
    flattens_patterns: List[str]
) -> Dict[Path, List[str]]:
    """
    Apply flatten transformation: copy files to staging directory.
    
    Directories matching flattens_patterns have their contents placed at the
    staging root. Non-matching directories are preserved as subdirectories.
    
    Args:
        src_dir: Source directory containing artifacts
        staging: Staging directory to copy to
        dir_names: List of directory names to process
        flattens_patterns: Glob patterns for directories to flatten
    
    Returns:
        Dict mapping archive_path (relative to staging) to list of source directories.
        Used for conflict detection.
    """
    dest_paths: Dict[Path, List[str]] = {}
    
    for dir_name in dir_names:
        source = src_dir / dir_name
        should_flatten = matches_any_pattern(dir_name, flattens_patterns)
        
        if should_flatten:
            # Copy contents directly to staging root
            target_base = staging
        else:
            # Preserve as subdirectory
            target_base = staging / dir_name
        
        # Copy files from source directory to staging, tracking paths for conflict detection
        for root, _, filenames in os.walk(source):
            root_path = Path(root)
            for filename in filenames:
                file_path = (root_path / filename).relative_to(source)
                src_file = source / file_path
                dest_file = target_base / file_path
                
                # Track for conflict detection
                archive_path_rel = dest_file.relative_to(staging)
                if archive_path_rel not in dest_paths:
                    dest_paths[archive_path_rel] = []
                dest_paths[archive_path_rel].append(dir_name)
                
                # Create parent directories and copy file
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
    
    return dest_paths


def _apply_rename_transform(
    staging: Path,
    renames_config: List[Dict[str, str]],
    group_name: str = ""
) -> None:
    """
    Apply rename transformation to top-level directories in staging.
    
    Renames are applied in list order. Each rename is a dict with one key-value
    pair where key=search string, value=replacement string. All occurrences of
    the search string in directory names are replaced.
    
    Args:
        staging: Staging directory containing artifacts
        renames_config: List of single-key dicts [{"search": "replace"}, ...]
        group_name: Name of the group (for error messages)
    
    Raises:
        SystemExit: If renames would cause directory name conflicts
    """
    if not renames_config:
        return
    
    # Get current top-level directories
    top_level_dirs = [d for d in staging.iterdir() if d.is_dir()]
    
    # Compute all new names first to detect conflicts
    renames_to_apply: List[Tuple[Path, str]] = []
    new_names: Dict[str, List[str]] = {}  # new_name -> [original_names]
    
    for dir_path in top_level_dirs:
        new_name = dir_path.name
        
        # Apply each rename rule in order
        for rename_rule in renames_config:
            for search, replace in rename_rule.items():
                new_name = new_name.replace(search, replace)
        
        renames_to_apply.append((dir_path, new_name))
        
        # Track for conflict detection
        if new_name not in new_names:
            new_names[new_name] = []
        new_names[new_name].append(dir_path.name)
    
    # Check for conflicts (multiple dirs renamed to same name)
    conflicts = [(name, sources) for name, sources in new_names.items() if len(sources) > 1]
    if conflicts:
        print(f"Error: Directory name conflicts after rename in group '{group_name}':", file=sys.stderr)
        for conflict_name, sources in conflicts:
            sources_str = ', '.join(sources)
            print(f"  - '{conflict_name}' would be produced by: {sources_str}", file=sys.stderr)
        sys.exit(1)
    
    # Apply renames
    for dir_path, new_name in renames_to_apply:
        if new_name != dir_path.name:
            new_path = staging / new_name
            dir_path.rename(new_path)


def _detect_conflicts(dest_paths: Dict[Path, List[str]], group_name: str) -> None:
    """
    Detect and report file path conflicts.
    
    If any file path would be written by multiple source directories,
    prints an error message and exits.
    
    Args:
        dest_paths: Dict mapping archive_path to list of source directories
        group_name: Name of the group (for error message)
    
    Raises:
        SystemExit: If conflicts are detected
    """
    conflicts = [(path, sources) for path, sources in dest_paths.items() if len(sources) > 1]
    
    if conflicts:
        print(f"Error: File path conflicts detected in group '{group_name}':", file=sys.stderr)
        for conflict_path, sources in conflicts:
            sources_str = ', '.join(sources)
            print(f"  - '{conflict_path}' exists in: {sources_str}", file=sys.stderr)
        sys.exit(1)
