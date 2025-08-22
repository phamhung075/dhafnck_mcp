"""
Test cases for Debug Service utility.
"""

import pytest
import json
import logging
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from fastmcp.utilities.debug_service import (
    DebugService, debug_service, log_request, log_response,
    log_api_v2_request, log_api_v2_response, log_auth_event,
    log_database_event, log_frontend_issue, debug_decorator,
    is_debug_enabled, get_debug_status
)


class TestDebugService:
    """Test cases for DebugService class."""
    
    @pytest.fixture
    def mock_env(self):
        """Mock environment variables."""
        env_vars = {
            "DEBUG_SERVICE_ENABLED": "true",
            "DEBUG_HTTP_REQUESTS": "true",
            "DEBUG_API_V2": "true",
            "DEBUG_MCP_TOOLS": "true",
            "DEBUG_AUTHENTICATION": "true",
            "DEBUG_DATABASE": "true",
            "DEBUG_FRONTEND_ISSUES": "true",
            "DEBUG_VERBOSE": "true",
            "DEBUG_STACK_TRACES": "true"
        }
        with patch.dict('os.environ', env_vars):
            yield env_vars
    
    @pytest.fixture
    def mock_env_disabled(self):
        """Mock environment with debug disabled."""
        env_vars = {
            "DEBUG_SERVICE_ENABLED": "false",
            "DEBUG_HTTP_REQUESTS": "false",
            "DEBUG_API_V2": "false",
            "DEBUG_MCP_TOOLS": "false",
            "DEBUG_AUTHENTICATION": "false",
            "DEBUG_DATABASE": "false",
            "DEBUG_FRONTEND_ISSUES": "false",
            "DEBUG_VERBOSE": "false",
            "DEBUG_STACK_TRACES": "false"
        }
        with patch.dict('os.environ', env_vars):
            yield env_vars
    
    @pytest.fixture
    def debug_service_enabled(self, mock_env):
        """Create debug service with all features enabled."""
        return DebugService()
    
    @pytest.fixture
    def debug_service_disabled(self, mock_env_disabled):
        """Create debug service with all features disabled."""
        return DebugService()
    
    def test_initialization_enabled(self, debug_service_enabled):
        """Test initialization with debug enabled."""
        assert debug_service_enabled.debug_enabled is True
        assert debug_service_enabled.debug_http is True
        assert debug_service_enabled.debug_api_v2 is True
        assert debug_service_enabled.debug_mcp is True
        assert debug_service_enabled.debug_auth is True
        assert debug_service_enabled.debug_database is True
        assert debug_service_enabled.debug_frontend is True
        assert debug_service_enabled.debug_verbose is True
        assert debug_service_enabled.debug_stack_traces is True
    
    def test_initialization_disabled(self, debug_service_disabled):
        """Test initialization with debug disabled."""
        assert debug_service_disabled.debug_enabled is False
        assert debug_service_disabled.debug_http is False
        assert debug_service_disabled.debug_api_v2 is False
        assert debug_service_disabled.debug_mcp is False
        assert debug_service_disabled.debug_auth is False
        assert debug_service_disabled.debug_database is False
        assert debug_service_disabled.debug_frontend is False
        assert debug_service_disabled.debug_verbose is False
        assert debug_service_disabled.debug_stack_traces is False
    
    def test_is_enabled_categories(self, debug_service_enabled):
        """Test is_enabled for different categories."""
        assert debug_service_enabled.is_enabled("general") is True
        assert debug_service_enabled.is_enabled("http") is True
        assert debug_service_enabled.is_enabled("api_v2") is True
        assert debug_service_enabled.is_enabled("mcp") is True
        assert debug_service_enabled.is_enabled("auth") is True
        assert debug_service_enabled.is_enabled("database") is True
        assert debug_service_enabled.is_enabled("frontend") is True
        assert debug_service_enabled.is_enabled("unknown") is False
    
    def test_is_enabled_when_disabled(self, debug_service_disabled):
        """Test is_enabled returns False when debug is disabled."""
        assert debug_service_disabled.is_enabled("general") is False
        assert debug_service_disabled.is_enabled("http") is False
        assert debug_service_disabled.is_enabled("api_v2") is False
    
    def test_log_request(self, debug_service_enabled):
        """Test HTTP request logging."""
        with patch.object(debug_service_enabled.http_logger, 'debug') as mock_debug:
            headers = {
                "authorization": "Bearer token1234567890abcdef",
                "content-type": "application/json",
                "user-agent": "TestClient/1.0"
            }
            body = json.dumps({"test": "data"})
            
            debug_service_enabled.log_request("POST", "/api/test", headers, body, "192.168.1.1")
            
            # Verify logging calls
            assert mock_debug.call_count >= 5
            mock_debug.assert_any_call("=" * 80)
            mock_debug.assert_any_call("🌐 HTTP REQUEST: POST /api/test")
            mock_debug.assert_any_call("📍 Client IP: 192.168.1.1")
            
            # Check authorization masking
            auth_calls = [call for call in mock_debug.call_args_list if "Bearer" in str(call)]
            assert any("Bearer token1234...90abcdef" in str(call) for call in auth_calls)
    
    def test_log_request_no_body(self, debug_service_enabled):
        """Test HTTP request logging without body."""
        with patch.object(debug_service_enabled.http_logger, 'debug') as mock_debug:
            headers = {"content-type": "text/plain"}
            
            debug_service_enabled.log_request("GET", "/api/test", headers, None)
            
            assert mock_debug.call_count >= 3
            # Should not log body
            body_calls = [call for call in mock_debug.call_args_list if "Request Body" in str(call)]
            assert len(body_calls) == 0
    
    def test_log_request_disabled(self, debug_service_disabled):
        """Test that logging doesn't occur when disabled."""
        with patch.object(debug_service_disabled.http_logger, 'debug') as mock_debug:
            debug_service_disabled.log_request("GET", "/api/test", {})
            
            mock_debug.assert_not_called()
    
    def test_log_response(self, debug_service_enabled):
        """Test HTTP response logging."""
        with patch.object(debug_service_enabled.http_logger, 'debug') as mock_debug:
            headers = {"content-type": "application/json"}
            body = json.dumps({"result": "success"})
            
            debug_service_enabled.log_response(200, headers, body, 0.123)
            
            assert mock_debug.call_count >= 4
            mock_debug.assert_any_call("✅ RESPONSE: 200 (0.123s)")
            mock_debug.assert_any_call("=" * 80)
    
    def test_log_response_error_status(self, debug_service_enabled):
        """Test HTTP response logging with error status."""
        with patch.object(debug_service_enabled.http_logger, 'debug') as mock_debug:
            debug_service_enabled.log_response(500, {}, None, 0.456)
            
            mock_debug.assert_any_call("❌ RESPONSE: 500 (0.456s)")
    
    def test_log_api_v2_request(self, debug_service_enabled):
        """Test API V2 request logging."""
        with patch.object(debug_service_enabled.api_logger, 'debug') as mock_debug:
            params = {"project_id": "123", "status": "active"}
            
            debug_service_enabled.log_api_v2_request(
                "/tasks/list", "user-456", "GET", params
            )
            
            assert mock_debug.call_count >= 4
            mock_debug.assert_any_call("🔗 API V2 REQUEST: GET /tasks/list")
            mock_debug.assert_any_call("👤 User ID: user-456")
    
    def test_log_api_v2_response_success(self, debug_service_enabled):
        """Test API V2 response logging for success."""
        with patch.object(debug_service_enabled.api_logger, 'debug') as mock_debug:
            data = {
                "tasks": [
                    {"title": "Task 1", "status": "active"},
                    {"title": "Task 2", "status": "completed"}
                ]
            }
            
            debug_service_enabled.log_api_v2_response("/tasks/list", True, data)
            
            mock_debug.assert_any_call("✅ API V2 RESPONSE: /tasks/list")
            mock_debug.assert_any_call("📋 Tasks returned: 2")
            mock_debug.assert_any_call("📝 First task: Task 1 [active]")
    
    def test_log_api_v2_response_error(self, debug_service_enabled):
        """Test API V2 response logging for errors."""
        with patch.object(debug_service_enabled.api_logger, 'debug') as mock_debug:
            debug_service_enabled.log_api_v2_response(
                "/tasks/create", False, None, "Validation failed"
            )
            
            mock_debug.assert_any_call("❌ API V2 RESPONSE: /tasks/create")
            mock_debug.assert_any_call("🚨 Error: Validation failed")
    
    def test_log_auth_event(self, debug_service_enabled):
        """Test authentication event logging."""
        with patch.object(debug_service_enabled.auth_logger, 'debug') as mock_debug:
            token_info = {
                "valid": True,
                "expires_at": "2024-12-31T23:59:59Z",
                "usage_count": 42
            }
            
            debug_service_enabled.log_auth_event(
                "token_validated", "user-789", token_info
            )
            
            mock_debug.assert_any_call("🔐 AUTH EVENT: token_validated")
            mock_debug.assert_any_call("👤 User ID: user-789")
            
            # Check that safe token info is logged
            token_calls = [call for call in mock_debug.call_args_list if "Token Info" in str(call)]
            assert len(token_calls) > 0
    
    def test_log_auth_event_with_error(self, debug_service_enabled):
        """Test authentication event logging with error."""
        with patch.object(debug_service_enabled.auth_logger, 'debug') as mock_debug:
            with patch('traceback.format_exc', return_value="Stack trace here"):
                debug_service_enabled.log_auth_event(
                    "login_failed", error="Invalid credentials"
                )
                
                mock_debug.assert_any_call("🚨 Auth Error: Invalid credentials")
                mock_debug.assert_any_call("🔍 Stack Trace:")
    
    def test_log_database_event(self, debug_service_enabled):
        """Test database event logging."""
        with patch.object(debug_service_enabled.db_logger, 'debug') as mock_debug:
            query_info = {"filter": {"status": "active"}, "limit": 10}
            
            debug_service_enabled.log_database_event(
                "SELECT", "tasks", query_info, result_count=5
            )
            
            mock_debug.assert_any_call("💾 DATABASE: SELECT")
            mock_debug.assert_any_call("📊 Table: tasks")
            mock_debug.assert_any_call("📊 Results: 5 rows")
    
    def test_log_database_event_with_error(self, debug_service_enabled):
        """Test database event logging with error."""
        with patch.object(debug_service_enabled.db_logger, 'debug') as mock_debug:
            with patch('traceback.format_exc', return_value="DB stack trace"):
                debug_service_enabled.log_database_event(
                    "INSERT", "users", error="Unique constraint violation"
                )
                
                mock_debug.assert_any_call("🚨 DB Error: Unique constraint violation")
                stack_calls = [call for call in mock_debug.call_args_list if "Stack Trace" in str(call)]
                assert len(stack_calls) > 0
    
    def test_log_frontend_issue(self, debug_service_enabled):
        """Test frontend issue logging."""
        with patch.object(debug_service_enabled.logger, 'debug') as mock_debug:
            details = {"error": "Network timeout", "endpoint": "/api/tasks"}
            user_context = {"browser": "Chrome", "version": "120.0"}
            
            debug_service_enabled.log_frontend_issue(
                "API_ERROR", details, user_context
            )
            
            mock_debug.assert_any_call("🖥️ FRONTEND ISSUE: API_ERROR")
            # Check JSON dumps were called
            detail_calls = [call for call in mock_debug.call_args_list if "Issue Details" in str(call)]
            assert len(detail_calls) > 0
    
    def test_debug_decorator_enabled(self, debug_service_enabled):
        """Test debug decorator when enabled."""
        with patch.object(debug_service_enabled.logger, 'debug') as mock_debug:
            @debug_service_enabled.debug_decorator("general")
            def test_function(x, y):
                return x + y
            
            result = test_function(2, 3)
            
            assert result == 5
            mock_debug.assert_any_call("🔧 CALLING: test_function")
            # Check for completion log
            completion_calls = [call for call in mock_debug.call_args_list if "COMPLETED" in str(call)]
            assert len(completion_calls) > 0
    
    def test_debug_decorator_with_exception(self, debug_service_enabled):
        """Test debug decorator with exception."""
        with patch.object(debug_service_enabled.logger, 'debug') as mock_debug:
            @debug_service_enabled.debug_decorator("general")
            def failing_function():
                raise ValueError("Test error")
            
            with pytest.raises(ValueError):
                failing_function()
            
            mock_debug.assert_any_call("🔧 CALLING: failing_function")
            # Check for failure log
            failure_calls = [call for call in mock_debug.call_args_list if "FAILED" in str(call)]
            assert len(failure_calls) > 0
    
    def test_debug_decorator_disabled(self, debug_service_disabled):
        """Test debug decorator when disabled."""
        with patch.object(debug_service_disabled.logger, 'debug') as mock_debug:
            @debug_service_disabled.debug_decorator("general")
            def test_function(x):
                return x * 2
            
            result = test_function(5)
            
            assert result == 10
            mock_debug.assert_not_called()
    
    def test_get_debug_status(self, debug_service_enabled):
        """Test getting debug status."""
        status = debug_service_enabled.get_debug_status()
        
        assert status["debug_enabled"] is True
        assert status["categories"]["http"] is True
        assert status["categories"]["api_v2"] is True
        assert status["categories"]["mcp"] is True
        assert status["categories"]["auth"] is True
        assert status["categories"]["database"] is True
        assert status["categories"]["frontend"] is True
        assert status["options"]["verbose"] is True
        assert status["options"]["stack_traces"] is True
    
    def test_partial_debug_configuration(self):
        """Test with partial debug configuration."""
        env_vars = {
            "DEBUG_SERVICE_ENABLED": "true",
            "DEBUG_HTTP_REQUESTS": "true",
            "DEBUG_API_V2": "false",
            "DEBUG_MCP_TOOLS": "true",
            "DEBUG_AUTHENTICATION": "false",
            "DEBUG_DATABASE": "false",
            "DEBUG_FRONTEND_ISSUES": "true",
            "DEBUG_VERBOSE": "false",
            "DEBUG_STACK_TRACES": "false"
        }
        
        with patch.dict('os.environ', env_vars):
            service = DebugService()
            
            assert service.is_enabled("http") is True
            assert service.is_enabled("api_v2") is False
            assert service.is_enabled("mcp") is True
            assert service.is_enabled("auth") is False


