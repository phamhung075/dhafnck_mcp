"""
Tests for auth MCP integration module imports and exports
"""

import pytest
from unittest.mock import patch, MagicMock


class TestMCPIntegrationImports:
    """Test suite for MCP integration module imports"""

    def test_imports_jwt_auth_backend(self):
        """Test that JWT auth backend components are imported"""
        from fastmcp.auth.mcp_integration import (
            JWTAuthBackend,
            MCPUserContext,
            create_jwt_auth_backend
        )
        
        # These should be imported from jwt_auth_backend module
        assert JWTAuthBackend is not None
        assert MCPUserContext is not None
        assert create_jwt_auth_backend is not None

    def test_imports_user_filtered_repository(self):
        """Test that UserFilteredRepository is imported"""
        from fastmcp.auth.mcp_integration import UserFilteredRepository
        
        assert UserFilteredRepository is not None

    def test_backward_compatibility_user_context_middleware(self):
        """Test backward compatibility import for UserContextMiddleware"""
        # Test successful import scenario
        mock_middleware_class = MagicMock()
        with patch('fastmcp.auth.mcp_integration.RequestContextMiddleware', mock_middleware_class):
            # Re-import to get the patched version
            import importlib
            import fastmcp.auth.mcp_integration
            importlib.reload(fastmcp.auth.mcp_integration)
            
            # Should have UserContextMiddleware as alias
            assert hasattr(fastmcp.auth.mcp_integration, 'UserContextMiddleware')
            if fastmcp.auth.mcp_integration.UserContextMiddleware is not None:
                assert fastmcp.auth.mcp_integration.UserContextMiddleware == mock_middleware_class

    def test_all_exports(self):
        """Test __all__ exports the expected names"""
        from fastmcp.auth import mcp_integration
        
        # Required exports
        required_exports = [
            "JWTAuthBackend",
            "MCPUserContext",
            "create_jwt_auth_backend",
            "UserFilteredRepository"
        ]
        
        for export in required_exports:
            assert export in mcp_integration.__all__
            assert hasattr(mcp_integration, export)

    def test_module_structure(self):
        """Test the module can be imported and has expected structure"""
        import fastmcp.auth.mcp_integration as mcp_integration
        
        # Check module attributes
        assert hasattr(mcp_integration, '__all__')
        assert isinstance(mcp_integration.__all__, list)
        
        # Check all exported names exist in module
        for name in mcp_integration.__all__:
            assert hasattr(mcp_integration, name)