"""Test suite for JWT authentication middleware"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastmcp.auth.middleware.jwt_auth_middleware import JWTAuthMiddleware
import json


class MockRequest:
    def __init__(self, headers=None, url="/test"):
        self.headers = headers or {}
        self.url = Mock()
        self.url.path = url
        self.state = Mock()

class MockResponse:
    def __init__(self, status_code=200, content=None):
        self.status_code = status_code
        self.content = content or {}


@pytest.mark.unit
class TestJWTAuthMiddleware:
    """Test JWT authentication middleware"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.middleware = JWTAuthMiddleware(None)
    
    def test_middleware_initialization(self):
        """Test middleware initializes correctly"""
        assert self.middleware is not None
        assert hasattr(self.middleware, 'app')
    
    @pytest.mark.asyncio
    async def test_allows_health_check_endpoint(self):
        """Test middleware allows health check endpoints without authentication"""
        request = MockRequest(url="/health")
        call_next = AsyncMock(return_value=MockResponse())
        
        response = await self.middleware.__call__(request, call_next)
        
        assert response.status_code == 200
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_allows_auth_endpoints(self):
        """Test middleware allows authentication endpoints without JWT"""
        auth_paths = ["/auth/login", "/auth/signup", "/auth/refresh"]
        
        for path in auth_paths:
            request = MockRequest(url=path)
            call_next = AsyncMock(return_value=MockResponse())
            
            response = await self.middleware.__call__(request, call_next)
            
            assert response.status_code == 200
            call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_requires_jwt_for_protected_endpoints(self):
        """Test middleware requires JWT for protected endpoints"""
        protected_paths = ["/tasks", "/projects", "/contexts"]
        
        for path in protected_paths:
            request = MockRequest(url=path)  # No Authorization header
            
            response = await self.middleware.__call__(request, Mock())
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_validates_bearer_token_format(self):
        """Test middleware validates Bearer token format"""
        invalid_formats = [
            "invalid_token",
            "Basic dGVzdDp0ZXN0",
            "Bearer",
            ""
        ]
        
        for invalid_format in invalid_formats:
            request = MockRequest(
                headers={"Authorization": invalid_format}, 
                url="/tasks"
            )
            
            response = await self.middleware.__call__(request, Mock())
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_validates_jwt_token_with_service(self):
        """Test middleware validates JWT token using JWT service"""
        request = MockRequest(
            headers={"Authorization": "Bearer valid_jwt_token"}, 
            url="/tasks"
        )
        call_next = AsyncMock(return_value=MockResponse())
        
        user_payload = {
            "user_id": "user123",
            "email": "test@example.com",
            "exp": 1234567890
        }
        
        with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
            mock_decode.return_value = user_payload
            
            response = await self.middleware.__call__(request, call_next)
            
        assert response.status_code == 200
        mock_decode.assert_called_once_with("valid_jwt_token")
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_rejects_expired_jwt_token(self):
        """Test middleware rejects expired JWT tokens"""
        request = MockRequest(
            headers={"Authorization": "Bearer expired_token"}, 
            url="/projects"
        )
        
        with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
            mock_decode.side_effect = Exception("Token expired")
            
            response = await self.middleware.__call__(request, Mock())
            
        assert response.status_code == 401
        mock_decode.assert_called_once_with("expired_token")
    
    @pytest.mark.asyncio
    async def test_rejects_invalid_jwt_token(self):
        """Test middleware rejects invalid JWT tokens"""
        request = MockRequest(
            headers={"Authorization": "Bearer invalid_token"}, 
            url="/contexts"
        )
        
        with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
            mock_decode.side_effect = Exception("Invalid token")
            
            response = await self.middleware.__call__(request, Mock())
            
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_sets_user_context_on_successful_auth(self):
        """Test middleware sets user context on successful authentication"""
        request = MockRequest(
            headers={"Authorization": "Bearer valid_token"}, 
            url="/tasks"
        )
        call_next = AsyncMock(return_value=MockResponse())
        
        user_payload = {
            "user_id": "user456",
            "email": "user@example.com",
            "role": "user"
        }
        
        with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
            mock_decode.return_value = user_payload
            
            await self.middleware.__call__(request, call_next)
            
        # Verify user context was set
        assert hasattr(request.state, 'user')
        assert request.state.user == user_payload
    
    def test_extract_bearer_token_from_header(self):
        """Test extraction of Bearer token from Authorization header"""
        valid_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        invalid_headers = [
            "Basic dGVzdA==",
            "Bearer",
            "invalid_format",
            ""
        ]
        
        # Test valid extraction
        token = self.middleware._extract_bearer_token(valid_header)
        assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        
        # Test invalid extractions
        for invalid_header in invalid_headers:
            token = self.middleware._extract_bearer_token(invalid_header)
            assert token is None
    
    def test_is_public_endpoint_identification(self):
        """Test identification of public vs protected endpoints"""
        public_endpoints = [
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/signup",
            "/auth/refresh"
        ]
        
        protected_endpoints = [
            "/tasks",
            "/projects", 
            "/contexts",
            "/users/profile",
            "/admin/settings"
        ]
        
        for endpoint in public_endpoints:
            assert self.middleware._is_public_endpoint(endpoint) is True
            
        for endpoint in protected_endpoints:
            assert self.middleware._is_public_endpoint(endpoint) is False
    
    @pytest.mark.asyncio
    async def test_handles_malformed_authorization_header(self):
        """Test middleware handles malformed Authorization headers gracefully"""
        malformed_headers = [
            {"Authorization": "Bearer "},
            {"Authorization": "Bearer\t\n"},
            {"Authorization": "Bearer multiple tokens here"},
            {"Authorization": "NotBearer token"}
        ]
        
        for headers in malformed_headers:
            request = MockRequest(headers=headers, url="/tasks")
            
            response = await self.middleware.__call__(request, Mock())
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_case_insensitive_bearer_matching(self):
        """Test Bearer token matching is case insensitive"""
        variations = ["Bearer token", "bearer token", "BEARER token"]
        
        for auth_header in variations:
            request = MockRequest(
                headers={"Authorization": auth_header}, 
                url="/tasks"
            )
            call_next = AsyncMock(return_value=MockResponse())
            
            with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
                mock_decode.return_value = {"user_id": "test"}
                
                response = await self.middleware.__call__(request, call_next)
                
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_preserves_request_state(self):
        """Test middleware preserves existing request state"""
        request = MockRequest(
            headers={"Authorization": "Bearer valid_token"}, 
            url="/tasks"
        )
        request.state.existing_data = "should_be_preserved"
        call_next = AsyncMock(return_value=MockResponse())
        
        user_payload = {"user_id": "user789"}
        
        with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
            mock_decode.return_value = user_payload
            
            await self.middleware.__call__(request, call_next)
            
        # Verify both existing and new state are preserved
        assert request.state.existing_data == "should_be_preserved"
        assert request.state.user == user_payload


