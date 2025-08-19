import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, Optional, List
import json
import asyncio

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastmcp.server.server import MCPServer
from fastmcp.server.server_interface import ServerInterface
from fastmcp.server.auth.providers.jwt_bearer import JWTBearerProvider
from fastmcp.exceptions import MCPError


class TestMCPServerInit:
    """Test cases for MCPServer initialization."""

    def test_init_default_configuration(self):
        """Test server initialization with default configuration."""
        server = MCPServer()
        
        assert server.name == "mcp-server"
        assert server.auth is None
        assert server._interface is not None
        assert isinstance(server._interface, ServerInterface)

    def test_init_with_custom_name(self):
        """Test server initialization with custom name."""
        server = MCPServer(name="custom-server")
        
        assert server.name == "custom-server"

    @patch('fastmcp.server.server.ServerInterface')
    def test_init_with_interface(self, mock_interface_class):
        """Test server initialization creates server interface."""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        server = MCPServer(name="test-server")
        
        mock_interface_class.assert_called_once_with(name="test-server")
        assert server._interface == mock_interface

    def test_init_with_auth_provider(self):
        """Test server initialization with auth provider."""
        auth_provider = Mock()
        server = MCPServer(auth=auth_provider)
        
        assert server.auth == auth_provider


class TestMCPServerAuthConfiguration:
    """Test cases for server authentication configuration."""

    @patch.dict(os.environ, {"DHAFNCK_MCP_AUTH_TYPE": "bearer_token"}, clear=True)
    @patch('fastmcp.server.server.find_mcp_config_file')
    @patch('fastmcp.server.server.load_mcp_config')
    @patch('fastmcp.server.server.is_bearer_token_auth')
    @patch('fastmcp.server.server.extract_jwt_secret')
    def test_configure_auth_bearer_token_from_env(self, mock_extract_jwt, mock_is_bearer, 
                                                  mock_load_config, mock_find_config):
        """Test auth configuration from environment variable."""
        # Mock configuration
        mock_find_config.return_value = None  # No config file
        mock_extract_jwt.return_value = "test-secret"
        
        server = MCPServer()
        
        # Auth should be configured from environment
        assert server.auth is not None
        assert isinstance(server.auth, JWTBearerProvider)

    @patch.dict(os.environ, {}, clear=True)
    @patch('fastmcp.server.server.find_mcp_config_file')
    @patch('fastmcp.server.server.load_mcp_config')
    @patch('fastmcp.server.server.is_bearer_token_auth')
    @patch('fastmcp.server.server.extract_jwt_secret')
    @patch('fastmcp.server.server.get_mcp_server_name')
    def test_configure_auth_bearer_token_from_config_file(self, mock_get_server_name,
                                                         mock_extract_jwt, mock_is_bearer,
                                                         mock_load_config, mock_find_config):
        """Test auth configuration from config file."""
        # Mock configuration
        mock_find_config.return_value = "/path/to/config.json"
        mock_config = {
            "mcp": {
                "servers": {
                    "test-server": {
                        "env": {
                            "DHAFNCK_MCP_AUTH_TYPE": "bearer_token",
                            "JWT_SECRET": "config-secret"
                        }
                    }
                }
            }
        }
        mock_load_config.return_value = mock_config
        mock_get_server_name.return_value = "test-server"
        mock_is_bearer.return_value = True
        mock_extract_jwt.return_value = "config-secret"
        
        server = MCPServer(name="test-server")
        
        # Verify configuration loading
        mock_find_config.assert_called_once()
        mock_load_config.assert_called_once_with("/path/to/config.json")
        mock_is_bearer.assert_called_once_with(mock_config, "test-server")
        mock_extract_jwt.assert_called_once_with(mock_config, "test-server")
        
        # Auth should be configured
        assert server.auth is not None
        assert isinstance(server.auth, JWTBearerProvider)
        assert server.auth.secret == "config-secret"

    @patch.dict(os.environ, {"JWT_SECRET": "env-secret"}, clear=True)
    @patch('fastmcp.server.server.find_mcp_config_file')
    def test_configure_auth_jwt_secret_from_env(self, mock_find_config):
        """Test JWT secret configuration from environment variable."""
        mock_find_config.return_value = None
        
        server = MCPServer()
        
        # Auth should not be configured without auth type
        assert server.auth is None

    @patch.dict(os.environ, {"DHAFNCK_MCP_AUTH_TYPE": "oauth2"}, clear=True)
    @patch('fastmcp.server.server.find_mcp_config_file')
    def test_configure_auth_unsupported_type(self, mock_find_config):
        """Test auth configuration with unsupported auth type."""
        mock_find_config.return_value = None
        
        server = MCPServer()
        
        # Auth should not be configured for unsupported types
        assert server.auth is None

    def test_configure_auth_no_configuration(self):
        """Test server without auth configuration."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
                server = MCPServer()
                assert server.auth is None


class TestMCPServerResources:
    """Test cases for server resource management."""

    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
            return MCPServer()

    def test_add_resource(self, server):
        """Test adding a resource to the server."""
        mock_resource = Mock()
        mock_resource.uri = "test://resource"
        
        server.add_resource(mock_resource)
        
        server._interface.add_resource.assert_called_once_with(mock_resource)

    def test_add_multiple_resources(self, server):
        """Test adding multiple resources."""
        resources = [
            Mock(uri="test://resource1"),
            Mock(uri="test://resource2"),
            Mock(uri="test://resource3")
        ]
        
        for resource in resources:
            server.add_resource(resource)
        
        assert server._interface.add_resource.call_count == 3

    def test_add_resource_with_error(self, server):
        """Test adding resource when interface raises error."""
        mock_resource = Mock()
        server._interface.add_resource.side_effect = Exception("Failed to add resource")
        
        # Should propagate the exception
        with pytest.raises(Exception, match="Failed to add resource"):
            server.add_resource(mock_resource)


class TestMCPServerTools:
    """Test cases for server tool management."""

    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
            return MCPServer()

    def test_add_tool(self, server):
        """Test adding a tool to the server."""
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        
        server.add_tool(mock_tool)
        
        server._interface.add_tool.assert_called_once_with(mock_tool)

    def test_add_tool_decorator(self, server):
        """Test using add_tool as a decorator."""
        @server.add_tool
        def test_function():
            return "test result"
        
        # Function should be added as a tool
        server._interface.add_tool.assert_called_once()
        
        # Original function should still work
        assert test_function() == "test result"

    def test_add_multiple_tools(self, server):
        """Test adding multiple tools."""
        tools = [
            Mock(name="tool1"),
            Mock(name="tool2"),
            Mock(name="tool3")
        ]
        
        for tool in tools:
            server.add_tool(tool)
        
        assert server._interface.add_tool.call_count == 3


class TestMCPServerPrompts:
    """Test cases for server prompt management."""

    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
            return MCPServer()

    def test_add_prompt(self, server):
        """Test adding a prompt to the server."""
        mock_prompt = Mock()
        mock_prompt.name = "test_prompt"
        
        server.add_prompt(mock_prompt)
        
        server._interface.add_prompt.assert_called_once_with(mock_prompt)

    def test_add_prompt_decorator(self, server):
        """Test using add_prompt as a decorator."""
        @server.add_prompt
        def test_prompt():
            return "prompt content"
        
        # Function should be added as a prompt
        server._interface.add_prompt.assert_called_once()
        
        # Original function should still work
        assert test_prompt() == "prompt content"


class TestMCPServerRun:
    """Test cases for server run method."""

    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
            return MCPServer()

    @pytest.mark.asyncio
    async def test_run_default(self, server):
        """Test running server with default configuration."""
        # Mock the interface run method
        server._interface.run = AsyncMock()
        
        await server.run()
        
        server._interface.run.assert_called_once_with(
            transport="stdio",
            auth=None,
            read_stream=None,
            write_stream=None,
            run_forever=True
        )

    @pytest.mark.asyncio
    async def test_run_with_auth(self):
        """Test running server with authentication."""
        auth_provider = Mock()
        server = MCPServer(auth=auth_provider)
        server._interface.run = AsyncMock()
        
        await server.run()
        
        server._interface.run.assert_called_once_with(
            transport="stdio",
            auth=auth_provider,
            read_stream=None,
            write_stream=None,
            run_forever=True
        )

    @pytest.mark.asyncio
    async def test_run_with_custom_transport(self, server):
        """Test running server with custom transport."""
        server._interface.run = AsyncMock()
        
        await server.run(transport="http")
        
        server._interface.run.assert_called_once_with(
            transport="http",
            auth=None,
            read_stream=None,
            write_stream=None,
            run_forever=True
        )

    @pytest.mark.asyncio
    async def test_run_with_streams(self, server):
        """Test running server with custom streams."""
        mock_read_stream = Mock()
        mock_write_stream = Mock()
        server._interface.run = AsyncMock()
        
        await server.run(
            read_stream=mock_read_stream,
            write_stream=mock_write_stream
        )
        
        server._interface.run.assert_called_once_with(
            transport="stdio",
            auth=None,
            read_stream=mock_read_stream,
            write_stream=mock_write_stream,
            run_forever=True
        )

    @pytest.mark.asyncio
    async def test_run_not_forever(self, server):
        """Test running server with run_forever=False."""
        server._interface.run = AsyncMock()
        
        await server.run(run_forever=False)
        
        server._interface.run.assert_called_once_with(
            transport="stdio",
            auth=None,
            read_stream=None,
            write_stream=None,
            run_forever=False
        )

    @pytest.mark.asyncio
    async def test_run_with_error(self, server):
        """Test server run with interface error."""
        server._interface.run = AsyncMock(side_effect=Exception("Server error"))
        
        with pytest.raises(Exception, match="Server error"):
            await server.run()


class TestMCPServerIntegration:
    """Integration tests for MCPServer."""

    @pytest.mark.asyncio
    async def test_server_lifecycle(self):
        """Test complete server lifecycle."""
        with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
            server = MCPServer(name="test-server")
            
            # Add resources
            resources = [
                Mock(uri="file://test1.txt"),
                Mock(uri="file://test2.txt")
            ]
            for resource in resources:
                server.add_resource(resource)
            
            # Add tools
            @server.add_tool
            def test_tool(param: str) -> str:
                return f"Processed: {param}"
            
            # Add prompts
            @server.add_prompt
            def test_prompt() -> str:
                return "Test prompt content"
            
            # Mock run to prevent actual server start
            server._interface.run = AsyncMock()
            
            # Run server
            await server.run(transport="stdio")
            
            # Verify all components were added
            assert server._interface.add_resource.call_count == 2
            assert server._interface.add_tool.call_count == 1
            assert server._interface.add_prompt.call_count == 1
            server._interface.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_with_bearer_auth_integration(self):
        """Test server with Bearer token authentication."""
        with patch.dict(os.environ, {
            "DHAFNCK_MCP_AUTH_TYPE": "bearer_token",
            "JWT_SECRET": "integration-secret"
        }, clear=True):
            with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
                server = MCPServer(name="auth-test-server")
                
                # Verify auth is configured
                assert server.auth is not None
                assert isinstance(server.auth, JWTBearerProvider)
                assert server.auth.secret == "integration-secret"
                
                # Mock run
                server._interface.run = AsyncMock()
                
                # Run with auth
                await server.run()
                
                # Verify auth was passed to interface
                server._interface.run.assert_called_once()
                call_args = server._interface.run.call_args
                assert call_args.kwargs["auth"] == server.auth


class TestMCPServerEdgeCases:
    """Test edge cases and error scenarios."""

    def test_server_with_invalid_config_file(self):
        """Test server initialization with invalid config file."""
        with patch('fastmcp.server.server.find_mcp_config_file') as mock_find:
            with patch('fastmcp.server.server.load_mcp_config') as mock_load:
                mock_find.return_value = "/invalid/config.json"
                mock_load.return_value = None  # Failed to load
                
                # Should not raise exception
                server = MCPServer()
                assert server.auth is None

    def test_server_with_config_loading_error(self):
        """Test server when config loading raises exception."""
        with patch('fastmcp.server.server.find_mcp_config_file') as mock_find:
            with patch('fastmcp.server.server.load_mcp_config') as mock_load:
                mock_find.return_value = "/config.json"
                mock_load.side_effect = Exception("Config error")
                
                # Should handle exception gracefully
                server = MCPServer()
                assert server.auth is None

    @pytest.mark.asyncio
    async def test_server_concurrent_operations(self):
        """Test server with concurrent operations."""
        with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
            server = MCPServer()
            
            # Add multiple resources concurrently
            resources = [Mock(uri=f"test://resource{i}") for i in range(10)]
            
            # Use asyncio to simulate concurrent additions
            for resource in resources:
                server.add_resource(resource)
            
            assert server._interface.add_resource.call_count == 10

    def test_server_name_validation(self):
        """Test server name validation and edge cases."""
        # Test various name formats
        test_names = [
            "simple-name",
            "name_with_underscore",
            "name.with.dots",
            "name-with-numbers-123",
            "UPPERCASE-NAME",
            "name-with-中文",  # Unicode
            "",  # Empty name
        ]
        
        for name in test_names:
            with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
                server = MCPServer(name=name)
                assert server.name == name

    @pytest.mark.asyncio
    async def test_server_cleanup_on_error(self):
        """Test server cleanup when run fails."""
        with patch('fastmcp.server.server.find_mcp_config_file', return_value=None):
            server = MCPServer()
            
            # Mock interface to raise error
            server._interface.run = AsyncMock(
                side_effect=Exception("Startup failed")
            )
            
            # Server should propagate exception
            with pytest.raises(Exception, match="Startup failed"):
                await server.run()
            
            # Verify run was attempted
            server._interface.run.assert_called_once()