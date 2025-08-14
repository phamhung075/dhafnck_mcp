"""
Simple integration tests for the Unified Context System.

Tests the basic functionality that's actually implemented.
"""

import pytest
from unittest.mock import Mock

from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory


class TestUnifiedContextIntegrationSimple:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Simple integration tests for the unified context system."""
    
    def test_controller_creation(self):
        """Test that we can create the controller without circular imports."""
        # Create facade factory
        facade_factory = Mock(spec=UnifiedContextFacadeFactory)
        
        # Create controller
        controller = UnifiedContextMCPController(unified_context_facade_factory=facade_factory)
        
        # Verify controller was created
        assert controller is not None
        assert controller._facade_factory == facade_factory
    
    def test_facade_factory_creation(self):
        """Test that we can create the facade factory."""
        # Mock session factory
        session_factory = Mock()
        
        # This should not raise any import errors
        try:
            facade_factory = UnifiedContextFacadeFactory(session_factory=session_factory)
            assert facade_factory is not None
        except ImportError as e:
            pytest.fail(f"Import error when creating UnifiedContextFacadeFactory: {e}")
    
    def test_facade_creation(self):
        """Test that we can create a facade through the factory."""
        # Mock session factory
        session_factory = Mock()
        
        try:
            facade_factory = UnifiedContextFacadeFactory(session_factory=session_factory)
            facade = facade_factory.create_facade()
            assert facade is not None
        except ImportError as e:
            pytest.fail(f"Import error when creating facade: {e}")
    
    def test_mcp_tool_registration(self):
        """Test that the controller can register tools with MCP."""
        # Create mock MCP
        mcp = Mock()
        tools_registered = []
        
        def mock_tool(name=None, description=None):
            def decorator(func):
                tools_registered.append(name)
                return func
            return decorator
        
        mcp.tool = mock_tool
        
        # Create controller
        facade_factory = Mock(spec=UnifiedContextFacadeFactory)
        controller = UnifiedContextMCPController(unified_context_facade_factory=facade_factory)
        
        # Register tools
        controller.register_tools(mcp)
        
        # Verify manage_context tool was registered
        assert "manage_context" in tools_registered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])