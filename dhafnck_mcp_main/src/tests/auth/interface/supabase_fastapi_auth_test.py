"""Test module for Supabase FastAPI authentication integration."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fastmcp.auth.interface.supabase_fastapi_auth import (
    get_current_user_supabase,
    get_current_user,
    get_supabase_auth
)
from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole
from fastmcp.auth.infrastructure.repositories.user_repository import UserRepository


class TestSupabaseFastAPIAuth:
    """Test suite for Supabase FastAPI authentication integration."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_credentials(self):
        """Create mock HTTPAuthorizationCredentials."""
        credentials = Mock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "valid-jwt-token"
        return credentials

    @pytest.fixture
    def mock_supabase_user(self):
        """Create a mock Supabase user object."""
        user = MagicMock()
        user.id = "supabase-user-123"
        user.email = "test@example.com"
        user.user_metadata = {
            "username": "testuser",
            "full_name": "Test User"
        }
        return user

    @pytest.fixture
    def mock_local_user(self):
        """Create a mock local user entity."""
        return User(
            id="supabase-user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_with_valid_token_existing_user(
        self, mock_db_session, mock_credentials, mock_supabase_user, mock_local_user
    ):
        """Test successful authentication with valid token and existing user."""
        # Mock get_supabase_auth function
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Setup successful token verification
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_supabase_user
            mock_auth_service.verify_token = AsyncMock(return_value=mock_result)
            
            # Mock user repository to return existing user
            with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserRepository') as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = mock_local_user
                mock_repo_class.return_value = mock_repo_instance
                
                # Call the function
                result = await get_current_user_supabase(
                    credentials=mock_credentials,
                    db=mock_db_session
                )
                
                # Assertions
                assert result == mock_local_user
                mock_auth_service.verify_token.assert_called_once_with("valid-jwt-token")
                mock_repo_instance.find_by_id.assert_called_once_with("supabase-user-123")
                # Should not create new user
                mock_db_session.add.assert_not_called()
                mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_with_valid_token_new_user(
        self, mock_db_session, mock_credentials, mock_supabase_user
    ):
        """Test successful authentication with valid token for new user."""
        # Mock get_supabase_auth function
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Setup successful token verification
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_supabase_user
            mock_auth_service.verify_token = AsyncMock(return_value=mock_result)
            
            # Mock user repository to return None (user not found)
            with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserRepository') as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                mock_repo_class.return_value = mock_repo_instance
                
                # Mock UserModel.from_domain and to_domain
                with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserModel') as MockUserModel:
                    mock_db_user = MagicMock()
                    mock_domain_user = User(
                        id="supabase-user-123",
                        email="test@example.com",
                        username="testuser",
                        full_name="Test User",
                        password_hash="",
                        status=UserStatus.ACTIVE,
                        roles=[UserRole.USER],
                        email_verified=True
                    )
                    mock_db_user.to_domain.return_value = mock_domain_user
                    MockUserModel.from_domain.return_value = mock_db_user
                    
                    # Call the function
                    result = await get_current_user_supabase(
                        credentials=mock_credentials,
                        db=mock_db_session
                    )
                    
                    # Assertions
                    mock_auth_service.verify_token.assert_called_once_with("valid-jwt-token")
                    mock_repo_instance.find_by_id.assert_called_once_with("supabase-user-123")
                    # Should create new user
                    mock_db_session.add.assert_called_once()
                    mock_db_session.commit.assert_called_once()
                    
                    # Check that from_domain was called with proper User entity
                    MockUserModel.from_domain.assert_called_once()
                    created_user_arg = MockUserModel.from_domain.call_args[0][0]
                    assert created_user_arg.id == "supabase-user-123"
                    assert created_user_arg.email == "test@example.com"
                    assert created_user_arg.username == "testuser"
                    assert created_user_arg.full_name == "Test User"
                    assert created_user_arg.status == UserStatus.ACTIVE
                    assert created_user_arg.email_verified is True

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_no_credentials(self, mock_db_session):
        """Test authentication fails when no credentials provided."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_supabase(
                credentials=None,
                db=mock_db_session
            )
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_invalid_token(
        self, mock_db_session, mock_credentials
    ):
        """Test authentication fails with invalid token."""
        # Mock get_supabase_auth function
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Setup failed token verification
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.user = None
            mock_result.error_message = "Token expired"
            mock_auth_service.verify_token = AsyncMock(return_value=mock_result)
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_supabase(
                    credentials=mock_credentials,
                    db=mock_db_session
                )
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Token expired"
            assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_missing_user_id(
        self, mock_db_session, mock_credentials
    ):
        """Test authentication fails when token has no user ID."""
        # Mock get_supabase_auth function
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Setup token verification with user missing ID
            mock_user = MagicMock()
            mock_user.id = None
            mock_user.get.return_value = None
            
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_user
            mock_auth_service.verify_token = AsyncMock(return_value=mock_result)
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_supabase(
                    credentials=mock_credentials,
                    db=mock_db_session
                )
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid token: missing user ID"

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_handles_dict_user_data(
        self, mock_db_session, mock_credentials
    ):
        """Test authentication handles user data as dictionary."""
        # Mock get_supabase_auth function
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Setup token verification with dict user data
            mock_user_dict = {
                'id': 'supabase-user-456',
                'email': 'dict@example.com',
                'user_metadata': {
                    'username': 'dictuser',
                    'full_name': 'Dict User'
                }
            }
            
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_user_dict
            mock_auth_service.verify_token = AsyncMock(return_value=mock_result)
            
            # Mock user repository to return None (create new user)
            with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserRepository') as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                mock_repo_class.return_value = mock_repo_instance
                
                # Mock UserModel.from_domain and to_domain
                with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserModel') as MockUserModel:
                    mock_db_user = MagicMock()
                    mock_domain_user = User(
                        id="supabase-user-456",
                        email="dict@example.com",
                        username="dictuser",
                        full_name="Dict User",
                        password_hash="",
                        status=UserStatus.ACTIVE,
                        roles=[UserRole.USER],
                        email_verified=True
                    )
                    mock_db_user.to_domain.return_value = mock_domain_user
                    MockUserModel.from_domain.return_value = mock_db_user
                    
                    # Call the function
                    result = await get_current_user_supabase(
                        credentials=mock_credentials,
                        db=mock_db_session
                    )
                    
                    # Check that from_domain was called with proper User entity from dict data
                    MockUserModel.from_domain.assert_called_once()
                    created_user_arg = MockUserModel.from_domain.call_args[0][0]
                    assert created_user_arg.id == "supabase-user-456"
                    assert created_user_arg.email == "dict@example.com"
                    assert created_user_arg.username == "dictuser"
                    assert created_user_arg.full_name == "Dict User"

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_generic_exception_handling(
        self, mock_db_session, mock_credentials
    ):
        """Test generic exception handling during authentication."""
        # Mock get_supabase_auth function to raise exception
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            mock_auth_service.verify_token = AsyncMock(side_effect=Exception("Network error"))
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_supabase(
                    credentials=mock_credentials,
                    db=mock_db_session
                )
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Authentication failed"

    def test_get_current_user_alias(self):
        """Test that get_current_user is an alias for get_current_user_supabase."""
        assert get_current_user == get_current_user_supabase

    def test_get_supabase_auth_singleton(self):
        """Test that get_supabase_auth returns singleton instance."""
        # Clear any existing singleton
        import fastmcp.auth.interface.supabase_fastapi_auth as auth_module
        auth_module.supabase_auth = None
        
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.SupabaseAuthService') as MockService:
            mock_instance = MagicMock()
            MockService.return_value = mock_instance
            
            # First call should create instance
            result1 = get_supabase_auth()
            assert result1 == mock_instance
            MockService.assert_called_once()
            
            # Second call should return same instance
            result2 = get_supabase_auth()
            assert result2 == mock_instance
            # Should not create another instance
            MockService.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_creation_with_minimal_metadata(self, mock_db_session, mock_credentials):
        """Test user creation with minimal Supabase metadata."""
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Setup user with minimal metadata
            mock_minimal_user = MagicMock()
            mock_minimal_user.id = "minimal-user-123"
            mock_minimal_user.email = "minimal@example.com"
            mock_minimal_user.user_metadata = {}  # Empty metadata
            
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_minimal_user
            mock_auth_service.verify_token = AsyncMock(return_value=mock_result)
            
            with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserRepository') as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                mock_repo_class.return_value = mock_repo_instance
                
                with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserModel') as MockUserModel:
                    mock_db_user = MagicMock()
                    mock_domain_user = User(
                        id="minimal-user-123",
                        email="minimal@example.com",
                        username="minimal",  # Should use email prefix
                        full_name="",  # Should be empty
                        password_hash="",
                        status=UserStatus.ACTIVE,
                        roles=[UserRole.USER],
                        email_verified=True
                    )
                    mock_db_user.to_domain.return_value = mock_domain_user
                    MockUserModel.from_domain.return_value = mock_db_user
                    
                    result = await get_current_user_supabase(
                        credentials=mock_credentials,
                        db=mock_db_session
                    )
                    
                    # Verify user was created with email prefix as username
                    created_user_arg = MockUserModel.from_domain.call_args[0][0]
                    assert created_user_arg.username == "minimal"  # email prefix
                    assert created_user_arg.full_name == ""  # empty when no metadata

    @pytest.mark.asyncio
    async def test_user_creation_with_email_without_at_symbol(self, mock_db_session, mock_credentials):
        """Test user creation when email doesn't contain @ symbol."""
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.get_supabase_auth') as mock_get_auth:
            mock_auth_service = MagicMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Setup user with no email
            mock_user_no_email = MagicMock()
            mock_user_no_email.id = "no-email-user-123"
            mock_user_no_email.email = None
            mock_user_no_email.user_metadata = {"username": "customuser"}
            
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_user_no_email
            mock_auth_service.verify_token = AsyncMock(return_value=mock_result)
            
            with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserRepository') as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                mock_repo_class.return_value = mock_repo_instance
                
                with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserModel') as MockUserModel:
                    mock_db_user = MagicMock()
                    mock_domain_user = User(
                        id="no-email-user-123",
                        email=None,
                        username="customuser",
                        full_name="",
                        password_hash="",
                        status=UserStatus.ACTIVE,
                        roles=[UserRole.USER],
                        email_verified=True
                    )
                    mock_db_user.to_domain.return_value = mock_domain_user
                    MockUserModel.from_domain.return_value = mock_db_user
                    
                    result = await get_current_user_supabase(
                        credentials=mock_credentials,
                        db=mock_db_session
                    )
                    
                    # Verify username fallback logic
                    created_user_arg = MockUserModel.from_domain.call_args[0][0]
                    assert created_user_arg.username == "customuser"  # from metadata