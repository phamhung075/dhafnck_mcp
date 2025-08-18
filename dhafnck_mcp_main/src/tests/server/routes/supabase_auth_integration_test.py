"""
Tests for Supabase Auth Integration routes in MCP Server
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route
import json
import os


class TestSupabaseAuthIntegration:
    """Test Supabase authentication integration with MCP server"""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")

    @pytest.fixture
    def mock_supabase_service(self):
        """Mock SupabaseAuthService"""
        with patch('fastmcp.server.routes.supabase_auth_integration.SupabaseAuthService') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_auth_result(self):
        """Create a mock auth result"""
        from dataclasses import dataclass
        
        @dataclass
        class MockAuthResult:
            success: bool
            user: dict = None
            session: dict = None
            error_message: str = None
            requires_email_verification: bool = False
        
        return MockAuthResult

    def test_create_supabase_auth_app_success(self, mock_env):
        """Test successful creation of Supabase auth app"""
        with patch('fastmcp.server.routes.supabase_auth_integration.supabase_router') as mock_router, \
             patch('fastmcp.server.routes.supabase_auth_integration.dev_router') as mock_dev_router:
            
            from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_app
            
            app = create_supabase_auth_app()
            
            assert isinstance(app, Starlette)
            # Check that middleware is configured
            assert len(app.middleware) > 0

    def test_create_supabase_auth_app_import_error(self, mock_env):
        """Test handling of import errors"""
        with patch('fastmcp.server.routes.supabase_auth_integration.supabase_router', side_effect=ImportError("Module not found")):
            from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_app
            
            app = create_supabase_auth_app()
            
            assert isinstance(app, Starlette)
            assert len(app.routes) == 0  # Empty routes on import error

    def test_create_supabase_auth_app_dev_mode(self, mock_env, monkeypatch):
        """Test that dev router is included in development mode"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        with patch('fastmcp.server.routes.supabase_auth_integration.supabase_router') as mock_router, \
             patch('fastmcp.server.routes.supabase_auth_integration.dev_router') as mock_dev_router, \
             patch('fastmcp.server.routes.supabase_auth_integration.logger') as mock_logger:
            
            from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_app
            
            app = create_supabase_auth_app()
            
            # Check that warning was logged
            mock_logger.warning.assert_called_with("⚠️  Development auth endpoints enabled at /auth/dev/*")

    def test_create_supabase_auth_integration_routes(self, mock_env, mock_supabase_service):
        """Test creation of integration routes"""
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        
        routes = create_supabase_auth_integration_routes()
        
        assert len(routes) == 6  # 5 auth endpoints + 1 health
        
        # Check route paths
        route_paths = [route.path for route in routes]
        assert "/auth/supabase/signup" in route_paths
        assert "/auth/supabase/signin" in route_paths
        assert "/auth/supabase/signout" in route_paths
        assert "/auth/supabase/password-reset" in route_paths
        assert "/auth/supabase/resend-verification" in route_paths
        assert "/auth/supabase/health" in route_paths

    def test_create_supabase_auth_integration_routes_import_error(self, mock_env):
        """Test handling of import errors in route creation"""
        with patch('fastmcp.server.routes.supabase_auth_integration.SupabaseAuthService', side_effect=ImportError("Module not found")):
            from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
            
            routes = create_supabase_auth_integration_routes()
            
            assert routes == []  # Empty routes on import error

    @pytest.mark.asyncio
    async def test_signup_endpoint_success(self, mock_env, mock_supabase_service, mock_auth_result):
        """Test successful signup endpoint"""
        # Setup mock
        mock_user = Mock(id="user-123", email="test@example.com", confirmed_at=None)
        mock_session = Mock(access_token="access-123", refresh_token="refresh-123")
        mock_result = mock_auth_result(
            success=True,
            user=mock_user,
            session=mock_session,
            requires_email_verification=True
        )
        mock_supabase_service.sign_up = AsyncMock(return_value=mock_result)
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/signup",
            json={
                "email": "test@example.com",
                "password": "password123",
                "username": "testuser"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["requires_email_verification"] is True
        assert "user" in data
        assert data["access_token"] == "access-123"

    @pytest.mark.asyncio
    async def test_signup_endpoint_failure(self, mock_env, mock_supabase_service, mock_auth_result):
        """Test failed signup endpoint"""
        # Setup mock
        mock_result = mock_auth_result(
            success=False,
            error_message="Email already registered"
        )
        mock_supabase_service.sign_up = AsyncMock(return_value=mock_result)
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/signup",
            json={
                "email": "existing@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_signin_endpoint_success(self, mock_env, mock_supabase_service, mock_auth_result):
        """Test successful signin endpoint"""
        # Setup mock
        mock_user = Mock(id="user-123", email="test@example.com")
        mock_session = Mock(access_token="access-123", refresh_token="refresh-123")
        mock_result = mock_auth_result(
            success=True,
            user=mock_user,
            session=mock_session
        )
        mock_supabase_service.sign_in = AsyncMock(return_value=mock_result)
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/signin",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["access_token"] == "access-123"
        assert "user" in data

    @pytest.mark.asyncio
    async def test_signin_endpoint_unverified_email(self, mock_env, mock_supabase_service, mock_auth_result):
        """Test signin with unverified email"""
        # Setup mock
        mock_result = mock_auth_result(
            success=False,
            requires_email_verification=True,
            error_message="Please verify your email"
        )
        mock_supabase_service.sign_in = AsyncMock(return_value=mock_result)
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/signin",
            json={
                "email": "unverified@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Please verify your email before signing in"

    @pytest.mark.asyncio
    async def test_signout_endpoint_success(self, mock_env, mock_supabase_service):
        """Test successful signout endpoint"""
        # Setup mock
        mock_supabase_service.sign_out = AsyncMock(return_value=True)
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/signout",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Signed out successfully"

    @pytest.mark.asyncio
    async def test_signout_endpoint_missing_auth(self, mock_env, mock_supabase_service):
        """Test signout without authorization header"""
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request without auth header
        response = client.post("/auth/supabase/signout")
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Missing authorization header"

    @pytest.mark.asyncio
    async def test_password_reset_endpoint_success(self, mock_env, mock_supabase_service, mock_auth_result):
        """Test successful password reset request"""
        # Setup mock
        mock_result = mock_auth_result(
            success=True,
            error_message="Password reset email sent"
        )
        mock_supabase_service.reset_password_request = AsyncMock(return_value=mock_result)
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/password-reset",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Password reset email sent"

    @pytest.mark.asyncio
    async def test_resend_verification_endpoint_success(self, mock_env, mock_supabase_service, mock_auth_result):
        """Test successful resend verification email"""
        # Setup mock
        mock_result = mock_auth_result(
            success=True,
            error_message="Verification email sent"
        )
        mock_supabase_service.resend_verification_email = AsyncMock(return_value=mock_result)
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/resend-verification",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Verification email sent"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, mock_env, mock_supabase_service):
        """Test health check endpoint"""
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.get("/auth/supabase/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "supabase_auth"
        assert len(data["endpoints"]) == 5

    @pytest.mark.asyncio
    async def test_endpoint_exception_handling(self, mock_env, mock_supabase_service):
        """Test exception handling in endpoints"""
        # Setup mock to raise exception
        mock_supabase_service.sign_up = AsyncMock(side_effect=Exception("Database error"))
        
        # Create app with routes
        from fastmcp.server.routes.supabase_auth_integration import create_supabase_auth_integration_routes
        routes = create_supabase_auth_integration_routes()
        app = Starlette(routes=routes)
        
        # Test client
        client = TestClient(app)
        
        # Make request
        response = client.post(
            "/auth/supabase/signup",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]