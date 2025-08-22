"""
Test cases for unified connection management tool.
"""

import pytest
import os
import time
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from fastmcp.server.manage_connection_tool import (
    manage_connection, register_manage_connection_tool,
    _format_health_check_response, _format_server_capabilities_response,
    _format_connection_health_response, _format_status_response,
    _format_register_updates_response
)
from fastmcp.server.context import Context


class TestManageConnection:
    """Test cases for manage_connection function."""
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        ctx = Mock(spec=Context)
        ctx.session_id = "test-session-123"
        ctx.user_id = "test-user-456"
        return ctx
    
    @pytest.fixture
    def mock_secure_health_check(self):
        """Create mock secure health check."""
        with patch('fastmcp.server.manage_connection_tool.secure_health_check') as mock:
            mock.return_value = {
                "success": True,
                "status": "healthy",
                "server_name": "DhafnckMCP",
                "version": "2.1.0",
                "timestamp": time.time(),
                "authentication": {"enabled": True, "mvp_mode": False},
                "task_management": {"task_management_enabled": True, "enabled_tools_count": 25},
                "connections": {
                    "active_connections": 2,
                    "server_restart_count": 0,
                    "uptime_seconds": 3600.5,
                    "recommended_action": "continue"
                }
            }
            yield mock
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create mock connection manager."""
        manager = Mock()
        manager.update_connection_activity = AsyncMock()
        manager.get_connection_stats = AsyncMock(return_value={
            "connections": {
                "active_connections": 2,
                "total_registered": 5,
                "stale_connections": 1
            },
            "server_info": {
                "restart_count": 0,
                "uptime_seconds": 3600.5,
                "start_time": datetime.now().isoformat()
            },
            "active_clients": [
                {
                    "session_id": "client-1",
                    "client_name": "cursor",
                    "client_version": "1.0",
                    "connection_age_seconds": 300.5,
                    "health_checks": 10
                }
            ]
        })
        manager.get_reconnection_info = AsyncMock(return_value={
            "recommended_action": "continue",
            "server_restarted": False
        })
        manager.register_connection = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_status_broadcaster(self):
        """Create mock status broadcaster."""
        broadcaster = Mock()
        broadcaster.get_last_status = Mock(return_value={
            "event_type": "server_status",
            "server_status": "healthy",
            "timestamp": time.time()
        })
        broadcaster.get_client_count = Mock(return_value=3)
        broadcaster.register_client = AsyncMock()
        return broadcaster
    
    @pytest.mark.asyncio
    async def test_health_check_action(self, mock_context, mock_secure_health_check):
        """Test health check action."""
        result = await manage_connection(mock_context, "health_check")
        
        assert result["success"] is True
        assert result["status"] == "healthy"
        mock_secure_health_check.assert_called_once()
        
        # Check default parameters
        call_args = mock_secure_health_check.call_args[1]
        assert call_args["user_id"] == "test-user-456"
        assert call_args["is_admin"] is True  # Default
        assert call_args["is_internal"] is True  # Default
    
    @pytest.mark.asyncio
    async def test_health_check_minimal_info(self, mock_context, mock_secure_health_check):
        """Test health check with minimal information requested."""
        result = await manage_connection(mock_context, "health_check", include_details=False)
        
        # Should use client-safe response
        call_args = mock_secure_health_check.call_args[1]
        assert call_args["is_admin"] is False
        assert call_args["is_internal"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_error(self, mock_context):
        """Test health check error handling."""
        with patch('fastmcp.server.manage_connection_tool.secure_health_check') as mock:
            mock.side_effect = Exception("Health check failed")
            
            result = await manage_connection(mock_context, "health_check")
            
            assert result["success"] is False
            assert result["status"] == "error"
            assert "Health check failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_server_capabilities_action(self, mock_context):
        """Test server capabilities action."""
        with patch.dict(os.environ, {"DHAFNCK_MVP_MODE": "true", "SUPABASE_URL": "https://test.supabase.co"}):
            result = await manage_connection(mock_context, "server_capabilities")
        
        assert result["success"] is True
        capabilities = result["capabilities"]
        
        # Check core features
        assert "Task Management" in capabilities["core_features"]
        assert "Token-based Authentication" in capabilities["core_features"]
        
        # Check available actions
        assert "connection_management" in capabilities["available_actions"]
        assert "health_check" in capabilities["available_actions"]["connection_management"]
        
        # Check security features
        assert capabilities["security_features"]["authentication_enabled"] is True
        assert capabilities["security_features"]["mvp_mode"] is True
        assert capabilities["security_features"]["supabase_integration"] is True
        
        # Check transport info
        assert "transport" in capabilities["transport_info"]
    
    @pytest.mark.asyncio
    async def test_connection_health_action(self, mock_context, mock_connection_manager):
        """Test connection health action."""
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            result = await manage_connection(mock_context, "connection_health")
        
        assert result["success"] is True
        assert result["server_status"] == "healthy"
        assert result["current_session_id"] == "test-session-123"
        assert result["recommendation"] == "All connections healthy."
        
        mock_connection_manager.update_connection_activity.assert_called_once_with("test-session-123")
        mock_connection_manager.get_connection_stats.assert_called_once()
        mock_connection_manager.get_reconnection_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_health_restarted_states(self, mock_context, mock_connection_manager):
        """Test connection health with various restart states."""
        # Test restarted with no clients
        mock_connection_manager.get_connection_stats.return_value["server_info"]["restart_count"] = 2
        mock_connection_manager.get_connection_stats.return_value["connections"]["active_connections"] = 0
        
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            result = await manage_connection(mock_context, "connection_health")
        
        assert result["server_status"] == "restarted_no_clients"
        assert "Server was restarted" in result["recommendation"]
        assert len(result["warnings"]) > 0
        
        # Test restarted with clients
        mock_connection_manager.get_connection_stats.return_value["connections"]["active_connections"] = 2
        
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            result = await manage_connection(mock_context, "connection_health")
        
        assert result["server_status"] == "restarted_with_clients"
    
    @pytest.mark.asyncio
    async def test_connection_health_no_context(self, mock_connection_manager):
        """Test connection health without context."""
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            result = await manage_connection(None, "connection_health")
        
        assert result["success"] is True
        assert result["current_session_id"] is None
        mock_connection_manager.update_connection_activity.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_connection_health_error(self, mock_context):
        """Test connection health error handling."""
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(side_effect=Exception("Connection error"))):
            result = await manage_connection(mock_context, "connection_health")
        
        assert result["success"] is False
        assert result["server_status"] == "error"
        assert "Connection error" in result["error"]
        assert "immediate_steps" in result["troubleshooting"]
    
    @pytest.mark.asyncio
    async def test_status_action(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test status action."""
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await manage_connection(mock_context, "status")
        
        assert result["success"] is True
        assert result["session_id"] == "test-session-123"
        assert result["server_info"]["status"] == "healthy"
        assert result["connection_info"]["active_connections"] == 2
        assert result["broadcast_info"]["broadcasting_active"] is True
        assert result["auth_info"]["enabled"] is True
        assert "container_info" in result
        assert result["tools_info"]["available"] is True
    
    @pytest.mark.asyncio
    async def test_status_various_server_states(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test status action with various server states."""
        # Test restarted state
        mock_connection_manager.get_connection_stats.return_value["server_info"]["restart_count"] = 1
        mock_connection_manager.get_connection_stats.return_value["connections"]["active_connections"] = 0
        
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await manage_connection(mock_context, "status")
        
        assert result["server_info"]["status"] == "restarted"
        assert "Server restarted, no active clients" in result["server_info"]["message"]
        assert len(result["recommendations"]) > 0
        
        # Test recently started state
        mock_connection_manager.get_connection_stats.return_value["server_info"]["restart_count"] = 0
        mock_connection_manager.get_connection_stats.return_value["server_info"]["uptime_seconds"] = 30
        mock_connection_manager.get_connection_stats.return_value["connections"]["active_connections"] = 1
        
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await manage_connection(mock_context, "status")
        
        assert result["server_info"]["status"] == "restarted"
        assert "Server recently started" in result["server_info"]["message"]
    
    @pytest.mark.asyncio
    async def test_status_without_details(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test status action without details."""
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await manage_connection(mock_context, "status", include_details=False)
        
        assert result["success"] is True
        assert "active_clients" not in result
    
    @pytest.mark.asyncio
    async def test_status_error_handling(self, mock_context):
        """Test status error handling."""
        # Test connection manager error
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(side_effect=Exception("Manager error"))):
            with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock()):
                result = await manage_connection(mock_context, "status")
        
        assert result["success"] is True  # Partial success
        assert "error" in result["connection_info"]
        assert result["server_info"]["status"] == "degraded"
        
        # Test broadcaster error
        mock_manager = Mock()
        mock_manager.get_connection_stats = AsyncMock(return_value={"connections": {"active_connections": 1}, "server_info": {"restart_count": 0, "uptime_seconds": 100}})
        mock_manager.get_reconnection_info = AsyncMock(return_value={"recommended_action": "continue"})
        
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_manager)):
            with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock(side_effect=Exception("Broadcaster error"))):
                result = await manage_connection(mock_context, "status")
        
        assert result["success"] is True
        assert result["broadcast_info"]["broadcasting_active"] is False
        assert "error" in result["broadcast_info"]
    
    @pytest.mark.asyncio
    async def test_register_updates_action(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test register updates action."""
        with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await manage_connection(mock_context, "register_updates")
        
        assert result["success"] is True
        assert result["session_id"] == "test-session-123"
        assert result["update_interval"] == 30
        assert "server_restart" in result["immediate_events"]
        
        mock_status_broadcaster.register_client.assert_called_once_with("test-session-123")
        mock_connection_manager.register_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_updates_no_context(self):
        """Test register updates without context."""
        result = await manage_connection(None, "register_updates")
        
        assert result["success"] is False
        assert "No valid session ID" in result["error"]
    
    @pytest.mark.asyncio
    async def test_register_updates_error(self, mock_context):
        """Test register updates error handling."""
        with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock(side_effect=Exception("Registration failed"))):
            result = await manage_connection(mock_context, "register_updates")
        
        assert result["success"] is False
        assert "Registration failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_unknown_action(self, mock_context):
        """Test unknown action handling."""
        result = await manage_connection(mock_context, "unknown_action")
        
        assert result["success"] is False
        assert "Unknown action: unknown_action" in result["error"]
        assert "health_check" in result["available_actions"]
    
    @pytest.mark.asyncio
    async def test_action_error_handling(self, mock_context):
        """Test general error handling for actions."""
        with patch('fastmcp.server.manage_connection_tool._health_check', AsyncMock(side_effect=Exception("Unexpected error"))):
            result = await manage_connection(mock_context, "health_check")
        
        assert result["success"] is False
        assert "Unexpected error" in result["error"]
        assert result["action"] == "health_check"


class TestFormatFunctions:
    """Test cases for response formatting functions."""
    
    def test_format_health_check_response(self):
        """Test health check response formatting."""
        result = {
            "status": "healthy",
            "server_name": "DhafnckMCP",
            "version": "2.1.0",
            "timestamp": time.time(),
            "authentication": {"enabled": True, "mvp_mode": False},
            "task_management": {"task_management_enabled": True, "enabled_tools_count": 25},
            "connections": {
                "active_connections": 2,
                "server_restart_count": 0,
                "uptime_seconds": 3600.5,
                "recommended_action": "continue"
            }
        }
        
        response = _format_health_check_response(result)
        
        assert "✅ **Server Health Check**" in response
        assert "DhafnckMCP" in response
        assert "Version: 2.1.0" in response
        assert "Authentication:" in response
        assert "Task Management:" in response
        assert "Active: 2" in response
        assert "Uptime: 3600.5s" in response
    
    def test_format_health_check_response_error_state(self):
        """Test health check response with error state."""
        result = {
            "status": "error",
            "timestamp": time.time(),
            "connections": {"error": "Connection manager unavailable"}
        }
        
        response = _format_health_check_response(result)
        
        assert "🚨 **Server Health Check**" in response
        assert "Error - Connection manager unavailable" in response
    
    def test_format_server_capabilities_response(self):
        """Test server capabilities response formatting."""
        result = {
            "capabilities": {
                "core_features": ["Task Management", "Authentication"],
                "available_actions": {
                    "connection_management": ["health_check", "status"],
                    "task_management": ["create", "update"]
                },
                "security_features": {
                    "authentication_enabled": True,
                    "mvp_mode": False,
                    "rate_limiting": True,
                    "supabase_integration": True
                },
                "transport_info": {
                    "is_docker": True,
                    "transport": "http",
                    "host": "localhost",
                    "port": "8000"
                }
            }
        }
        
        response = _format_server_capabilities_response(result)
        
        assert "🔧 **Server Capabilities**" in response
        assert "Core Features (2):" in response
        assert "Task Management" in response
        assert "Connection Management: health_check, status" in response
        assert "Authentication: Enabled" in response
        assert "Environment: Docker" in response
        assert "Endpoint: localhost:8000" in response
    
    def test_format_connection_health_response(self):
        """Test connection health response formatting."""
        result = {
            "server_status": "healthy",
            "current_session_id": "test-123",
            "timestamp": datetime.now().isoformat(),
            "connection_manager": {
                "server_info": {
                    "uptime_seconds": 3600.5,
                    "restart_count": 0,
                    "start_time": datetime.now().isoformat()
                },
                "connections": {
                    "active_connections": 2,
                    "total_registered": 5,
                    "stale_connections": 1
                },
                "active_clients": [
                    {
                        "client_name": "cursor",
                        "client_version": "1.0",
                        "connection_age_seconds": 300.5,
                        "health_checks": 10
                    }
                ]
            },
            "recommendation": "All connections healthy.",
            "warnings": ["1 stale connections detected."],
            "troubleshooting": {
                "cursor_reconnection": ["Step 1", "Step 2"],
                "docker_rebuild": ["Docker step 1", "Docker step 2"]
            },
            "reconnection_info": {"recommended_action": "continue"}
        }
        
        response = _format_connection_health_response(result)
        
        assert "✅ **Connection Health Status: Healthy**" in response
        assert "Session ID: test-123" in response
        assert "Uptime: 3600.5 seconds" in response
        assert "Active Connections: 2" in response
        assert "cursor (v1.0)" in response
        assert "💡 Recommendation:" in response
        assert "⚠️ Warnings:" in response
        assert "🔄 Quick Cursor Reconnection" in response
        assert "🐳 After Docker Rebuild:" in response
    
    def test_format_connection_health_error_response(self):
        """Test connection health error response formatting."""
        result = {
            "server_status": "error",
            "error": "Database connection failed",
            "troubleshooting": {
                "immediate_steps": ["Check Docker", "Check logs"]
            }
        }
        
        response = _format_connection_health_response(result)
        
        assert "🚨 **Connection Health Status: Error**" in response
        assert "🚨 Error Details:" in response
        assert "Database connection failed" in response
        assert "🚨 Immediate Troubleshooting:" in response
    
    def test_format_status_response(self):
        """Test status response formatting."""
        result = {
            "server_info": {
                "name": "DhafnckMCP",
                "version": "2.1.0",
                "status": "healthy",
                "message": "All systems operational"
            },
            "iso_timestamp": datetime.now().isoformat(),
            "connection_info": {
                "active_connections": 2,
                "total_registered": 5,
                "stale_connections": 0,
                "server_restart_count": 0,
                "uptime_seconds": 3600.5,
                "recommended_action": "continue"
            },
            "broadcast_info": {
                "broadcasting_active": True,
                "registered_clients": 3,
                "last_broadcast": {
                    "event_type": "server_status",
                    "server_status": "healthy"
                }
            },
            "auth_info": {"enabled": True, "mvp_mode": False},
            "container_info": {
                "is_docker": True,
                "transport": "http",
                "host": "localhost",
                "port": "8000"
            },
            "active_clients": [
                {
                    "client_name": "cursor",
                    "client_version": "1.0",
                    "session_id": "client-1",
                    "connection_age_seconds": 300.5,
                    "health_checks": 10
                }
            ],
            "recommendations": ["Use Cursor MCP toggle"]
        }
        
        response = _format_status_response(result)
        
        assert "✅ **MCP Server Status: Healthy**" in response
        assert "DhafnckMCP" in response
        assert "Version: 2.1.0" in response
        assert "All systems operational" in response
        assert "Active Connections: 2" in response
        assert "Broadcasting Active: ✅" in response
        assert "cursor (v1.0)" in response
        assert "💡 Recommendations:" in response
        assert "🔧 Quick Actions:" in response
    
    def test_format_status_degraded_response(self):
        """Test status response with degraded state."""
        result = {
            "server_info": {
                "status": "degraded",
                "message": "Connection manager error"
            },
            "connection_info": {"error": "Manager unavailable"}
        }
        
        response = _format_status_response(result)
        
        assert "⚠️ **MCP Server Status: Degraded**" in response
        assert "Connection Error: Manager unavailable" in response
    
    def test_format_register_updates_success_response(self):
        """Test register updates success response formatting."""
        result = {
            "success": True,
            "session_id": "test-123",
            "update_interval": 30,
            "immediate_events": ["server_restart", "tools_unavailable"]
        }
        
        response = _format_register_updates_response(result)
        
        assert "✅ **Successfully Registered for Status Updates**" in response
        assert "Session ID: test-123" in response
        assert "Update Interval: 30 seconds" in response
        assert "server_restart, tools_unavailable" in response
        assert "What This Means:" in response
        assert "Next Steps:" in response
    
    def test_format_register_updates_failure_response(self):
        """Test register updates failure response formatting."""
        result = {
            "success": False,
            "error": "Invalid session"
        }
        
        response = _format_register_updates_response(result)
        
        assert "❌ **Registration Failed**" in response
        assert "Error: Invalid session" in response
        assert "Troubleshooting:" in response


class TestRegisterManageConnectionTool:
    """Test cases for tool registration."""
    
    def test_register_tool(self):
        """Test tool registration."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tool_func = register_manage_connection_tool(mock_server)
        
        assert tool_func is not None
        mock_server.tool.assert_called_once()
        
        # Check tool metadata
        call_args = mock_server.tool.call_args[1]
        assert call_args["name"] == "manage_connection"
        assert "UNIFIED CONNECTION MANAGEMENT" in call_args["description"]
    
    @pytest.mark.asyncio
    async def test_tool_function_success(self):
        """Test the registered tool function with success."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tool_func = register_manage_connection_tool(mock_server)
        
        mock_ctx = Mock()
        mock_ctx.session_id = "test-123"
        
        with patch('fastmcp.server.manage_connection_tool.manage_connection', AsyncMock(return_value={"success": True, "status": "healthy"})):
            with patch('fastmcp.server.manage_connection_tool._format_health_check_response', Mock(return_value="Formatted response")):
                result = await tool_func(mock_ctx, "health_check")
        
        assert result == "Formatted response"
    
    @pytest.mark.asyncio
    async def test_tool_function_error(self):
        """Test the registered tool function with error."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tool_func = register_manage_connection_tool(mock_server)
        
        mock_ctx = Mock()
        
        with patch('fastmcp.server.manage_connection_tool.manage_connection', AsyncMock(return_value={
            "success": False,
            "error": "Test error",
            "available_actions": ["health_check", "status"]
        })):
            result = await tool_func(mock_ctx, "bad_action")
        
        assert "❌ **Connection Management Error**" in result
        assert "Test error" in result
        assert "health_check, status" in result
    
    @pytest.mark.asyncio
    async def test_tool_function_unknown_action(self):
        """Test tool function with truly unknown action (no formatter)."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tool_func = register_manage_connection_tool(mock_server)
        
        mock_ctx = Mock()
        
        # Return success but with unknown action
        with patch('fastmcp.server.manage_connection_tool.manage_connection', AsyncMock(return_value={"success": True})):
            result = await tool_func(mock_ctx, "completely_unknown")
        
        assert "❓ **Unknown Action:** completely_unknown" in result
        assert "Available Actions:" in result


class TestEnvironmentSettings:
    """Test cases for environment-based behavior."""
    
    @pytest.mark.asyncio
    async def test_mvp_mode_detection(self):
        """Test MVP mode detection in various functions."""
        mock_ctx = Mock()
        mock_ctx.session_id = "test-123"
        
        with patch.dict(os.environ, {"DHAFNCK_MVP_MODE": "true"}):
            # Test in server capabilities
            result = await manage_connection(mock_ctx, "server_capabilities")
            assert result["capabilities"]["security_features"]["mvp_mode"] is True
            
            # Test in status
            with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock()):
                with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock()):
                    result = await manage_connection(mock_ctx, "status")
                    assert result["auth_info"]["mvp_mode"] is True
    
    @pytest.mark.asyncio
    async def test_docker_detection(self):
        """Test Docker environment detection."""
        mock_ctx = Mock()
        
        with patch('os.path.exists', Mock(return_value=True)):
            result = await manage_connection(mock_ctx, "server_capabilities")
            assert result["capabilities"]["transport_info"]["is_docker"] is True
            
            with patch('fastmcp.server.manage_connection_tool.get_connection_manager', AsyncMock()):
                with patch('fastmcp.server.manage_connection_tool.get_status_broadcaster', AsyncMock()):
                    result = await manage_connection(mock_ctx, "status")
                    assert result["container_info"]["is_docker"] is True