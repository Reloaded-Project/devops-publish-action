"""
Tests for renames functionality in artifact grouping.
"""

import tempfile
from pathlib import Path

from .conftest import (
    create_temp_artifacts,
    get_archive_contents,
    get_script_stderr,
    run_compress_script,
    verify_subdirs_preserved,
)


class TestRenamesSingleRule:
    """Test basic rename behavior with a single rule."""
    
    def test_rename_removes_prefix(self, temp_output_dir):
        """
        Test that a rename rule can remove a prefix from directory names.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'C-Library-prs-rs-linux-x64': {'lib.so': 'linux lib'},
                'C-Library-prs-rs-windows-x64': {'lib.dll': 'windows lib'},
                'C-Library-prs-rs-macos-arm64': {'lib.dylib': 'macos lib'},
            })
            
            groups_yaml = '''
c-library:
  patterns: "C-Library-*"
  renames:
    - "C-Library-prs-rs-": ""
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'c-library.zip'
            assert archive.exists(), f"{archive.name} not created"
            
            contents = get_archive_contents(archive)
            
            # Directories should be renamed (prefix removed)
            assert 'linux-x64/lib.so' in contents, "linux-x64 should exist after rename"
            assert 'windows-x64/lib.dll' in contents, "windows-x64 should exist after rename"
            assert 'macos-arm64/lib.dylib' in contents, "macos-arm64 should exist after rename"
            
            # Original directory names should NOT exist
            for path in contents:
                assert not path.startswith('C-Library-'), f"Original prefix should be removed: {path}"
    
    def test_rename_replaces_substring(self, temp_output_dir):
        """
        Test that a rename rule can replace a substring in directory names.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'binary-linux-x64': {'app': 'linux app'},
                'binary-windows-x64': {'app.exe': 'windows app'},
            })
            
            groups_yaml = '''
binaries:
  patterns: "binary-*"
  renames:
    - "-x64": "-amd64"
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'binaries.zip'
            assert archive.exists(), f"{archive.name} not created"
            
            contents = get_archive_contents(archive)
            
            # Should have -amd64 suffix instead of -x64
            assert 'binary-linux-amd64/app' in contents, "linux-amd64 should exist after rename"
            assert 'binary-windows-amd64/app.exe' in contents, "windows-amd64 should exist after rename"
            
            # Original names should NOT exist
            for path in contents:
                assert '-x64/' not in path, f"Original -x64 suffix should be replaced: {path}"


class TestRenamesMultipleRules:
    """Test rename behavior with multiple rules."""
    
    def test_rename_multiple_rules_applied_in_order(self, temp_output_dir):
        """
        Test that multiple rename rules are applied in list order.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'prefix-middle-suffix': {'file.txt': 'content'},
            })
            
            # Rules applied in order: first remove prefix, then remove suffix
            groups_yaml = '''
test:
  patterns: "*"
  renames:
    - "prefix-": ""
    - "-suffix": ""
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'test.zip'
            assert archive.exists(), f"{archive.name} not created"
            
            contents = get_archive_contents(archive)
            
            # After both renames, only "middle" should remain
            assert 'middle/file.txt' in contents, "Only 'middle' should remain after both renames"
    
    def test_rename_chained_transformations(self, temp_output_dir):
        """
        Test that rename rules can be chained for complex transformations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'C-Library-prs-rs-linux-x64': {'lib.so': 'linux lib'},
            })
            
            # Chain: remove prefix, then replace x64 with amd64
            groups_yaml = '''
c-library:
  patterns: "C-Library-*"
  renames:
    - "C-Library-prs-rs-": ""
    - "-x64": "-amd64"
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'c-library.zip'
            contents = get_archive_contents(archive)
            
            # After both rules: "linux-amd64"
            assert 'linux-amd64/lib.so' in contents, "Chained renames should produce linux-amd64"


class TestRenamesWithFlattens:
    """Test renames combined with flattens."""
    
    def test_renames_applied_after_flattens(self, temp_output_dir):
        """
        Test that renames are applied after flattens.
        
        Flattened directories don't get renamed (their contents go to root).
        Only non-flattened directories get renamed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'C-Library-linux-x64': {'lib.so': 'linux lib'},
                'C-Library-windows-x64': {'lib.dll': 'windows lib'},
            })
            
            # Flatten linux, rename windows
            groups_yaml = '''
c-library:
  patterns: "C-Library-*"
  flattens: "C-Library-linux-*"
  renames:
    - "C-Library-": ""
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'c-library.zip'
            contents = get_archive_contents(archive)
            
            # Linux should be flattened (at root)
            assert 'lib.so' in contents, "Linux lib should be at root (flattened)"
            
            # Windows should be renamed (prefix removed)
            assert 'windows-x64/lib.dll' in contents, "Windows should be renamed to windows-x64"
            
            # Original C-Library- prefix should not exist in any path
            for path in contents:
                assert not path.startswith('C-Library-'), f"C-Library prefix should be removed: {path}"


class TestRenamesConflictDetection:
    """Test conflict detection when renames would cause duplicate names."""
    
    def test_rename_causing_conflict_fails(self, temp_output_dir):
        """
        Test that renames causing duplicate directory names fail with error.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'prefix-a-target': {'file-a.txt': 'content a'},
                'prefix-b-target': {'file-b.txt': 'content b'},
            })
            
            # This rename would cause both dirs to become "target"
            groups_yaml = '''
