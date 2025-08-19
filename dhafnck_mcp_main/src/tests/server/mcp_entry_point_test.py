"""Tests for MCP Entry Point module."""

import pytest
import os
import sys
import json
import logging
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from starlette.responses import JSONResponse
from starlette.requests import Request

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastmcp.server.mcp_entry_point import (
    create_dhafnck_mcp_server,
    main,
    DebugLoggingMiddleware
)


class TestDebugLoggingMiddleware:
    """Test the DebugLoggingMiddleware class."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create a DebugLoggingMiddleware instance."""
        return DebugLoggingMiddleware(mock_app)

    @pytest.mark.asyncio
    async def test_non_http_passthrough(self, middleware, mock_app):
        """Test that non-HTTP requests are passed through."""
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)
        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_http_request_logging(self, middleware, mock_app):
        """Test HTTP request logging."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"param=value",
            "client": ["127.0.0.1", 8080],
            "server": ["localhost", 8000],
            "headers": [
                (b"user-agent", b"test-agent"),
                (b"content-type", b"application/json")
            ]
        }
        
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": b'{"test": "data"}'
        })
        
        send = AsyncMock()
        
        # Mock the app to send a response
        async def mock_app_handler(scope, receive_wrapper, send_wrapper):
            await send_wrapper({
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")]
            })
            await send_wrapper({
                "type": "http.response.body",
                "body": b'{"result": "success"}',
                "more_body": False
            })
        
        mock_app.side_effect = mock_app_handler

        with patch.object(middleware.logger, 'debug') as mock_debug:
            await middleware(scope, receive, send)
            
            # Verify logging calls were made
            assert mock_debug.called
            # Check that important log messages were generated
            log_messages = [call[0][0] for call in mock_debug.call_args_list]
            assert any("INCOMING REQUEST: GET" in msg for msg in log_messages)
            assert any("Client: 127.0.0.1:8080" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_error_response_logging(self, middleware, mock_app):
        """Test error response logging."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/error",
            "query_string": b"",
            "client": ["127.0.0.1", 8080],
            "server": ["localhost", 8000],
            "headers": []
        }
        
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": b""
        })
        
        send = AsyncMock()
        
        # Mock the app to send an error response
        async def mock_app_handler(scope, receive_wrapper, send_wrapper):
            await send_wrapper({
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"application/json")]
            })
            await send_wrapper({
                "type": "http.response.body",
                "body": b'{"error": "Internal Server Error"}',
                "more_body": False
            })
        
        mock_app.side_effect = mock_app_handler

        with patch.object(middleware.logger, 'error') as mock_error:
            await middleware(scope, receive, send)
            
            # Verify error logging was called
            assert mock_error.called
            error_messages = [call[0][0] for call in mock_error.call_args_list]
            assert any("ERROR RESPONSE: 500" in msg for msg in error_messages)


