"""
Tests for Starlette bridge token management routes with Supabase authentication.

This module tests the Starlette-compatible routes for token management
using Supabase authentication integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.applications import Starlette
from datetime import datetime

from fastmcp.server.routes.token_routes_starlette_bridge_backup import (
    get_current_user_from_request,
    handle_generate_token,
    handle_list_tokens,
    handle_get_token_details,
    handle_revoke_token,
    token_routes
)
from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole


class TestGetCurrentUserFromRequest:
    """Test user extraction and validation with Supabase authentication."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth', None)
    async def test_get_current_user_no_supabase_auth(self):
        """Test handling when Supabase auth is not available."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_db = Mock()
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth')
    async def test_get_current_user_no_auth_header(self, mock_supabase_auth):
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
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth')
    async def test_get_current_user_invalid_auth_header(self, mock_supabase_auth):
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
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth')
    async def test_get_current_user_invalid_token(self, mock_supabase_auth):
        """Test handling request with invalid Supabase token."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer invalid_token"}
        mock_db = Mock()
        mock_auth_result = Mock()
        mock_auth_result.success = False
        mock_auth_result.user = None
        mock_supabase_auth.verify_token.return_value = mock_auth_result
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None
        mock_supabase_auth.verify_token.assert_called_with("invalid_token")
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth')
    async def test_get_current_user_valid_token(self, mock_supabase_auth):
        """Test successful user extraction with valid Supabase token."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        mock_db = Mock()
        
        # Mock Supabase user
        mock_supabase_user = Mock()
        mock_supabase_user.id = "user123"
        mock_supabase_user.email = "test@example.com"
        mock_supabase_user.email_confirmed_at = datetime.now()
        mock_supabase_user.last_sign_in_at = datetime.now()
        mock_supabase_user.user_metadata = {
            'username': 'testuser',
            'full_name': 'Test User'
        }
        
        mock_auth_result = Mock()
        mock_auth_result.success = True
        mock_auth_result.user = mock_supabase_user
        mock_supabase_auth.verify_token.return_value = mock_auth_result
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is not None
        assert isinstance(result, User)
        assert result.id == "user123"
        assert result.email == "test@example.com"
        assert result.username == "testuser"
        assert result.full_name == "Test User"
        assert result.status == UserStatus.ACTIVE
        assert UserRole.USER in result.roles
        assert result.email_verified is True
        mock_supabase_auth.verify_token.assert_called_with("valid_token")
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth')
    async def test_get_current_user_unverified_email(self, mock_supabase_auth):
        """Test user with unverified email."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        mock_db = Mock()
        
        # Mock Supabase user with unverified email
        mock_supabase_user = Mock()
        mock_supabase_user.id = "user123"
        mock_supabase_user.email = "test@example.com"
        mock_supabase_user.email_confirmed_at = None  # Unverified
        mock_supabase_user.last_sign_in_at = None
        mock_supabase_user.user_metadata = {}
        
        mock_auth_result = Mock()
        mock_auth_result.success = True
        mock_auth_result.user = mock_supabase_user
        mock_supabase_auth.verify_token.return_value = mock_auth_result
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is not None
        assert result.status == UserStatus.PENDING_VERIFICATION
        assert result.email_verified is False
        assert result.username == "test"  # Derived from email
        assert result.full_name == ""  # Default empty
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth')
    async def test_get_current_user_exception_handling(self, mock_supabase_auth):
        """Test exception handling during token validation."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer error_token"}
        mock_db = Mock()
        mock_supabase_auth.verify_token.side_effect = Exception("Supabase error")
        
        # Act
        result = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert result is None


class TestHandleGenerateToken:
    """Test token generation handler with Supabase authentication."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
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
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.generate_token_handler')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_generate_token_success(self, mock_get_user, mock_get_db, mock_generate_handler):
        """Test successful token generation."""
        # Arrange
        mock_request = AsyncMock(spec=Request)
        mock_request.json = AsyncMock(return_value={"name": "test-token"})
        mock_db = Mock()
        mock_user = Mock(spec=User)
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
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_generate_token_exception(self, mock_get_user, mock_get_db):
        """Test token generation with exception."""
        # Arrange
        mock_request = AsyncMock(spec=Request)
        mock_request.json = AsyncMock(side_effect=Exception("JSON parse error"))
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        
        # Act
        response = await handle_generate_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        mock_db.close.assert_called_once()