conflicting:
  patterns: "prefix-*"
  renames:
    - "prefix-a-": ""
    - "prefix-b-": ""
'''
            
            result = run_compress_script(
                str(artifacts_dir), str(temp_output_dir), 
                groups=groups_yaml, expect_failure=True
            )
            assert result, "Script should fail when renames cause conflicts"
    
    def test_rename_conflict_error_message(self, temp_output_dir):
        """
        Test that conflict error message includes relevant information.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'lib-a-common': {'file-a.txt': 'content a'},
                'lib-b-common': {'file-b.txt': 'content b'},
            })
            
            # Both would become "common" after rename
            groups_yaml = '''
conflicting:
  patterns: "lib-*"
  renames:
    - "lib-a-": ""
    - "lib-b-": ""
'''
            
            stderr = get_script_stderr(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            # Check error message format
            assert "conflict" in stderr.lower(), "Error should mention conflict"
            assert "common" in stderr, "Error should mention the conflicting name"


class TestRenamesEdgeCases:
    """Test edge cases in renames behavior."""
    
    def test_empty_renames_list(self, temp_output_dir):
        """
        Test that empty renames list behaves like no renames.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'dir-a': {'file.txt': 'content'},
            })
            
            groups_yaml = '''
test:
  patterns: "dir-*"
  renames: []
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'test.zip'
            contents = get_archive_contents(archive)
            
            # Directory should be unchanged
            assert 'dir-a/file.txt' in contents, "Directory should be unchanged with empty renames"
    
    def test_renames_no_match(self, temp_output_dir):
        """
        Test that directories not matching rename pattern remain unchanged.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'other-dir': {'file.txt': 'content'},
            })
            
            groups_yaml = '''
test:
  patterns: "*"
  renames:
    - "nonexistent-prefix-": ""
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'test.zip'
            contents = get_archive_contents(archive)
            
            # Directory should be unchanged (rename pattern didn't match)
            assert 'other-dir/file.txt' in contents, "Directory should be unchanged when rename doesn't match"
    
    def test_renames_only_top_level_dirs(self, temp_output_dir):
        """
        Test that only top-level directories are renamed, not nested dirs or files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'prefix-main': {
                    'prefix-file.txt': 'content',
                    'prefix-subdir': {'nested.txt': 'nested content'},
                },
            })
            
            groups_yaml = '''
test:
  patterns: "prefix-*"
  renames:
    - "prefix-": ""
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'test.zip'
            contents = get_archive_contents(archive)
            
            # Top-level dir should be renamed
            assert 'main/prefix-file.txt' in contents, "Top-level dir renamed, but file kept original name"
            assert 'main/prefix-subdir/nested.txt' in contents, "Nested dir should keep original name"
            
            # Original top-level dir name should NOT exist
            for path in contents:
                assert not path.startswith('prefix-main/'), f"Top-level dir should be renamed: {path}"
    
    def test_renames_replaces_all_occurrences(self, temp_output_dir):
        """
        Test that rename replaces ALL occurrences of the search string.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'aa-bb-aa': {'file.txt': 'content'},
            })
            
            groups_yaml = '''
test:
  patterns: "*"
  renames:
    - "aa": "XX"
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'test.zip'
            contents = get_archive_contents(archive)
            
            # Both occurrences of "aa" should be replaced
            assert 'XX-bb-XX/file.txt' in contents, "All occurrences should be replaced"


class TestRenamesListSyntaxIgnored:
    """Test that list syntax for groups ignores renames."""
    
    def test_list_syntax_ignores_renames(self, temp_output_dir):
        """
        Test that list syntax ignores renames (it's not supported for lists).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = create_temp_artifacts(Path(tmpdir), {
                'prefix-dir': {'file.txt': 'content'},
            })
            
            # List syntax - renames key is ignored
            groups_yaml = '''
grouped:
  - prefix-dir
'''
            
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir), groups=groups_yaml)
            
            archive = temp_output_dir / 'grouped.zip'
            contents = get_archive_contents(archive)
            
            # Directory should be preserved as-is (list syntax doesn't support renames)
            assert 'prefix-dir/file.txt' in contents, "List syntax should preserve dir structure"
