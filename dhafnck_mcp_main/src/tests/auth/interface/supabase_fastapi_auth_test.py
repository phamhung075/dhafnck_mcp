"""Test module for Supabase FastAPI authentication integration."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fastmcp.auth.interface.supabase_fastapi_auth import (
    get_current_user_supabase,
    get_current_user
)
from fastmcp.auth.domain.entities.user import User
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
            is_active=True,
            is_superuser=False,
            hashed_password=""
        )

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_with_valid_token_existing_user(
        self, mock_db_session, mock_credentials, mock_supabase_user, mock_local_user
    ):
        """Test successful authentication with valid token and existing user."""
        # Mock Supabase auth service
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.supabase_auth') as mock_auth:
            # Setup successful token verification
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_supabase_user
            mock_auth.verify_token = AsyncMock(return_value=mock_result)
            
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
                mock_auth.verify_token.assert_called_once_with("valid-jwt-token")
                mock_repo_instance.find_by_id.assert_called_once_with("supabase-user-123")
                # Should not create new user
                mock_db_session.add.assert_not_called()
                mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_with_valid_token_new_user(
        self, mock_db_session, mock_credentials, mock_supabase_user
    ):
        """Test successful authentication with valid token for new user."""
        # Mock Supabase auth service
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.supabase_auth') as mock_auth:
            # Setup successful token verification
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_supabase_user
            mock_auth.verify_token = AsyncMock(return_value=mock_result)
            
            # Mock user repository to return None (user not found)
            with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserRepository') as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                mock_repo_class.return_value = mock_repo_instance
                
                # Call the function
                result = await get_current_user_supabase(
                    credentials=mock_credentials,
                    db=mock_db_session
                )
                
                # Assertions
                mock_auth.verify_token.assert_called_once_with("valid-jwt-token")
                mock_repo_instance.find_by_id.assert_called_once_with("supabase-user-123")
                # Should create new user
                mock_db_session.add.assert_called_once()
                mock_db_session.commit.assert_called_once()
                mock_db_session.refresh.assert_called_once()
                
                # Check created user properties
                created_user = mock_db_session.add.call_args[0][0]
                assert created_user.id == "supabase-user-123"
                assert created_user.email == "test@example.com"
                assert created_user.username == "testuser"
                assert created_user.full_name == "Test User"
                assert created_user.is_active is True
                assert created_user.is_superuser is False
                assert created_user.hashed_password == ""

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
        # Mock Supabase auth service
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.supabase_auth') as mock_auth:
            # Setup failed token verification
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.user = None
            mock_result.error_message = "Token expired"
            mock_auth.verify_token = AsyncMock(return_value=mock_result)
            
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
        # Mock Supabase auth service
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.supabase_auth') as mock_auth:
            # Setup token verification with user missing ID
            mock_user = MagicMock()
            mock_user.id = None
            mock_user.get.return_value = None
            
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.user = mock_user
            mock_auth.verify_token = AsyncMock(return_value=mock_result)
            
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
        # Mock Supabase auth service returning dict instead of object
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.supabase_auth') as mock_auth:
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
            mock_auth.verify_token = AsyncMock(return_value=mock_result)
            
            # Mock user repository to return None (create new user)
            with patch('fastmcp.auth.interface.supabase_fastapi_auth.UserRepository') as mock_repo_class:
                mock_repo_instance = MagicMock()
                mock_repo_instance.find_by_id.return_value = None
                mock_repo_class.return_value = mock_repo_instance
                
                # Call the function
                result = await get_current_user_supabase(
                    credentials=mock_credentials,
                    db=mock_db_session
                )
                
                # Check created user from dict data
                created_user = mock_db_session.add.call_args[0][0]
                assert created_user.id == "supabase-user-456"
                assert created_user.email == "dict@example.com"
                assert created_user.username == "dictuser"

    @pytest.mark.asyncio
    async def test_get_current_user_supabase_generic_exception_handling(
        self, mock_db_session, mock_credentials
    ):
        """Test generic exception handling during authentication."""
        # Mock Supabase auth service to raise exception
        with patch('fastmcp.auth.interface.supabase_fastapi_auth.supabase_auth') as mock_auth:
            mock_auth.verify_token = AsyncMock(side_effect=Exception("Network error"))
            
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