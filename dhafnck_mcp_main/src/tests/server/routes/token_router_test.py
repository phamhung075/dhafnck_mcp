import pytest
import json
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fastmcp.server.routes.token_router import (
    router,
    TokenCreate,
    TokenUpdate,
    TokenResponse,
    TokenValidate,
    TokenStats,
    get_token_service,
)


class TestTokenModels:
    """Test Pydantic models used in token router."""

    def test_token_create_model(self):
        """Test TokenCreate model validation."""
        # Valid data
        data = {
            "name": "Test Token",
            "description": "Test description",
            "rate_limit": 100
        }
        token_create = TokenCreate(**data)
        assert token_create.name == "Test Token"
        assert token_create.description == "Test description"
        assert token_create.rate_limit == 100

    def test_token_create_minimal(self):
        """Test TokenCreate with minimal data."""
        token_create = TokenCreate(name="Minimal Token")
        assert token_create.name == "Minimal Token"
        assert token_create.description is None
        assert token_create.rate_limit is None

    def test_token_update_model(self):
        """Test TokenUpdate model validation."""
        data = {
            "description": "Updated description",
            "is_active": False,
            "rate_limit": 200
        }
        token_update = TokenUpdate(**data)
        assert token_update.description == "Updated description"
        assert token_update.is_active is False
        assert token_update.rate_limit == 200

    def test_token_update_partial(self):
        """Test TokenUpdate with partial data."""
        token_update = TokenUpdate(is_active=True)
        assert token_update.is_active is True
        assert token_update.description is None
        assert token_update.rate_limit is None

    def test_token_validate_model(self):
        """Test TokenValidate model."""
        token_validate = TokenValidate(token="test-token-value")
        assert token_validate.token == "test-token-value"


