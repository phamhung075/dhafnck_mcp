import pytest
import json
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fastmcp.server.routes.token_router import (
    router,
    TokenGenerateRequest,
    TokenResponse,
    TokenListResponse,
    TokenUpdateRequest,
    TokenValidateResponse,
    APIToken,
    generate_secure_token,
    hash_token,
    create_jwt_for_token,
)


class TestTokenModels:
    """Test Pydantic models used in token router."""

    def test_token_generate_request_model(self):
        """Test TokenGenerateRequest model validation."""
        # Valid data with all fields
        data = {
            "name": "Test Token",
            "scopes": ["read", "write"],
            "expires_in_days": 90,
            "rate_limit": 500,
            "metadata": {"purpose": "testing"}
        }
        token_request = TokenGenerateRequest(**data)
        assert token_request.name == "Test Token"
        assert token_request.scopes == ["read", "write"]
        assert token_request.expires_in_days == 90
        assert token_request.rate_limit == 500
        assert token_request.metadata == {"purpose": "testing"}

    def test_token_generate_request_minimal(self):
        """Test TokenGenerateRequest with minimal data."""
        token_request = TokenGenerateRequest(name="Minimal Token")
        assert token_request.name == "Minimal Token"
        assert token_request.scopes == []
        assert token_request.expires_in_days == 30
        assert token_request.rate_limit == 1000
        assert token_request.metadata == {}

    def test_token_update_request_model(self):
        """Test TokenUpdateRequest model validation."""
        data = {
            "name": "Updated Name",
            "scopes": ["admin"],
            "rate_limit": 2000,
            "is_active": False
        }
        token_update = TokenUpdateRequest(**data)
        assert token_update.name == "Updated Name"
        assert token_update.scopes == ["admin"]
        assert token_update.rate_limit == 2000
        assert token_update.is_active is False

    def test_token_update_request_partial(self):
        """Test TokenUpdateRequest with partial data."""
        token_update = TokenUpdateRequest(is_active=True)
        assert token_update.is_active is True
        assert token_update.name is None
        assert token_update.scopes is None
        assert token_update.rate_limit is None

    def test_token_validate_response_model(self):
        """Test TokenValidateResponse model."""
        response = TokenValidateResponse(
            valid=True,
            user_id="user-123",
            scopes=["read", "write"],
            expires_at=datetime.utcnow()
        )
        assert response.valid is True
        assert response.user_id == "user-123"
        assert response.scopes == ["read", "write"]
        assert isinstance(response.expires_at, datetime)


class TestTokenUtilities:
    """Test utility functions used in token router."""

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        # Tokens should be different
        assert token1 != token2
        # Tokens should be URL-safe base64
        assert isinstance(token1, str)
        assert len(token1) > 0
        # Should not contain URL-unsafe characters
        assert '+' not in token1
        assert '/' not in token1

    def test_hash_token(self):
        """Test token hashing."""
        token = "test-token-value"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        # Same token should produce same hash
        assert hash1 == hash2
        # Hash should be SHA256 hex digest (64 chars)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
        
        # Different tokens should produce different hashes
        different_hash = hash_token("different-token")
        assert hash1 != different_hash

    @patch('fastmcp.server.routes.token_router.jwt_backend')
    def test_create_jwt_for_token(self, mock_jwt_backend):
        """Test JWT creation for API tokens."""
        mock_jwt_backend.secret_key = "test-secret"
        mock_jwt_backend.algorithm = "HS256"
        
        token_id = "tok_123"
        user_id = "user_456"
        scopes = ["read", "write"]
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        with patch('jwt.encode') as mock_encode:
            mock_encode.return_value = "mock.jwt.token"
            
            result = create_jwt_for_token(token_id, user_id, scopes, expires_at)
            
            assert result == "mock.jwt.token"
            mock_encode.assert_called_once()
            
            # Check the payload structure
            call_args = mock_encode.call_args[0][0]
            assert call_args["token_id"] == token_id
            assert call_args["user_id"] == user_id
            assert call_args["scopes"] == scopes
            assert call_args["exp"] == expires_at
            assert call_args["type"] == "api_token"
            assert "iat" in call_args


