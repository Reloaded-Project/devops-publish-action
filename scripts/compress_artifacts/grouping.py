"""
Artifact grouping logic - matching directories against patterns.
"""

import fnmatch
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def matches_any_pattern(name: str, patterns: List[str]) -> bool:
    """
    Check if a name matches any of the given glob patterns.
    
    Args:
        name: The name to check
        patterns: List of glob patterns to match against
    
    Returns:
        True if name matches any pattern, False otherwise
    """
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


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


def resolve_group_directories(base_dir: Path, group_config) -> Tuple[List[str], List[str]]:
    """
    Resolve a group configuration to a list of directory names and flattens patterns.
    
    Args:
        base_dir: Directory containing artifact subdirectories
        group_config: Either a list of dir names, or a dict with 'patterns', 'excludes',
                      and 'flattens'. The 'patterns', 'excludes', and 'flattens' keys 
                      accept either a string or list.
    
    Returns:
        Tuple of (directory names list, flattens patterns list)
    """
    if isinstance(group_config, list):
        # Explicit list of directories - flattens not supported
        return ([d for d in group_config if (base_dir / d).is_dir()], [])
    
    if isinstance(group_config, dict):
        # Get patterns - handle both string and list (inline normalization)
        patterns_raw = group_config.get('patterns', [])
        if patterns_raw is None:
            patterns = []
        elif isinstance(patterns_raw, str):
            patterns = [patterns_raw]
        else:
            patterns = list(patterns_raw)
        
        # Get excludes - handle both string and list (inline normalization)
        excludes_raw = group_config.get('excludes', [])
        if excludes_raw is None:
            excludes = []
        elif isinstance(excludes_raw, str):
            excludes = [excludes_raw]
        else:
            excludes = list(excludes_raw)
        
        # Get flattens - handle both string and list (inline normalization)
        flattens_raw = group_config.get('flattens')
        if flattens_raw is None:
            flattens = []
        elif isinstance(flattens_raw, str):
            flattens = [flattens_raw]
        else:
            flattens = list(flattens_raw)
        
        dir_names = match_directories_multi(base_dir, patterns, excludes)
        return (dir_names, flattens)
    
    print(f"Warning: Invalid group config type: {type(group_config).__name__}", file=sys.stderr)
    return ([], [])
