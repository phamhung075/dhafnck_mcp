"""Test suite for dual authentication middleware functionality"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastmcp.auth.middleware.dual_auth_middleware import DualAuthMiddleware
import sys
import os

# Mock external dependencies
class MockRequest:
    def __init__(self, headers=None, url="/test"):
        self.headers = headers or {}
        self.url = Mock()
        self.url.path = url
        self.state = Mock()

class MockResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

@pytest.mark.unit
class TestDualAuthMiddleware:
    """Test dual authentication middleware"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.middleware = DualAuthMiddleware(None)
    
    def test_middleware_initialization(self):
        """Test middleware properly initializes"""
        assert self.middleware is not None
        assert hasattr(self.middleware, 'app')
    
    @pytest.mark.asyncio
    async def test_middleware_allows_public_endpoints(self):
        """Test middleware allows access to public endpoints"""
        request = MockRequest(url="/public")
        call_next = AsyncMock(return_value=MockResponse())
        
        with patch.object(self.middleware, '_is_public_endpoint', return_value=True):
            response = await self.middleware.__call__(request, call_next)
            
        assert response.status_code == 200
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_middleware_validates_jwt_token(self):
        """Test middleware validates JWT tokens for protected endpoints"""
        request = MockRequest(headers={"Authorization": "Bearer valid_token"}, url="/protected")
        call_next = AsyncMock(return_value=MockResponse())
        
        with patch.object(self.middleware, '_is_public_endpoint', return_value=False), \
             patch.object(self.middleware, '_validate_jwt_token', return_value={"user_id": "123"}):
            response = await self.middleware.__call__(request, call_next)
            
        assert response.status_code == 200
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_middleware_validates_mcp_token(self):
        """Test middleware validates MCP tokens for protected endpoints"""
        request = MockRequest(headers={"X-MCP-Token": "mcp_token"}, url="/mcp")
        call_next = AsyncMock(return_value=MockResponse())
        
        with patch.object(self.middleware, '_is_public_endpoint', return_value=False), \
             patch.object(self.middleware, '_validate_mcp_token', return_value={"user_id": "456"}):
            response = await self.middleware.__call__(request, call_next)
            
        assert response.status_code == 200
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_middleware_rejects_invalid_token(self):
        """Test middleware rejects requests with invalid tokens"""
        request = MockRequest(headers={"Authorization": "Bearer invalid_token"}, url="/protected")
        
        with patch.object(self.middleware, '_is_public_endpoint', return_value=False), \
             patch.object(self.middleware, '_validate_jwt_token', return_value=None), \
             patch.object(self.middleware, '_validate_mcp_token', return_value=None):
            
            response = await self.middleware.__call__(request, Mock())
            
        assert response.status_code == 401
    
    def test_is_public_endpoint_identification(self):
        """Test identification of public endpoints"""
        public_paths = ["/auth/login", "/auth/signup", "/health", "/docs"]
        protected_paths = ["/tasks", "/projects", "/contexts"]
        
        for path in public_paths:
            assert self.middleware._is_public_endpoint(path) is True
            
        for path in protected_paths:
            assert self.middleware._is_public_endpoint(path) is False
    
    def test_extract_jwt_token_from_header(self):
        """Test JWT token extraction from Authorization header"""
        headers_with_token = {"Authorization": "Bearer test_token_123"}
        headers_without_token = {}
        headers_invalid_format = {"Authorization": "Basic test_token_123"}
        
        assert self.middleware._extract_jwt_token(headers_with_token) == "test_token_123"
        assert self.middleware._extract_jwt_token(headers_without_token) is None
        assert self.middleware._extract_jwt_token(headers_invalid_format) is None
    
    def test_extract_mcp_token_from_header(self):
        """Test MCP token extraction from X-MCP-Token header"""
        headers_with_token = {"X-MCP-Token": "mcp_test_token_456"}
        headers_without_token = {}
        
        assert self.middleware._extract_mcp_token(headers_with_token) == "mcp_test_token_456"
        assert self.middleware._extract_mcp_token(headers_without_token) is None
    
    @pytest.mark.asyncio
    async def test_middleware_handles_missing_auth_header(self):
        """Test middleware properly handles missing authentication headers"""
        request = MockRequest(url="/protected")
        
        with patch.object(self.middleware, '_is_public_endpoint', return_value=False):
            response = await self.middleware.__call__(request, Mock())
            
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_middleware_sets_user_context(self):
        """Test middleware sets user context on successful authentication"""
        request = MockRequest(headers={"Authorization": "Bearer valid_token"}, url="/protected")
        call_next = AsyncMock(return_value=MockResponse())
        
        user_data = {"user_id": "test_user_123", "email": "test@example.com"}
        
        with patch.object(self.middleware, '_is_public_endpoint', return_value=False), \
             patch.object(self.middleware, '_validate_jwt_token', return_value=user_data):
            
            await self.middleware.__call__(request, call_next)
            
        # Check that user context was set on request state
        assert hasattr(request.state, 'user')
        assert request.state.user == user_data
    
    def test_validate_jwt_token_with_valid_token(self):
        """Test JWT token validation with valid token"""
        valid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        
        with patch('fastmcp.auth.services.mcp_token_service.validate_jwt_token') as mock_validate:
            mock_validate.return_value = {"user_id": "123", "email": "test@example.com"}
            
            result = self.middleware._validate_jwt_token(valid_token)
            
        assert result is not None
        assert result["user_id"] == "123"
    
    def test_validate_jwt_token_with_invalid_token(self):
        """Test JWT token validation with invalid token"""
        invalid_token = "invalid.jwt.token"
        
        with patch('fastmcp.auth.services.mcp_token_service.validate_jwt_token') as mock_validate:
            mock_validate.return_value = None
            
            result = self.middleware._validate_jwt_token(invalid_token)
            
        assert result is None
    
    def test_validate_mcp_token_with_valid_token(self):
        """Test MCP token validation with valid token"""
        valid_token = "mcp_valid_token_789"
        
        with patch('fastmcp.auth.services.mcp_token_service.validate_mcp_token') as mock_validate:
            mock_validate.return_value = {"user_id": "456", "session_id": "session_123"}
            
            result = self.middleware._validate_mcp_token(valid_token)
            
        assert result is not None
        assert result["user_id"] == "456"
    
    def test_validate_mcp_token_with_invalid_token(self):
        """Test MCP token validation with invalid token"""
        invalid_token = "invalid_mcp_token"
        
        with patch('fastmcp.auth.services.mcp_token_service.validate_mcp_token') as mock_validate:
            mock_validate.return_value = None
            
            result = self.middleware._validate_mcp_token(invalid_token)
            
        assert result is None


