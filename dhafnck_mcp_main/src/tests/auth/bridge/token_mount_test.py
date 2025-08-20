"""
Tests for FastAPI token router mounting on Starlette application.

This module tests the integration of FastAPI token management router
with the Starlette MCP server, replacing the Starlette bridge layer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from starlette.routing import BaseRoute, Mount
from starlette.middleware import Middleware
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.testclient import TestClient

from fastmcp.auth.bridge.token_mount import (
    create_token_fastapi_app,
    mount_token_router_on_starlette,
    integrate_token_router_with_mcp_server
)


class TestCreateTokenFastAPIApp:
    """Test creation of token management FastAPI application."""
    
    def test_create_token_fastapi_app_returns_fastapi_instance(self):
        """Test that function returns a FastAPI instance."""
        # Act
        app = create_token_fastapi_app()
        
        # Assert
        assert isinstance(app, FastAPI)
        assert app.title == "Token Management API"
        assert app.description == "API token management endpoints"
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"
    
    @patch('fastmcp.auth.bridge.token_mount.logger')
    def test_create_token_fastapi_app_logs_creation(self, mock_logger):
        """Test that app creation is logged."""
        # Act
        create_token_fastapi_app()
        
        # Assert
        mock_logger.info.assert_called_with("Created FastAPI token management app")
    
    def test_create_token_fastapi_app_has_cors_middleware(self):
        """Test that CORS middleware is properly configured."""
        # Act
        app = create_token_fastapi_app()
        
        # Assert
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == 'CORSMiddleware':
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
        assert "http://localhost:3000" in cors_middleware.kwargs["allow_origins"]
        assert "http://localhost:3800" in cors_middleware.kwargs["allow_origins"]
        assert cors_middleware.kwargs["allow_credentials"] is True
        assert cors_middleware.kwargs["allow_methods"] == ["*"]
        assert cors_middleware.kwargs["allow_headers"] == ["*"]
    
    @patch('fastmcp.auth.bridge.token_mount.token_router')
    def test_create_token_fastapi_app_includes_token_router(self, mock_router):
        """Test that token router is included in the app."""
        # Act
        app = create_token_fastapi_app()
        
        # Assert - Check that router was added
        assert len(app.routes) > 0
    
    def test_create_token_fastapi_app_has_health_endpoint(self):
        """Test that health check endpoint is available."""
        # Arrange
        app = create_token_fastapi_app()
        client = TestClient(app)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "token-management"


class TestMountTokenRouterOnStarlette:
    """Test mounting FastAPI token router on Starlette routes."""
    
    def test_mount_token_router_adds_mount_to_routes(self):
        """Test that a Mount is added to the routes list."""
        # Arrange
        initial_routes = []
        
        # Act
        updated_routes = mount_token_router_on_starlette(initial_routes)
        
        # Assert
        assert len(updated_routes) == 1
        assert isinstance(updated_routes[0], Mount)
        assert updated_routes[0].path == "/"
        assert isinstance(updated_routes[0].app, FastAPI)
    
    def test_mount_token_router_preserves_existing_routes(self):
        """Test that existing routes are preserved."""
        # Arrange
        mock_route = Mock(spec=BaseRoute)
        initial_routes = [mock_route]
        
        # Act
        updated_routes = mount_token_router_on_starlette(initial_routes)
        
        # Assert
        assert len(updated_routes) == 2
        assert mock_route in updated_routes
        assert isinstance(updated_routes[1], Mount)
    
    def test_mount_token_router_custom_mount_path(self):
        """Test mounting with custom path."""
        # Arrange
        initial_routes = []
        custom_path = "/custom/tokens"
        
        # Act
        updated_routes = mount_token_router_on_starlette(
            initial_routes, 
            mount_path=custom_path
        )
        
        # Assert
        assert len(updated_routes) == 1
        mount = updated_routes[0]
        assert isinstance(mount, Mount)
        # The mount path is always "/" as the FastAPI app handles the prefix
        assert mount.path == "/"
    
    @patch('fastmcp.auth.bridge.token_mount.logger')
    def test_mount_token_router_logs_mounting(self, mock_logger):
        """Test that mounting is logged."""
        # Arrange
        initial_routes = []
        mount_path = "/api/v2/tokens"
        
        # Act
        mount_token_router_on_starlette(initial_routes, mount_path)
        
        # Assert
        mock_logger.info.assert_called_with(
            f"Mounted FastAPI token router at {mount_path} (eliminating Starlette bridge)"
        )


class TestIntegrateTokenRouterWithMCPServer:
    """Test full integration of token router with MCP server."""
    
    def test_integrate_token_router_enabled(self):
        """Test integration when token router is enabled."""
        # Arrange
        initial_routes = []
        initial_middleware = []
        
        # Act
        routes, middleware = integrate_token_router_with_mcp_server(
            initial_routes,
            initial_middleware,
            enable_token_router=True
        )
        
        # Assert
        assert len(routes) == 1
        assert isinstance(routes[0], Mount)
        assert middleware == initial_middleware  # Middleware unchanged
    
    def test_integrate_token_router_disabled(self):
        """Test integration when token router is disabled."""
        # Arrange
        initial_routes = []
        initial_middleware = []
        
        # Act
        routes, middleware = integrate_token_router_with_mcp_server(
            initial_routes,
            initial_middleware,
            enable_token_router=False
        )
        
        # Assert
        assert routes == initial_routes  # No changes
        assert middleware == initial_middleware  # No changes
    
    def test_integrate_token_router_preserves_existing_routes_and_middleware(self):
        """Test that existing routes and middleware are preserved."""
        # Arrange
        mock_route = Mock(spec=BaseRoute)
        mock_middleware = Mock(spec=Middleware)
        initial_routes = [mock_route]
        initial_middleware = [mock_middleware]
        
        # Act
        routes, middleware = integrate_token_router_with_mcp_server(
            initial_routes,
            initial_middleware,
            enable_token_router=True
        )
        
        # Assert
        assert mock_route in routes
        assert mock_middleware in middleware
        assert len(routes) == 2  # Original + new mount
        assert len(middleware) == 1  # Unchanged
    
    @patch('fastmcp.auth.bridge.token_mount.logger')
    def test_integrate_token_router_logs_integration(self, mock_logger):
        """Test that integration is logged when enabled."""
        # Arrange
        initial_routes = []
        initial_middleware = []
        
        # Act
        integrate_token_router_with_mcp_server(
            initial_routes,
            initial_middleware,
            enable_token_router=True
        )
        
        # Assert
        mock_logger.info.assert_any_call(
            "Integrated token management with MCP server using FastAPI router"
        )
        mock_logger.info.assert_any_call(
            "✅ Starlette bridge layer eliminated - using direct FastAPI integration"
        )
    
    @patch('fastmcp.auth.bridge.token_mount.logger')
    def test_integrate_token_router_no_logging_when_disabled(self, mock_logger):
        """Test that no integration logging occurs when disabled."""
        # Arrange
        initial_routes = []
        initial_middleware = []
        
        # Act
        integrate_token_router_with_mcp_server(
            initial_routes,
            initial_middleware,
            enable_token_router=False
        )
        
        # Assert
        # Should not log integration messages
        integration_calls = [
            call for call in mock_logger.info.call_args_list
            if "Integrated token management" in str(call)
        ]
        assert len(integration_calls) == 0
    
    def test_integrate_token_router_returns_tuple(self):
        """Test that function returns a tuple of routes and middleware."""
        # Arrange
        initial_routes = []
        initial_middleware = []
        
        # Act
        result = integrate_token_router_with_mcp_server(
            initial_routes,
            initial_middleware,
            enable_token_router=True
        )
        
        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        routes, middleware = result
        assert isinstance(routes, list)
        assert isinstance(middleware, list)


class TestTokenMountIntegration:
    """Integration tests for token mount functionality."""
    
    def test_mounted_app_is_accessible(self):
        """Test that mounted FastAPI app is accessible through Starlette."""
        # Arrange
        starlette_app = Starlette()
        initial_routes = list(starlette_app.routes)
        
        # Act
        updated_routes = mount_token_router_on_starlette(initial_routes)
        starlette_app.routes = updated_routes
        client = TestClient(starlette_app)
        
        # Assert
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "token-management"
    
    def test_integration_with_mcp_server_flow(self):
        """Test the complete integration flow."""
        # Arrange
        starlette_app = Starlette()
        initial_routes = list(starlette_app.routes)
        initial_middleware = []
        
        # Act
        routes, middleware = integrate_token_router_with_mcp_server(
            initial_routes,
            initial_middleware,
            enable_token_router=True
        )
        starlette_app.routes = routes
        client = TestClient(starlette_app)
        
        # Assert
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "token-management"


if __name__ == "__main__":
    pytest.main([__file__])