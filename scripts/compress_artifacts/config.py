"""
YAML configuration parsing for artifact grouping.
"""

import sys

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def parse_artifact_groups(yaml_str: str) -> dict:
    """
    Parse YAML grouping configuration.
    
    Supported formats:
    - Explicit list: group_name: [dir1, dir2, dir3]
    - Pattern matching: group_name: {patterns: "*.symbols"} or {patterns: ["p1", "p2"]}
    - With exclusions: group_name: {patterns: ..., excludes: "*.symbols"} or {excludes: [...]}
    
    The 'patterns' and 'excludes' keys accept either a single string or a list of strings.
    Directories matching ANY pattern in the list are included.
    
    Returns dict mapping group names to their config.
    """
    if not yaml_str or not yaml_str.strip():
        return {}
    
    if yaml is None:
        print("Error: pyyaml is required for artifact grouping. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    
    try:
        config = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML grouping config: {e}", file=sys.stderr)
        sys.exit(1)
    
    if config is None:
        return {}
    
    if not isinstance(config, dict):
        print(f"Error: artifact-groups must be a YAML mapping, got {type(config).__name__}", file=sys.stderr)
        sys.exit(1)
    
    return config
