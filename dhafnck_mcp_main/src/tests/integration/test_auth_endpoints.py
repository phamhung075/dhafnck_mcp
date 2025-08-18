"""
Integration tests for authentication endpoints

This module tests the complete authentication flow including:
- User registration
- Login with email/password
- Token refresh
- Password reset
- Email verification
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastmcp.auth.api.endpoints import router as auth_router
from fastmcp.auth.domain.entities.user import User, UserStatus
from fastmcp.auth.domain.services.jwt_service import JWTService
from fastmcp.auth.application.services.auth_service import AuthService
from fastmcp.auth.infrastructure.repositories.user_repository import UserRepository


@pytest.fixture
def client(test_app):
    """Create test client with auth routes"""
    test_app.include_router(auth_router, prefix="/api/auth")
    return TestClient(test_app)


@pytest.fixture
def jwt_service():
    """Create JWT service for testing"""
    return JWTService(secret_key="test-secret-key-for-testing")


@pytest.fixture
def auth_service(db_session, jwt_service):
    """Create auth service with test database"""
    user_repository = UserRepository(db_session)
    return AuthService(
        user_repository=user_repository,
        jwt_service=jwt_service
    )


class TestRegistrationEndpoint:
    """Test user registration endpoint"""
    
    def test_successful_registration(self, client, db_session):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response contains user info
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data  # Password should not be returned
        
        # Check user was created in database
        user = db_session.query(User).filter_by(email="newuser@example.com").first()
        assert user is not None
        assert user.username == "newuser"
        assert user.status == UserStatus.PENDING_VERIFICATION
    
    def test_registration_with_existing_email(self, client, db_session):
        """Test registration with already registered email"""
        # Create existing user
        existing_user = User(
            email="existing@example.com",
            username="existinguser",
            password_hash="hashed"
        )
        db_session.add(existing_user)
        db_session.commit()
        
        # Try to register with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "existing@example.com",
                "username": "newusername",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_registration_with_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 422  # Validation error
        
    def test_registration_with_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "weak"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestLoginEndpoint:
    """Test user login endpoint"""
    
    @pytest.fixture
    def registered_user(self, auth_service):
        """Create a registered and verified user"""
        user = auth_service.register_user(
            email="testuser@example.com",
            username="testuser",
            password="SecurePassword123!"
        )
        # Manually verify user for testing
        user.status = UserStatus.ACTIVE
        auth_service._user_repository.save(user)
        return user
    
    def test_successful_login(self, client, registered_user):
        """Test successful login with correct credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check tokens are returned
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_wrong_password(self, client, registered_user):
        """Test login with incorrect password"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_with_unregistered_email(self, client):
        """Test login with unregistered email"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_with_unverified_account(self, client, auth_service):
        """Test login with unverified account"""
        # Create unverified user
        user = auth_service.register_user(
            email="unverified@example.com",
            username="unverified",
            password="SecurePassword123!"
        )
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "unverified@example.com",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 403
        assert "not verified" in response.json()["detail"].lower()
    
    def test_login_with_locked_account(self, client, auth_service, registered_user):
        """Test login with locked account"""
        # Lock the account
        registered_user.lock_account("Too many failed attempts")
        auth_service._user_repository.save(registered_user)
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()


class TestTokenRefreshEndpoint:
    """Test token refresh endpoint"""
    
    def test_successful_token_refresh(self, client, jwt_service):
        """Test successful token refresh"""
        # Create tokens
        refresh_token, family = jwt_service.create_refresh_token(
            user_id="test-user-id"
        )
        
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check new tokens are returned
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token  # Should be rotated
    
    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
    
    def test_refresh_with_expired_token(self, client, jwt_service):
        """Test refresh with expired token"""
        # Create expired token
        with patch('fastmcp.auth.domain.services.jwt_service.datetime') as mock_datetime:
            # Set time to past
            past_time = datetime.utcnow() - timedelta(days=31)
            mock_datetime.now.return_value = past_time
            mock_datetime.utcnow.return_value = past_time
            
            refresh_token, _ = jwt_service.create_refresh_token(
                user_id="test-user-id"
            )
        
        # Try to use expired token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()


class TestPasswordResetEndpoint:
    """Test password reset endpoints"""
    
    def test_request_password_reset(self, client, registered_user):
        """Test requesting password reset"""
        with patch('fastmcp.auth.application.services.email_service.send_reset_email') as mock_send:
            response = client.post(
                "/api/auth/password-reset/request",
                json={"email": "testuser@example.com"}
            )
            
            assert response.status_code == 200
            assert "Password reset email sent" in response.json()["message"]
            
            # Check email was sent
            mock_send.assert_called_once()
    
    def test_request_reset_for_nonexistent_email(self, client):
        """Test requesting reset for non-existent email"""
        # Should return success to prevent email enumeration
        response = client.post(
            "/api/auth/password-reset/request",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 200
        assert "Password reset email sent" in response.json()["message"]
    
    def test_confirm_password_reset(self, client, auth_service, registered_user):
        """Test confirming password reset with token"""
        # Generate reset token
        reset_token = auth_service._jwt_service.create_reset_token(
            user_id=str(registered_user.id.value),
            email=registered_user.email
        )
        
        response = client.post(
            "/api/auth/password-reset/confirm",
            json={
                "token": reset_token,
                "new_password": "NewSecurePassword123!"
            }
        )
        
        assert response.status_code == 200
        assert "Password reset successful" in response.json()["message"]
        
        # Verify can login with new password
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "NewSecurePassword123!"
            }
        )
        assert login_response.status_code == 200


class TestProtectedEndpoints:
    """Test protected endpoints that require authentication"""
    
    def test_get_current_user(self, client, jwt_service):
        """Test getting current user info"""
        # Create access token
        access_token = jwt_service.create_access_token(
            user_id="test-user-id",
            email="test@example.com",
            roles=["user"]
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-id"
        assert data["email"] == "test@example.com"
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]


class TestEmailVerification:
    """Test email verification endpoints"""
    
    def test_verify_email(self, client, auth_service):
        """Test email verification with token"""
        # Create unverified user
        user = auth_service.register_user(
            email="verify@example.com",
            username="verifyuser",
            password="SecurePassword123!"
        )
        
        # Generate verification token
        verification_token = auth_service._jwt_service.create_reset_token(
            user_id=str(user.id.value),
            email=user.email
        )
        
        response = client.post(
            "/api/auth/verify-email",
            json={"token": verification_token}
        )
        
        assert response.status_code == 200
        assert "Email verified successfully" in response.json()["message"]
        
        # Check user is now verified
        verified_user = auth_service._user_repository.find_by_email(user.email)
        assert verified_user.status == UserStatus.ACTIVE
    
    def test_resend_verification_email(self, client, auth_service):
        """Test resending verification email"""
        # Create unverified user
        user = auth_service.register_user(
            email="resend@example.com",
            username="resenduser",
            password="SecurePassword123!"
        )
        
        with patch('fastmcp.auth.application.services.email_service.send_verification_email') as mock_send:
            response = client.post(
                "/api/auth/verify-email/resend",
                json={"email": "resend@example.com"}
            )
            
            assert response.status_code == 200
            assert "Verification email sent" in response.json()["message"]
            mock_send.assert_called_once()