"""
Tests for flattens functionality in artifact grouping.
"""

import tempfile
from pathlib import Path

from .conftest import (
    create_temp_artifacts,
    get_archive_contents,
    get_script_stderr,
    run_compress_script,
    verify_files_at_root,
    verify_subdirs_preserved,
)


class TestFlattensSinglePattern:
    """Test basic flatten behavior with a single pattern."""
    
    def test_flatten_single_pattern_string(self, temp_output_dir, symbols_bundled_path):
        """
        Test flattens as a string (not list) works correctly.
        """
        groups_yaml = '''
linux-bins:
  patterns: "linux-*"
  flattens: "linux-*"
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'linux-bins.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        # Files should be at root
        assert verify_files_at_root(archive, ['prs-rs-cli'])


class TestFlattensMixedMode:
    """Test partial flattening - some directories flattened, others preserved."""
    
    def test_flatten_subset_of_directories(self, temp_output_dir, symbols_bundled_path):
        """
        Test that only matched directories are flattened.
        
        linux-* should be flattened, c-library-* preserved as subdirs.
        """
        groups_yaml = '''
mixed:
  patterns:
    - "linux-*"
    - "c-library-linux-*"
  flattens: "linux-*"
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'mixed.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        contents = get_archive_contents(archive)
        
        # linux-x64 files should be at root (flattened)
        assert 'prs-rs-cli' in contents, "linux-x64 files should be flattened to root"
        
        # c-library-linux-x64 should be preserved as subdir
        c_lib_paths = [p for p in contents if p.startswith('c-library-linux-x64/')]
        assert c_lib_paths, "c-library-linux-x64 should be preserved as subdirectory"
    
    def test_flatten_multiple_patterns(self, temp_output_dir, symbols_bundled_path):
        """
        Test flattens with multiple patterns (list syntax).
        """
        groups_yaml = '''
binaries:
  patterns:
    - "linux-*"
    - "windows-*"
  flattens:
    - "linux-*"
    - "windows-*"
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'binaries.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        contents = get_archive_contents(archive)
        
        # Both linux-x64 and windows-x64 should be flattened
        # Files should be at root, not under linux-x64/ or windows-x64/
        for path in contents:
            assert not path.startswith('linux-x64/'), f"linux-x64 not flattened: {path}"
            assert not path.startswith('windows-x64/'), f"windows-x64 not flattened: {path}"


class TestFlattensConflictDetection:
    """Test conflict error message format when flattening would cause file collisions."""
    
    def test_conflict_error_message_lists_files(self, temp_output_dir):
        """
        Test that conflict error message includes file paths and sources.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'dir-a': {'config.json': '{}', 'shared.txt': 'a'},
                'dir-b': {'config.json': '{}', 'shared.txt': 'b'},
            })
            
            groups_yaml = '''
conflicting:
  patterns: "dir-*"
  flattens: "*"
'''
            
            stderr = get_script_stderr(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            # Check error message format
            assert "conflict" in stderr.lower()
            assert "config.json" in stderr or "shared.txt" in stderr
            assert "dir-a" in stderr
            assert "dir-b" in stderr


class TestFlattensNestedDirectories:
    """Test that macOS bundle structure is preserved when flattening."""
    
    def test_dSYM_structure_preserved(self, temp_output_dir, symbols_bundled_path):
        """
        Test that macOS .dSYM bundle structure is preserved when flattening.
        """
        groups_yaml = '''
macos:
  patterns: "macos-*"
  flattens: "*"
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'macos.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        contents = get_archive_contents(archive)
        
        # Should have prs-rs-cli at root (flattened)
        assert 'prs-rs-cli' in contents
        
        # .dSYM bundle structure should be preserved
        dsym_paths = [p for p in contents if '.dSYM/' in p]
        assert dsym_paths, "dSYM bundle paths should exist"
        # Check internal structure
        assert any('Contents/Info.plist' in p for p in dsym_paths), "dSYM internal structure preserved"


