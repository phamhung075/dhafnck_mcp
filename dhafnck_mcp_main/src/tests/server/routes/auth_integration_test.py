"""
Tests for Auth API Integration

This module tests the authentication endpoints integrated into the MCP server.
Tests cover registration, login, token refresh, and health check endpoints.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from starlette.requests import Request
from starlette.responses import JSONResponse
import json


class TestAuthIntegrationRoutes:
    """Test suite for auth integration routes."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        return session
    
    @pytest.fixture
    def mock_db_config(self, mock_db_session):
        """Create a mock database config."""
        config = Mock()
        config.get_session = Mock(return_value=mock_db_session)
        return config
    
    @pytest.fixture
    def mock_jwt_service(self):
        """Create a mock JWT service."""
        service = Mock()
        service.create_access_token = Mock(return_value="mock_access_token")
        service.create_refresh_token = Mock(return_value="mock_refresh_token")
        service.verify_refresh_token = Mock(return_value={"sub": "user123"})
        return service
    
    @pytest.fixture
    def mock_auth_service(self):
        """Create a mock auth service."""
        service = Mock()
        return service
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock Starlette request."""
        request = Mock(spec=Request)
        request.json = AsyncMock()
        return request
    
    @pytest.mark.asyncio
    async def test_register_endpoint_success(self, mock_request, mock_db_config, mock_jwt_service):
        """Test successful user registration."""
        # Setup
        mock_request.json.return_value = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.get_db_config', return_value=mock_db_config):
            with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.UserRepository') as MockUserRepo:
                with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.AuthService') as MockAuthService:
                    # Setup auth service mock
                    mock_user = Mock()
                    mock_user.username = "testuser"
                    
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.user = mock_user
                    mock_result.error_message = None
                    
                    mock_auth_instance = Mock()
                    mock_auth_instance.register_user = AsyncMock(return_value=mock_result)
                    MockAuthService.return_value = mock_auth_instance
                    
                    # Import and call the endpoint
                    from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
                    routes = create_auth_integration_routes()
                    
                    # Find register endpoint
                    register_endpoint = None
                    for route in routes:
                        if route.path == "/api/auth/register":
                            register_endpoint = route.endpoint
                            break
                    
                    assert register_endpoint is not None
                    
                    # Call the endpoint
                    response = await register_endpoint(mock_request)
                    
                    # Assertions
                    assert isinstance(response, JSONResponse)
                    assert response.status_code == 200
                    
                    # Check database commit was called
                    mock_db_config.get_session().commit.assert_called_once()
                    mock_db_config.get_session().close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_endpoint_failure(self, mock_request, mock_db_config):
        """Test failed user registration."""
        # Setup
        mock_request.json.return_value = {
            "email": "existing@example.com",
            "username": "existinguser",
            "password": "password"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.get_db_config', return_value=mock_db_config):
            with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.UserRepository') as MockUserRepo:
                with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.AuthService') as MockAuthService:
                    # Setup auth service mock for failure
                    mock_result = Mock()
                    mock_result.success = False
                    mock_result.user = None
                    mock_result.error_message = "User already exists"
                    
                    mock_auth_instance = Mock()
                    mock_auth_instance.register_user = AsyncMock(return_value=mock_result)
                    MockAuthService.return_value = mock_auth_instance
                    
                    # Import and call the endpoint
                    from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
                    routes = create_auth_integration_routes()
                    
                    # Find register endpoint
                    register_endpoint = None
                    for route in routes:
                        if route.path == "/api/auth/register":
                            register_endpoint = route.endpoint
                            break
                    
                    assert register_endpoint is not None
                    
                    # Call the endpoint
                    response = await register_endpoint(mock_request)
                    
                    # Assertions
                    assert isinstance(response, JSONResponse)
                    assert response.status_code == 400
                    
                    # Check database rollback was called
                    mock_db_config.get_session().rollback.assert_called_once()
                    mock_db_config.get_session().close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_endpoint_success(self, mock_request, mock_db_config):
        """Test successful user login."""
        # Setup
        mock_request.json.return_value = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.get_db_config', return_value=mock_db_config):
            with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.UserRepository') as MockUserRepo:
                with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.AuthService') as MockAuthService:
                    # Setup auth service mock
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.access_token = "mock_access_token"
                    mock_result.refresh_token = "mock_refresh_token"
                    mock_result.error_message = None
                    
                    mock_auth_instance = Mock()
                    mock_auth_instance.login = AsyncMock(return_value=mock_result)
                    MockAuthService.return_value = mock_auth_instance
                    
                    # Import and call the endpoint
                    from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
                    routes = create_auth_integration_routes()
                    
                    # Find login endpoint
                    login_endpoint = None
                    for route in routes:
                        if route.path == "/api/auth/login":
                            login_endpoint = route.endpoint
                            break
                    
                    assert login_endpoint is not None
                    
                    # Call the endpoint
                    response = await login_endpoint(mock_request)
                    
                    # Assertions
                    assert isinstance(response, JSONResponse)
                    assert response.status_code == 200
                    
                    # Check database commit was called
                    mock_db_config.get_session().commit.assert_called_once()
                    mock_db_config.get_session().close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_endpoint_invalid_credentials(self, mock_request, mock_db_config):
        """Test login with invalid credentials."""
        # Setup
        mock_request.json.return_value = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.get_db_config', return_value=mock_db_config):
            with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.UserRepository') as MockUserRepo:
                with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.AuthService') as MockAuthService:
                    # Setup auth service mock for failure
                    mock_result = Mock()
                    mock_result.success = False
                    mock_result.access_token = None
                    mock_result.refresh_token = None
                    mock_result.error_message = "Invalid credentials"
                    
                    mock_auth_instance = Mock()
                    mock_auth_instance.login = AsyncMock(return_value=mock_result)
                    MockAuthService.return_value = mock_auth_instance
                    
                    # Import and call the endpoint
                    from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
                    routes = create_auth_integration_routes()
                    
                    # Find login endpoint
                    login_endpoint = None
                    for route in routes:
                        if route.path == "/api/auth/login":
                            login_endpoint = route.endpoint
                            break
                    
                    assert login_endpoint is not None
                    
                    # Call the endpoint
                    response = await login_endpoint(mock_request)
                    
                    # Assertions
                    assert isinstance(response, JSONResponse)
                    assert response.status_code == 401
                    
                    # Check database rollback was called
                    mock_db_config.get_session().rollback.assert_called_once()
                    mock_db_config.get_session().close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_endpoint_success(self, mock_request):
        """Test successful token refresh."""
        # Setup
        mock_request.json.return_value = {
            "refresh_token": "valid_refresh_token"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.JWTService') as MockJWTService:
            # Setup JWT service mock
            mock_jwt_instance = Mock()
            mock_jwt_instance.verify_refresh_token = Mock(return_value={"sub": "user123"})
            mock_jwt_instance.create_access_token = Mock(return_value="new_access_token")
            mock_jwt_instance.create_refresh_token = Mock(return_value="new_refresh_token")
            MockJWTService.return_value = mock_jwt_instance
            
            # Import and call the endpoint
            from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
            routes = create_auth_integration_routes()
            
            # Find refresh endpoint
            refresh_endpoint = None
            for route in routes:
                if route.path == "/api/auth/refresh":
                    refresh_endpoint = route.endpoint
                    break
            
            assert refresh_endpoint is not None
            
            # Call the endpoint
            response = await refresh_endpoint(mock_request)
            
            # Assertions
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_refresh_endpoint_invalid_token(self, mock_request):
        """Test token refresh with invalid token."""
        # Setup
        mock_request.json.return_value = {
            "refresh_token": "invalid_refresh_token"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.JWTService') as MockJWTService:
            # Setup JWT service mock for invalid token
            mock_jwt_instance = Mock()
            mock_jwt_instance.verify_refresh_token = Mock(return_value=None)
            MockJWTService.return_value = mock_jwt_instance
            
            # Import and call the endpoint
            from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
            routes = create_auth_integration_routes()
            
            # Find refresh endpoint
            refresh_endpoint = None
            for route in routes:
                if route.path == "/api/auth/refresh":
                    refresh_endpoint = route.endpoint
                    break
            
            assert refresh_endpoint is not None
            
            # Call the endpoint
            response = await refresh_endpoint(mock_request)
            
            # Assertions
            assert isinstance(response, JSONResponse)
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_endpoint_missing_token(self, mock_request):
        """Test token refresh without providing token."""
        # Setup
        mock_request.json.return_value = {}
        
        # Import and call the endpoint
        from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
        routes = create_auth_integration_routes()
        
        # Find refresh endpoint
        refresh_endpoint = None
        for route in routes:
            if route.path == "/api/auth/refresh":
                refresh_endpoint = route.endpoint
                break
        
        assert refresh_endpoint is not None
        
        # Call the endpoint
        response = await refresh_endpoint(mock_request)
        
        # Assertions
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_auth_health_endpoint(self, mock_request):
        """Test auth health check endpoint."""
        # Import and call the endpoint
        from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
        routes = create_auth_integration_routes()
        
        # Find health endpoint
        health_endpoint = None
        for route in routes:
            if route.path == "/api/auth/health":
                health_endpoint = route.endpoint
                break
        
        assert health_endpoint is not None
        
        # Call the endpoint
        response = await health_endpoint(mock_request)
        
        # Assertions
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_register_endpoint_exception_handling(self, mock_request, mock_db_config):
        """Test register endpoint exception handling."""
        # Setup
        mock_request.json.return_value = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.get_db_config', return_value=mock_db_config):
            with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.UserRepository') as MockUserRepo:
                with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.AuthService') as MockAuthService:
                    # Setup auth service to raise exception
                    mock_auth_instance = Mock()
                    mock_auth_instance.register_user = AsyncMock(side_effect=Exception("Database error"))
                    MockAuthService.return_value = mock_auth_instance
                    
                    # Import and call the endpoint
                    from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
                    routes = create_auth_integration_routes()
                    
                    # Find register endpoint
                    register_endpoint = None
                    for route in routes:
                        if route.path == "/api/auth/register":
                            register_endpoint = route.endpoint
                            break
                    
                    assert register_endpoint is not None
                    
                    # Call the endpoint
                    response = await register_endpoint(mock_request)
                    
                    # Assertions
                    assert isinstance(response, JSONResponse)
                    assert response.status_code == 400
                    
                    # Check database rollback was called
                    mock_db_config.get_session().rollback.assert_called_once()
                    mock_db_config.get_session().close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_endpoint_exception_handling(self, mock_request, mock_db_config):
        """Test login endpoint exception handling."""
        # Setup
        mock_request.json.return_value = {
            "email": "test@example.com",
            "password": "password"
        }
        
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.get_db_config', return_value=mock_db_config):
            with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.UserRepository') as MockUserRepo:
                with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.AuthService') as MockAuthService:
                    # Setup auth service to raise exception
                    mock_auth_instance = Mock()
                    mock_auth_instance.login = AsyncMock(side_effect=Exception("Authentication error"))
                    MockAuthService.return_value = mock_auth_instance
                    
                    # Import and call the endpoint
                    from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
                    routes = create_auth_integration_routes()
                    
                    # Find login endpoint
                    login_endpoint = None
                    for route in routes:
                        if route.path == "/api/auth/login":
                            login_endpoint = route.endpoint
                            break
                    
                    assert login_endpoint is not None
                    
                    # Call the endpoint
                    response = await login_endpoint(mock_request)
                    
                    # Assertions
                    assert isinstance(response, JSONResponse)
                    assert response.status_code == 400
                    
                    # Check database rollback was called
                    mock_db_config.get_session().rollback.assert_called_once()
                    mock_db_config.get_session().close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_invalid_json(self, mock_request):
        """Test register endpoint with invalid JSON."""
        # Setup - simulate JSON parsing error
        mock_request.json.side_effect = Exception("Invalid JSON")
        
        # Import and call the endpoint
        from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
        routes = create_auth_integration_routes()
        
        # Find register endpoint
        register_endpoint = None
        for route in routes:
            if route.path == "/api/auth/register":
                register_endpoint = route.endpoint
                break
        
        assert register_endpoint is not None
        
        # Call the endpoint
        response = await register_endpoint(mock_request)
        
        # Assertions
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
    
    def test_create_auth_integration_routes_import_error(self):
        """Test route creation when imports fail."""
        with patch('dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration.AuthService', side_effect=ImportError("Module not found")):
            from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
            routes = create_auth_integration_routes()
            
            # Should return empty list on import error
            assert routes == []
    
    def test_route_paths_and_methods(self):
        """Test that all expected routes are created with correct paths and methods."""
        from dhafnck_mcp_main.src.fastmcp.server.routes.auth_integration import create_auth_integration_routes
        routes = create_auth_integration_routes()
        
        # Expected routes
        expected_routes = {
            "/api/auth/register": ["POST"],
            "/api/auth/login": ["POST"],
            "/api/auth/refresh": ["POST"],
            "/api/auth/health": ["GET"]
        }
        
        # Check all expected routes exist
        route_map = {}
        for route in routes:
            route_map[route.path] = route.methods
        
        for path, methods in expected_routes.items():
            assert path in route_map, f"Route {path} not found"
            assert route_map[path] == methods, f"Route {path} has wrong methods"