class TestTokenEndpoints:
    """Test token router endpoints."""

    @pytest.fixture
    def mock_token_service(self):
        """Create a mock token service."""
        return Mock()

    @pytest.fixture
    def client(self, mock_token_service):
        """Create a test client with mocked dependencies."""
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        
        # Override the dependency
        app.dependency_overrides[get_token_service] = lambda: mock_token_service
        
        return TestClient(app)

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    def test_list_tokens(self, mock_get_db, mock_get_current_user, client):
        """Test GET /api/v2/tokens endpoint."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database session and tokens
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        # Create mock tokens
        token1 = Mock(spec=APIToken)
        token1.id = "tok_1"
        token1.name = "Token 1"
        token1.scopes = ["read"]
        token1.created_at = datetime.utcnow()
        token1.expires_at = datetime.utcnow() + timedelta(days=30)
        token1.last_used_at = None
        token1.usage_count = 0
        token1.rate_limit = 1000
        token1.is_active = True
        token1.metadata = {}
        
        token2 = Mock(spec=APIToken)
        token2.id = "tok_2"
        token2.name = "Token 2"
        token2.scopes = ["read", "write"]
        token2.created_at = datetime.utcnow()
        token2.expires_at = datetime.utcnow() + timedelta(days=60)
        token2.last_used_at = datetime.utcnow()
        token2.usage_count = 42
        token2.rate_limit = 500
        token2.is_active = False
        token2.metadata = {"env": "test"}
        
        # Setup query chain
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [token1, token2]
        
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/v2/tokens?skip=0&limit=100")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "tok_1"
        assert data["data"][0]["name"] == "Token 1"
        assert data["data"][1]["id"] == "tok_2"
        assert data["data"][1]["name"] == "Token 2"

    def test_list_tokens_empty(self, client, mock_token_service):
        """Test GET /tokens with empty result."""
        mock_token_service.list_tokens.return_value = []
        
        response = client.get("/tokens")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_list_tokens_error(self, client, mock_token_service):
        """Test GET /tokens with service error."""
        mock_token_service.list_tokens.side_effect = Exception("Database error")
        
        response = client.get("/tokens")
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    def test_get_token(self, client, mock_token_service):
        """Test GET /tokens/{token_id} endpoint."""
        token_id = "test-token-id"
        mock_token = {
            "id": token_id,
            "name": "Test Token",
            "description": "Test description",
            "is_active": True,
            "rate_limit": 100,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_token_service.get_token.return_value = mock_token
        
        response = client.get(f"/tokens/{token_id}")
        
        assert response.status_code == 200
        assert response.json() == mock_token
        mock_token_service.get_token.assert_called_once_with(token_id)

    def test_get_token_not_found(self, client, mock_token_service):
        """Test GET /tokens/{token_id} when token not found."""
        token_id = "nonexistent-token"
        mock_token_service.get_token.return_value = None
        
        response = client.get(f"/tokens/{token_id}")
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    @patch('fastmcp.server.routes.token_router.generate_secure_token')
    @patch('fastmcp.server.routes.token_router.hash_token')
    @patch('fastmcp.server.routes.token_router.create_jwt_for_token')
    def test_generate_token(self, mock_create_jwt, mock_hash_token, mock_generate_token, mock_get_db, mock_get_current_user, client):
        """Test POST /api/v2/tokens endpoint."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock token generation
        mock_generate_token.return_value = "secure-token-value"
        mock_hash_token.return_value = "hashed-token-value"
        mock_create_jwt.return_value = "jwt.token.value"
        
        # Mock database
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Request data
        create_data = {
            "name": "New API Token",
            "scopes": ["read", "write"],
            "expires_in_days": 60,
            "rate_limit": 2000,
            "metadata": {"purpose": "CI/CD"}
        }
        
        response = client.post("/api/v2/tokens", json=create_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New API Token"
        assert data["token"] == "jwt.token.value"
        assert data["scopes"] == ["read", "write"]
        assert data["rate_limit"] == 2000
        assert data["is_active"] is True
        assert data["metadata"] == {"purpose": "CI/CD"}
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_token_minimal(self, client, mock_token_service):
        """Test POST /tokens with minimal data."""
        create_data = {"name": "Minimal Token"}
        
        mock_created_token = {
            "id": "minimal-token-id",
            "name": "Minimal Token",
            "token": "minimal-token-value",
            "is_active": True
        }
        mock_token_service.create_token.return_value = mock_created_token
        
        response = client.post("/tokens", json=create_data)
        
        assert response.status_code == 200
        mock_token_service.create_token.assert_called_once_with(
            name="Minimal Token",
            description=None,
            rate_limit=None
        )

    def test_create_token_validation_error(self, client, mock_token_service):
        """Test POST /tokens with validation error."""
        # Missing required field
        create_data = {"description": "No name provided"}
        
        response = client.post("/tokens", json=create_data)
        
        assert response.status_code == 422  # Validation error

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    def test_update_token(self, mock_get_db, mock_get_current_user, client):
        """Test PATCH /api/v2/tokens/{token_id} endpoint."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database and token
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        # Create mock token
        mock_token = Mock(spec=APIToken)
        mock_token.id = "tok_update123"
        mock_token.user_id = "user-123"
        mock_token.name = "Original Name"
        mock_token.scopes = ["read"]
        mock_token.rate_limit = 1000
        mock_token.is_active = True
        mock_token.created_at = datetime.utcnow()
        mock_token.expires_at = datetime.utcnow() + timedelta(days=30)
        mock_token.last_used_at = None
        mock_token.usage_count = 0
        mock_token.metadata = {}
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_token
        
        mock_get_db.return_value = mock_db
        
        # Update data
        update_data = {
            "name": "Updated Name",
            "scopes": ["read", "write", "admin"],
            "rate_limit": 5000,
            "is_active": False
        }
        
        response = client.patch(f"/api/v2/tokens/tok_update123", json=update_data)
        
        assert response.status_code == 200
        
        # Verify updates were applied
        assert mock_token.name == "Updated Name"
        assert mock_token.scopes == ["read", "write", "admin"]
        assert mock_token.rate_limit == 5000
        assert mock_token.is_active is False
        
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_token)

    def test_update_token_partial(self, client, mock_token_service):
        """Test PUT /tokens/{token_id} with partial update."""
        token_id = "partial-update-token"
        update_data = {"is_active": True}
        
        mock_updated_token = {
            "id": token_id,
            "name": "Test Token",
            "is_active": True
        }
        mock_token_service.update_token.return_value = mock_updated_token
        
        response = client.put(f"/tokens/{token_id}", json=update_data)
        
        assert response.status_code == 200
        mock_token_service.update_token.assert_called_once_with(
            token_id,
            description=None,
            is_active=True,
            rate_limit=None
        )

    def test_update_token_not_found(self, client, mock_token_service):
        """Test PUT /tokens/{token_id} when token not found."""
        token_id = "nonexistent-token"
        update_data = {"is_active": False}
        
        mock_token_service.update_token.return_value = None
        
        response = client.put(f"/tokens/{token_id}", json=update_data)
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    def test_revoke_token(self, mock_get_db, mock_get_current_user, client):
        """Test DELETE /api/v2/tokens/{token_id} endpoint."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database and token
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        mock_token = Mock(spec=APIToken)
        mock_token.id = "tok_delete123"
        mock_token.user_id = "user-123"
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_token
        
        mock_get_db.return_value = mock_db
        
        response = client.delete(f"/api/v2/tokens/tok_delete123")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Token revoked successfully"}
        
        mock_db.delete.assert_called_once_with(mock_token)
        mock_db.commit.assert_called_once()

    def test_delete_token_not_found(self, client, mock_token_service):
        """Test DELETE /tokens/{token_id} when token not found."""
        token_id = "nonexistent-token"
        mock_token_service.delete_token.return_value = False
        
        response = client.delete(f"/tokens/{token_id}")
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    @patch('fastmcp.server.routes.token_router.generate_secure_token')
    @patch('fastmcp.server.routes.token_router.hash_token')
    @patch('fastmcp.server.routes.token_router.create_jwt_for_token')
    @patch('secrets.token_hex')
    def test_rotate_token(self, mock_token_hex, mock_create_jwt, mock_hash_token, mock_generate_token, mock_get_db, mock_get_current_user, client):
        """Test POST /api/v2/tokens/{token_id}/rotate endpoint."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock token generation
        mock_generate_token.return_value = "new-secure-token"
        mock_hash_token.return_value = "new-hashed-token"
        mock_create_jwt.return_value = "new.jwt.token"
        mock_token_hex.return_value = "abc123"
        
        # Mock database and old token
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        old_token = Mock(spec=APIToken)
        old_token.id = "tok_old123"
        old_token.user_id = "user-123"
        old_token.name = "Original Token"
        old_token.scopes = ["read", "write"]
        old_token.rate_limit = 2000
        old_token.metadata = {"env": "prod"}
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = old_token
        
        mock_get_db.return_value = mock_db
        
        response = client.post(f"/api/v2/tokens/tok_old123/rotate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original Token (rotated)"
        assert data["token"] == "new.jwt.token"
        assert data["scopes"] == ["read", "write"]
        assert data["rate_limit"] == 2000
        assert "rotated_from" in data["metadata"]
        assert data["metadata"]["rotated_from"] == "tok_old123"
        
        # Verify old token was deleted and new one added
        mock_db.delete.assert_called_once_with(old_token)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_regenerate_token_not_found(self, client, mock_token_service):
        """Test POST /tokens/{token_id}/regenerate when token not found."""
        token_id = "nonexistent-token"
        mock_token_service.regenerate_token.return_value = None
        
        response = client.post(f"/tokens/{token_id}/regenerate")
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    @patch('fastmcp.server.routes.token_router.get_db')
    @patch('fastmcp.server.routes.token_router.security')
    @patch('jwt.decode')
    def test_validate_token(self, mock_jwt_decode, mock_security, mock_get_db, client):
        """Test POST /api/v2/tokens/validate endpoint."""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "valid.jwt.token"
        mock_security.return_value = mock_credentials
        
        # Mock JWT decode
        mock_payload = {
            "type": "api_token",
            "token_id": "tok_123",
            "user_id": "user-456",
            "scopes": ["read", "write"]
        }
        mock_jwt_decode.return_value = mock_payload
        
        # Mock database and token
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        mock_token = Mock(spec=APIToken)
        mock_token.id = "tok_123"
        mock_token.is_active = True
        mock_token.expires_at = datetime.utcnow() + timedelta(days=10)
        mock_token.last_used_at = None
        mock_token.usage_count = 5
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_token
        
        mock_get_db.return_value = mock_db
        
        # Need to pass the authorization header
        response = client.post("/api/v2/tokens/validate", headers={"Authorization": "Bearer valid.jwt.token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == "user-456"
        assert data["scopes"] == ["read", "write"]
        
        # Verify usage stats were updated
        assert mock_token.usage_count == 6
        assert mock_token.last_used_at is not None
        mock_db.commit.assert_called_once()

    def test_validate_token_invalid(self, client, mock_token_service):
        """Test POST /tokens/validate with invalid token."""
        validate_data = {"token": "invalid-token"}
        
        mock_validation_result = {
            "valid": False,
            "error": "Invalid token"
        }
        mock_token_service.validate_token.return_value = mock_validation_result
        
        response = client.post("/tokens/validate", json=validate_data)
        
        assert response.status_code == 200
        assert response.json() == mock_validation_result
        assert response.json()["valid"] is False

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    def test_get_token_usage_stats(self, mock_get_db, mock_get_current_user, client):
        """Test GET /api/v2/tokens/{token_id}/usage endpoint."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database and token
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        # Create token with usage data
        created_at = datetime.utcnow() - timedelta(hours=48)
        expires_at = datetime.utcnow() + timedelta(days=28)
        last_used = datetime.utcnow() - timedelta(hours=2)
        
        mock_token = Mock(spec=APIToken)
        mock_token.id = "tok_stats123"
        mock_token.user_id = "user-123"
        mock_token.usage_count = 240
        mock_token.last_used_at = last_used
        mock_token.created_at = created_at
        mock_token.expires_at = expires_at
        mock_token.is_active = True
        mock_token.rate_limit = 1000
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_token
        
        mock_get_db.return_value = mock_db
        
        response = client.get(f"/api/v2/tokens/tok_stats123/usage")
        
        assert response.status_code == 200
        data = response.json()
        assert data["token_id"] == "tok_stats123"
        assert data["total_requests"] == 240
        assert data["last_used_at"] == last_used
        assert data["is_active"] is True
        assert data["is_expired"] is False
        assert data["rate_limit"] == 1000
        assert data["avg_requests_per_hour"] == 5.0  # 240 requests / 48 hours
        assert data["time_until_expiry"] > 0

    def test_get_token_stats_not_found(self, client, mock_token_service):
        """Test GET /tokens/{token_id}/stats when token not found."""
        token_id = "nonexistent-token"
        mock_token_service.get_token_stats.return_value = None
        
        response = client.get(f"/tokens/{token_id}/stats")
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]