class TestCreateDhafnckMCPServer:
    """Test the create_dhafnck_mcp_server function."""

    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.server.mcp_entry_point.configure_logging')
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    def test_server_creation_basic(self, mock_fastmcp, mock_configure_logging, mock_init_db):
        """Test basic server creation."""
        # Setup mocks
        mock_server = Mock()
        mock_fastmcp.return_value = mock_server
        mock_server.tool = Mock(return_value=lambda x: x)
        mock_server.custom_route = Mock(return_value=lambda x: x)
        
        # Create server
        server = create_dhafnck_mcp_server()
        
        # Verify calls
        mock_configure_logging.assert_called_once()
        mock_init_db.assert_called_once()
        mock_fastmcp.assert_called_once()
        assert server == mock_server

    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    @patch.dict(os.environ, {'DHAFNCK_AUTH_ENABLED': 'true', 'SUPABASE_URL': 'https://test.supabase.co'})
    def test_server_with_auth_enabled(self, mock_fastmcp, mock_init_db):
        """Test server creation with authentication enabled."""
        mock_server = Mock()
        mock_server.tool = Mock(return_value=lambda x: x)
        mock_server.custom_route = Mock(return_value=lambda x: x)
        mock_fastmcp.return_value = mock_server
        
        server = create_dhafnck_mcp_server()
        
        # Verify auth tools were registered
        # Count number of times tool() was called for auth endpoints
        auth_tool_calls = [call for call in mock_server.tool.call_args_list]
        assert len(auth_tool_calls) >= 4  # validate_token, get_rate_limit_status, revoke_token, get_auth_status, generate_token

    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    @patch.dict(os.environ, {'DHAFNCK_AUTH_ENABLED': 'false'})
    def test_server_with_auth_disabled(self, mock_fastmcp, mock_init_db):
        """Test server creation with authentication disabled."""
        mock_server = Mock()
        mock_server.tool = Mock(return_value=lambda x: x)
        mock_server.custom_route = Mock(return_value=lambda x: x)
        mock_fastmcp.return_value = mock_server
        
        server = create_dhafnck_mcp_server()
        
        # Verify minimal tool calls (no auth tools)
        auth_tool_calls = [call for call in mock_server.tool.call_args_list]
        assert len(auth_tool_calls) == 0  # No auth tools should be registered

    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    def test_server_with_no_supabase_url(self, mock_fastmcp, mock_init_db):
        """Test server creation without Supabase URL forces auth disabled."""
        mock_server = Mock()
        mock_server.tool = Mock(return_value=lambda x: x)
        mock_server.custom_route = Mock(return_value=lambda x: x)
        mock_fastmcp.return_value = mock_server
        
        # Remove SUPABASE_URL if it exists
        with patch.dict(os.environ, {'SUPABASE_URL': ''}, clear=True):
            server = create_dhafnck_mcp_server()
        
        # Verify no auth tools were registered
        auth_tool_calls = [call for call in mock_server.tool.call_args_list]
        assert len(auth_tool_calls) == 0

    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    @patch('fastmcp.server.mcp_entry_point.DDDCompliantMCPTools')
    def test_ddd_tools_registration(self, mock_ddd_tools, mock_fastmcp, mock_init_db):
        """Test DDD-compliant tools registration."""
        mock_server = Mock()
        mock_server.tool = Mock(return_value=lambda x: x)
        mock_server.custom_route = Mock(return_value=lambda x: x)
        mock_fastmcp.return_value = mock_server
        
        mock_ddd_instance = Mock()
        mock_ddd_tools.return_value = mock_ddd_instance
        
        server = create_dhafnck_mcp_server()
        
        # Verify DDD tools were registered
        mock_ddd_tools.assert_called_once()
        mock_ddd_instance.register_tools.assert_called_once_with(mock_server)

    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    def test_health_endpoint_registration(self, mock_fastmcp, mock_init_db):
        """Test health endpoint is registered."""
        mock_server = Mock()
        mock_server.tool = Mock(return_value=lambda x: x)
        mock_server.custom_route = Mock(return_value=lambda x: x)
        mock_fastmcp.return_value = mock_server
        
        server = create_dhafnck_mcp_server()
        
        # Verify health endpoint was registered
        custom_route_calls = mock_server.custom_route.call_args_list
        assert any(call[0][0] == "/health" for call in custom_route_calls)

    @patch('fastmcp.task_management.infrastructure.database.init_database.init_database')
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    @patch('fastmcp.server.mcp_entry_point.get_connection_manager')
    @patch('fastmcp.server.connection_status_broadcaster.get_status_broadcaster')
    @pytest.mark.asyncio
    async def test_health_endpoint_functionality(self, mock_get_broadcaster, mock_get_conn_mgr, mock_fastmcp, mock_init_db):
        """Test health endpoint functionality."""
        # Create server and capture health endpoint
        mock_server = Mock()
        mock_server.tool = Mock(return_value=lambda x: x)
        health_handler = None
        
        def capture_health_handler(path, methods=None):
            def decorator(func):
                nonlocal health_handler
                if path == "/health":
                    health_handler = func
                return func
            return decorator
        
        mock_server.custom_route = capture_health_handler
        mock_fastmcp.return_value = mock_server
        
        # Setup connection manager mock
        mock_conn_mgr = AsyncMock()
        mock_conn_mgr.get_connection_stats = AsyncMock(return_value={
            "connections": {"active_connections": 5},
            "server_info": {"restart_count": 1, "uptime_seconds": 3600}
        })
        mock_conn_mgr.get_reconnection_info = AsyncMock(return_value={
            "recommended_action": "maintain_connection"
        })
        mock_get_conn_mgr.return_value = mock_conn_mgr
        
        # Setup status broadcaster mock
        mock_broadcaster = AsyncMock()
        mock_broadcaster.get_last_status = Mock(return_value={
            "event_type": "server_started",
            "timestamp": 1234567890
        })
        mock_broadcaster.get_client_count = Mock(return_value=3)
        mock_get_broadcaster.return_value = mock_broadcaster
        
        server = create_dhafnck_mcp_server()
        
        # Test health endpoint
        assert health_handler is not None
        
        mock_request = Mock(spec=Request)
        response = await health_handler(mock_request)
        
        assert isinstance(response, JSONResponse)
        # Get the response content
        response_data = json.loads(response.body.decode())
        
        assert response_data["status"] == "healthy"
        assert "timestamp" in response_data
        assert response_data["version"] == "2.1.0"
        assert "connections" in response_data
        assert response_data["connections"]["active_connections"] == 5


