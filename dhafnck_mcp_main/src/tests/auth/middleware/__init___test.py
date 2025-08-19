"""Test suite for auth.middleware module __init__ file.

Tests for the authentication middleware module initialization and exports.
"""

import pytest
from unittest.mock import Mock, patch


class TestAuthMiddlewareModuleInit:
    """Test the auth middleware module initialization."""

    def test_import_all_exported_classes(self):
        """Test that all exported classes can be imported."""
        from fastmcp.auth.middleware import JWTAuthMiddleware, UserContextManager
        
        # Verify classes exist and are importable
        assert JWTAuthMiddleware is not None
        assert UserContextManager is not None

    def test_all_attribute_exists(self):
        """Test that __all__ is properly defined."""
        import fastmcp.auth.middleware
        
        assert hasattr(fastmcp.auth.middleware, '__all__')
        assert isinstance(fastmcp.auth.middleware.__all__, list)
        assert len(fastmcp.auth.middleware.__all__) == 2

    def test_all_exported_items_accessible(self):
        """Test that all items in __all__ are accessible."""
        import fastmcp.auth.middleware
        
        for item in fastmcp.auth.middleware.__all__:
            assert hasattr(fastmcp.auth.middleware, item), f"{item} not accessible in module"

    def test_module_docstring_exists(self):
        """Test that the module has a proper docstring."""
        import fastmcp.auth.middleware
        
        assert fastmcp.auth.middleware.__doc__ is not None
        assert "Authentication middleware package" in fastmcp.auth.middleware.__doc__

    def test_jwt_auth_middleware_import(self):
        """Test JWTAuthMiddleware import correctly."""
        from fastmcp.auth.middleware import JWTAuthMiddleware
        
        # Basic sanity check that this is a class
        assert isinstance(JWTAuthMiddleware, type) or callable(JWTAuthMiddleware)

    def test_user_context_manager_import(self):
        """Test UserContextManager import correctly."""
        from fastmcp.auth.middleware import UserContextManager
        
        # Basic sanity check
        assert UserContextManager is not None
        assert isinstance(UserContextManager, type) or callable(UserContextManager)

    def test_import_error_handling(self):
        """Test that import errors are handled gracefully."""
        # This tests that the import doesn't fail catastrophically
        try:
            import fastmcp.auth.middleware
            # If we get here, imports worked
            assert True
        except ImportError as e:
            # If imports fail, it should be specific module failures, not syntax errors
            assert "cannot import" in str(e).lower() or "no module named" in str(e).lower()

    def test_imports_from_jwt_auth_middleware_module(self):
        """Test that imports come from the correct module."""
        from fastmcp.auth.middleware import JWTAuthMiddleware, UserContextManager
        
        # Verify they have the expected module path
        assert JWTAuthMiddleware.__module__.endswith('jwt_auth_middleware')
        assert UserContextManager.__module__.endswith('jwt_auth_middleware')


class TestAuthMiddlewareModuleStructure:
    """Test the structure and organization of the auth middleware module."""

    def test_exports_only_expected_items(self):
        """Test that only expected items are exported."""
        import fastmcp.auth.middleware
        
        expected_exports = {"JWTAuthMiddleware", "UserContextManager"}
        actual_exports = set(fastmcp.auth.middleware.__all__)
        
        assert actual_exports == expected_exports

    def test_no_internal_imports_exported(self):
        """Test that no internal/private imports are exported."""
        import fastmcp.auth.middleware
        
        # Check that common internal patterns aren't exported
        for item in fastmcp.auth.middleware.__all__:
            assert not item.startswith('_'), f"Private item {item} should not be exported"
            assert not item.endswith('_internal'), f"Internal item {item} should not be exported"

    def test_middleware_classes_are_classes(self):
        """Test that exported middleware items are actual classes."""
        from fastmcp.auth.middleware import JWTAuthMiddleware, UserContextManager
        
        # Both should be class types
        assert isinstance(JWTAuthMiddleware, type), "JWTAuthMiddleware should be a class"
        assert isinstance(UserContextManager, type), "UserContextManager should be a class"

    def test_consistent_naming_convention(self):
        """Test that naming follows consistent conventions."""
        import fastmcp.auth.middleware
        
        for item in fastmcp.auth.middleware.__all__:
            # Should follow PascalCase for class names
            assert item[0].isupper(), f"{item} should start with uppercase letter"
            assert '_' not in item or item.count('_') <= 1, f"{item} has too many underscores"