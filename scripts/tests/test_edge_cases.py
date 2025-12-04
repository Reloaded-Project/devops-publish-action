"""
Tests for edge cases and error handling.
"""

import tempfile
from pathlib import Path

from .conftest import run_compress_script

class TestEmptyDirectory:
    """Test handling of empty directories."""
    
    def test_empty_artifacts_dir_handled_gracefully(self, temp_output_dir):
        """Test that empty artifacts directory is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / 'empty-artifacts'
            empty_dir.mkdir()
            
            # Should complete without error
            assert run_compress_script(str(empty_dir), str(temp_output_dir))
            
            # No archives should be created
            archives = list(temp_output_dir.glob('*'))
            assert len(archives) == 0, f"Unexpected archives created: {archives}"


class TestNonExistentDirectory:
    """Test handling of non-existent directories."""
    
    def test_nonexistent_dir_handled_gracefully(self, temp_output_dir):
        """Test that non-existent artifacts directory is handled gracefully."""
        # Should complete without error (exit 0)
        assert run_compress_script('/nonexistent/path/that/does/not/exist', str(temp_output_dir))


class TestEmptySubdirectory:
    """Test handling of empty subdirectories within artifacts."""
    
    def test_empty_subdir_skipped(self, temp_output_dir):
        """Test that empty subdirectories are skipped with a warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir) / 'artifacts'
            artifacts_dir.mkdir()
            
            # Create an empty subdirectory
            empty_subdir = artifacts_dir / 'empty-artifact'
            empty_subdir.mkdir()
            
            # Create a non-empty subdirectory
            non_empty_subdir = artifacts_dir / 'real-artifact'
            non_empty_subdir.mkdir()
            (non_empty_subdir / 'file.txt').write_text('content')
            
            # Should complete without error
            assert run_compress_script(str(artifacts_dir), str(temp_output_dir))
            
            # Only real-artifact.zip should be created
            archives = list(temp_output_dir.glob('*.zip'))
            assert len(archives) == 1
            assert archives[0].name == 'real-artifact.zip'
