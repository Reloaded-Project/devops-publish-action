"""
Shared fixtures and utilities for compress_artifacts tests.
"""

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Set

import pytest

# Path to the compression script
SCRIPT_PATH = Path(__file__).parent.parent / 'compress-artifacts.py'

# Test data paths
TEST_DATA_ROOT = Path(__file__).parent.parent.parent / '.github' / 'workflows' / 'test-data' / 'rust'
SYMBOLS_SEPARATE = TEST_DATA_ROOT / 'symbols-separate'
SYMBOLS_BUNDLED = TEST_DATA_ROOT / 'symbols-bundled-simple'

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / 'output'
        output_dir.mkdir()
        yield output_dir


@pytest.fixture
def symbols_separate_path():
    """Path to symbols-separate test data."""
    return SYMBOLS_SEPARATE


@pytest.fixture
def symbols_bundled_path():
    """Path to symbols-bundled-simple test data."""
    return SYMBOLS_BUNDLED


def get_archive_contents(archive_path: Path) -> Set[str]:
    """Get the set of file paths within a zip archive."""
    with zipfile.ZipFile(archive_path, 'r') as zf:
        return set(zf.namelist())


def verify_files_at_root(archive_path: Path, expected_files: List[str]) -> bool:
    """
    Verify that expected files exist at the root of the archive (no parent directory).
    
    For ungrouped archives, files should be directly at root, not nested in a subdirectory.
    """
    contents = get_archive_contents(archive_path)
    for expected in expected_files:
        # File should be at root or be a directory at root
        # Note: Files appear directly in contents (e.g., "myapp.exe"), but directories
        # don't appear as standalone entries - only their contents do (e.g., "config/settings.json").
        # So we check: (1) if it's a file at root, or (2) if any paths start with "expected/" (directory at root)
        if expected not in contents and not any(c.startswith(expected + '/') for c in contents):
            print(f"  FAIL: Expected '{expected}' at archive root, not found")
            print(f"  Archive contents: {sorted(contents)}")
            return False
    return True


def verify_subdirs_preserved(archive_path: Path, expected_subdirs: List[str]) -> bool:
    """
    Verify that subdirectory structure is preserved in the archive.
    
    For grouped archives, files should be inside subdirectories matching the original dir names.
    """
    contents = get_archive_contents(archive_path)
    for subdir in expected_subdirs:
        # Check that at least one file exists under this subdirectory
        subdir_prefix = subdir + '/'
        has_files = any(c.startswith(subdir_prefix) for c in contents)
        if not has_files:
            print(f"  FAIL: Expected subdirectory '{subdir}' not found in archive")
            print(f"  Archive contents: {sorted(contents)}")
            return False
    return True


def verify_no_nested_parent(archive_path: Path, forbidden_prefix: str) -> bool:
    """
    Verify that files are NOT nested under a specific parent directory.
    
    This checks that the archive structure bug is fixed.
    """
    contents = get_archive_contents(archive_path)
    for item in contents:
        if item.startswith(forbidden_prefix + '/'):
            print(f"  FAIL: Found nested parent '{forbidden_prefix}' in archive")
            print(f"  Archive contents: {sorted(contents)}")
            return False
    return True


def run_compress_script(artifacts_dir: str, output_dir: str, groups: str = '', 
                        tool: str = 'zip', extra_args: str = '',
                        expect_failure: bool = False) -> bool:
    """
    Run the compression script with the given arguments.
    
    Args:
        artifacts_dir: Path to directory containing artifact subdirectories.
        output_dir: Path to output directory for compressed archives.
        groups: YAML grouping configuration (inline string or @filename).
                Supports explicit directory lists or 'patterns:' for glob matching.
        tool: Compression tool - 'zip' (default), '7z', or any archiver command.
              For 7z, auto-detects '7z' or '7zz' binary.
        extra_args: Additional arguments for the compression tool.
                    Examples: '-mx=9' for 7z max compression, '-9' for zip.
        expect_failure: If True, expect the script to fail (for conflict tests).
    
    Returns:
        True if script succeeded (or failed when expected), False otherwise.
    """
    cmd = [
        sys.executable, str(SCRIPT_PATH),
        '--artifacts-dir', artifacts_dir,
        '--output-dir', output_dir,
        '--tool', tool,
    ]
    if groups:
        cmd.extend(['--groups', groups])
    if extra_args:
        cmd.extend(['--args', extra_args])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if expect_failure:
        if result.returncode != 0:
            print(f"Script failed as expected")
            print(f"stderr: {result.stderr}")
            return True
        print(f"Script succeeded but expected failure")
        return False
    
    if result.returncode != 0:
        print(f"Script failed with return code {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    print(result.stdout)
    return True


def get_script_stderr(artifacts_dir: str, output_dir: str, groups: str = '', 
                      tool: str = 'zip', extra_args: str = '') -> str:
    """
    Run the compression script and return stderr output.
    
    Useful for checking error messages in conflict detection tests.
    """
    cmd = [
        sys.executable, str(SCRIPT_PATH),
        '--artifacts-dir', artifacts_dir,
        '--output-dir', output_dir,
        '--tool', tool,
    ]
    if groups:
        cmd.extend(['--groups', groups])
    if extra_args:
        cmd.extend(['--args', extra_args])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stderr


def create_temp_artifacts(temp_dir: Path, structure: dict) -> Path:
    """
    Create temporary artifact directories with known structure.
    
    Args:
        temp_dir: Base temp directory
        structure: Dict mapping dir_name -> {filename: content}
                   Supports nested dicts for subdirectories
    
    Returns:
        Path to the artifacts directory
    
    Example:
        create_temp_artifacts(tmp, {
            'dir-a': {'file.txt': 'content a'},
            'dir-b': {'file.txt': 'content b', 'subdir': {'nested.txt': 'nested'}}
        })
    """
    artifacts_dir = temp_dir / 'artifacts'
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    def create_contents(base_path: Path, contents: dict):
        for name, value in contents.items():
            path = base_path / name
            if isinstance(value, dict):
                path.mkdir(parents=True, exist_ok=True)
                create_contents(path, value)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value)
    
    for dir_name, contents in structure.items():
        dir_path = artifacts_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        create_contents(dir_path, contents)
    
    return artifacts_dir
