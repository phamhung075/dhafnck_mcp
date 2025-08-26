"""
Test cases for MCP status tool.
"""

import pytest
import os
import time
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from fastmcp.server.mcp_status_tool import (
    get_mcp_status, register_for_status_updates, register_mcp_status_tools
)
from fastmcp.server.context import Context


class TestGetMCPStatus:
    """Test cases for get_mcp_status function."""
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        ctx = Mock(spec=Context)
        ctx.session_id = "test-session-123"
        return ctx
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create mock connection manager."""
        manager = Mock()
        manager.get_connection_stats = AsyncMock(return_value={
            "connections": {
                "active_connections": 2,
                "total_registered": 5,
                "stale_connections": 0
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
        return broadcaster
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_success(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test successful status retrieval."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                with patch.dict(os.environ, {"DHAFNCK_MVP_MODE": "true"}):
                    result = await get_mcp_status(mock_context)
        
        # Check basic structure
        assert "timestamp" in result
        assert "iso_timestamp" in result
        assert result["session_id"] == "test-session-123"
        
        # Check server info
        assert result["server_info"]["name"] == "DhafnckMCP - Task Management & Agent Orchestration"
        assert result["server_info"]["version"] == "2.1.0"
        assert result["server_info"]["status"] == "healthy"
        assert result["server_info"]["message"] == "Server operating normally"
        
        # Check connection info
        assert result["connection_info"]["active_connections"] == 2
        assert result["connection_info"]["total_registered"] == 5
        assert result["connection_info"]["stale_connections"] == 0
        assert result["connection_info"]["server_restart_count"] == 0
        assert result["connection_info"]["uptime_seconds"] == 3600.5
        assert result["connection_info"]["recommended_action"] == "continue"
        
        # Check broadcast info
        assert result["broadcast_info"]["registered_clients"] == 3
        assert result["broadcast_info"]["broadcasting_active"] is True
        assert result["broadcast_info"]["last_broadcast"]["event_type"] == "server_status"
        
        # Check auth info
        assert result["auth_info"]["enabled"] is True
        assert result["auth_info"]["mvp_mode"] is True
        
        # Check container info
        assert "container_info" in result
        assert "transport" in result["container_info"]
        
        # Check tools info
        assert result["tools_info"]["available"] is True
        assert "last_check" in result["tools_info"]
        
        # Check active clients
        assert len(result["active_clients"]) == 1
        assert result["active_clients"][0]["client_name"] == "cursor"
        
        # No recommendations for healthy status
        assert result["recommendations"] == []
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_without_details(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test status retrieval without details."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await get_mcp_status(mock_context, include_details=False)
        
        # Should not include active clients
        assert "active_clients" not in result
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_restarted(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test status with recently restarted server."""
        # Mock recent restart
        mock_connection_manager.get_connection_stats.return_value["server_info"]["restart_count"] = 2
        mock_connection_manager.get_connection_stats.return_value["server_info"]["uptime_seconds"] = 30.5
        
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await get_mcp_status(mock_context)
        
        assert result["server_info"]["status"] == "restarted"
        assert "recently restarted" in result["server_info"]["message"]
        assert len(result["recommendations"]) > 0
        assert any("Cursor MCP toggle" in rec for rec in result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_no_clients(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test status with no active clients."""
        # Mock no active clients
        mock_connection_manager.get_connection_stats.return_value["connections"]["active_connections"] = 0
        mock_connection_manager.get_connection_stats.return_value["server_info"]["uptime_seconds"] = 3600.5
        
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await get_mcp_status(mock_context)
        
        assert result["server_info"]["status"] == "no_clients"
        assert "no active client connections" in result["server_info"]["message"]
        assert len(result["recommendations"]) > 0
        assert any("mcp.json" in rec for rec in result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_stale_connections(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test status with stale connections."""
        # Mock stale connections
        mock_connection_manager.get_connection_stats.return_value["connections"]["stale_connections"] = 3
        
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await get_mcp_status(mock_context)
        
        assert result["connection_info"]["stale_connections"] == 3
        assert len(result["recommendations"]) > 0
        assert any("stale" in rec for rec in result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_connection_manager_error(self, mock_context, mock_status_broadcaster):
        """Test status with connection manager error."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(side_effect=Exception("Connection manager failed"))):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await get_mcp_status(mock_context)
        
        assert result["server_info"]["status"] == "degraded"
        assert "Connection manager error" in result["server_info"]["message"]
        assert "error" in result["connection_info"]
        assert result["connection_info"]["error"] == "Connection manager failed"
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_broadcaster_error(self, mock_context, mock_connection_manager):
        """Test status with broadcaster error."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(side_effect=Exception("Broadcaster failed"))):
                result = await get_mcp_status(mock_context)
        
        assert result["broadcast_info"]["broadcasting_active"] is False
        assert result["broadcast_info"]["error"] == "Broadcaster failed"
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_no_context(self, mock_connection_manager, mock_status_broadcaster):
        """Test status without context."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await get_mcp_status(None)
        
        assert result["session_id"] == "unknown"
        assert result["server_info"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_complete_error(self, mock_context):
        """Test complete error in status retrieval."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(side_effect=Exception("Fatal error"))):
            result = await get_mcp_status(mock_context)
        
        assert result["server_info"]["status"] == "error"
        assert "Status check failed" in result["server_info"]["message"]
        assert result["error"] == "Fatal error"
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_docker_detection(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test Docker environment detection."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                with patch('os.path.exists', Mock(return_value=True)):
                    result = await get_mcp_status(mock_context)
        
        assert result["container_info"]["is_docker"] is True
    
    @pytest.mark.asyncio
    async def test_get_mcp_status_transport_config(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test transport configuration from environment."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                with patch.dict(os.environ, {
                    "FASTMCP_TRANSPORT": "http",
                    "FASTMCP_HOST": "0.0.0.0",
                    "FASTMCP_PORT": "9000"
                }):
                    result = await get_mcp_status(mock_context)
        
        assert result["container_info"]["transport"] == "http"
        assert result["container_info"]["host"] == "0.0.0.0"
        assert result["container_info"]["port"] == "9000"


class TestRegisterForStatusUpdates:
    """Test cases for register_for_status_updates function."""
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        ctx = Mock(spec=Context)
        ctx.session_id = "test-session-456"
        return ctx
    
    @pytest.fixture
    def mock_status_broadcaster(self):
        """Create mock status broadcaster."""
        broadcaster = Mock()
        broadcaster.register_client = AsyncMock()
        return broadcaster
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create mock connection manager."""
        manager = Mock()
        manager.register_connection = AsyncMock()
        return manager
    
    @pytest.mark.asyncio
    async def test_register_success(self, mock_context, mock_connection_manager, mock_status_broadcaster):
        """Test successful registration."""
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_connection_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
                result = await register_for_status_updates(mock_context)
        
        assert result["success"] is True
        assert result["session_id"] == "test-session-456"
        assert result["message"] == "Successfully registered for status updates"
        assert result["update_interval"] == 30
        assert "server_restart" in result["immediate_events"]
        assert "tools_unavailable" in result["immediate_events"]
        
        mock_status_broadcaster.register_client.assert_called_once_with("test-session-456")
        mock_connection_manager.register_connection.assert_called_once()
        
        # Check registration details
        call_args = mock_connection_manager.register_connection.call_args[0]
        assert call_args[0] == "test-session-456"
        assert call_args[1]["name"] == "cursor"
        assert call_args[1]["type"] == "mcp_client"
    
    @pytest.mark.asyncio
    async def test_register_no_context(self):
        """Test registration without context."""
        result = await register_for_status_updates(None)
        
        assert result["success"] is False
        assert "No valid session ID" in result["error"]
    
    @pytest.mark.asyncio
    async def test_register_no_session_id(self):
        """Test registration with context but no session ID."""
        ctx = Mock(spec=Context)
        ctx.session_id = None
        
        result = await register_for_status_updates(ctx)
        
        assert result["success"] is False
        assert "No valid session ID" in result["error"]
    
    @pytest.mark.asyncio
    async def test_register_broadcaster_error(self, mock_context):
        """Test registration with broadcaster error."""
        with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(side_effect=Exception("Broadcaster error"))):
            result = await register_for_status_updates(mock_context)
        
        assert result["success"] is False
        assert result["error"] == "Broadcaster error"
    
    @pytest.mark.asyncio
    async def test_register_connection_manager_error(self, mock_context, mock_status_broadcaster):
        """Test registration with connection manager error."""
        with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock(return_value=mock_status_broadcaster)):
            with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(side_effect=Exception("Manager error"))):
                result = await register_for_status_updates(mock_context)
        
        assert result["success"] is False
        assert result["error"] == "Manager error"


class TestRegisterMCPStatusTools:
    """Test cases for tool registration."""
    
    def test_register_tools(self):
        """Test tool registration."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tools = register_mcp_status_tools(mock_server)
        
        assert len(tools) == 2
        assert mock_server.tool.call_count == 2
        
        # Check first tool (get_mcp_status)
        first_call = mock_server.tool.call_args_list[0][1]
        assert first_call["name"] == "get_mcp_status"
        assert "comprehensive MCP server status" in first_call["description"]
        
        # Check second tool (register_for_status_updates)
        second_call = mock_server.tool.call_args_list[1][1]
        assert second_call["name"] == "register_for_status_updates"
        assert "real-time MCP status updates" in second_call["description"]
    
    @pytest.mark.asyncio
    async def test_mcp_status_tool_success(self):
        """Test MCP status tool function."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tools = register_mcp_status_tools(mock_server)
        status_tool = tools[0]
        
        mock_ctx = Mock()
        mock_ctx.session_id = "test-123"
        
        mock_status = {
            "server_info": {
                "name": "Test Server",
                "version": "1.0",
                "status": "healthy",
                "message": "All good"
            },
            "iso_timestamp": datetime.now().isoformat(),
            "connection_info": {
                "active_connections": 2,
                "total_registered": 5,
                "stale_connections": 0,
                "server_restart_count": 0,
                "uptime_seconds": 1000.5,
                "recommended_action": "continue"
            },
            "broadcast_info": {
                "broadcasting_active": True,
                "registered_clients": 3,
                "last_broadcast": {
                    "event_type": "test",
                    "server_status": "healthy"
                }
            },
            "auth_info": {"enabled": True, "mvp_mode": False},
            "container_info": {"is_docker": True, "transport": "http", "host": "localhost", "port": "8000"},
            "active_clients": [{
                "client_name": "test-client",
                "client_version": "1.0",
                "session_id": "client-1",
                "connection_age_seconds": 100.5,
                "health_checks": 5
            }],
            "recommendations": ["Test recommendation"]
        }
        
        with patch('fastmcp.server.mcp_status_tool.get_mcp_status', AsyncMock(return_value=mock_status)):
            result = await status_tool(mock_ctx)
        
        # Check formatted response
        assert "✅ **MCP Server Status: Healthy**" in result
        assert "Test Server" in result
        assert "Version: 1.0" in result
        assert "Active Connections: 2" in result
        assert "Broadcasting Active: ✅" in result
        assert "test-client (v1.0)" in result
        assert "💡 Recommendations:" in result
        assert "Test recommendation" in result
        assert "🔧 Quick Actions:" in result
    
    @pytest.mark.asyncio
    async def test_mcp_status_tool_error_state(self):
        """Test MCP status tool with error state."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tools = register_mcp_status_tools(mock_server)
        status_tool = tools[0]
        
        mock_ctx = Mock()
        
        mock_status = {
            "server_info": {"status": "error"},
            "connection_info": {"error": "Connection failed"}
        }
        
        with patch('fastmcp.server.mcp_status_tool.get_mcp_status', AsyncMock(return_value=mock_status)):
            result = await status_tool(mock_ctx)
        
        assert "🚨 **MCP Server Status: Error**" in result
        assert "Connection Error: Connection failed" in result
    
    @pytest.mark.asyncio
    async def test_register_status_updates_tool_success(self):
        """Test register status updates tool function."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tools = register_mcp_status_tools(mock_server)
        register_tool = tools[1]
        
        mock_ctx = Mock()
        mock_ctx.session_id = "test-789"
        
        mock_result = {
            "success": True,
            "session_id": "test-789",
            "update_interval": 30,
            "immediate_events": ["server_restart", "tools_unavailable"]
        }
        
        with patch('fastmcp.server.mcp_status_tool.register_for_status_updates', AsyncMock(return_value=mock_result)):
            result = await register_tool(mock_ctx)
        
        assert "✅ **Successfully Registered for Status Updates**" in result
        assert "Session ID: test-789" in result
        assert "Update Interval: 30 seconds" in result
        assert "server_restart, tools_unavailable" in result
        assert "What This Means:" in result
        assert "Next Steps:" in result
    
    @pytest.mark.asyncio
    async def test_register_status_updates_tool_failure(self):
        """Test register status updates tool with failure."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        tools = register_mcp_status_tools(mock_server)
        register_tool = tools[1]
        
        mock_ctx = Mock()
        
        mock_result = {
            "success": False,
            "error": "Registration failed"
        }
        
        with patch('fastmcp.server.mcp_status_tool.register_for_status_updates', AsyncMock(return_value=mock_result)):
            result = await register_tool(mock_ctx)
        
        assert "❌ **Registration Failed**" in result
        assert "Error: Registration failed" in result
        assert "Troubleshooting:" in result


class TestLogging:
    """Test cases for logging behavior."""
    
    @pytest.mark.asyncio
    async def test_status_check_logging(self):
        """Test logging during status check."""
        mock_ctx = Mock()
        mock_ctx.session_id = "log-test-123"
        
        mock_manager = Mock()
        mock_manager.get_connection_stats = AsyncMock(return_value={
            "connections": {"active_connections": 1, "total_registered": 1, "stale_connections": 0},
            "server_info": {"restart_count": 0, "uptime_seconds": 100}
        })
        mock_manager.get_reconnection_info = AsyncMock(return_value={"recommended_action": "continue"})
        
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(return_value=mock_manager)):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock()):
                with patch('fastmcp.server.mcp_status_tool.logger') as mock_logger:
                    await get_mcp_status(mock_ctx)
                    
                    mock_logger.info.assert_called_with("MCP status check completed for session log-test-123")
    
    @pytest.mark.asyncio
    async def test_registration_logging(self):
        """Test logging during registration."""
        mock_ctx = Mock()
        mock_ctx.session_id = "reg-test-456"
        
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock()):
            with patch('fastmcp.server.mcp_status_tool.get_status_broadcaster', AsyncMock()):
                with patch('fastmcp.server.mcp_status_tool.logger') as mock_logger:
                    await register_for_status_updates(mock_ctx)
                    
                    mock_logger.info.assert_called_with("Session reg-test-456 registered for status updates")
    
    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test error logging."""
        mock_ctx = Mock()
        
        with patch('fastmcp.server.mcp_status_tool.get_connection_manager', AsyncMock(side_effect=Exception("Test error"))):
            with patch('fastmcp.server.mcp_status_tool.logger') as mock_logger:
                await get_mcp_status(mock_ctx)
                
                mock_logger.error.assert_any_call("Error getting connection manager info: Test error")
                mock_logger.error.assert_any_call("Error in get_mcp_status: Test error")
    
    def test_tool_registration_logging(self):
        """Test logging during tool registration."""
        mock_server = Mock()
        mock_server.tool = Mock(side_effect=lambda **kwargs: lambda func: func)
        
        with patch('fastmcp.server.mcp_status_tool.logger') as mock_logger:
            register_mcp_status_tools(mock_server)
            
            mock_logger.info.assert_called_with("MCP status tools registered successfully")