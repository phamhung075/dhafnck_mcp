"""
Tests for Starlette-compatible token management routes backup.

This module tests the Starlette bridge routes for token management
that bridge FastAPI token router with the main MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.applications import Starlette
import json

from fastmcp.server.routes.token_routes_backup import (
    get_current_user_from_request,
    handle_generate_token,
    handle_list_tokens,
    handle_get_token_details,
    handle_revoke_token,
    handle_update_token,
    handle_rotate_token,
    handle_validate_token,
    handle_get_token_usage,
    token_routes
)


class TestGetCurrentUserFromRequest:
    """Test user extraction and validation from Starlette request."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_auth_header(self):
        """Test handling request without Authorization header."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_db = Mock()
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_auth_header(self):
        """Test handling request with invalid Authorization header."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Basic sometoken"}
        mock_db = Mock()
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.jwt_service')
    async def test_get_current_user_invalid_token(self, mock_jwt_service):
        """Test handling request with invalid JWT token."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer invalid_token"}
        mock_db = Mock()
        mock_jwt_service.verify_access_token.return_value = None
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None
        mock_jwt_service.verify_access_token.assert_called_with("invalid_token")
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.UserRepository')
    @patch('fastmcp.server.routes.token_routes_backup.jwt_service')
    async def test_get_current_user_valid_token(self, mock_jwt_service, mock_user_repo_class):
        """Test successful user extraction with valid token."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        mock_db = Mock()
        mock_user = Mock()
        mock_user_repo = Mock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo
        mock_jwt_service.verify_access_token.return_value = {"sub": "user123"}
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result == mock_user
        mock_jwt_service.verify_access_token.assert_called_with("valid_token")
        mock_user_repo_class.assert_called_with(mock_db)
        mock_user_repo.find_by_id.assert_called_with("user123")
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.jwt_service')
    async def test_get_current_user_token_without_subject(self, mock_jwt_service):
        """Test handling token without subject claim."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer token_without_sub"}
        mock_db = Mock()
        mock_jwt_service.verify_access_token.return_value = {"exp": 123456}
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.jwt_service')
    async def test_get_current_user_exception_handling(self, mock_jwt_service):
        """Test exception handling during token validation."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer error_token"}
        mock_db = Mock()
        mock_jwt_service.verify_access_token.side_effect = Exception("Token error")
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None


