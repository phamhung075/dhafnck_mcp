"""
Tests for development authentication endpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
import os

# Mock the environment variable before importing the module
@pytest.fixture(autouse=True)
def mock_development_env(monkeypatch):
    """Ensure development environment for all tests"""
    monkeypatch.setenv("ENVIRONMENT", "development")

# Import after setting environment
from fastmcp.auth.api.dev_endpoints import router, DevConfirmRequest


class TestDevEndpoints:
    """Test development-only authentication endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with dev endpoints"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def mock_supabase_service(self):
        """Mock SupabaseAuthService"""
        with patch('fastmcp.auth.api.dev_endpoints.SupabaseAuthService') as mock:
            yield mock

    def test_router_disabled_in_production(self, monkeypatch):
        """Test that router is empty when not in development"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        # Re-import to get production version
        import importlib
        import fastmcp.auth.api.dev_endpoints
        importlib.reload(fastmcp.auth.api.dev_endpoints)
        
        # Check that router has no routes
        assert len(fastmcp.auth.api.dev_endpoints.router.routes) == 0
        
        # Reset to development for other tests
        monkeypatch.setenv("ENVIRONMENT", "development")
        importlib.reload(fastmcp.auth.api.dev_endpoints)

    def test_dev_confirm_user_success(self, client, mock_supabase_service):
        """Test successful user confirmation"""
        # Setup mocks
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = None
        mock_user.id = "user-123"
        
        mock_response = Mock()
        mock_response.users = [mock_user]
        
        mock_admin = Mock()
        mock_admin.auth.admin.list_users.return_value = mock_response
        mock_admin.auth.admin.update_user_by_id.return_value = Mock()
        
        mock_supabase_service.return_value.admin_client = mock_admin
        
        # Make request
        response = client.post(
            "/auth/dev/confirm-user",
            json={"email": "test@example.com"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "manually confirmed" in data["message"]
        assert data["warning"] == "This is a development-only feature"
        
        # Verify admin client calls
        mock_admin.auth.admin.list_users.assert_called_once()
        mock_admin.auth.admin.update_user_by_id.assert_called_once_with(
            "user-123",
            {"email_confirmed_at": "now()"}
        )

    def test_dev_confirm_user_already_confirmed(self, client, mock_supabase_service):
        """Test confirmation of already confirmed user"""
        # Setup mocks
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = "2024-01-01T00:00:00Z"
        
        mock_response = Mock()
        mock_response.users = [mock_user]
        
        mock_admin = Mock()
        mock_admin.auth.admin.list_users.return_value = mock_response
        
        mock_supabase_service.return_value.admin_client = mock_admin
        
        # Make request
        response = client.post(
            "/auth/dev/confirm-user",
            json={"email": "test@example.com"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "User already confirmed"
        assert data["confirmed_at"] == "2024-01-01T00:00:00Z"

    def test_dev_confirm_user_not_found(self, client, mock_supabase_service):
        """Test confirmation of non-existent user"""
        # Setup mocks
        mock_response = Mock()
        mock_response.users = []
        
        mock_admin = Mock()
        mock_admin.auth.admin.list_users.return_value = mock_response
        
        mock_supabase_service.return_value.admin_client = mock_admin
        
        # Make request
        response = client.post(
            "/auth/dev/confirm-user",
            json={"email": "nonexistent@example.com"}
        )
        
        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_dev_confirm_user_error(self, client, mock_supabase_service):
        """Test error handling in user confirmation"""
        # Setup mock to raise exception
        mock_supabase_service.side_effect = Exception("Database error")
        
        # Make request
        response = client.post(
            "/auth/dev/confirm-user",
            json={"email": "test@example.com"}
        )
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to manually confirm user" in response.json()["detail"]

    def test_dev_list_unconfirmed_users(self, client, mock_supabase_service):
        """Test listing unconfirmed users"""
        # Setup mocks
        mock_user1 = Mock()
        mock_user1.email = "unconfirmed1@example.com"
        mock_user1.email_confirmed_at = None
        mock_user1.id = "user-1"
        mock_user1.created_at = "2024-01-01T00:00:00Z"
        mock_user1.last_sign_in_at = None
        
        mock_user2 = Mock()
        mock_user2.email = "confirmed@example.com"
        mock_user2.email_confirmed_at = "2024-01-01T00:00:00Z"
        
        mock_user3 = Mock()
        mock_user3.email = "unconfirmed2@example.com"
        mock_user3.email_confirmed_at = None
        mock_user3.id = "user-3"
        mock_user3.created_at = "2024-01-02T00:00:00Z"
        mock_user3.last_sign_in_at = "2024-01-02T12:00:00Z"
        
        mock_response = Mock()
        mock_response.users = [mock_user1, mock_user2, mock_user3]
        
        mock_admin = Mock()
        mock_admin.auth.admin.list_users.return_value = mock_response
        
        mock_supabase_service.return_value.admin_client = mock_admin
        
        # Make request
        response = client.get("/auth/dev/list-unconfirmed")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_unconfirmed"] == 2
        assert len(data["users"]) == 2
        assert data["warning"] == "This is a development-only feature"
        
        # Check unconfirmed users
        emails = [u["email"] for u in data["users"]]
        assert "unconfirmed1@example.com" in emails
        assert "unconfirmed2@example.com" in emails
        assert "confirmed@example.com" not in emails

    def test_dev_list_unconfirmed_users_error(self, client, mock_supabase_service):
        """Test error handling in listing unconfirmed users"""
        # Setup mock to raise exception
        mock_supabase_service.side_effect = Exception("Database error")
        
        # Make request
        response = client.get("/auth/dev/list-unconfirmed")
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to list unconfirmed users" in response.json()["detail"]

    def test_dev_check_email_status(self, client, monkeypatch):
        """Test email configuration status check"""
        # Set environment variables
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        
        # Make request
        response = client.get("/auth/dev/email-status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["environment"] == "development"
        assert data["smtp_configured"] is True
        assert data["supabase_configured"] is True
        assert "rate_limits" in data
        assert "recommendations" in data
        assert data["warning"] == "This is a development-only feature"

    def test_dev_check_email_status_no_config(self, client, monkeypatch):
        """Test email status with no configuration"""
        # Clear environment variables
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        
        # Make request
        response = client.get("/auth/dev/email-status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["smtp_configured"] is False
        assert data["supabase_configured"] is False

    def test_dev_check_email_status_error(self, client, monkeypatch):
        """Test error handling in email status check"""
        # Mock os.getenv to raise exception
        with patch('fastmcp.auth.api.dev_endpoints.os.getenv', side_effect=Exception("Config error")):
            response = client.get("/auth/dev/email-status")
            
            # Assertions
            assert response.status_code == 500
            assert "Failed to check email status" in response.json()["detail"]