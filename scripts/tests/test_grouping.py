"""
Tests for artifact grouping functionality.
"""

from .conftest import (
    get_archive_contents,
    run_compress_script,
    verify_files_at_root,
    verify_no_nested_parent,
    verify_subdirs_preserved,
)

class TestExplicitListGrouping:
    """Test explicit list grouping where directories are listed by name."""
    
    def test_grouped_archive_preserves_subdirs(self, temp_output_dir, symbols_bundled_path):
        """
        Test that explicit list grouping preserves subdirectory structure.
        
        Multiple directories grouped together should appear as subdirectories in the archive.
        """
        groups_yaml = '''
c-library:
  - c-library-linux-x64
  - c-library-windows-x64
  - c-library-macos-arm64
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        # Check c-library.zip exists
        c_lib_zip = temp_output_dir / 'c-library.zip'
        assert c_lib_zip.exists(), f"{c_lib_zip.name} not created"
        
        # Should have subdirectories
        assert verify_subdirs_preserved(c_lib_zip, [
            'c-library-linux-x64',
            'c-library-windows-x64', 
            'c-library-macos-arm64'
        ])


class TestPatternBasedGrouping:
    """Test pattern-based grouping using glob patterns."""
    
    def test_single_pattern(self, temp_output_dir, symbols_separate_path):
        """Test that a single glob pattern matches correct directories."""
        groups_yaml = '''
symbols:
  patterns:
    - "*.symbols"
'''
        
        assert run_compress_script(str(symbols_separate_path), str(temp_output_dir), groups=groups_yaml)
        
        symbols_zip = temp_output_dir / 'symbols.zip'
        assert symbols_zip.exists(), f"{symbols_zip.name} not created"
        
        assert verify_subdirs_preserved(symbols_zip, [
            'c-library-linux-x64.symbols',
            'c-library-windows-x64.symbols',
            'c-library-macos-arm64.symbols',
            'linux-x64.symbols',
            'windows-x64.symbols',
            'macos-arm64.symbols'
        ])
    
    def test_multiple_patterns_union(self, temp_output_dir, symbols_separate_path):
        """Test that multiple patterns create a union of matching directories."""
        groups_yaml = '''
x64-binaries:
  patterns:
    - "linux-x64"
    - "windows-x64"
'''
        
        assert run_compress_script(str(symbols_separate_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'x64-binaries.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        assert verify_subdirs_preserved(archive, ['linux-x64', 'windows-x64'])

    def test_patterns_with_excludes(self, temp_output_dir, symbols_separate_path):
        """Test that excludes filter out matching directories from pattern results."""
        groups_yaml = '''
non-symbol-libs:
  patterns:
    - "c-library-*"
    - "*-x64"
  excludes:
    - "*.symbols"
'''
        
        assert run_compress_script(str(symbols_separate_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'non-symbol-libs.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        contents = get_archive_contents(archive)
        
        # Should have c-library dirs and x64 dirs, but NOT .symbols ones
        expected_dirs = ['c-library-linux-x64', 'c-library-windows-x64', 'c-library-macos-arm64',
                        'linux-x64', 'windows-x64']
        assert verify_subdirs_preserved(archive, expected_dirs)
        
        # Verify no .symbols dirs
        for name in contents:
            assert '.symbols' not in name, f"Excluded .symbols dir found: {name}"


class TestMixedMode:
    """Test mixed mode with both grouped and individual archives."""
    
    def test_grouped_and_individual_coexist(self, temp_output_dir, symbols_bundled_path):
        """
        Test that mixed mode creates both grouped and individual archives.
        
        Directories matching groups are grouped; remaining dirs are compressed individually.
        """
        # Group c-library dirs, leave others individual
        groups_yaml = '''
c-library:
  patterns:
    - "c-library-*"