class TestHandleGenerateToken:
    """Test token generation handler."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_generate_token_unauthorized(self, mock_get_user, mock_get_db):
        """Test token generation with unauthorized user."""
        # Arrange
        mock_request = AsyncMock(spec=Request)
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = None
        
        # Act
        response = await handle_generate_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.generate_token_handler')
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_generate_token_success(self, mock_get_user, mock_get_db, mock_generate_handler):
        """Test successful token generation."""
        # Arrange
        mock_request = AsyncMock(spec=Request)
        mock_request.json = AsyncMock(return_value={"name": "test-token"})
        mock_db = Mock()
        mock_user = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        mock_token_response = Mock()
        mock_token_response.dict.return_value = {"token_id": "123", "token": "abc123"}
        mock_generate_handler.return_value = mock_token_response
        
        # Act
        response = await handle_generate_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        mock_generate_handler.assert_called_once()
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_generate_token_exception(self, mock_get_user, mock_get_db):
        """Test token generation with exception."""
        # Arrange
        mock_request = AsyncMock(spec=Request)
        mock_request.json = AsyncMock(side_effect=Exception("JSON parse error"))
        mock_db = Mock()
        mock_user = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        
        # Act
        response = await handle_generate_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        mock_db.close.assert_called_once()


class TestHandleListTokens:
    """Test token listing handler."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_list_tokens_unauthorized(self, mock_get_user, mock_get_db):
        """Test token listing with unauthorized user."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {}
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = None
        
        # Act
        response = await handle_list_tokens(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.list_tokens_handler')
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_list_tokens_success(self, mock_get_user, mock_get_db, mock_list_handler):
        """Test successful token listing."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {"skip": "10", "limit": "50"}
        mock_db = Mock()
        mock_user = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        mock_list_response = Mock()
        mock_list_response.dict.return_value = {"tokens": []}
        mock_list_handler.return_value = mock_list_response
        
        # Act
        response = await handle_list_tokens(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        mock_list_handler.assert_called_with(mock_user, mock_db, 10, 50)
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.list_tokens_handler')
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_list_tokens_default_params(self, mock_get_user, mock_get_db, mock_list_handler):
        """Test token listing with default parameters."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {}
        mock_db = Mock()
        mock_user = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        mock_list_response = Mock()
        mock_list_response.dict.return_value = {"tokens": []}
        mock_list_handler.return_value = mock_list_response
        
        # Act
        response = await handle_list_tokens(mock_request)
        
        # Assert
        mock_list_handler.assert_called_with(mock_user, mock_db, 0, 100)


class TestHandleGetTokenDetails:
    """Test token details retrieval handler."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_get_token_details_unauthorized(self, mock_get_user):
        """Test token details with unauthorized user."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {"token_id": "123"}
        mock_get_user.return_value = None
        
        # Act
        response = await handle_get_token_details(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_handle_get_token_details_missing_token_id(self, mock_get_user):
        """Test token details without token ID."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {}
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        
        # Act
        response = await handle_get_token_details(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400


class TestHandleValidateToken:
    """Test token validation handler."""
    
    @pytest.mark.asyncio
    async def test_handle_validate_token_no_auth_header(self):
        """Test token validation without Authorization header."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        
        # Act
        response = await handle_validate_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        # Note: Current implementation returns {"valid": False}
    
    @pytest.mark.asyncio
    async def test_handle_validate_token_invalid_auth_header(self):
        """Test token validation with invalid Authorization header."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Basic sometoken"}
        
        # Act
        response = await handle_validate_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        # Note: Current implementation returns {"valid": False}
    
    @pytest.mark.asyncio
    async def test_handle_validate_token_bearer_token(self):
        """Test token validation with Bearer token."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer some_token"}
        
        # Act
        response = await handle_validate_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        # Note: Current implementation always returns {"valid": False}


class TestTokenRoutes:
    """Test token routes configuration."""
    
    def test_token_routes_structure(self):
        """Test that token routes are properly configured."""
        # Assert
        assert len(token_routes) == 8
        
        # Check route paths and methods
        route_configs = [
            ("/api/v2/tokens", ["POST"]),
            ("/api/v2/tokens", ["GET"]),
            ("/api/v2/tokens/{token_id}", ["GET"]),
            ("/api/v2/tokens/{token_id}", ["DELETE"]),
            ("/api/v2/tokens/{token_id}", ["PATCH"]),
            ("/api/v2/tokens/{token_id}/rotate", ["POST"]),
            ("/api/v2/tokens/validate", ["POST"]),
            ("/api/v2/tokens/{token_id}/usage", ["GET"]),
        ]
        
        for i, (expected_path, expected_methods) in enumerate(route_configs):
            route = token_routes[i]
            assert route.path == expected_path
            assert route.methods == set(expected_methods)
    
    def test_token_routes_handlers(self):
        """Test that routes have correct handlers assigned."""
        # Arrange
        expected_handlers = [
            handle_generate_token,
            handle_list_tokens,
            handle_get_token_details,
            handle_revoke_token,
            handle_update_token,
            handle_rotate_token,
            handle_validate_token,
            handle_get_token_usage,
        ]
        
        # Assert
        for i, expected_handler in enumerate(expected_handlers):
            route = token_routes[i]
            assert route.endpoint == expected_handler


class TestTokenRoutesIntegration:
    """Integration tests for token routes."""
    
    def test_starlette_app_with_token_routes(self):
        """Test that token routes can be integrated with Starlette app."""
        # Arrange
        app = Starlette(routes=token_routes)
        client = TestClient(app)
        
        # Act & Assert - Test that routes are accessible (will return 401/400 but routes exist)
        response = client.get("/api/v2/tokens")
        assert response.status_code in [400, 401]  # Expected for unauthorized access
        
        response = client.post("/api/v2/tokens/validate")
        assert response.status_code == 200  # This endpoint has different behavior
    
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    def test_token_routes_authentication_flow(self, mock_get_user, mock_get_db):
        """Test authentication flow through routes."""
        # Arrange
        app = Starlette(routes=token_routes)
        client = TestClient(app)
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = None  # Unauthorized user
        
        # Act
        response = client.get("/api/v2/tokens")
        
        # Assert
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}


class TestDatabaseConnectionHandling:
    """Test database connection handling in route handlers."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_database_connection_cleanup_on_success(self, mock_get_user, mock_get_db):
        """Test that database connection is properly closed on success."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {}
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        
        with patch('fastmcp.server.routes.token_routes_backup.list_tokens_handler') as mock_handler:
            mock_response = Mock()
            mock_response.dict.return_value = {"tokens": []}
            mock_handler.return_value = mock_response
            
            # Act
            await handle_list_tokens(mock_request)
            
            # Assert
            mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_backup.get_current_user_from_request')
    async def test_database_connection_cleanup_on_exception(self, mock_get_user, mock_get_db):
        """Test that database connection is properly closed on exception."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {}
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        
        with patch('fastmcp.server.routes.token_routes_backup.list_tokens_handler') as mock_handler:
            mock_handler.side_effect = Exception("Database error")
            
            # Act
            await handle_list_tokens(mock_request)
            
            # Assert
            mock_db.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])