class TestTokenService:
    """Test token service dependency."""

    def test_get_token_service(self):
        """Test get_token_service dependency."""
        with patch('fastmcp.server.routes.token_router.TokenApplicationFacade') as mock_facade:
            mock_instance = Mock()
            mock_facade.return_value = mock_instance
            
            service = get_token_service()
            
            assert service == mock_instance
            mock_facade.assert_called_once()


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

    def test_list_tokens(self, client, mock_token_service):
        """Test GET /tokens endpoint."""
        # Mock response
        mock_tokens = [
            {
                "id": "token-1",
                "name": "Token 1",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "token-2",
                "name": "Token 2",
                "is_active": False,
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        mock_token_service.list_tokens.return_value = mock_tokens
        
        response = client.get("/tokens")
        
        assert response.status_code == 200
        assert response.json() == mock_tokens
        mock_token_service.list_tokens.assert_called_once()

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

    def test_create_token(self, client, mock_token_service):
        """Test POST /tokens endpoint."""
        # Request data
        create_data = {
            "name": "New Token",
            "description": "New token description",
            "rate_limit": 150
        }
        
        # Mock response
        mock_created_token = {
            "id": "new-token-id",
            "name": "New Token",
            "description": "New token description",
            "token": "generated-token-value",
            "is_active": True,
            "rate_limit": 150,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_token_service.create_token.return_value = mock_created_token
        
        response = client.post("/tokens", json=create_data)
        
        assert response.status_code == 200
        assert response.json() == mock_created_token
        mock_token_service.create_token.assert_called_once_with(
            name="New Token",
            description="New token description",
            rate_limit=150
        )

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

    def test_update_token(self, client, mock_token_service):
        """Test PUT /tokens/{token_id} endpoint."""
        token_id = "update-token-id"
        update_data = {
            "description": "Updated description",
            "is_active": False,
            "rate_limit": 200
        }
        
        mock_updated_token = {
            "id": token_id,
            "name": "Test Token",
            "description": "Updated description",
            "is_active": False,
            "rate_limit": 200
        }
        mock_token_service.update_token.return_value = mock_updated_token
        
        response = client.put(f"/tokens/{token_id}", json=update_data)
        
        assert response.status_code == 200
        assert response.json() == mock_updated_token
        mock_token_service.update_token.assert_called_once_with(
            token_id,
            description="Updated description",
            is_active=False,
            rate_limit=200
        )

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

    def test_delete_token(self, client, mock_token_service):
        """Test DELETE /tokens/{token_id} endpoint."""
        token_id = "delete-token-id"
        mock_token_service.delete_token.return_value = True
        
        response = client.delete(f"/tokens/{token_id}")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Token deleted successfully"}
        mock_token_service.delete_token.assert_called_once_with(token_id)

    def test_delete_token_not_found(self, client, mock_token_service):
        """Test DELETE /tokens/{token_id} when token not found."""
        token_id = "nonexistent-token"
        mock_token_service.delete_token.return_value = False
        
        response = client.delete(f"/tokens/{token_id}")
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    def test_regenerate_token(self, client, mock_token_service):
        """Test POST /tokens/{token_id}/regenerate endpoint."""
        token_id = "regenerate-token-id"
        mock_regenerated = {
            "id": token_id,
            "name": "Test Token",
            "token": "new-regenerated-token",
            "is_active": True
        }
        mock_token_service.regenerate_token.return_value = mock_regenerated
        
        response = client.post(f"/tokens/{token_id}/regenerate")
        
        assert response.status_code == 200
        assert response.json() == mock_regenerated
        assert "new-regenerated-token" in response.json()["token"]
        mock_token_service.regenerate_token.assert_called_once_with(token_id)

    def test_regenerate_token_not_found(self, client, mock_token_service):
        """Test POST /tokens/{token_id}/regenerate when token not found."""
        token_id = "nonexistent-token"
        mock_token_service.regenerate_token.return_value = None
        
        response = client.post(f"/tokens/{token_id}/regenerate")
        
        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    def test_validate_token(self, client, mock_token_service):
        """Test POST /tokens/validate endpoint."""
        validate_data = {"token": "test-token-to-validate"}
        
        mock_validation_result = {
            "valid": True,
            "user_id": "user-123",
            "token_id": "token-123"
        }
        mock_token_service.validate_token.return_value = mock_validation_result
        
        response = client.post("/tokens/validate", json=validate_data)
        
        assert response.status_code == 200
        assert response.json() == mock_validation_result
        mock_token_service.validate_token.assert_called_once_with("test-token-to-validate")

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

    def test_get_token_stats(self, client, mock_token_service):
        """Test GET /tokens/{token_id}/stats endpoint."""
        token_id = "stats-token-id"
        mock_stats = {
            "total_requests": 1500,
            "requests_today": 75,
            "rate_limit_hits": 10,
            "last_used": "2024-01-01T12:00:00Z",
            "average_response_time": 45.2
        }
        mock_token_service.get_token_stats.return_value = mock_stats
        
        response = client.get(f"/tokens/{token_id}/stats")
        
        assert response.status_code == 200
        assert response.json() == mock_stats
        mock_token_service.get_token_stats.assert_called_once_with(token_id)

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

    def test_internal_server_error_handling(self, client):
        """Test handling of internal server errors."""
        with patch('fastmcp.server.routes.token_router.get_token_service') as mock_get_service:
            mock_service = Mock()
            mock_service.list_tokens.side_effect = Exception("Unexpected error")
            mock_get_service.return_value = mock_service
            
            response = client.get("/tokens")
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_database_connection_error(self, client):
        """Test handling of database connection errors."""
        with patch('fastmcp.server.routes.token_router.get_token_service') as mock_get_service:
            mock_service = Mock()
            mock_service.create_token.side_effect = Exception("Database connection failed")
            mock_get_service.return_value = mock_service
            
            response = client.post("/tokens", json={"name": "Test Token"})
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]


class TestTokenRouterIntegration:
    """Integration tests for token router."""

    @pytest.fixture
    def mock_jwt_secret(self):
        """Mock JWT secret for testing."""
        return "test-integration-secret"

    @pytest.fixture
    def client(self, mock_jwt_secret):
        """Create a test client with real service."""
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        
        # Mock the token service with more realistic behavior
        mock_service = Mock()
        
        # Token storage
        tokens = {}
        token_counter = 0
        
        def create_token(name, description=None, rate_limit=None):
            nonlocal token_counter
            token_counter += 1
            token_id = f"token-{token_counter}"
            
            # Generate JWT token
            payload = {
                "token_id": token_id,
                "user_id": "test-user",
                "exp": datetime.now(timezone.utc) + timedelta(days=30)
            }
            jwt_token = jwt.encode(payload, mock_jwt_secret, algorithm="HS256")
            
            token = {
                "id": token_id,
                "name": name,
                "description": description,
                "token": jwt_token,
                "is_active": True,
                "rate_limit": rate_limit or 100,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_used_at": None
            }
            tokens[token_id] = token.copy()
            return token
        
        def list_tokens():
            return [{k: v for k, v in token.items() if k != "token"} for token in tokens.values()]
        
        def get_token(token_id):
            token = tokens.get(token_id)
            if token:
                return {k: v for k, v in token.items() if k != "token"}
            return None
        
        def update_token(token_id, **kwargs):
            if token_id in tokens:
                for key, value in kwargs.items():
                    if value is not None and key in tokens[token_id]:
                        tokens[token_id][key] = value
                return {k: v for k, v in tokens[token_id].items() if k != "token"}
            return None
        
        def delete_token(token_id):
            if token_id in tokens:
                del tokens[token_id]
                return True
            return False
        
        mock_service.create_token = create_token
        mock_service.list_tokens = list_tokens
        mock_service.get_token = get_token
        mock_service.update_token = update_token
        mock_service.delete_token = delete_token
        
        app.dependency_overrides[get_token_service] = lambda: mock_service
        
        return TestClient(app)

    def test_full_token_lifecycle(self, client):
        """Test complete token lifecycle."""
        # Create token
        create_response = client.post("/tokens", json={
            "name": "Lifecycle Test Token",
            "description": "Testing full lifecycle",
            "rate_limit": 500
        })
        assert create_response.status_code == 200
        created_token = create_response.json()
        assert "token" in created_token
        assert created_token["name"] == "Lifecycle Test Token"
        
        token_id = created_token["id"]
        
        # List tokens
        list_response = client.get("/tokens")
        assert list_response.status_code == 200
        tokens = list_response.json()
        assert len(tokens) == 1
        assert tokens[0]["id"] == token_id
        
        # Get specific token
        get_response = client.get(f"/tokens/{token_id}")
        assert get_response.status_code == 200
        retrieved_token = get_response.json()
        assert retrieved_token["id"] == token_id
        assert "token" not in retrieved_token  # Token value should not be exposed
        
        # Update token
        update_response = client.put(f"/tokens/{token_id}", json={
            "description": "Updated description",
            "is_active": False
        })
        assert update_response.status_code == 200
        updated_token = update_response.json()
        assert updated_token["description"] == "Updated description"
        assert updated_token["is_active"] is False
        
        # Delete token
        delete_response = client.delete(f"/tokens/{token_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted_response = client.get(f"/tokens/{token_id}")
        assert get_deleted_response.status_code == 404

    def test_multiple_tokens_management(self, client):
        """Test managing multiple tokens."""
        # Create multiple tokens
        token_names = ["Token A", "Token B", "Token C"]
        created_tokens = []
        
        for name in token_names:
            response = client.post("/tokens", json={"name": name})
            assert response.status_code == 200
            created_tokens.append(response.json())
        
        # List all tokens
        list_response = client.get("/tokens")
        assert list_response.status_code == 200
        tokens = list_response.json()
        assert len(tokens) == 3
        
        # Update middle token
        middle_token = created_tokens[1]
        update_response = client.put(f"/tokens/{middle_token['id']}", json={
            "is_active": False
        })
        assert update_response.status_code == 200
        
        # Delete first token
        first_token = created_tokens[0]
        delete_response = client.delete(f"/tokens/{first_token['id']}")
        assert delete_response.status_code == 200
        
        # Verify final state
        final_list_response = client.get("/tokens")
        assert final_list_response.status_code == 200
        final_tokens = final_list_response.json()
        assert len(final_tokens) == 2
        
        # Check that the right tokens remain
        remaining_ids = [t["id"] for t in final_tokens]
        assert first_token["id"] not in remaining_ids
        assert middle_token["id"] in remaining_ids
        assert created_tokens[2]["id"] in remaining_ids