class TestHandleListTokens:
    """Test token listing handler with Supabase authentication."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
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
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.list_tokens_handler')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_list_tokens_success(self, mock_get_user, mock_get_db, mock_list_handler):
        """Test successful token listing."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {"skip": "10", "limit": "50"}
        mock_db = Mock()
        mock_user = Mock(spec=User)
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
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.list_tokens_handler')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_list_tokens_default_params(self, mock_get_user, mock_get_db, mock_list_handler):
        """Test token listing with default parameters."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {}
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        mock_list_response = Mock()
        mock_list_response.dict.return_value = {"tokens": []}
        mock_list_handler.return_value = mock_list_response
        
        # Act
        response = await handle_list_tokens(mock_request)
        
        # Assert
        mock_list_handler.assert_called_with(mock_user, mock_db, 0, 100)
        mock_db.close.assert_called_once()


class TestHandleGetTokenDetails:
    """Test token details retrieval handler with Supabase authentication."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_get_token_details_unauthorized(self, mock_get_user, mock_get_db):
        """Test token details with unauthorized user."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {"token_id": "123"}
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = None
        
        # Act
        response = await handle_get_token_details(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_get_token_details_missing_token_id(self, mock_get_user, mock_get_db):
        """Test token details without token ID."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {}
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        
        # Act
        response = await handle_get_token_details(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_token_details_handler')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_get_token_details_success(self, mock_get_user, mock_get_db, mock_details_handler):
        """Test successful token details retrieval."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {"token_id": "123"}
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        mock_token_response = Mock()
        mock_token_response.dict.return_value = {"token_id": "123", "name": "test-token"}
        mock_details_handler.return_value = mock_token_response
        
        # Act
        response = await handle_get_token_details(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        mock_details_handler.assert_called_with("123", mock_user, mock_db)
        mock_db.close.assert_called_once()


class TestHandleRevokeToken:
    """Test token revocation handler with Supabase authentication."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_revoke_token_unauthorized(self, mock_get_user, mock_get_db):
        """Test token revocation with unauthorized user."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {"token_id": "123"}
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = None
        
        # Act
        response = await handle_revoke_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_revoke_token_missing_token_id(self, mock_get_user, mock_get_db):
        """Test token revocation without token ID."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {}
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        
        # Act
        response = await handle_revoke_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.revoke_token_handler')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_handle_revoke_token_success(self, mock_get_user, mock_get_db, mock_revoke_handler):
        """Test successful token revocation."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.path_params = {"token_id": "123"}
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_get_db.return_value = iter([mock_db])
        mock_get_user.return_value = mock_user
        mock_revoke_handler.return_value = {"message": "Token revoked"}
        
        # Act
        response = await handle_revoke_token(mock_request)
        
        # Assert
        assert isinstance(response, JSONResponse)
        mock_revoke_handler.assert_called_with("123", mock_user, mock_db)
        mock_db.close.assert_called_once()


class TestTokenRoutes:
    """Test token routes configuration for Supabase bridge."""
    
    def test_token_routes_structure(self):
        """Test that token routes are properly configured."""
        # Assert
        assert len(token_routes) == 4
        
        # Check route paths and methods
        route_configs = [
            ("/api/v2/tokens", ["POST"]),
            ("/api/v2/tokens", ["GET"]),
            ("/api/v2/tokens/{token_id}", ["GET"]),
            ("/api/v2/tokens/{token_id}", ["DELETE"]),
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
        ]
        
        # Assert
        for i, expected_handler in enumerate(expected_handlers):
            route = token_routes[i]
            assert route.endpoint == expected_handler


class TestSupabaseIntegration:
    """Test Supabase-specific integration features."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.supabase_auth')
    async def test_supabase_user_mapping(self, mock_supabase_auth):
        """Test proper mapping of Supabase user to internal User entity."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        mock_db = Mock()
        
        # Mock Supabase user with complete metadata
        mock_supabase_user = Mock()
        mock_supabase_user.id = "supabase-user-id"
        mock_supabase_user.email = "user@example.com"
        mock_supabase_user.email_confirmed_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_supabase_user.last_sign_in_at = datetime(2023, 1, 2, 12, 0, 0)
        mock_supabase_user.user_metadata = {
            'username': 'custom_username',
            'full_name': 'John Doe'
        }
        
        mock_auth_result = Mock()
        mock_auth_result.success = True
        mock_auth_result.user = mock_supabase_user
        mock_supabase_auth.verify_token.return_value = mock_auth_result
        
        # Act
        user = await get_current_user_from_request(mock_request, mock_db)
        
        # Assert
        assert user.id == "supabase-user-id"
        assert user.email == "user@example.com"
        assert user.username == "custom_username"
        assert user.full_name == "John Doe"
        assert user.email_verified is True
        assert user.email_verified_at == datetime(2023, 1, 1, 12, 0, 0)
        assert user.last_login_at == datetime(2023, 1, 2, 12, 0, 0)
        assert user.status == UserStatus.ACTIVE
        assert UserRole.USER in user.roles


class TestTokenRoutesIntegration:
    """Integration tests for Supabase token routes."""
    
    def test_starlette_app_with_supabase_token_routes(self):
        """Test that Supabase token routes can be integrated with Starlette app."""
        # Arrange
        app = Starlette(routes=token_routes)
        client = TestClient(app)
        
        # Act & Assert - Test that routes are accessible (will return 401/400 but routes exist)
        response = client.get("/api/v2/tokens")
        assert response.status_code in [400, 401]  # Expected for unauthorized access
        
        response = client.post("/api/v2/tokens", json={"name": "test"})
        assert response.status_code in [400, 401]  # Expected for unauthorized access
    
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    def test_supabase_token_routes_authentication_flow(self, mock_get_user, mock_get_db):
        """Test Supabase authentication flow through routes."""
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


class TestErrorHandling:
    """Test error handling in Supabase token routes."""
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_database_connection_cleanup_on_success(self, mock_get_user, mock_get_db):
        """Test that database connection is properly closed on success."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {}
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_user = Mock(spec=User)
        mock_get_user.return_value = mock_user
        
        with patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.list_tokens_handler') as mock_handler:
            mock_response = Mock()
            mock_response.dict.return_value = {"tokens": []}
            mock_handler.return_value = mock_response
            
            # Act
            await handle_list_tokens(mock_request)
            
            # Assert
            mock_db.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_db')
    @patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.get_current_user_from_request')
    async def test_database_connection_cleanup_on_exception(self, mock_get_user, mock_get_db):
        """Test that database connection is properly closed on exception."""
        # Arrange
        mock_request = Mock(spec=Request)
        mock_request.query_params = {}
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_user = Mock(spec=User)
        mock_get_user.return_value = mock_user
        
        with patch('fastmcp.server.routes.token_routes_starlette_bridge_backup.list_tokens_handler') as mock_handler:
            mock_handler.side_effect = Exception("Database error")
            
            # Act
            await handle_list_tokens(mock_request)
            
            # Assert
            mock_db.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])