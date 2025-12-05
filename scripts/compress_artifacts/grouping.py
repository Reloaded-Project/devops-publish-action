"""
Artifact grouping logic - matching directories against patterns.
"""

import fnmatch
import sys
from pathlib import Path
from typing import Optional


def match_directories_multi(base_dir: Path, patterns: list, excludes: Optional[list] = None) -> list:
    """
    Find directories matching ANY of the given glob patterns, optionally excluding some.
    
    Args:
        base_dir: Directory containing artifact subdirectories
        patterns: List of glob patterns to match directory names (union - any match)
        excludes: List of patterns to exclude
    
    Returns:
        List of matching directory names (not full paths)
    """
    excludes = excludes or []
    matches = set()
    
    for entry in base_dir.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        
        # Check if name matches ANY of the patterns
        matched = any(fnmatch.fnmatch(name, pattern) for pattern in patterns)
        if not matched:
            continue
        
        # Check exclusions
        excluded = any(fnmatch.fnmatch(name, excl) for excl in excludes)
        if not excluded:
            matches.add(name)
    
    return sorted(matches)


def resolve_group_directories(base_dir: Path, group_config) -> list:
    """
    Resolve a group configuration to a list of directory names.
    
    Args:
        base_dir: Directory containing artifact subdirectories
        group_config: Either a list of dir names, or a dict with 'patterns' and 'excludes'.
                      The 'patterns' and 'excludes' keys accept either a string or list.
    
    Returns:
        List of directory names belonging to this group
    """
    if isinstance(group_config, list):
        # Explicit list of directories
        return [d for d in group_config if (base_dir / d).is_dir()]
    
    if isinstance(group_config, dict):
        # Get patterns - handle both string and list
        patterns = group_config.get('patterns', [])
        if isinstance(patterns, str):
            patterns = [patterns]
        
        # Get excludes - handle both string and list
        excludes = group_config.get('excludes', [])
        if isinstance(excludes, str):
            excludes = [excludes]
        
        return match_directories_multi(base_dir, patterns, excludes)
    
    print(f"Warning: Invalid group config type: {type(group_config).__name__}", file=sys.stderr)
    return []
