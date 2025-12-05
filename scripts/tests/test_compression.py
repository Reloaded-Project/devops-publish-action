"""
Tests for compression tool configuration and arguments.
"""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from .conftest import (
    run_compress_script,
)

# Add parent to path for module imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from compress_artifacts.compression import resolve_7z_binary


class TestCompressionArgs:
    """Test compression argument handling."""
    
    def test_compression_args_create_valid_archives(self, temp_output_dir, symbols_bundled_path):
        """
        Test that compression args are passed to the tool.
        
        Extra arguments should be included in the compression command.
        """
        # Test with -9 compression level
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), extra_args='-9')
        
        # Just verify archives were created (we can't easily verify -9 was used)
        archives = list(temp_output_dir.glob('*.zip'))
        assert len(archives) > 0, "No archives created"


class Test7zDetection:
    """Test 7z/7zz binary detection."""
    
    def test_resolve_7z_prefers_7z(self):
        """Test that resolve_7z_binary prefers '7z' over '7zz'."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda x: '/usr/bin/7z' if x == '7z' else None
            assert resolve_7z_binary() == '7z'
    
    def test_resolve_7z_falls_back_to_7zz(self):
        """Test that resolve_7z_binary falls back to '7zz' when '7z' not found."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda x: '/usr/bin/7zz' if x == '7zz' else None
            assert resolve_7z_binary() == '7zz'
    
    def test_resolve_7z_raises_when_not_found(self):
        """Test that resolve_7z_binary raises FileNotFoundError when neither found."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None
            with pytest.raises(FileNotFoundError, match="Neither '7z' nor '7zz' found"):
                resolve_7z_binary()
    
    @pytest.mark.skipif(
        not shutil.which('7z') and not shutil.which('7zz'),
        reason="Neither 7z nor 7zz is installed"
    )
    def test_7z_tool_creates_archive(self, temp_output_dir, symbols_bundled_path):
        """Test that 7z tool creates valid archives when available."""
        assert run_compress_script(str(symbols_bundled_path), str(temp_output_dir), tool='7z')
        
        # Check for .7z files
        archives = list(temp_output_dir.glob('*.7z'))
        assert len(archives) > 0, "No .7z archives created"
