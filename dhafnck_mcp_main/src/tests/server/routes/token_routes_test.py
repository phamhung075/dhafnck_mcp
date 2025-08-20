import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import json

import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fastmcp.server.routes.token_routes import (
    handle_generate_token,
    handle_list_tokens,
    handle_get_token_details,
    handle_revoke_token,
    handle_update_token,
    handle_rotate_token,
    handle_validate_token,
    handle_get_token_usage,
    token_routes,
)


class TestTokenRoutesHandlers:
    """Test individual token route handlers."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = Mock()
        user.id = "user-123"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.generate_token_handler')
    async def test_handle_generate_token_success(self, mock_generate_handler, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test successful token generation."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Mock token response
        mock_token_response = Mock()
        mock_token_response.dict.return_value = {
            "id": "tok_123",
            "name": "Test Token",
            "token": "jwt.token.value",
            "scopes": ["read"],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "is_active": True,
            "rate_limit": 1000,
            "metadata": {}
        }
        mock_generate_handler.return_value = mock_token_response
        
        # Create request
        request = Mock(spec=Request)
        request.json = AsyncMock(return_value={
            "name": "Test Token",
            "scopes": ["read"],
            "expires_in_days": 30
        })
        
        # Call handler
        response = await handle_generate_token(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["id"] == "tok_123"
        assert body["name"] == "Test Token"
        assert body["token"] == "jwt.token.value"
        
        # Verify calls
        mock_get_current_user.assert_called_once_with(request)
        mock_generate_handler.assert_called_once()

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    async def test_handle_generate_token_unauthorized(self, mock_get_current_user):
        """Test token generation with unauthorized user."""
        # Setup mock to return None (no user)
        mock_get_current_user.return_value = None
        
        # Create request
        request = Mock(spec=Request)
        
        # Call handler
        response = await handle_generate_token(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        body = json.loads(response.body)
        assert body["error"] == "Unauthorized"

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    async def test_handle_generate_token_invalid_request(self, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test token generation with invalid request data."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Create request with invalid data (missing required field)
        request = Mock(spec=Request)
        request.json = AsyncMock(return_value={
            "scopes": ["read"]  # Missing required "name" field
        })
        
        # Call handler
        response = await handle_generate_token(request)
        
        # Verify error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        body = json.loads(response.body)
        assert "error" in body

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.list_tokens_handler')
    async def test_handle_list_tokens_success(self, mock_list_handler, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test successful token listing."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Mock list response
        mock_list_response = Mock()
        mock_list_response.dict.return_value = {
            "data": [
                {
                    "id": "tok_1",
                    "name": "Token 1",
                    "scopes": ["read"],
                    "is_active": True
                },
                {
                    "id": "tok_2",
                    "name": "Token 2",
                    "scopes": ["read", "write"],
                    "is_active": False
                }
            ],
            "total": 2
        }
        mock_list_handler.return_value = mock_list_response
        
        # Create request
        request = Mock(spec=Request)
        request.query_params = {"skip": "0", "limit": "10"}
        
        # Call handler
        response = await handle_list_tokens(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["total"] == 2
        assert len(body["data"]) == 2
        assert body["data"][0]["id"] == "tok_1"
        
        # Verify handler was called with correct params
        mock_list_handler.assert_called_once_with(mock_user, mock_db, 0, 10)

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.get_token_details_handler')
    async def test_handle_get_token_details_success(self, mock_details_handler, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test getting token details successfully."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Mock token details response
        mock_token_response = Mock()
        mock_token_response.dict.return_value = {
            "id": "tok_123",
            "name": "Test Token",
            "scopes": ["read", "write"],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "last_used_at": None,
            "usage_count": 0,
            "rate_limit": 1000,
            "is_active": True,
            "metadata": {}
        }
        mock_details_handler.return_value = mock_token_response
        
        # Create request
        request = Mock(spec=Request)
        request.path_params = {"token_id": "tok_123"}
        
        # Call handler
        response = await handle_get_token_details(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["id"] == "tok_123"
        assert body["name"] == "Test Token"
        
        # Verify handler was called
        mock_details_handler.assert_called_once_with("tok_123", mock_user, mock_db)

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    async def test_handle_get_token_details_missing_id(self, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test getting token details without token ID."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Create request without token_id
        request = Mock(spec=Request)
        request.path_params = {}
        
        # Call handler
        response = await handle_get_token_details(request)
        
        # Verify error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["error"] == "Token ID required"

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.revoke_token_handler')
    async def test_handle_revoke_token_success(self, mock_revoke_handler, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test successful token revocation."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        mock_revoke_handler.return_value = {"message": "Token revoked successfully"}
        
        # Create request
        request = Mock(spec=Request)
        request.path_params = {"token_id": "tok_123"}
        
        # Call handler
        response = await handle_revoke_token(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["message"] == "Token revoked successfully"
        
        # Verify handler was called
        mock_revoke_handler.assert_called_once_with("tok_123", mock_user, mock_db)

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.update_token_handler')
    async def test_handle_update_token_success(self, mock_update_handler, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test successful token update."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Mock updated token response
        mock_token_response = Mock()
        mock_token_response.dict.return_value = {
            "id": "tok_123",
            "name": "Updated Token",
            "scopes": ["read", "write", "admin"],
            "is_active": False,
            "rate_limit": 2000
        }
        mock_update_handler.return_value = mock_token_response
        
        # Create request
        request = Mock(spec=Request)
        request.path_params = {"token_id": "tok_123"}
        request.json = AsyncMock(return_value={
            "name": "Updated Token",
            "scopes": ["read", "write", "admin"],
            "is_active": False,
            "rate_limit": 2000
        })
        
        # Call handler
        response = await handle_update_token(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["name"] == "Updated Token"
        assert body["is_active"] is False
        assert body["rate_limit"] == 2000
        
        # Verify handler was called
        mock_update_handler.assert_called_once()

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.rotate_token_handler')
    async def test_handle_rotate_token_success(self, mock_rotate_handler, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test successful token rotation."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Mock rotated token response
        mock_rotate_handler.return_value = {
            "id": "tok_new123",
            "name": "Test Token (rotated)",
            "token": "new.jwt.token",
            "scopes": ["read", "write"],
            "metadata": {"rotated_from": "tok_123"}
        }
        
        # Create request
        request = Mock(spec=Request)
        request.path_params = {"token_id": "tok_123"}
        
        # Call handler
        response = await handle_rotate_token(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["id"] == "tok_new123"
        assert body["name"] == "Test Token (rotated)"
        assert body["token"] == "new.jwt.token"
        assert body["metadata"]["rotated_from"] == "tok_123"
        
        # Verify handler was called
        mock_rotate_handler.assert_called_once_with("tok_123", mock_user, mock_db)

    @pytest.mark.asyncio
    async def test_handle_validate_token_no_auth_header(self):
        """Test token validation without authorization header."""
        # Create request without auth header
        request = Mock(spec=Request)
        request.headers = {}
        
        # Call handler
        response = await handle_validate_token(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["valid"] is False

    @pytest.mark.asyncio
    async def test_handle_validate_token_invalid_header(self):
        """Test token validation with invalid authorization header."""
        # Create request with invalid auth header
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Basic invalid"}
        
        # Call handler
        response = await handle_validate_token(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["valid"] is False

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.get_token_usage_stats_handler')
    async def test_handle_get_token_usage_success(self, mock_usage_handler, mock_get_db, mock_get_current_user, mock_user, mock_db):
        """Test getting token usage statistics successfully."""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([mock_db])
        
        # Mock usage stats response
        mock_usage_handler.return_value = {
            "token_id": "tok_123",
            "total_requests": 1500,
            "last_used_at": datetime.utcnow().isoformat(),
            "created_at": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=23)).isoformat(),
            "is_expired": False,
            "is_active": True,
            "rate_limit": 1000,
            "avg_requests_per_hour": 8.93,
            "time_until_expiry": 1987200.0
        }
        
        # Create request
        request = Mock(spec=Request)
        request.path_params = {"token_id": "tok_123"}
        
        # Call handler
        response = await handle_get_token_usage(request)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["token_id"] == "tok_123"
        assert body["total_requests"] == 1500
        assert body["avg_requests_per_hour"] == 8.93
        assert body["is_expired"] is False
        
        # Verify handler was called
        mock_usage_handler.assert_called_once_with("tok_123", mock_user, mock_db)


class TestTokenRoutesIntegration:
    """Test token routes integration with Starlette app."""

    @pytest.fixture
    def app(self):
        """Create a Starlette app with token routes."""
        app = Starlette(routes=token_routes)
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    def test_token_routes_registered(self):
        """Test that all token routes are properly registered."""
        assert len(token_routes) == 8
        
        # Check route paths and methods
        route_specs = [
            ("/api/v2/tokens", ["POST"]),  # generate
            ("/api/v2/tokens", ["GET"]),   # list
            ("/api/v2/tokens/{token_id}", ["GET"]),  # details
            ("/api/v2/tokens/{token_id}", ["DELETE"]),  # revoke
            ("/api/v2/tokens/{token_id}", ["PATCH"]),  # update
            ("/api/v2/tokens/{token_id}/rotate", ["POST"]),  # rotate
            ("/api/v2/tokens/validate", ["POST"]),  # validate
            ("/api/v2/tokens/{token_id}/usage", ["GET"]),  # usage
        ]
        
        for i, (path, methods) in enumerate(route_specs):
            route = token_routes[i]
            assert route.path == path
            assert route.methods == set(methods)

    @patch('fastmcp.server.routes.token_routes.get_current_user')
    def test_unauthorized_access(self, mock_get_current_user, client):
        """Test that all endpoints return 401 for unauthorized access."""
        # Mock no user (unauthorized)
        mock_get_current_user.return_value = None
        
        # Test all endpoints that require auth
        test_cases = [
            ("POST", "/api/v2/tokens", {"name": "Test"}),
            ("GET", "/api/v2/tokens", None),
            ("GET", "/api/v2/tokens/tok_123", None),
            ("DELETE", "/api/v2/tokens/tok_123", None),
            ("PATCH", "/api/v2/tokens/tok_123", {"name": "Updated"}),
            ("POST", "/api/v2/tokens/tok_123/rotate", None),
            ("GET", "/api/v2/tokens/tok_123/usage", None),
        ]
        
        for method, path, json_data in test_cases:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path, json=json_data)
            elif method == "DELETE":
                response = client.delete(path)
            elif method == "PATCH":
                response = client.patch(path, json=json_data)
            
            assert response.status_code == 401
            assert response.json()["error"] == "Unauthorized"

    def test_validate_endpoint_without_auth(self, client):
        """Test validate endpoint works without user auth (uses token auth)."""
        # Test without auth header
        response = client.post("/api/v2/tokens/validate")
        assert response.status_code == 200
        assert response.json()["valid"] is False
        
        # Test with wrong auth type
        response = client.post(
            "/api/v2/tokens/validate",
            headers={"Authorization": "Basic dGVzdDp0ZXN0"}
        )
        assert response.status_code == 200
        assert response.json()["valid"] is False


class TestErrorHandling:
    """Test error handling in token routes."""

    @pytest.fixture
    def app(self):
        """Create a Starlette app with token routes."""
        return Starlette(routes=token_routes)

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    def test_database_error_handling(self, mock_get_db, mock_get_current_user, client):
        """Test handling of database errors."""
        # Setup mocks
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database error
        mock_get_db.side_effect = Exception("Database connection failed")
        
        # Test token generation with DB error
        response = client.post("/api/v2/tokens", json={"name": "Test Token"})
        
        assert response.status_code == 400
        assert "Database connection failed" in response.json()["error"]

    @patch('fastmcp.server.routes.token_routes.get_current_user')
    @patch('fastmcp.server.routes.token_routes.get_db')
    @patch('fastmcp.server.routes.token_routes.generate_token_handler')
    def test_handler_exception_handling(self, mock_handler, mock_get_db, mock_get_current_user, client):
        """Test handling of exceptions from route handlers."""
        # Setup mocks
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = iter([Mock()])
        
        # Mock handler raising exception
        mock_handler.side_effect = ValueError("Invalid token configuration")
        
        # Test token generation with handler error
        response = client.post("/api/v2/tokens", json={"name": "Test Token"})
        
        assert response.status_code == 400
        assert "Invalid token configuration" in response.json()["error"]


class TestRequestParsing:
    """Test request parsing in token routes."""

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    async def test_query_params_parsing(self, mock_get_current_user):
        """Test parsing of query parameters."""
        mock_get_current_user.return_value = Mock(id="user-123")
        
        # Test with custom skip/limit
        request = Mock(spec=Request)
        request.query_params = {"skip": "20", "limit": "50"}
        
        with patch('fastmcp.server.routes.token_routes.get_db') as mock_get_db:
            with patch('fastmcp.server.routes.token_routes.list_tokens_handler') as mock_handler:
                mock_get_db.return_value = iter([Mock()])
                mock_handler.return_value = Mock(dict=Mock(return_value={"data": [], "total": 0}))
                
                await handle_list_tokens(request)
                
                # Verify parsed values
                mock_handler.assert_called_once()
                call_args = mock_handler.call_args[0]
                assert call_args[2] == 20  # skip
                assert call_args[3] == 50  # limit

    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes.get_current_user')
    async def test_default_query_params(self, mock_get_current_user):
        """Test default query parameters."""
        mock_get_current_user.return_value = Mock(id="user-123")
        
        # Test without query params
        request = Mock(spec=Request)
        request.query_params = {}
        
        with patch('fastmcp.server.routes.token_routes.get_db') as mock_get_db:
            with patch('fastmcp.server.routes.token_routes.list_tokens_handler') as mock_handler:
                mock_get_db.return_value = iter([Mock()])
                mock_handler.return_value = Mock(dict=Mock(return_value={"data": [], "total": 0}))
                
                await handle_list_tokens(request)
                
                # Verify default values
                mock_handler.assert_called_once()
                call_args = mock_handler.call_args[0]
                assert call_args[2] == 0    # default skip
                assert call_args[3] == 100  # default limit