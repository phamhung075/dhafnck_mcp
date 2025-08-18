"""
Unit tests for authentication service

This module tests the AuthService class methods in isolation.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import bcrypt

from fastmcp.auth.application.services.auth_service import AuthService
from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole
from fastmcp.auth.domain.value_objects import UserId
from fastmcp.auth.domain.services.jwt_service import JWTService
from fastmcp.auth.domain.exceptions import (
    AuthenticationError,
    UserNotFoundError,
    InvalidCredentialsError,
    AccountLockedError,
    EmailNotVerifiedError
)


class TestAuthService:
    """Test AuthService class"""
    
    @pytest.fixture
    def mock_user_repository(self):
        """Create mock user repository"""
        return Mock()
    
    @pytest.fixture
    def jwt_service(self):
        """Create JWT service for testing"""
        return JWTService(secret_key="test-secret-key")
    
    @pytest.fixture
    def auth_service(self, mock_user_repository, jwt_service):
        """Create auth service with mocks"""
        return AuthService(
            user_repository=mock_user_repository,
            jwt_service=jwt_service
        )
    
    def test_register_user_success(self, auth_service, mock_user_repository):
        """Test successful user registration"""
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.save.side_effect = lambda user: user
        
        user = auth_service.register_user(
            email="newuser@example.com",
            username="newuser",
            password="SecurePassword123!"
        )
        
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.status == UserStatus.PENDING_VERIFICATION
        assert bcrypt.checkpw(b"SecurePassword123!", user.password_hash.encode())
        
        mock_user_repository.save.assert_called_once()
    
    def test_register_user_with_existing_email(self, auth_service, mock_user_repository):
        """Test registration with already existing email"""
        existing_user = Mock()
        mock_user_repository.find_by_email.return_value = existing_user
        
        with pytest.raises(ValueError, match="Email already registered"):
            auth_service.register_user(
                email="existing@example.com",
                username="newuser",
                password="SecurePassword123!"
            )
    
    def test_authenticate_user_success(self, auth_service, mock_user_repository):
        """Test successful user authentication"""
        # Create test user with hashed password
        password = "SecurePassword123!"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash=password_hash
        )
        test_user.id = UserId("550e8400-e29b-41d4-a716-446655440000")
        test_user.status = UserStatus.ACTIVE
        
        mock_user_repository.find_by_email.return_value = test_user
        
        tokens = auth_service.authenticate_user(
            email="test@example.com",
            password=password
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_authenticate_user_with_wrong_password(self, auth_service, mock_user_repository):
        """Test authentication with wrong password"""
        password_hash = bcrypt.hashpw(b"CorrectPassword", bcrypt.gensalt()).decode()
        
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash=password_hash
        )
        test_user.status = UserStatus.ACTIVE
        
        mock_user_repository.find_by_email.return_value = test_user
        
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate_user(
                email="test@example.com",
                password="WrongPassword"
            )
    
    def test_authenticate_nonexistent_user(self, auth_service, mock_user_repository):
        """Test authentication with non-existent user"""
        mock_user_repository.find_by_email.return_value = None
        
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate_user(
                email="nonexistent@example.com",
                password="SomePassword"
            )
    
    def test_authenticate_unverified_user(self, auth_service, mock_user_repository):
        """Test authentication with unverified account"""
        password_hash = bcrypt.hashpw(b"Password123", bcrypt.gensalt()).decode()
        
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash=password_hash
        )
        test_user.status = UserStatus.PENDING_VERIFICATION
        
        mock_user_repository.find_by_email.return_value = test_user
        
        with pytest.raises(EmailNotVerifiedError):
            auth_service.authenticate_user(
                email="test@example.com",
                password="Password123"
            )
    
    def test_authenticate_locked_account(self, auth_service, mock_user_repository):
        """Test authentication with locked account"""
        password_hash = bcrypt.hashpw(b"Password123", bcrypt.gensalt()).decode()
        
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash=password_hash
        )
        test_user.status = UserStatus.ACTIVE
        test_user.is_locked = True
        test_user.locked_at = datetime.utcnow()
        test_user.lock_reason = "Too many failed attempts"
        
        mock_user_repository.find_by_email.return_value = test_user
        
        with pytest.raises(AccountLockedError):
            auth_service.authenticate_user(
                email="test@example.com",
                password="Password123"
            )
    
    def test_refresh_access_token_success(self, auth_service, jwt_service):
        """Test successful token refresh"""
        # Create valid refresh token
        refresh_token, family = jwt_service.create_refresh_token(
            user_id="test-user-id"
        )
        
        new_tokens = auth_service.refresh_access_token(refresh_token)
        
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["refresh_token"] != refresh_token  # Token should be rotated
    
    def test_refresh_with_invalid_token(self, auth_service):
        """Test refresh with invalid token"""
        with pytest.raises(AuthenticationError):
            auth_service.refresh_access_token("invalid.token.here")
    
    def test_request_password_reset(self, auth_service, mock_user_repository):
        """Test password reset request"""
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed"
        )
        test_user.id = UserId("550e8400-e29b-41d4-a716-446655440000")
        
        mock_user_repository.find_by_email.return_value = test_user
        
        with patch('fastmcp.auth.application.services.email_service.send_reset_email') as mock_send:
            reset_token = auth_service.request_password_reset("test@example.com")
            
            assert reset_token is not None
            mock_send.assert_called_once_with("test@example.com", reset_token)
    
    def test_reset_password_success(self, auth_service, mock_user_repository, jwt_service):
        """Test successful password reset"""
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash="old_hash"
        )
        test_user.id = UserId("550e8400-e29b-41d4-a716-446655440000")
        
        mock_user_repository.find_by_id.return_value = test_user
        mock_user_repository.save.side_effect = lambda user: user
        
        # Create reset token
        reset_token = jwt_service.create_reset_token(
            user_id=str(test_user.id.value),
            email=test_user.email
        )
        
        # Reset password
        auth_service.reset_password(reset_token, "NewSecurePassword123!")
        
        # Check password was updated
        mock_user_repository.save.assert_called_once()
        saved_user = mock_user_repository.save.call_args[0][0]
        assert bcrypt.checkpw(b"NewSecurePassword123!", saved_user.password_hash.encode())
    
    def test_verify_email_success(self, auth_service, mock_user_repository, jwt_service):
        """Test successful email verification"""
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed"
        )
        test_user.id = UserId("550e8400-e29b-41d4-a716-446655440000")
        test_user.status = UserStatus.PENDING_VERIFICATION
        
        mock_user_repository.find_by_id.return_value = test_user
        mock_user_repository.save.side_effect = lambda user: user
        
        # Create verification token
        verification_token = jwt_service.create_reset_token(
            user_id=str(test_user.id.value),
            email=test_user.email
        )
        
        # Verify email
        auth_service.verify_email(verification_token)
        
        # Check user status was updated
        mock_user_repository.save.assert_called_once()
        saved_user = mock_user_repository.save.call_args[0][0]
        assert saved_user.status == UserStatus.ACTIVE
        assert saved_user.verified_at is not None
    
    def test_lock_account_after_failed_attempts(self, auth_service, mock_user_repository):
        """Test account locking after multiple failed login attempts"""
        password_hash = bcrypt.hashpw(b"CorrectPassword", bcrypt.gensalt()).decode()
        
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash=password_hash
        )
        test_user.status = UserStatus.ACTIVE
        test_user.failed_login_attempts = 4  # One away from lock
        
        mock_user_repository.find_by_email.return_value = test_user
        mock_user_repository.save.side_effect = lambda user: user
        
        # Attempt login with wrong password
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate_user(
                email="test@example.com",
                password="WrongPassword"
            )
        
        # Check account was locked
        saved_user = mock_user_repository.save.call_args[0][0]
        assert saved_user.is_locked
        assert saved_user.failed_login_attempts == 5
        assert saved_user.lock_reason == "Too many failed login attempts"
    
    def test_get_user_by_id(self, auth_service, mock_user_repository):
        """Test getting user by ID"""
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed"
        )
        test_user.id = UserId("550e8400-e29b-41d4-a716-446655440000")
        
        mock_user_repository.find_by_id.return_value = test_user
        
        user = auth_service.get_user_by_id("550e8400-e29b-41d4-a716-446655440000")
        
        assert user == test_user
        mock_user_repository.find_by_id.assert_called_once()
    
    def test_update_user_roles(self, auth_service, mock_user_repository):
        """Test updating user roles"""
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed"
        )
        test_user.id = UserId("550e8400-e29b-41d4-a716-446655440000")
        test_user.roles = [UserRole.USER]
        
        mock_user_repository.find_by_id.return_value = test_user
        mock_user_repository.save.side_effect = lambda user: user
        
        # Update roles
        auth_service.update_user_roles(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            roles=[UserRole.USER, UserRole.ADMIN]
        )
        
        # Check roles were updated
        saved_user = mock_user_repository.save.call_args[0][0]
        assert UserRole.ADMIN in saved_user.roles
        assert UserRole.USER in saved_user.roles