class TestMain:
    """Test the main function."""

    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    @patch('sys.argv', ['mcp_entry_point.py'])
    def test_main_stdio_mode(self, mock_create_server):
        """Test main function in stdio mode."""
        mock_server = Mock()
        mock_create_server.return_value = mock_server
        
        with patch.dict(os.environ, {'FASTMCP_TRANSPORT': 'stdio'}):
            main()
        
        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once_with(transport="stdio")

    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    @patch('sys.argv', ['mcp_entry_point.py'])
    def test_main_http_mode(self, mock_create_server):
        """Test main function in HTTP mode."""
        mock_server = Mock()
        mock_create_server.return_value = mock_server
        
        with patch.dict(os.environ, {
            'FASTMCP_TRANSPORT': 'streamable-http',
            'FASTMCP_HOST': '0.0.0.0',
            'FASTMCP_PORT': '9000'
        }):
            main()
        
        mock_create_server.assert_called_once()
        # Verify HTTP mode parameters
        call_kwargs = mock_server.run.call_args[1]
        assert call_kwargs['transport'] == 'streamable-http'
        assert call_kwargs['host'] == '0.0.0.0'
        assert call_kwargs['port'] == 9000
        assert 'middleware' in call_kwargs

    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    @patch('sys.argv', ['mcp_entry_point.py', '--transport', 'streamable-http'])
    def test_main_command_line_override(self, mock_create_server):
        """Test command line transport override."""
        mock_server = Mock()
        mock_create_server.return_value = mock_server
        
        with patch.dict(os.environ, {'FASTMCP_TRANSPORT': 'stdio'}):
            main()
        
        # Should use command line argument over environment variable
        call_kwargs = mock_server.run.call_args[1]
        assert call_kwargs['transport'] == 'streamable-http'

    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    def test_main_keyboard_interrupt(self, mock_create_server):
        """Test handling of keyboard interrupt."""
        mock_server = Mock()
        mock_server.run.side_effect = KeyboardInterrupt()
        mock_create_server.return_value = mock_server
        
        # Should not raise exception
        main()

    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    def test_main_exception_handling(self, mock_create_server):
        """Test handling of general exceptions."""
        mock_server = Mock()
        mock_server.run.side_effect = Exception("Test error")
        mock_create_server.return_value = mock_server
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])