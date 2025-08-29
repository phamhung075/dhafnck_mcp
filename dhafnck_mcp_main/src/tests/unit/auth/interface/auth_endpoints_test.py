"""
Comprehensive Unit Tests for Auth Endpoints Interface Controller

This module tests the FastAPI authentication endpoints which handle all authentication
operations including registration, login, token refresh, password reset, and user management.
These are critical security components that require thorough testing.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException, status, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import os
from datetime import datetime

from fastmcp.auth.interface.auth_endpoints import (
    router,
    get_jwt_service,
    get_db_config, 
    get_db,
    get_auth_service,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    RefreshTokenRequest
)
from fastmcp.auth.application.services.auth_service import AuthService
from fastmcp.auth.domain.services.jwt_service import JWTService
from fastmcp.auth.domain.entities.user import User, UserRole
from fastmcp.auth.infrastructure.repositories.user_repository import UserRepository


class TestGetJWTService:
    """Test suite for JWT service initialization"""
    
    def setup_method(self):
        """Reset global JWT service before each test"""
        import fastmcp.auth.interface.auth_endpoints as endpoints_module
        endpoints_module._jwt_service = None
    
    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key-12345"})
    def test_get_jwt_service_success(self):
        """Test successful JWT service initialization"""
        service = get_jwt_service()
        
        assert isinstance(service, JWTService)
        assert service.secret_key == "test-secret-key-12345"
        
        # Test singleton behavior - should return same instance
        service2 = get_jwt_service()
        assert service is service2
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_jwt_service_missing_key(self):
        """Test JWT service initialization with missing secret key"""
        with pytest.raises(ValueError, match="Secret key is required for JWT service"):
            get_jwt_service()
    
    @patch.dict(os.environ, {"JWT_SECRET_KEY": "your-secret-key-change-in-production"})
    def test_get_jwt_service_default_key(self):
        """Test JWT service initialization with default/insecure key"""
        with pytest.raises(ValueError, match="Secret key is required for JWT service"):
            get_jwt_service()


class TestGetDatabaseDependencies:
    """Test suite for database dependency functions"""
    
    @patch('fastmcp.auth.interface.auth_endpoints.DatabaseConfig')
    def test_get_db_config_lazy_loading(self, mock_db_config_class):
        """Test database config lazy loading"""
        # Reset global config
        import fastmcp.auth.interface.auth_endpoints as endpoints_module
        endpoints_module._db_config = None
        
        mock_config_instance = Mock()
        mock_db_config_class.return_value = mock_config_instance
        
        # First call should create instance
        config1 = get_db_config()
        assert config1 is mock_config_instance
        assert mock_db_config_class.call_count == 1
        
        # Second call should return same instance
        config2 = get_db_config()
        assert config2 is mock_config_instance
        assert mock_db_config_class.call_count == 1  # Not called again
    
    @patch('fastmcp.auth.interface.auth_endpoints.get_db_config')
    def test_get_db_session_lifecycle(self, mock_get_db_config):
        """Test database session creation and cleanup"""
        mock_session = Mock(spec=Session)
        mock_session_local = Mock(return_value=mock_session)
        mock_config = Mock(SessionLocal=mock_session_local)
        mock_get_db_config.return_value = mock_config
        
        # Use generator to test lifecycle
        db_generator = get_db()
        
        # Get session
        db_session = next(db_generator)
        assert db_session is mock_session
        mock_session_local.assert_called_once()
        
        # Test cleanup when generator completes
        try:
            next(db_generator)
        except StopIteration:
            pass
        
        mock_session.close.assert_called_once()
    
    @patch('fastmcp.auth.interface.auth_endpoints.UserRepository')
    @patch('fastmcp.auth.interface.auth_endpoints.get_jwt_service')
    def test_get_auth_service(self, mock_get_jwt_service, mock_user_repo_class):
        """Test auth service dependency injection"""
        mock_db = Mock(spec=Session)
        mock_jwt_service = Mock(spec=JWTService)
        mock_user_repo = Mock(spec=UserRepository)
        
        mock_get_jwt_service.return_value = mock_jwt_service
        mock_user_repo_class.return_value = mock_user_repo
        
        auth_service = get_auth_service(mock_db)
        
        assert isinstance(auth_service, AuthService)
        mock_user_repo_class.assert_called_once_with(mock_db)


class TestRegisterEndpoint:
    """Test suite for user registration endpoint"""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock(spec=AuthService)
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI router"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_register_success(self, mock_auth_service):
        """Test successful user registration"""
        # Arrange
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
            full_name="Test User"
        )
        
        # Mock successful registration
        mock_result = Mock(success=True, error_message=None)
        mock_auth_service.register_user = AsyncMock(return_value=mock_result)
        
        # Import and patch the register function directly
        from fastmcp.auth.interface.auth_endpoints import register
        
        with patch('fastmcp.auth.interface.auth_endpoints.get_auth_service', return_value=mock_auth_service):
            # Act
            response = await register(register_request, mock_auth_service)
            
            # Assert
            assert isinstance(response, MessageResponse)
            assert response.success is True
            assert "Registration successful" in response.message
            
            mock_auth_service.register_user.assert_called_once_with(
                email="test@example.com",
                username="testuser",
                password="securepassword123",
                full_name="Test User"
            )
    
    @pytest.mark.asyncio
    async def test_register_failure_validation_error(self, mock_auth_service):
        """Test registration failure due to validation error"""
        # Arrange
        register_request = RegisterRequest(
            email="invalid@example.com",
            username="taken",
            password="password123",
            full_name="Test User"
        )
        
        mock_result = Mock(success=False, error_message="Username already exists")
        mock_auth_service.register_user = AsyncMock(return_value=mock_result)
        
        from fastmcp.auth.interface.auth_endpoints import register
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register(register_request, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Username already exists"
    
    @pytest.mark.asyncio
    async def test_register_internal_error(self, mock_auth_service):
        """Test registration internal error handling"""
        # Arrange
        register_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        mock_auth_service.register_user = AsyncMock(side_effect=Exception("Database error"))
        
        from fastmcp.auth.interface.auth_endpoints import register
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register(register_request, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Registration failed"


class TestLoginEndpoint:
    """Test suite for login endpoint"""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock(spec=AuthService)
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request"""
        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        return mock_request
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_auth_service, mock_request):
        """Test successful login"""
        # Arrange
        login_request = LoginRequest(
            email_or_username="test@example.com",
            password="password123"
        )
        
        mock_result = Mock(
            success=True,
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            requires_email_verification=False,
            error_message=None
        )
        mock_auth_service.login = AsyncMock(return_value=mock_result)
        
        from fastmcp.auth.interface.auth_endpoints import login
        
        # Act
        response = await login(login_request, mock_request, mock_auth_service)
        
        # Assert
        assert isinstance(response, TokenResponse)
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_456"
        assert response.token_type == "Bearer"
        assert response.expires_in == 900
        
        mock_auth_service.login.assert_called_once_with(
            email_or_username="test@example.com",
            password="password123",
            ip_address="192.168.1.1"
        )
    
    @pytest.mark.asyncio
    async def test_login_email_verification_required(self, mock_auth_service, mock_request):
        """Test login failure due to email verification requirement"""
        # Arrange
        login_request = LoginRequest(
            email_or_username="unverified@example.com",
            password="password123"
        )
        
        mock_result = Mock(
            success=False,
            requires_email_verification=True,
            error_message="Email not verified"
        )
        mock_auth_service.login = AsyncMock(return_value=mock_result)
        
        from fastmcp.auth.interface.auth_endpoints import login
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(login_request, mock_request, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Email verification required"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_auth_service, mock_request):
        """Test login failure due to invalid credentials"""
        # Arrange
        login_request = LoginRequest(
            email_or_username="test@example.com",
            password="wrongpassword"
        )
        
        mock_result = Mock(
            success=False,
            requires_email_verification=False,
            error_message="Invalid credentials"
        )
        mock_auth_service.login = AsyncMock(return_value=mock_result)
        
        from fastmcp.auth.interface.auth_endpoints import login
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(login_request, mock_request, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"
    
    @pytest.mark.asyncio
    async def test_login_no_client_ip(self, mock_auth_service):
        """Test login with no client IP information"""
        # Arrange
        login_request = LoginRequest(
            email_or_username="test@example.com",
            password="password123"
        )
        
        mock_request = Mock(spec=Request)
        mock_request.client = None  # No client info
        
        mock_result = Mock(
            success=True,
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            requires_email_verification=False
        )
        mock_auth_service.login = AsyncMock(return_value=mock_result)
        
        from fastmcp.auth.interface.auth_endpoints import login
        
        # Act
        await login(login_request, mock_request, mock_auth_service)
        
        # Assert - should handle None client gracefully
        mock_auth_service.login.assert_called_once_with(
            email_or_username="test@example.com",
            password="password123",
            ip_address=None
        )


class TestRefreshTokensEndpoint:
    """Test suite for token refresh endpoint"""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock(spec=AuthService)
    
    @pytest.mark.asyncio
    async def test_refresh_tokens_success(self, mock_auth_service):
        """Test successful token refresh"""
        # Arrange
        refresh_request = RefreshTokenRequest(refresh_token="refresh_token_123")
        
        mock_auth_service.refresh_tokens = AsyncMock(
            return_value=("new_access_token", "new_refresh_token")
        )
        
        from fastmcp.auth.interface.auth_endpoints import refresh_tokens
        
        # Act
        response = await refresh_tokens(refresh_request, mock_auth_service)
        
        # Assert
        assert isinstance(response, TokenResponse)
        assert response.access_token == "new_access_token"
        assert response.refresh_token == "new_refresh_token"
        assert response.token_type == "Bearer"
        assert response.expires_in == 900
        
        mock_auth_service.refresh_tokens.assert_called_once_with("refresh_token_123")
    
    @pytest.mark.asyncio
    async def test_refresh_tokens_invalid_token(self, mock_auth_service):
        """Test token refresh with invalid refresh token"""
        # Arrange
        refresh_request = RefreshTokenRequest(refresh_token="invalid_token")
        
        mock_auth_service.refresh_tokens = AsyncMock(return_value=None)
        
        from fastmcp.auth.interface.auth_endpoints import refresh_tokens
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh_tokens(refresh_request, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid or expired refresh token"


class TestGetCurrentUserEndpoint:
    """Test suite for get current user endpoint"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock user entity"""
        user = Mock(spec=User)
        user.id = "user-123"
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.email_verified = True
        user.roles = [UserRole.USER, UserRole.ADMIN]
        user.created_at = datetime(2023, 1, 1, 12, 0, 0)
        return user
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user):
        """Test successful current user retrieval"""
        from fastmcp.auth.interface.auth_endpoints import get_current_user_endpoint
        
        # Act
        response = await get_current_user_endpoint(mock_user)
        
        # Assert
        assert isinstance(response, UserResponse)
        assert response.id == "user-123"
        assert response.email == "test@example.com"
        assert response.username == "testuser"
        assert response.full_name == "Test User"
        assert response.email_verified is True
        assert response.roles == ["USER", "ADMIN"]
        assert response.created_at == "2023-01-01T12:00:00"
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_created_at(self, mock_user):
        """Test current user retrieval with no created_at timestamp"""
        mock_user.created_at = None
        
        from fastmcp.auth.interface.auth_endpoints import get_current_user_endpoint
        
        # Act
        response = await get_current_user_endpoint(mock_user)
        
        # Assert
        assert response.created_at == ""
    
    @pytest.mark.asyncio
    async def test_get_current_user_exception_handling(self, mock_user):
        """Test current user endpoint exception handling"""
        # Arrange - simulate user object issue
        mock_user.id = Mock(side_effect=Exception("User data error"))
        
        from fastmcp.auth.interface.auth_endpoints import get_current_user_endpoint
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_endpoint(mock_user)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Failed to get user information"


class TestLogoutEndpoint:
    """Test suite for logout endpoint"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock user entity"""
        user = Mock(spec=User)
        user.id = "user-123"
        return user
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock(spec=AuthService)
    
    @pytest.mark.asyncio
    async def test_logout_success(self, mock_user, mock_auth_service):
        """Test successful logout"""
        # Arrange
        mock_auth_service.logout = AsyncMock(return_value=True)
        
        from fastmcp.auth.interface.auth_endpoints import logout
        
        # Act
        response = await logout(mock_user, mock_auth_service)
        
        # Assert
        assert isinstance(response, MessageResponse)
        assert response.message == "Logged out successfully"
        assert response.success is True
        
        mock_auth_service.logout.assert_called_once_with("user-123", revoke_all_tokens=True)
    
    @pytest.mark.asyncio
    async def test_logout_failure(self, mock_user, mock_auth_service):
        """Test logout failure"""
        # Arrange
        mock_auth_service.logout = AsyncMock(return_value=False)
        
        from fastmcp.auth.interface.auth_endpoints import logout
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await logout(mock_user, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Logout failed"


class TestEmailVerificationEndpoint:
    """Test suite for email verification endpoint"""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock(spec=AuthService)
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, mock_auth_service):
        """Test successful email verification"""
        # Arrange
        token = "verification_token_123"
        mock_auth_service.verify_email = AsyncMock(return_value=(True, None))
        
        from fastmcp.auth.interface.auth_endpoints import verify_email
        
        # Act
        response = await verify_email(token, mock_auth_service)
        
        # Assert
        assert isinstance(response, MessageResponse)
        assert response.success is True
        assert "Email verified successfully" in response.message
        
        mock_auth_service.verify_email.assert_called_once_with(token)
    
    @pytest.mark.asyncio
    async def test_verify_email_failure(self, mock_auth_service):
        """Test email verification failure"""
        # Arrange
        token = "invalid_token"
        mock_auth_service.verify_email = AsyncMock(return_value=(False, "Token expired"))
        
        from fastmcp.auth.interface.auth_endpoints import verify_email
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_email(token, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Token expired"


class TestPasswordResetEndpoints:
    """Test suite for password reset endpoints"""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock(spec=AuthService)
    
    @pytest.mark.asyncio
    async def test_request_password_reset_success(self, mock_auth_service):
        """Test successful password reset request"""
        # Arrange
        reset_request = PasswordResetRequest(email="test@example.com")
        mock_auth_service.request_password_reset = AsyncMock(
            return_value=(True, "reset_token_123", None)
        )
        
        from fastmcp.auth.interface.auth_endpoints import request_password_reset
        
        # Act
        response = await request_password_reset(reset_request, mock_auth_service)
        
        # Assert
        assert isinstance(response, MessageResponse)
        assert response.success is True
        assert "password reset link has been sent" in response.message
        
        mock_auth_service.request_password_reset.assert_called_once_with("test@example.com")
    
    @pytest.mark.asyncio
    async def test_request_password_reset_exception(self, mock_auth_service):
        """Test password reset request exception handling"""
        # Arrange
        reset_request = PasswordResetRequest(email="test@example.com")
        mock_auth_service.request_password_reset = AsyncMock(side_effect=Exception("Service error"))
        
        from fastmcp.auth.interface.auth_endpoints import request_password_reset
        
        # Act - should not raise exception but return success to avoid info leakage
        response = await request_password_reset(reset_request, mock_auth_service)
        
        # Assert - still returns success message for security
        assert isinstance(response, MessageResponse)
        assert response.success is True
        assert "password reset link has been sent" in response.message
    
    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(self, mock_auth_service):
        """Test successful password reset confirmation"""
        # Arrange
        confirm_request = PasswordResetConfirm(
            token="reset_token_123",
            new_password="newsecurepassword123"
        )
        mock_auth_service.reset_password = AsyncMock(return_value=(True, None))
        
        from fastmcp.auth.interface.auth_endpoints import confirm_password_reset
        
        # Act
        response = await confirm_password_reset(confirm_request, mock_auth_service)
        
        # Assert
        assert isinstance(response, MessageResponse)
        assert response.success is True
        assert "Password reset successfully" in response.message
        
        mock_auth_service.reset_password.assert_called_once_with(
            token="reset_token_123",
            new_password="newsecurepassword123"
        )
    
    @pytest.mark.asyncio
    async def test_confirm_password_reset_failure(self, mock_auth_service):
        """Test password reset confirmation failure"""
        # Arrange
        confirm_request = PasswordResetConfirm(
            token="invalid_token",
            new_password="newpassword123"
        )
        mock_auth_service.reset_password = AsyncMock(return_value=(False, "Token expired"))
        
        from fastmcp.auth.interface.auth_endpoints import confirm_password_reset
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await confirm_password_reset(confirm_request, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Token expired"


class TestHealthCheckEndpoint:
    """Test suite for health check endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint"""
        from fastmcp.auth.interface.auth_endpoints import health_check
        
        # Act
        response = await health_check()
        
        # Assert
        assert isinstance(response, MessageResponse)
        assert response.success is True
        assert response.message == "Authentication service is healthy"


class TestRequestResponseModels:
    """Test suite for Pydantic request/response models"""
    
    def test_register_request_validation(self):
        """Test RegisterRequest model validation"""
        # Valid request
        valid_request = RegisterRequest(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
            full_name="Test User"
        )
        assert valid_request.email == "test@example.com"
        assert valid_request.username == "testuser"
        assert valid_request.full_name == "Test User"
        
        # Test without optional full_name
        minimal_request = RegisterRequest(
            email="test2@example.com",
            username="testuser2",
            password="password123"
        )
        assert minimal_request.full_name is None
    
    def test_login_request_validation(self):
        """Test LoginRequest model validation"""
        request = LoginRequest(
            email_or_username="test@example.com",
            password="password123"
        )
        assert request.email_or_username == "test@example.com"
        assert request.password == "password123"
    
    def test_token_response_model(self):
        """Test TokenResponse model"""
        response = TokenResponse(
            access_token="access_123",
            refresh_token="refresh_456"
        )
        assert response.access_token == "access_123"
        assert response.refresh_token == "refresh_456"
        assert response.token_type == "Bearer"  # Default value
        assert response.expires_in == 900  # Default value
    
    def test_user_response_model(self):
        """Test UserResponse model"""
        response = UserResponse(
            id="user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            email_verified=True,
            roles=["USER", "ADMIN"],
            created_at="2023-01-01T12:00:00"
        )
        assert response.id == "user-123"
        assert response.email == "test@example.com"
        assert response.roles == ["USER", "ADMIN"]
    
    def test_message_response_model(self):
        """Test MessageResponse model"""
        # Default success
        response1 = MessageResponse(message="Operation completed")
        assert response1.message == "Operation completed"
        assert response1.success is True  # Default value
        
        # Explicit failure
        response2 = MessageResponse(message="Operation failed", success=False)
        assert response2.success is False
    
    def test_password_reset_models(self):
        """Test password reset request/confirm models"""
        request = PasswordResetRequest(email="test@example.com")
        assert request.email == "test@example.com"
        
        confirm = PasswordResetConfirm(
            token="token_123",
            new_password="newsecurepassword"
        )
        assert confirm.token == "token_123"
        assert confirm.new_password == "newsecurepassword"
    
    def test_refresh_token_request_model(self):
        """Test RefreshTokenRequest model"""
        request = RefreshTokenRequest(refresh_token="refresh_token_123")
        assert request.refresh_token == "refresh_token_123"