@pytest.mark.integration
class TestDualAuthMiddlewareIntegration:
    """Integration tests for dual authentication middleware"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.middleware = DualAuthMiddleware(None)
    
    @pytest.mark.asyncio
    async def test_middleware_with_real_jwt_service(self):
        """Test middleware integration with real JWT service"""
        request = MockRequest(headers={"Authorization": "Bearer test_token"}, url="/tasks")
        call_next = AsyncMock(return_value=MockResponse())
        
        # This would require actual JWT service configuration
        # For now, we mock the service but test the integration points
        with patch('fastmcp.auth.services.mcp_token_service.validate_jwt_token') as mock_jwt:
            mock_jwt.return_value = {"user_id": "integration_test_user"}
            
            response = await self.middleware.__call__(request, call_next)
            
        assert response.status_code == 200
        mock_jwt.assert_called_once_with("test_token")
    
    @pytest.mark.asyncio
    async def test_middleware_fallback_authentication(self):
        """Test middleware falls back from JWT to MCP token authentication"""
        request = MockRequest(
            headers={
                "Authorization": "Bearer invalid_jwt",
                "X-MCP-Token": "valid_mcp_token"
            }, 
            url="/contexts"
        )
        call_next = AsyncMock(return_value=MockResponse())
        
        with patch('fastmcp.auth.services.mcp_token_service.validate_jwt_token') as mock_jwt, \
             patch('fastmcp.auth.services.mcp_token_service.validate_mcp_token') as mock_mcp:
            
            mock_jwt.return_value = None  # JWT validation fails
            mock_mcp.return_value = {"user_id": "mcp_user"}  # MCP validation succeeds
            
            response = await self.middleware.__call__(request, call_next)
            
        assert response.status_code == 200
        mock_jwt.assert_called_once_with("invalid_jwt")
        mock_mcp.assert_called_once_with("valid_mcp_token")
    
    @pytest.mark.asyncio
    async def test_middleware_with_error_handling(self):
        """Test middleware handles authentication service errors gracefully"""
        request = MockRequest(headers={"Authorization": "Bearer test_token"}, url="/projects")
        
        with patch('fastmcp.auth.services.mcp_token_service.validate_jwt_token') as mock_jwt:
            mock_jwt.side_effect = Exception("Authentication service error")
            
            response = await self.middleware.__call__(request, Mock())
            
        assert response.status_code == 401  # Should handle errors gracefully