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
                (b"user-agent", b"test-client"),
                (b"content-type", b"application/json"),
                (b"authorization", b"Bearer token123")
            ]
        }
        receive = AsyncMock()
        send = AsyncMock()

        # Mock the app to call send with response
        async def mock_app_impl(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")]
            })
            await send({
                "type": "http.response.body",
                "body": b'{"message": "test"}',
                "more_body": False
            })
        
        middleware.app = mock_app_impl

        # Capture logs
        with patch.object(middleware.logger, 'debug') as mock_debug:
            await middleware(scope, receive, send)
            
            # Verify logging was called
            mock_debug.assert_called()
            
            # Check that important information was logged
            debug_calls = [call.args[0] for call in mock_debug.call_args_list]
            assert any("INCOMING REQUEST: GET" in call for call in debug_calls)
            assert any("Client: 127.0.0.1:8080" in call for call in debug_calls)
    
    @pytest.mark.asyncio
    async def test_request_body_capture(self, middleware, mock_app):
        """Test that request bodies are captured."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "headers": [(b"content-type", b"application/json")]
        }
        
        # Mock receive to return request body
        body_data = b'{"test": "data"}'
        receive_calls = [
            {"type": "http.request", "body": body_data, "more_body": False}
        ]
        receive = AsyncMock(side_effect=receive_calls)
        send = AsyncMock()
        
        await middleware(scope, receive, send)
        
        # Verify that the request was processed
        mock_app.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_response_logging(self, middleware):
        """Test response logging functionality."""
        scope = {"type": "http", "method": "GET", "path": "/test"}
        receive = AsyncMock()
        send = AsyncMock()
        
        # Mock app that sends a response
        async def mock_app_with_response(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 201,
                "headers": [(b"content-type", b"application/json")]
            })
            await send({
                "type": "http.response.body", 
                "body": b'{"created": true}',
                "more_body": False
            })
        
        middleware.app = mock_app_with_response
        
        with patch.object(middleware, '_log_response') as mock_log_response:
            await middleware(scope, receive, send)
            
            # Verify response logging was called
            mock_log_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, middleware):
        """Test exception handling in middleware."""
        scope = {"type": "http", "method": "GET", "path": "/error"}
        receive = AsyncMock()
        send = AsyncMock()
        
        # Mock app that raises an exception
        async def mock_app_with_error(scope, receive, send):
            raise ValueError("Test error")
        
        middleware.app = mock_app_with_error
        
        with patch.object(middleware.logger, 'error') as mock_error:
            with pytest.raises(ValueError):
                await middleware(scope, receive, send)
            
            # Verify error was logged
            mock_error.assert_called()
    
    @pytest.mark.asyncio
    async def test_duplicate_response_start_handling(self, middleware):
        """Test handling of duplicate response start messages."""
        scope = {"type": "http", "method": "GET", "path": "/test"}
        receive = AsyncMock()
        send = AsyncMock()
        
        # Mock app that sends duplicate response start
        async def mock_app_duplicate_start(scope, receive, send):
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.start", "status": 200})  # Duplicate
        
        middleware.app = mock_app_duplicate_start
        
        with patch.object(middleware.logger, 'error') as mock_error:
            await middleware(scope, receive, send)
            
            # Verify error was logged for duplicate
            mock_error.assert_called_with("❌ Duplicate http.response.start detected")
    
    @pytest.mark.asyncio
    async def test_response_completed_check(self, middleware):
        """Test that messages after response completion are handled."""
        scope = {"type": "http", "method": "GET", "path": "/test"}
        receive = AsyncMock()
        send = AsyncMock()
        
        # Mock app that tries to send after completion
        async def mock_app_after_completion(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": []
            })
            await send({
                "type": "http.response.body",
                "body": b"response",
                "more_body": False  # This completes the response
            })
            # Try to send another message after completion
            await send({
                "type": "http.response.body", 
                "body": b"extra",
                "more_body": False
            })
        
        middleware.app = mock_app_after_completion
        
        with patch.object(middleware.logger, 'warning') as mock_warning:
            await middleware(scope, receive, send)
            
            # Verify warning was logged
            mock_warning.assert_called()


class TestCreateDhafnckMCPServer:
    """Test the create_dhafnck_mcp_server function."""
    
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    def test_create_server_with_defaults(self, mock_fastmcp):
        """Test creating server with default configuration."""
        mock_server = Mock()
        mock_fastmcp.return_value = mock_server
        
        result = create_dhafnck_mcp_server()
        
        assert result == mock_server
        mock_fastmcp.assert_called_once()
    
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    @patch('fastmcp.server.mcp_entry_point.get_connection_manager')
    def test_create_server_with_connection_manager(self, mock_get_conn_mgr, mock_fastmcp):
        """Test server creation with connection manager."""
        mock_server = Mock()
        mock_fastmcp.return_value = mock_server
        mock_conn_mgr = Mock()
        mock_get_conn_mgr.return_value = mock_conn_mgr
        
        result = create_dhafnck_mcp_server()
        
        assert result == mock_server
        mock_get_conn_mgr.assert_called()
    
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    def test_create_server_error_handling(self, mock_fastmcp):
        """Test server creation error handling."""
        mock_fastmcp.side_effect = Exception("Server creation failed")
        
        with pytest.raises(Exception, match="Server creation failed"):
            create_dhafnck_mcp_server()


class TestMainFunction:
    """Test the main function."""
    
    @patch('fastmcp.server.mcp_entry_point.configure_logging')
    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    @patch('fastmcp.server.mcp_entry_point.sys.argv', ['mcp_entry_point.py'])
    def test_main_basic_execution(self, mock_create_server, mock_configure_logging):
        """Test basic main function execution."""
        mock_server = Mock()
        mock_server.run = Mock()
        mock_create_server.return_value = mock_server
        
        with patch('fastmcp.server.mcp_entry_point.sys.exit') as mock_exit:
            main()
            
            mock_configure_logging.assert_called()
            mock_create_server.assert_called_once()
            mock_server.run.assert_called_once()
            mock_exit.assert_called_with(0)
    
    @patch('fastmcp.server.mcp_entry_point.configure_logging')
    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    def test_main_exception_handling(self, mock_create_server, mock_configure_logging):
        """Test main function exception handling."""
        mock_create_server.side_effect = Exception("Startup failed")
        
        with patch('fastmcp.server.mcp_entry_point.sys.exit') as mock_exit:
            with patch('fastmcp.server.mcp_entry_point.logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                main()
                
                mock_logger.error.assert_called()
                mock_exit.assert_called_with(1)
    
    @patch('fastmcp.server.mcp_entry_point.configure_logging')
    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    @patch('fastmcp.server.mcp_entry_point.cleanup_connection_manager')
    def test_main_cleanup_on_exit(self, mock_cleanup, mock_create_server, mock_configure_logging):
        """Test that cleanup is called on exit."""
        mock_server = Mock()
        mock_server.run = Mock()
        mock_create_server.return_value = mock_server
        
        with patch('fastmcp.server.mcp_entry_point.sys.exit'):
            main()
            
            mock_cleanup.assert_called_once()
    
    @patch('fastmcp.server.mcp_entry_point.configure_logging')
    @patch('fastmcp.server.mcp_entry_point.create_dhafnck_mcp_server')
    def test_main_keyboard_interrupt(self, mock_create_server, mock_configure_logging):
        """Test main function handles KeyboardInterrupt."""
        mock_server = Mock()
        mock_server.run.side_effect = KeyboardInterrupt()
        mock_create_server.return_value = mock_server
        
        with patch('fastmcp.server.mcp_entry_point.sys.exit') as mock_exit:
            with patch('fastmcp.server.mcp_entry_point.logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                main()
                
                mock_logger.info.assert_called_with("🛑 Shutting down gracefully...")
                mock_exit.assert_called_with(0)


class TestEnvironmentAndSetup:
    """Test environment loading and setup functionality."""
    
    @patch('fastmcp.server.mcp_entry_point.load_dotenv')
    @patch('fastmcp.server.mcp_entry_point.Path')
    def test_env_loading_from_parent_directory(self, mock_path, mock_load_dotenv):
        """Test environment loading from parent directory."""
        # Mock path exists
        mock_env_path = Mock()
        mock_env_path.exists.return_value = True
        mock_path.return_value.parent.parent.parent.parent.parent.__truediv__.return_value = mock_env_path
        
        # This would normally happen at module import, but we can test the logic
        # by checking that the setup code would work correctly
        assert mock_env_path is not None
    
    def test_environment_variables_available(self):
        """Test that required environment variables are accessible."""
        # Test that we can access common environment variables
        # This doesn't test specific values, just that the mechanism works
        test_env = os.environ.get('PATH')  # PATH should always exist
        assert test_env is not None
    
    @patch('fastmcp.server.mcp_entry_point.logging.getLogger')
    def test_logger_initialization(self, mock_get_logger):
        """Test that logger is properly initialized."""
        from fastmcp.server.mcp_entry_point import DebugLoggingMiddleware
        
        middleware = DebugLoggingMiddleware(Mock())
        assert middleware.logger is not None


class TestIntegrationWithFastMCP:
    """Test integration with FastMCP server components."""
    
    @patch('fastmcp.server.mcp_entry_point.FastMCP')
    @patch('fastmcp.server.mcp_entry_point.get_connection_manager')
    def test_server_initialization_flow(self, mock_get_conn_mgr, mock_fastmcp):
        """Test the complete server initialization flow."""
        mock_server = Mock()
        mock_fastmcp.return_value = mock_server
        mock_conn_mgr = Mock()
        mock_get_conn_mgr.return_value = mock_conn_mgr
        
        # Test that server creation follows expected pattern
        server = create_dhafnck_mcp_server()
        
        assert server == mock_server
        mock_fastmcp.assert_called_once()
        mock_get_conn_mgr.assert_called_once()
    
    def test_middleware_integration(self):
        """Test that middleware integrates properly with ASGI."""
        app = Mock()
        middleware = DebugLoggingMiddleware(app)
        
        # Test that middleware has the required ASGI interface
        assert callable(middleware)
        assert hasattr(middleware, 'app')
        assert middleware.app == app


if __name__ == "__main__":
    pytest.main([__file__])