@pytest.mark.integration
class TestJWTAuthMiddlewareIntegration:
    """Integration tests for JWT authentication middleware"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.middleware = JWTAuthMiddleware(None)
    
    @pytest.mark.asyncio
    async def test_end_to_end_authentication_flow(self):
        """Test complete authentication flow from token to user context"""
        # Simulate a real JWT token (would be created by auth service)
        test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdF91c2VyIn0"
        
        request = MockRequest(
            headers={"Authorization": f"Bearer {test_token}"}, 
            url="/projects"
        )
        call_next = AsyncMock(return_value=MockResponse())
        
        expected_user = {
            "user_id": "test_user",
            "email": "test@example.com",
            "permissions": ["read", "write"]
        }
        
        with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
            mock_decode.return_value = expected_user
            
            response = await self.middleware.__call__(request, call_next)
            
        assert response.status_code == 200
        assert request.state.user == expected_user
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_middleware_with_jwt_service_error_handling(self):
        """Test middleware handles JWT service errors appropriately"""
        request = MockRequest(
            headers={"Authorization": "Bearer problematic_token"}, 
            url="/tasks"
        )
        
        # Test various JWT service exceptions
        jwt_exceptions = [
            Exception("Token signature verification failed"),
            Exception("Token has expired"), 
            Exception("Invalid token format"),
            ValueError("Malformed payload"),
            KeyError("Missing required claim")
        ]
        
        for exception in jwt_exceptions:
            with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
                mock_decode.side_effect = exception
                
                response = await self.middleware.__call__(request, Mock())
                
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_middleware_performance_with_valid_tokens(self):
        """Test middleware performance with valid tokens"""
        import time
        
        request = MockRequest(
            headers={"Authorization": "Bearer performance_test_token"}, 
            url="/contexts"
        )
        call_next = AsyncMock(return_value=MockResponse())
        
        user_payload = {"user_id": "perf_test_user"}
        
        with patch('fastmcp.auth.domain.services.jwt_service.JWTService.decode_token') as mock_decode:
            mock_decode.return_value = user_payload
            
            start_time = time.time()
            response = await self.middleware.__call__(request, call_next)
            end_time = time.time()
            
        # Middleware should be fast (< 100ms for mocked operations)
        processing_time = end_time - start_time
        assert processing_time < 0.1
        assert response.status_code == 200