"""Test module for the FastMCP __init__ module."""
import pytest
from unittest.mock import patch, MagicMock


class TestFastMCPInit:
    """Test cases for the FastMCP initialization module."""
    
    def test_settings_initialized(self):
        """Test that settings are properly initialized."""
        from fastmcp import settings
        assert settings is not None
        assert hasattr(settings, '__class__')
        assert settings.__class__.__name__ == 'Settings'
    
    def test_exports(self):
        """Test that required exports are available."""
        import fastmcp
        assert hasattr(fastmcp, 'settings')
        assert hasattr(fastmcp, 'FastMCP')
        assert hasattr(fastmcp, 'Context')
    
    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        import fastmcp
        assert '__all__' in dir(fastmcp)
        assert 'settings' in fastmcp.__all__
        assert 'FastMCP' in fastmcp.__all__
        assert 'Context' in fastmcp.__all__
        assert len(fastmcp.__all__) == 3
    
    def test_version_attribute(self):
        """Test that version is set correctly."""
        import fastmcp
        assert hasattr(fastmcp, '__version__')
        assert isinstance(fastmcp.__version__, str)
        # Should be either the package version or fallback
        assert fastmcp.__version__ == "2.0.2.dev" or '.' in fastmcp.__version__
    
    @patch('fastmcp.version')
    def test_version_fallback(self, mock_version):
        """Test version fallback when package version is not available."""
        # Force an exception to trigger fallback
        mock_version.side_effect = Exception("Package not found")
        
        # Re-import to trigger the version logic
        import importlib
        import fastmcp
        importlib.reload(fastmcp)
        
        assert fastmcp.__version__ == "2.0.2.dev"
    
    def test_fastmcp_import(self):
        """Test that FastMCP can be imported from server module."""
        from fastmcp import FastMCP
        assert FastMCP is not None
        assert hasattr(FastMCP, '__name__')
    
    def test_context_import(self):
        """Test that Context can be imported from server module."""
        from fastmcp import Context
        assert Context is not None
        assert hasattr(Context, '__name__')
    
    def test_no_deprecated_imports(self):
        """Test that deprecated imports are not exposed."""
        import fastmcp
        # These should not be in the module
        assert not hasattr(fastmcp, 'Client')
        assert not hasattr(fastmcp, 'client')
        assert not hasattr(fastmcp, 'Image')