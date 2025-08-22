"""
Test cases for MCP token management routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastmcp.server.routes.mcp_token_routes import (
    router, GenerateTokenRequest, TokenResponse, TokenStatsResponse,
    generate_mcp_token, revoke_mcp_tokens, get_token_stats,
    cleanup_expired_tokens, mcp_token_service_health
)
from fastmcp.auth.domain.entities.user import User
from fastmcp.auth.services.mcp_token_service import MCPToken


class TestMCPTokenRoutes:
    """Test cases for MCP token routes."""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock authenticated user."""
        user = Mock(spec=User)
        user.id = "test-user-123"
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_mcp_token(self):
        """Create mock MCP token."""
        return MCPToken(
            token="mcp_test_token_12345",
            user_id="test-user-123",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            source_type="api_endpoint",
            metadata={"description": "Test token"}
        )
    
    @pytest.fixture
    def mock_token_service(self):
        """Create mock token service."""
        with patch('fastmcp.server.routes.mcp_token_routes.mcp_token_service') as mock:
            mock.generate_mcp_token_from_user_id = AsyncMock()
            mock.revoke_user_tokens = AsyncMock()
            mock.get_token_stats = Mock()
            mock.cleanup_expired_tokens = AsyncMock()
            yield mock
    
    @pytest.fixture
    def test_client(self, mock_user):
        """Create test client with mocked dependencies."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: Mock(spec=Session)
        
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_success(self, mock_user, mock_db, mock_mcp_token, mock_token_service):
        """Test successful MCP token generation."""
        mock_token_service.generate_mcp_token_from_user_id.return_value = mock_mcp_token
        
        request = GenerateTokenRequest(expires_in_hours=24, description="Test token")
        
        result = await generate_mcp_token(request, mock_user, mock_db)
        
        assert isinstance(result, TokenResponse)
        assert result.success is True
        assert result.token == "mcp_test_token_12345"
        assert result.expires_at == mock_mcp_token.expires_at.isoformat()
        assert "successfully" in result.message
        
        mock_token_service.generate_mcp_token_from_user_id.assert_called_once_with(
            user_id="test-user-123",
            email="test@example.com",
            expires_in_hours=24,
            metadata={
                'description': 'Test token',
                'generated_via': 'api_endpoint',
                'user_agent': 'frontend'
            }
        )
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_default_expiry(self, mock_user, mock_db, mock_mcp_token, mock_token_service):
        """Test token generation with default expiry."""
        mock_token_service.generate_mcp_token_from_user_id.return_value = mock_mcp_token
        
        request = GenerateTokenRequest()  # No expiry specified
        
        result = await generate_mcp_token(request, mock_user, mock_db)
        
        assert result.success is True
        assert "Expires in 24 hours" in result.message
        
        # Check default expiry was used
        call_args = mock_token_service.generate_mcp_token_from_user_id.call_args[1]
        assert call_args["expires_in_hours"] == 24
    
    @pytest.mark.asyncio
    async def test_generate_mcp_token_error(self, mock_user, mock_db, mock_token_service):
        """Test token generation error handling."""
        mock_token_service.generate_mcp_token_from_user_id.side_effect = Exception("Service error")
        
        request = GenerateTokenRequest()
        
        with pytest.raises(HTTPException) as exc_info:
            await generate_mcp_token(request, mock_user, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to generate MCP token"
    
    @pytest.mark.asyncio
    async def test_revoke_mcp_tokens_success(self, mock_user, mock_db, mock_token_service):
        """Test successful token revocation."""
        mock_token_service.revoke_user_tokens.return_value = True
        
        result = await revoke_mcp_tokens(mock_user, mock_db)
        
        assert isinstance(result, TokenResponse)
        assert result.success is True
        assert result.message == "All MCP tokens revoked successfully"
        assert result.token is None
        
        mock_token_service.revoke_user_tokens.assert_called_once_with("test-user-123")
    
    @pytest.mark.asyncio
    async def test_revoke_mcp_tokens_no_tokens(self, mock_user, mock_db, mock_token_service):
        """Test revocation when no tokens exist."""
        mock_token_service.revoke_user_tokens.return_value = False
        
        result = await revoke_mcp_tokens(mock_user, mock_db)
        
        assert result.success is True
        assert result.message == "No MCP tokens found to revoke"
    
    @pytest.mark.asyncio
    async def test_revoke_mcp_tokens_error(self, mock_user, mock_db, mock_token_service):
        """Test revocation error handling."""
        mock_token_service.revoke_user_tokens.side_effect = Exception("Revocation error")
        
        with pytest.raises(HTTPException) as exc_info:
            await revoke_mcp_tokens(mock_user, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to revoke MCP tokens"
    
    @pytest.mark.asyncio
    async def test_get_token_stats_success(self, mock_user, mock_db, mock_token_service):
        """Test successful token statistics retrieval."""
        mock_stats = {
            "total_tokens": 10,
            "active_tokens": 3,
            "expired_tokens": 7,
            "unique_users": 5
        }
        mock_token_service.get_token_stats.return_value = mock_stats
        
        result = await get_token_stats(mock_user, mock_db)
        
        assert isinstance(result, TokenStatsResponse)
        assert result.success is True
        assert result.stats == mock_stats
        assert "successfully" in result.message
        
        mock_token_service.get_token_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_token_stats_error(self, mock_user, mock_db, mock_token_service):
        """Test statistics retrieval error handling."""
        mock_token_service.get_token_stats.side_effect = Exception("Stats error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_token_stats(mock_user, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to get token statistics"
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_success(self, mock_user, mock_db, mock_token_service):
        """Test successful token cleanup."""
        mock_token_service.cleanup_expired_tokens.return_value = 5
        
        result = await cleanup_expired_tokens(mock_user, mock_db)
        
        assert result["success"] is True
        assert result["cleaned_tokens"] == 5
        assert result["message"] == "Cleaned up 5 expired tokens"
        
        mock_token_service.cleanup_expired_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_none(self, mock_user, mock_db, mock_token_service):
        """Test cleanup when no expired tokens."""
        mock_token_service.cleanup_expired_tokens.return_value = 0
        
        result = await cleanup_expired_tokens(mock_user, mock_db)
        
        assert result["success"] is True
        assert result["cleaned_tokens"] == 0
        assert result["message"] == "Cleaned up 0 expired tokens"
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_error(self, mock_user, mock_db, mock_token_service):
        """Test cleanup error handling."""
        mock_token_service.cleanup_expired_tokens.side_effect = Exception("Cleanup error")
        
        with pytest.raises(HTTPException) as exc_info:
            await cleanup_expired_tokens(mock_user, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to clean up expired tokens"
    
    @pytest.mark.asyncio
    async def test_mcp_token_service_health_success(self, mock_token_service):
        """Test successful health check."""
        mock_stats = {
            "total_tokens": 10,
            "active_tokens": 3,
            "expired_tokens": 7,
            "unique_users": 5
        }
        mock_token_service.get_token_stats.return_value = mock_stats
        
        result = await mcp_token_service_health()
        
        assert result["status"] == "healthy"
        assert result["service"] == "mcp_token_service"
        assert result["stats"] == mock_stats
        assert "operational" in result["message"]
    
    @pytest.mark.asyncio
    async def test_mcp_token_service_health_failure(self, mock_token_service):
        """Test health check failure."""
        mock_token_service.get_token_stats.side_effect = Exception("Service down")
        
        with pytest.raises(HTTPException) as exc_info:
            await mcp_token_service_health()
        
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc_info.value.detail == "MCP token service is not healthy"


class TestIntegrationWithTestClient:
    """Integration tests using TestClient."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies."""
        mock_user = Mock(spec=User)
        mock_user.id = "test-user-123"
        mock_user.email = "test@example.com"
        
        mock_token = MCPToken(
            token="mcp_integration_test",
            user_id="test-user-123",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            source_type="api_endpoint",
            metadata={}
        )
        
        return {
            "user": mock_user,
            "token": mock_token
        }
    
    def test_generate_token_endpoint(self, test_client, mock_dependencies):
        """Test POST /generate endpoint."""
        with patch('fastmcp.server.routes.mcp_token_routes.mcp_token_service') as mock_service:
            mock_service.generate_mcp_token_from_user_id = AsyncMock(return_value=mock_dependencies["token"])
            
            response = test_client.post(
                "/api/v2/mcp-tokens/generate",
                json={"expires_in_hours": 48, "description": "Integration test"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["token"] == "mcp_integration_test"
            assert data["expires_at"] is not None
            assert "successfully" in data["message"]
    
    def test_revoke_tokens_endpoint(self, test_client):
        """Test DELETE /revoke endpoint."""
        with patch('fastmcp.server.routes.mcp_token_routes.mcp_token_service') as mock_service:
            mock_service.revoke_user_tokens = AsyncMock(return_value=True)
            
            response = test_client.delete("/api/v2/mcp-tokens/revoke")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "All MCP tokens revoked successfully"
    
    def test_get_stats_endpoint(self, test_client):
        """Test GET /stats endpoint."""
        with patch('fastmcp.server.routes.mcp_token_routes.mcp_token_service') as mock_service:
            mock_stats = {
                "total_tokens": 15,
                "active_tokens": 5,
                "expired_tokens": 10,
                "unique_users": 3
            }
            mock_service.get_token_stats = Mock(return_value=mock_stats)
            
            response = test_client.get("/api/v2/mcp-tokens/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["stats"] == mock_stats
            assert "successfully" in data["message"]
    
    def test_cleanup_endpoint(self, test_client):
        """Test POST /cleanup endpoint."""
        with patch('fastmcp.server.routes.mcp_token_routes.mcp_token_service') as mock_service:
            mock_service.cleanup_expired_tokens = AsyncMock(return_value=8)
            
            response = test_client.post("/api/v2/mcp-tokens/cleanup")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["cleaned_tokens"] == 8
            assert data["message"] == "Cleaned up 8 expired tokens"
    
    def test_health_endpoint(self, test_client):
        """Test GET /health endpoint."""
        with patch('fastmcp.server.routes.mcp_token_routes.mcp_token_service') as mock_service:
            mock_stats = {"total_tokens": 10, "active_tokens": 3}
            mock_service.get_token_stats = Mock(return_value=mock_stats)
            
            response = test_client.get("/api/v2/mcp-tokens/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "mcp_token_service"
            assert data["stats"] == mock_stats
    
    def test_endpoint_authentication_required(self):
        """Test that endpoints require authentication."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        app.include_router(router)
        
        # Don't override authentication dependency
        client = TestClient(app)
        
        # All endpoints should fail without authentication
        endpoints = [
            ("POST", "/api/v2/mcp-tokens/generate", {"expires_in_hours": 24}),
            ("DELETE", "/api/v2/mcp-tokens/revoke", None),
            ("GET", "/api/v2/mcp-tokens/stats", None),
            ("POST", "/api/v2/mcp-tokens/cleanup", None),
        ]
        
        for method, path, json_data in endpoints:
            if method == "POST":
                response = client.post(path, json=json_data)
            elif method == "DELETE":
                response = client.delete(path)
            elif method == "GET":
                response = client.get(path)
            
            # Should fail with authentication error (specific status depends on auth implementation)
            assert response.status_code in [401, 403, 422]


class TestLogging:
    """Test cases for logging behavior."""
    
    @pytest.mark.asyncio
    async def test_generate_token_logging(self, mock_user, mock_db, mock_mcp_token, mock_token_service):
        """Test logging during token generation."""
        mock_token_service.generate_mcp_token_from_user_id.return_value = mock_mcp_token
        
        with patch('fastmcp.server.routes.mcp_token_routes.logger') as mock_logger:
            request = GenerateTokenRequest()
            await generate_mcp_token(request, mock_user, mock_db)
            
            assert mock_logger.info.call_count == 2
            mock_logger.info.assert_any_call("Generating MCP token for user test@example.com")
            mock_logger.info.assert_any_call("Generated MCP token for user test@example.com")
    
    @pytest.mark.asyncio
    async def test_revoke_tokens_logging(self, mock_user, mock_db, mock_token_service):
        """Test logging during token revocation."""
        mock_token_service.revoke_user_tokens.return_value = True
        
        with patch('fastmcp.server.routes.mcp_token_routes.logger') as mock_logger:
            await revoke_mcp_tokens(mock_user, mock_db)
            
            mock_logger.info.assert_called_once_with("Revoked all MCP tokens for user test@example.com")
    
    @pytest.mark.asyncio
    async def test_cleanup_logging(self, mock_user, mock_db, mock_token_service):
        """Test logging during cleanup."""
        mock_token_service.cleanup_expired_tokens.return_value = 5
        
        with patch('fastmcp.server.routes.mcp_token_routes.logger') as mock_logger:
            await cleanup_expired_tokens(mock_user, mock_db)
            
            mock_logger.info.assert_called_once_with("User test@example.com triggered token cleanup: 5 tokens cleaned")
    
    @pytest.mark.asyncio
    async def test_error_logging(self, mock_user, mock_db, mock_token_service):
        """Test error logging."""
        mock_token_service.generate_mcp_token_from_user_id.side_effect = Exception("Test error")
        
        with patch('fastmcp.server.routes.mcp_token_routes.logger') as mock_logger:
            with pytest.raises(HTTPException):
                request = GenerateTokenRequest()
                await generate_mcp_token(request, mock_user, mock_db)
            
            mock_logger.error.assert_called()
            error_msg = mock_logger.error.call_args[0][0]
            assert "Error generating MCP token for user test-user-123" in error_msg