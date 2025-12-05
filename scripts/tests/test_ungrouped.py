"""
Tests for ungrouped (individual) artifact compression.
"""

from .conftest import (
    run_compress_script,
    verify_files_at_root,
    verify_no_nested_parent,
)

class TestUngroupedCompression:
    """Test ungrouped compression where each directory becomes a separate archive."""
    
    def test_files_at_archive_root(self, temp_output_dir, symbols_bundled_path):
        """
        Test that ungrouped compression produces files at archive root.
        
        Each artifact directory should become a separate archive with files at root,
        not nested under the original directory name.
        """
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir))
        
        # Check linux-x64.zip - should have files at root
        linux_zip = temp_output_dir / 'linux-x64.zip'
        assert linux_zip.exists(), f"{linux_zip.name} not created"
        
        # Files should be at root, not under linux-x64/
        assert verify_files_at_root(linux_zip, ['prs-rs-cli', 'prs-rs-cli.dwp'])
        
        # Verify NO nested parent directory
        assert verify_no_nested_parent(linux_zip, 'linux-x64')
    
    def test_windows_archive_structure(self, temp_output_dir, symbols_bundled_path):
        """Test Windows artifact archive has correct structure."""
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir))
        
        windows_zip = temp_output_dir / 'windows-x64.zip'
        assert windows_zip.exists(), f"{windows_zip.name} not created"
        
        assert verify_files_at_root(windows_zip, ['prs-rs-cli.exe', 'prs_rs_cli.pdb'])
        assert verify_no_nested_parent(windows_zip, 'windows-x64')
    
    def test_macos_archive_with_dsym(self, temp_output_dir, symbols_bundled_path):
        """Test macOS artifact archive preserves .dSYM bundle."""
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir))
        
        macos_zip = temp_output_dir / 'macos-arm64.zip'
        assert macos_zip.exists(), f"{macos_zip.name} not created"
        
        # Should have the executable and the dSYM directory at root
        assert verify_files_at_root(macos_zip, ['prs-rs-cli', 'prs-rs-cli.dSYM'])
        assert verify_no_nested_parent(macos_zip, 'macos-arm64')
    
    def test_all_expected_archives_created(self, temp_output_dir, symbols_bundled_path):
        """Test that all expected archives are created."""
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir))
        
        expected_archives = [
            'linux-x64.zip',
            'windows-x64.zip',
            'macos-arm64.zip',
            'c-library-linux-x64.zip',
            'c-library-windows-x64.zip',
            'c-library-macos-arm64.zip',
        ]
        
        for name in expected_archives:
            archive = temp_output_dir / name
            assert archive.exists(), f"Expected archive {name} not created"
