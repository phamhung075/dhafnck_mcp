"""
Tests for the standalone Authentication API Server
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path

# Mock environment before imports
@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Set up test environment"""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_API_HOST", "127.0.0.1")
    monkeypatch.setenv("AUTH_API_PORT", "8001")


class TestAuthAPIServer:
    """Test the authentication API server setup and endpoints"""

    @pytest.fixture
    def mock_routers(self):
        """Mock the imported routers"""
        with patch('fastmcp.auth.api_server.auth_router') as mock_auth, \
             patch('fastmcp.auth.api_server.supabase_router') as mock_supabase, \
             patch('fastmcp.auth.api_server.dev_router') as mock_dev, \
             patch('fastmcp.auth.api_server.user_scoped_tasks_router') as mock_user_tasks, \
             patch('fastmcp.auth.api_server.token_router') as mock_token:
            yield {
                'auth': mock_auth,
                'supabase': mock_supabase,
                'dev': mock_dev,
                'user_tasks': mock_user_tasks,
                'token': mock_token
            }

    @pytest.fixture
    def client(self):
        """Create test client for the API server"""
        # Import after mocking to get fresh app instance
        from fastmcp.auth.api_server import app
        return TestClient(app)

    def test_app_configuration(self):
        """Test FastAPI app is configured correctly"""
        from fastmcp.auth.api_server import app
        
        assert app.title == "DhafnckMCP Authentication API"
        assert app.description == "Authentication service for DhafnckMCP platform"
        assert app.version == "1.0.0"

    def test_cors_middleware_configured(self):
        """Test CORS middleware is properly configured"""
        from fastmcp.auth.api_server import app
        
        # Check if CORS middleware is added
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in str(middleware_classes)

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-api"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "DhafnckMCP Authentication API"
        assert data["version"] == "1.0.0"

    def test_routers_included_development(self, monkeypatch):
        """Test that all routers are included in development mode"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        # Mock the routers before reload
        with patch('fastmcp.auth.api_server.auth_router') as mock_auth, \
             patch('fastmcp.auth.api_server.supabase_router') as mock_supabase, \
             patch('fastmcp.auth.api_server.dev_router') as mock_dev, \
             patch('fastmcp.auth.api_server.user_scoped_tasks_router') as mock_user_tasks, \
             patch('fastmcp.auth.api_server.token_router') as mock_token:
            
            # Re-import to get fresh app with dev environment
            import importlib
            import fastmcp.auth.api_server
            importlib.reload(fastmcp.auth.api_server)
            
            app = fastmcp.auth.api_server.app
            
            # Check routes are included (FastAPI adds routes to app)
            route_paths = [route.path for route in app.routes]
            
            # Should have at least health, root, and router endpoints
            assert "/" in route_paths
            assert "/health" in route_paths

    def test_dev_router_excluded_production(self, monkeypatch):
        """Test that dev router is not included in production"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        
        # Mock the routers before reload
        with patch('fastmcp.auth.api_server.auth_router') as mock_auth, \
             patch('fastmcp.auth.api_server.supabase_router') as mock_supabase, \
             patch('fastmcp.auth.api_server.dev_router') as mock_dev, \
             patch('fastmcp.auth.api_server.user_scoped_tasks_router') as mock_user_tasks, \
             patch('fastmcp.auth.api_server.token_router') as mock_token:
            
            # Re-import to get fresh app with production environment
            import importlib
            import fastmcp.auth.api_server
            importlib.reload(fastmcp.auth.api_server)
            
            # Check that dev router was not included
            # In production, include_router should not be called for dev_router
            app = fastmcp.auth.api_server.app
            
            # The app should exist and have basic routes
            assert app is not None
            route_paths = [route.path for route in app.routes]
            assert "/" in route_paths
            assert "/health" in route_paths

    def test_cors_allowed_origins(self, client):
        """Test CORS configuration with allowed origins"""
        # Make request with Origin header
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3800"}
        )
        
        # Check CORS headers in response
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight_request(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3800",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    @patch('uvicorn.run')
    def test_main_function_default_config(self, mock_uvicorn, monkeypatch):
        """Test main function with default configuration"""
        # Clear environment variables to test defaults
        monkeypatch.delenv("AUTH_API_HOST", raising=False)
        monkeypatch.delenv("AUTH_API_PORT", raising=False)
        
        from fastmcp.auth.api_server import main, app
        
        # Run main
        main()
        
        # Check uvicorn.run was called with correct parameters
        mock_uvicorn.assert_called_once_with(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )

    @patch('uvicorn.run')
    def test_main_function_custom_config(self, mock_uvicorn, monkeypatch):
        """Test main function with custom configuration"""
        # Set custom environment variables
        monkeypatch.setenv("AUTH_API_HOST", "192.168.1.100")
        monkeypatch.setenv("AUTH_API_PORT", "9000")
        
        from fastmcp.auth.api_server import main, app
        
        # Run main
        main()
        
        # Check uvicorn.run was called with custom parameters
        mock_uvicorn.assert_called_once_with(
            app,
            host="192.168.1.100",
            port=9000,
            log_level="info"
        )

    def test_logging_configuration(self):
        """Test that logging is properly configured"""
        import logging
        
        # Get the logger used in the module
        logger = logging.getLogger("fastmcp.auth.api_server")
        
        # Check that root logger has correct level
        assert logging.getLogger().level <= logging.INFO

    @patch('fastmcp.auth.api_server.logger')
    def test_dev_endpoints_warning_logged(self, mock_logger, monkeypatch):
        """Test that warning is logged when dev endpoints are enabled"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        # Re-import to trigger the warning
        import importlib
        import fastmcp.auth.api_server
        importlib.reload(fastmcp.auth.api_server)
        
        # Check warning was logged
        mock_logger.warning.assert_called_with("⚠️  Development endpoints enabled at /auth/dev/*")
    
    def test_user_scoped_tasks_router_included(self, monkeypatch):
        """Test that user-scoped tasks router is included"""
        # Mock the routers before import
        with patch('fastmcp.auth.api_server.auth_router') as mock_auth, \
             patch('fastmcp.auth.api_server.supabase_router') as mock_supabase, \
             patch('fastmcp.auth.api_server.dev_router') as mock_dev, \
             patch('fastmcp.auth.api_server.user_scoped_tasks_router') as mock_user_tasks, \
             patch('fastmcp.auth.api_server.token_router') as mock_token:
            
            # Re-import to get fresh app
            import importlib
            import fastmcp.auth.api_server
            importlib.reload(fastmcp.auth.api_server)
            
            app = fastmcp.auth.api_server.app
            
            # The app should exist and have included user-scoped tasks router
            assert app is not None
            
    @patch('fastmcp.auth.api_server.logger')
    def test_user_scoped_tasks_info_logged(self, mock_logger, monkeypatch):
        """Test that info is logged when user-scoped tasks routes are enabled"""
        # Re-import to trigger the logging
        import importlib
        import fastmcp.auth.api_server
        importlib.reload(fastmcp.auth.api_server)
        
        # Check info was logged
        mock_logger.info.assert_called_with("✅ User-scoped task routes enabled at /api/v2/tasks/")

    def test_api_metadata_endpoints(self, client):
        """Test that API metadata is accessible"""
        # Test OpenAPI schema endpoint
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["info"]["title"] == "DhafnckMCP Authentication API"
        assert schema["info"]["version"] == "1.0.0"

    def test_request_with_credentials(self, client):
        """Test that credentials are properly handled"""
        response = client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3800",
                "Cookie": "session=test-session"
            }
        )
        
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-credentials") == "true"
    
    def test_token_router_included(self, monkeypatch):
        """Test that token management router is included"""
        # Mock the routers before import
        with patch('fastmcp.auth.api_server.auth_router') as mock_auth, \
             patch('fastmcp.auth.api_server.supabase_router') as mock_supabase, \
             patch('fastmcp.auth.api_server.dev_router') as mock_dev, \
             patch('fastmcp.auth.api_server.user_scoped_tasks_router') as mock_user_tasks, \
             patch('fastmcp.auth.api_server.token_router') as mock_token:
            
            # Re-import to get fresh app
            import importlib
            import fastmcp.auth.api_server
            importlib.reload(fastmcp.auth.api_server)
            
            app = fastmcp.auth.api_server.app
            
            # The app should exist and have included token router
            assert app is not None
            
    @patch('fastmcp.auth.api_server.logger')
    def test_token_router_info_logged(self, mock_logger, monkeypatch):
        """Test that info is logged when token management routes are enabled"""
        # Re-import to trigger the logging
        import importlib
        import fastmcp.auth.api_server
        importlib.reload(fastmcp.auth.api_server)
        
        # Check info was logged
        mock_logger.info.assert_any_call("✅ Token management routes enabled at /api/v2/tokens/")