class TestTokenRouterErrorHandling:
    """Test error handling in token router."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        
        return TestClient(app)

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    def test_token_not_found_error(self, mock_get_db, mock_get_current_user, client):
        """Test handling of token not found errors."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database returning None
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/v2/tokens/nonexistent-token")
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    @patch('fastmcp.server.routes.token_router.get_db')
    @patch('fastmcp.server.routes.token_router.security')
    @patch('jwt.decode')
    def test_validate_token_expired(self, mock_jwt_decode, mock_security, mock_get_db, client):
        """Test validation of expired token."""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "expired.jwt.token"
        mock_security.return_value = mock_credentials
        
        # Mock JWT decode to raise ExpiredSignatureError
        mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
        
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        response = client.post("/api/v2/tokens/validate", headers={"Authorization": "Bearer expired.jwt.token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @patch('fastmcp.server.routes.token_router.get_db')
    @patch('fastmcp.server.routes.token_router.security')
    @patch('jwt.decode')
    def test_validate_token_invalid(self, mock_jwt_decode, mock_security, mock_get_db, client):
        """Test validation of invalid token."""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid.jwt.token"
        mock_security.return_value = mock_credentials
        
        # Mock JWT decode to raise InvalidTokenError
        mock_jwt_decode.side_effect = jwt.InvalidTokenError("Invalid token")
        
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        response = client.post("/api/v2/tokens/validate", headers={"Authorization": "Bearer invalid.jwt.token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


class TestTokenValidationEdgeCases:
    """Test edge cases and security scenarios for token validation."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        
        return TestClient(app)

    @patch('fastmcp.server.routes.token_router.get_db')
    @patch('fastmcp.server.routes.token_router.security')
    @patch('jwt.decode')
    def test_validate_token_wrong_type(self, mock_jwt_decode, mock_security, mock_get_db, client):
        """Test validation of token with wrong type."""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "wrong.type.token"
        mock_security.return_value = mock_credentials
        
        # Mock JWT decode with wrong token type
        mock_payload = {
            "type": "user_token",  # Wrong type, should be "api_token"
            "token_id": "tok_123",
            "user_id": "user-456"
        }
        mock_jwt_decode.return_value = mock_payload
        
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        response = client.post("/api/v2/tokens/validate", headers={"Authorization": "Bearer wrong.type.token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @patch('fastmcp.server.routes.token_router.get_db')
    @patch('fastmcp.server.routes.token_router.security')
    @patch('jwt.decode')
    def test_validate_token_inactive(self, mock_jwt_decode, mock_security, mock_get_db, client):
        """Test validation of inactive token."""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "inactive.jwt.token"
        mock_security.return_value = mock_credentials
        
        # Mock JWT decode
        mock_payload = {
            "type": "api_token",
            "token_id": "tok_inactive",
            "user_id": "user-789",
            "scopes": ["read"]
        }
        mock_jwt_decode.return_value = mock_payload
        
        # Mock database with inactive token
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        mock_token = Mock(spec=APIToken)
        mock_token.id = "tok_inactive"
        mock_token.is_active = False  # Token is inactive
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_token
        
        mock_get_db.return_value = mock_db
        
        response = client.post("/api/v2/tokens/validate", headers={"Authorization": "Bearer inactive.jwt.token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    def test_generate_token_with_empty_scopes(self, mock_get_db, mock_get_current_user, client):
        """Test token generation with empty scopes."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Mock token generation functions
        with patch('fastmcp.server.routes.token_router.generate_secure_token', return_value="test-token"):
            with patch('fastmcp.server.routes.token_router.hash_token', return_value="hashed-token"):
                with patch('fastmcp.server.routes.token_router.create_jwt_for_token', return_value="jwt.token"):
                    
                    # Request with empty scopes
                    create_data = {
                        "name": "Token with no scopes",
                        "scopes": []  # Empty scopes
                    }
                    
                    response = client.post("/api/v2/tokens", json=create_data)
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["scopes"] == []

    @patch('fastmcp.server.routes.token_router.get_current_user')
    @patch('fastmcp.server.routes.token_router.get_db')
    def test_get_usage_stats_expired_token(self, mock_get_db, mock_get_current_user, client):
        """Test getting usage stats for expired token."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_get_current_user.return_value = mock_user
        
        # Mock database with expired token
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        
        # Create expired token
        created_at = datetime.utcnow() - timedelta(days=60)
        expires_at = datetime.utcnow() - timedelta(days=30)  # Expired 30 days ago
        
        mock_token = Mock(spec=APIToken)
        mock_token.id = "tok_expired"
        mock_token.user_id = "user-123"
        mock_token.usage_count = 1000
        mock_token.last_used_at = expires_at - timedelta(days=1)
        mock_token.created_at = created_at
        mock_token.expires_at = expires_at
        mock_token.is_active = True
        mock_token.rate_limit = 500
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_token
        
        mock_get_db.return_value = mock_db
        
        response = client.get(f"/api/v2/tokens/tok_expired/usage")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_expired"] is True
        assert data["time_until_expiry"] == 0