class TestFlattensBackwardCompatibility:
    """Test that flattens logic does not affect groups where it's not specified."""
    
    def test_no_flattens_allows_same_filenames_in_subdirs(self, temp_output_dir):
        """
        Test that without flattens, directories with same-named files coexist as subdirs.
        
        This verifies flattens logic isn't accidentally applied - if it were, this would
        cause a conflict error. Without flattens, files stay in separate subdirectories.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directories with conflicting filenames (would error if flattened)
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'dir-a': {'README.md': 'readme a'},
                'dir-b': {'README.md': 'readme b'},
            })
            
            # No flattens key - should NOT apply flattening
            groups_yaml = '''
grouped:
  patterns: "dir-*"
'''
            
            # Should succeed (not fail with conflict error)
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'grouped.zip'
            assert archive.exists(), f"{archive.name} not created"
            
            contents = get_archive_contents(archive)
            
            # Both files should exist in their respective subdirectories (not flattened)
            assert 'dir-a/README.md' in contents, "dir-a/README.md should be preserved in subdir"
            assert 'dir-b/README.md' in contents, "dir-b/README.md should be preserved in subdir"
    
    def test_list_syntax_ignores_flattens_patterns(self, temp_output_dir):
        """
        Test that list syntax ignores flattens (it's not supported for lists).
        
        Even if the directory names match what would be a flattens pattern,
        list syntax should always preserve subdirectory structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directories matching a potential flattens pattern
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'flatten-me-a': {'file-a.txt': 'content a'},
                'flatten-me-b': {'file-b.txt': 'content b'},
            })
            
            # List syntax - flattens key is ignored (not supported)
            groups_yaml = '''
grouped:
  - flatten-me-a
  - flatten-me-b
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'grouped.zip'
            assert archive.exists(), f"{archive.name} not created"
            
            contents = get_archive_contents(archive)
            
            # Files should be in subdirectories (not flattened to root)
            assert 'flatten-me-a/file-a.txt' in contents, "Should preserve subdir structure"
            assert 'flatten-me-b/file-b.txt' in contents, "Should preserve subdir structure"
            # Verify NOT flattened
            assert 'file-a.txt' not in contents, "Should not be flattened"
            assert 'file-b.txt' not in contents, "Should not be flattened"


class TestFlattensWithExcludes:
    """Test flattens combined with excludes."""
    
    def test_flattens_respects_excludes(self, temp_output_dir):
        """
        Test that excludes are applied before flattens.
        
        Excludes should filter directories, flattens only applies to included dirs.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directories where excludes and flattens interact
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'lib-linux': {'lib-linux.txt': 'linux lib'},
                'lib-windows': {'lib-windows.txt': 'windows lib'},
                'lib-linux.symbols': {'debug.txt': 'debug symbols'},
            })
            
            groups_yaml = '''
non-symbol-libs:
  patterns: "lib-*"
  excludes: "*.symbols"
  flattens: "*"
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'non-symbol-libs.zip'
            assert archive.exists(), f"{archive.name} not created"
            
            contents = get_archive_contents(archive)
            
            # No .symbols directories should be included
            for path in contents:
                assert '.symbols' not in path, f"Excluded .symbols dir found: {path}"
            
            # Files should be flattened - directory names should not appear as path prefixes
            # e.g., 'lib-linux/lib-linux.txt' would mean not flattened
            for path in contents:
                assert not path.startswith('lib-linux/'), f"lib-linux directory not flattened: {path}"
                assert not path.startswith('lib-windows/'), f"lib-windows directory not flattened: {path}"
            
            # Check expected files exist at root
            assert 'lib-linux.txt' in contents
            assert 'lib-windows.txt' in contents


class TestFlattensEdgeCases:
    """Test edge cases in flattens behavior."""
    
    def test_empty_flattens_list(self, temp_output_dir, symbols_bundled_path):
        """
        Test that empty flattens list behaves like no flattens.
        """
        groups_yaml = '''
c-library:
  patterns: "c-library-*"
  flattens: []
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'c-library.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        # Should preserve subdirectory structure
        assert verify_subdirs_preserved(archive, [
            'c-library-linux-x64',
            'c-library-windows-x64',
            'c-library-macos-arm64'
        ])
    
    def test_flattens_pattern_no_match(self, temp_output_dir, symbols_bundled_path):
        """
        Test that a flattens pattern matching nothing preserves all subdirs.
        """
        groups_yaml = '''
c-library:
  patterns: "c-library-*"
  flattens: "nonexistent-*"
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'c-library.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        # All directories should be preserved as subdirs
        assert verify_subdirs_preserved(archive, [
            'c-library-linux-x64',
            'c-library-windows-x64',
            'c-library-macos-arm64'
        ])
