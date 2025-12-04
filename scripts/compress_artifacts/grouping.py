"""
Artifact grouping logic - matching directories against patterns.
"""

import fnmatch
import sys
from pathlib import Path
from typing import Optional


def match_directories(base_dir: Path, pattern: str, excludes: Optional[list] = None) -> list:
    """
    Find directories matching a glob pattern, optionally excluding some.
    
    Args:
        base_dir: Directory containing artifact subdirectories
        pattern: Glob pattern to match directory names
        excludes: List of patterns to exclude
    
    Returns:
        List of matching directory names (not full paths)
    """
    excludes = excludes or []
    matches = []
    
    for entry in base_dir.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        if fnmatch.fnmatch(name, pattern):
            # Check exclusions
            excluded = False
            for exclude_pattern in excludes:
                if fnmatch.fnmatch(name, exclude_pattern):
                    excluded = True
                    break
            if not excluded:
                matches.append(name)
    
    return sorted(matches)


def resolve_group_directories(base_dir: Path, group_config) -> list:
    """
    Resolve a group configuration to a list of directory names.
    
    Args:
        base_dir: Directory containing artifact subdirectories
        group_config: Either a list of dir names, or a dict with pattern/exclude
    
    Returns:
        List of directory names belonging to this group
    """
    if isinstance(group_config, list):
        # Explicit list of directories
        return [d for d in group_config if (base_dir / d).is_dir()]
    
    if isinstance(group_config, dict):
        pattern = group_config.get('pattern', '')
        excludes = group_config.get('exclude', [])
        if isinstance(excludes, str):
            excludes = [excludes]
        return match_directories(base_dir, pattern, excludes)
    
    print(f"Warning: Invalid group config type: {type(group_config).__name__}", file=sys.stderr)
    return []
