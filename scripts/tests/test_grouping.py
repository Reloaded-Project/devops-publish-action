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
    
    def test_pattern_matches_directories(self, temp_output_dir, symbols_separate_path):
        """
        Test that pattern-based grouping matches correct directories.
        
        Using a glob pattern should group all matching directories.
        """
        groups_yaml = '''
symbols:
  pattern: "*.symbols"
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


class TestPatternWithExclusion:
    """Test pattern matching with exclusion lists."""
    
    def test_exclusion_filters_directories(self, temp_output_dir, symbols_separate_path):
        """
        Test that exclusion patterns work correctly.
        
        Exclude patterns should prevent matching directories from being included.
        """
        # Match all *-x64 directories but exclude *.symbols
        groups_yaml = '''
non-symbol-x64:
  pattern: "*-x64"
  exclude:
    - "*.symbols"
'''
        
        assert run_compress_script(str(symbols_separate_path), str(temp_output_dir), groups=groups_yaml)
        
        # Check archive exists
        archive = temp_output_dir / 'non-symbol-x64.zip'
        assert archive.exists(), f"{archive.name} not created"
        
        contents = get_archive_contents(archive)
        
        # Should have c-library-linux-x64, c-library-windows-x64, linux-x64, windows-x64
        expected_dirs = ['c-library-linux-x64', 'c-library-windows-x64', 'linux-x64', 'windows-x64']
        excluded_dirs = ['c-library-linux-x64.symbols', 'c-library-windows-x64.symbols', 
                        'linux-x64.symbols', 'windows-x64.symbols']
        
        assert verify_subdirs_preserved(archive, expected_dirs)
        
        # Verify excluded dirs are NOT present
        for excluded in excluded_dirs:
            assert not any(c.startswith(excluded + '/') for c in contents), \
                f"Excluded directory '{excluded}' found in archive"


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
  pattern: "c-library-*"
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