class TestConvenienceFunctions:
    """Test convenience functions that wrap the global debug service."""
    
    @pytest.fixture
    def mock_debug_service(self):
        """Mock the global debug service."""
        with patch('fastmcp.utilities.debug_service.debug_service') as mock:
            yield mock
    
    def test_log_request_convenience(self, mock_debug_service):
        """Test log_request convenience function."""
        log_request("GET", "/test", {"header": "value"})
        
        mock_debug_service.log_request.assert_called_once_with(
            "GET", "/test", {"header": "value"}
        )
    
    def test_log_response_convenience(self, mock_debug_service):
        """Test log_response convenience function."""
        log_response(200, {"content-type": "text/plain"}, "OK", 0.1)
        
        mock_debug_service.log_response.assert_called_once_with(
            200, {"content-type": "text/plain"}, "OK", 0.1
        )
    
    def test_log_api_v2_request_convenience(self, mock_debug_service):
        """Test log_api_v2_request convenience function."""
        log_api_v2_request("/endpoint", "user-123", "POST", {"data": "value"})
        
        mock_debug_service.log_api_v2_request.assert_called_once_with(
            "/endpoint", "user-123", "POST", {"data": "value"}
        )
    
    def test_log_api_v2_response_convenience(self, mock_debug_service):
        """Test log_api_v2_response convenience function."""
        log_api_v2_response("/endpoint", True, {"result": "success"})
        
        mock_debug_service.log_api_v2_response.assert_called_once_with(
            "/endpoint", True, {"result": "success"}
        )
    
    def test_log_auth_event_convenience(self, mock_debug_service):
        """Test log_auth_event convenience function."""
        log_auth_event("login", "user-456", {"valid": True})
        
        mock_debug_service.log_auth_event.assert_called_once_with(
            "login", "user-456", {"valid": True}
        )
    
    def test_log_database_event_convenience(self, mock_debug_service):
        """Test log_database_event convenience function."""
        log_database_event("SELECT", "users", result_count=10)
        
        mock_debug_service.log_database_event.assert_called_once_with(
            "SELECT", "users", result_count=10
        )
    
    def test_log_frontend_issue_convenience(self, mock_debug_service):
        """Test log_frontend_issue convenience function."""
        log_frontend_issue("ERROR", {"msg": "Failed"}, {"browser": "Safari"})
        
        mock_debug_service.log_frontend_issue.assert_called_once_with(
            "ERROR", {"msg": "Failed"}, {"browser": "Safari"}
        )
    
    def test_debug_decorator_convenience(self, mock_debug_service):
        """Test debug_decorator convenience function."""
        mock_debug_service.debug_decorator.return_value = lambda f: f
        
        @debug_decorator("api")
        def test_func():
            pass
        
        mock_debug_service.debug_decorator.assert_called_once_with("api")
    
    def test_is_debug_enabled_convenience(self, mock_debug_service):
        """Test is_debug_enabled convenience function."""
        mock_debug_service.is_enabled.return_value = True
        
        result = is_debug_enabled("database")
        
        assert result is True
        mock_debug_service.is_enabled.assert_called_once_with("database")
    
    def test_get_debug_status_convenience(self, mock_debug_service):
        """Test get_debug_status convenience function."""
        expected_status = {"debug_enabled": True, "categories": {}}
        mock_debug_service.get_debug_status.return_value = expected_status
        
        result = get_debug_status()
        
        assert result == expected_status
        mock_debug_service.get_debug_status.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def debug_service_verbose(self):
        """Create debug service with verbose enabled."""
        with patch.dict('os.environ', {
            "DEBUG_SERVICE_ENABLED": "true",
            "DEBUG_HTTP_REQUESTS": "true",
            "DEBUG_VERBOSE": "true"
        }):
            return DebugService()
    
    def test_log_request_invalid_json(self, debug_service_verbose):
        """Test request logging with invalid JSON body."""
        with patch.object(debug_service_verbose.http_logger, 'debug') as mock_debug:
            headers = {"content-type": "application/json"}
            body = "Invalid JSON {"
            
            debug_service_verbose.log_request("POST", "/api/test", headers, body)
            
            # Should log parse error
            error_calls = [call for call in mock_debug.call_args_list if "Parse error" in str(call)]
            assert len(error_calls) > 0
    
    def test_log_response_non_json_body(self, debug_service_verbose):
        """Test response logging with non-JSON body."""
        with patch.object(debug_service_verbose.http_logger, 'debug') as mock_debug:
            headers = {"content-type": "text/html"}
            body = "<html><body>Test page</body></html>" * 50  # Long HTML
            
            debug_service_verbose.log_response(200, headers, body, 0.1)
            
            # Should truncate body
            body_calls = [call for call in mock_debug.call_args_list if "Response Body:" in str(call)]
            assert any("..." in str(call) for call in body_calls)
    
    def test_authorization_masking_short_token(self, debug_service_verbose):
        """Test authorization masking with short token."""
        with patch.object(debug_service_verbose.http_logger, 'debug') as mock_debug:
            headers = {"authorization": "Bearer short"}
            
            debug_service_verbose.log_request("GET", "/api/test", headers)
            
            # Should mask as [MASKED]
            auth_calls = [call for call in mock_debug.call_args_list if "Authorization" in str(call)]
            assert any("Bearer [MASKED]" in str(call) for call in auth_calls)
    
    def test_logger_configuration(self):
        """Test logger configuration based on debug flags."""
        with patch.dict('os.environ', {
            "DEBUG_SERVICE_ENABLED": "true",
            "DEBUG_HTTP_REQUESTS": "false",
            "DEBUG_API_V2": "true"
        }):
            service = DebugService()
            
            # HTTP logger should not be set to DEBUG
            assert service.http_logger.level != logging.DEBUG
            # API logger should be set to DEBUG
            assert service.api_logger.level == logging.DEBUG