'''
        
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), groups=groups_yaml)
        
        # Should have c-library.zip (grouped)
        c_lib_zip = temp_output_dir / 'c-library.zip'
        assert c_lib_zip.exists(), f"Grouped archive {c_lib_zip.name} not created"
        
        # Should also have individual archives for non-c-library dirs
        expected_individual = ['linux-x64.zip', 'windows-x64.zip', 'macos-arm64.zip']
        for name in expected_individual:
            archive = temp_output_dir / name
            assert archive.exists(), f"Individual archive {name} not created"
        
        # Verify grouped archive has subdirs
        assert verify_subdirs_preserved(c_lib_zip, [
            'c-library-linux-x64',
            'c-library-windows-x64',
            'c-library-macos-arm64'
        ])
        
        # Verify individual archives have files at root
        linux_zip = temp_output_dir / 'linux-x64.zip'
        assert verify_files_at_root(linux_zip, ['prs-rs-cli'])
        assert verify_no_nested_parent(linux_zip, 'linux-x64')


class TestStringSyntax:
    """Test that patterns and excludes accept single strings (not just lists)."""
    
    def test_patterns_as_string(self, temp_output_dir, symbols_separate_path):
        """
        Test that patterns accepts a single string value.
        
        Using patterns: "*.symbols" (string) should work like patterns: ["*.symbols"] (list).
        """
        groups_yaml = '''
symbols:
  patterns: "*.symbols"
'''
        
        assert run_compress_script(str(symbols_separate_path), str(temp_output_dir), groups=groups_yaml)
        
        # Check symbols.zip exists
        symbols_zip = temp_output_dir / 'symbols.zip'
        assert symbols_zip.exists(), f"{symbols_zip.name} not created"
        
        # Should have all .symbols directories
        assert verify_subdirs_preserved(symbols_zip, [
            'c-library-linux-x64.symbols',
            'c-library-windows-x64.symbols',
            'c-library-macos-arm64.symbols',
            'linux-x64.symbols',
            'windows-x64.symbols',
            'macos-arm64.symbols'
        ])
    
    def test_excludes_as_string(self, temp_output_dir, symbols_separate_path):
        """
        Test that excludes accepts a single string value.
        
        Using excludes: "*.symbols" (string) should work like excludes: ["*.symbols"] (list).
        """
        groups_yaml = '''
non-symbol-x64:
  patterns:
    - "*-x64"
  excludes: "*.symbols"
'''
        
        assert run_compress_script(str(symbols_separate_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'non-symbol-x64.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        contents = get_archive_contents(archive)
        
        # Should have non-symbol x64 directories
        expected_dirs = ['c-library-linux-x64', 'c-library-windows-x64', 'linux-x64', 'windows-x64']
        assert verify_subdirs_preserved(archive, expected_dirs)
        
        # Verify no .symbols dirs
        for name in contents:
            assert '.symbols' not in name, f"Excluded .symbols dir found: {name}"
    
    def test_both_patterns_and_excludes_as_strings(self, temp_output_dir, symbols_separate_path):
        """
        Test that both patterns and excludes can be strings simultaneously.
        
        Using patterns: "*" and excludes: "*.symbols" should match all except .symbols dirs.
        """
        groups_yaml = '''
non-symbols:
  patterns: "*"
  excludes: "*.symbols"
'''
        
        assert run_compress_script(str(symbols_separate_path), str(temp_output_dir), groups=groups_yaml)
        
        archive = temp_output_dir / 'non-symbols.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        contents = get_archive_contents(archive)
        
        # Should have all non-symbol directories
        expected_dirs = [
            'c-library-linux-x64', 'c-library-windows-x64', 'c-library-macos-arm64',
            'linux-x64', 'windows-x64', 'macos-arm64'
        ]
        assert verify_subdirs_preserved(archive, expected_dirs)
        
        # Verify no .symbols dirs
        for name in contents:
            assert '.symbols' not in name, f"Excluded .symbols dir found: {name}"
