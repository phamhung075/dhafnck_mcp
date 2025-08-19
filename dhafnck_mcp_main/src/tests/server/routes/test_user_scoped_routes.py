"""
Tests for user-scoped API routes with JWT authentication.

These tests verify that API routes properly extract user context from JWT tokens
and create user-scoped services and repositories.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import the routes and dependencies
from fastmcp.server.routes.user_scoped_task_routes import router as task_router
from fastmcp.server.routes.user_scoped_project_routes import router as project_router
from fastmcp.auth.middleware.jwt_auth_middleware import JWTAuthMiddleware, UserContextManager


class TestUserScopedRoutes:
    """Test suite for user-scoped API routes with JWT authentication."""
    
    @pytest.fixture
    def secret_key(self):
        """JWT secret key for testing."""
        return "test-secret-key-for-jwt"
    
    @pytest.fixture
    def user1_id(self):
        """Generate user 1 ID."""
        return str(uuid4())
    
    @pytest.fixture
    def user2_id(self):
        """Generate user 2 ID."""
        return str(uuid4())
    
    @pytest.fixture
    def user1_token(self, user1_id, secret_key):
        """Generate JWT token for user 1."""
        payload = {
            "sub": user1_id,
            "email": "user1@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @pytest.fixture
    def user2_token(self, user2_id, secret_key):
        """Generate JWT token for user 2."""
        payload = {
            "sub": user2_id,
            "email": "user2@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @pytest.fixture
    def expired_token(self, user1_id, secret_key):
        """Generate expired JWT token."""
        payload = {
            "sub": user1_id,
            "email": "user1@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @pytest.fixture
    def invalid_token(self):
        """Generate invalid JWT token."""
        return "invalid.jwt.token"
    
    @pytest.fixture
    def jwt_middleware(self, secret_key):
        """Create JWT middleware instance."""
        return JWTAuthMiddleware(secret_key)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with routes."""
        app = FastAPI()
        app.include_router(task_router)
        app.include_router(project_router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    # ==================== JWT Middleware Tests ====================
    
    def test_jwt_middleware_extracts_user_from_valid_token(self, jwt_middleware, user1_token, user1_id):
        """Test that JWT middleware correctly extracts user_id from valid token."""
        # Extract user from token
        extracted_user_id = jwt_middleware.extract_user_from_token(user1_token)
        
        # Verify correct user_id was extracted
        assert extracted_user_id == user1_id
    
    def test_jwt_middleware_handles_bearer_prefix(self, jwt_middleware, user1_token, user1_id):
        """Test that JWT middleware handles Bearer prefix in token."""
        # Add Bearer prefix
        token_with_bearer = f"Bearer {user1_token}"
        
        # Extract user from token
        extracted_user_id = jwt_middleware.extract_user_from_token(token_with_bearer)
        
        # Verify correct user_id was extracted
        assert extracted_user_id == user1_id
    
    def test_jwt_middleware_returns_none_for_invalid_token(self, jwt_middleware, invalid_token):
        """Test that JWT middleware returns None for invalid token."""
        # Extract user from invalid token
        extracted_user_id = jwt_middleware.extract_user_from_token(invalid_token)
        
        # Should return None
        assert extracted_user_id is None
    
    def test_jwt_middleware_returns_none_for_expired_token(self, jwt_middleware, expired_token):
        """Test that JWT middleware returns None for expired token."""
        # Extract user from expired token
        extracted_user_id = jwt_middleware.extract_user_from_token(expired_token)
        
        # Should return None (expired tokens are invalid)
        assert extracted_user_id is None
    
    def test_jwt_middleware_handles_missing_user_claim(self, jwt_middleware, secret_key):
        """Test that JWT middleware handles tokens without user_id/sub claim."""
        # Create token without sub/user_id
        payload = {
            "email": "user@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        # Extract user from token
        extracted_user_id = jwt_middleware.extract_user_from_token(token)
        
        # Should return None
        assert extracted_user_id is None
    
    # ==================== User Context Manager Tests ====================
    
    def test_user_context_manager_stores_user_id(self, user1_id):
        """Test that UserContextManager stores user_id."""
        manager = UserContextManager(user1_id)
        assert manager.user_id == user1_id
    
    def test_user_context_manager_creates_scoped_repository(self, user1_id, mock_db_session):
        """Test that UserContextManager creates user-scoped repositories."""
        manager = UserContextManager(user1_id)
        
        # Mock repository class
        MockRepo = Mock()
        MockRepo.__name__ = "MockRepo"
        mock_instance = Mock()
        mock_instance.with_user = Mock(return_value=Mock())
        MockRepo.return_value = mock_instance
        
        # Get repository
        repo = manager.get_repository(MockRepo, mock_db_session)
        
        # Verify repository was created with user context
        MockRepo.assert_called_with(session=mock_db_session)
        mock_instance.with_user.assert_called_with(user1_id)
    
    def test_user_context_manager_caches_repositories(self, user1_id, mock_db_session):
        """Test that UserContextManager caches repositories to avoid duplicates."""
        manager = UserContextManager(user1_id)
        
        # Mock repository class
        MockRepo = Mock()
        MockRepo.__name__ = "MockRepo"
        mock_instance = Mock()
        mock_instance.with_user = Mock(return_value=Mock())
        MockRepo.return_value = mock_instance
        
        # Get repository twice
        repo1 = manager.get_repository(MockRepo, mock_db_session)
        repo2 = manager.get_repository(MockRepo, mock_db_session)
        
        # Should be the same instance (cached)
        assert repo1 is repo2
        
        # Repository should only be created once
        MockRepo.assert_called_once()
    
    def test_user_context_manager_creates_scoped_service(self, user1_id):
        """Test that UserContextManager creates user-scoped services."""
        manager = UserContextManager(user1_id)
        
        # Mock service class
        MockService = Mock()
        MockService.__name__ = "MockService"
        mock_instance = Mock()
        mock_instance.with_user = Mock(return_value=Mock())
        MockService.return_value = mock_instance
        
        # Get service
        service = manager.get_service(MockService, repo=Mock())
        
        # Verify service was created with user context
        MockService.assert_called_with(repo=Mock())
        mock_instance.with_user.assert_called_with(user1_id)
    
    def test_user_context_manager_clear_cache(self, user1_id):
        """Test that UserContextManager can clear its cache."""
        manager = UserContextManager(user1_id)
        
        # Add some cached items
        manager._scoped_repositories["test"] = Mock()
        manager._scoped_services["test"] = Mock()
        
        # Clear cache
        manager.clear_cache()
        
        # Cache should be empty
        assert len(manager._scoped_repositories) == 0
        assert len(manager._scoped_services) == 0
    
    # ==================== Repository Creation Tests ====================
    
    def test_create_user_scoped_repository_with_user_id_param(self, jwt_middleware, user1_id, mock_db_session):
        """Test creating repository when class accepts user_id parameter."""
        # Mock repository class that accepts user_id
        class MockRepo:
            def __init__(self, session, user_id=None):
                self.session = session
                self.user_id = user_id
        
        # Create user-scoped repository
        repo = jwt_middleware.create_user_scoped_repository(
            MockRepo, mock_db_session, user1_id
        )
        
        # Verify repository has user_id
        assert repo.user_id == user1_id
        assert repo.session == mock_db_session
    
    def test_create_user_scoped_repository_with_with_user_method(self, jwt_middleware, user1_id, mock_db_session):
        """Test creating repository when class has with_user method."""
        # Mock repository with with_user method
        mock_repo = Mock()
        mock_scoped = Mock()
        mock_repo.with_user = Mock(return_value=mock_scoped)
        
        MockRepo = Mock(return_value=mock_repo)
        
        # Create user-scoped repository
        repo = jwt_middleware.create_user_scoped_repository(
            MockRepo, mock_db_session, user1_id
        )
        
        # Verify with_user was called
        mock_repo.with_user.assert_called_with(user1_id)
        assert repo == mock_scoped
    
    def test_create_user_scoped_repository_without_support(self, jwt_middleware, user1_id, mock_db_session):
        """Test creating repository when class doesn't support user scoping."""
        # Mock repository without user support
        class MockRepo:
            def __init__(self, session):
                self.session = session
        
        # Create repository (should return as-is)
        repo = jwt_middleware.create_user_scoped_repository(
            MockRepo, mock_db_session, user1_id
        )
        
        # Should return repository without user_id
        assert repo.session == mock_db_session
        assert not hasattr(repo, 'user_id')
    
    # ==================== Service Creation Tests ====================
    
    def test_create_user_scoped_service_with_user_id_param(self, jwt_middleware, user1_id):
        """Test creating service when class accepts user_id parameter."""
        # Mock service class that accepts user_id
        class MockService:
            def __init__(self, repo, user_id=None):
                self.repo = repo
                self._user_id = user_id
        
        mock_repo = Mock()
        
        # Create user-scoped service
        service = jwt_middleware.create_user_scoped_service(
            MockService, user1_id, repo=mock_repo
        )
        
        # Verify service has user_id
        assert service._user_id == user1_id
        assert service.repo == mock_repo
    
    def test_create_user_scoped_service_with_with_user_method(self, jwt_middleware, user1_id):
        """Test creating service when class has with_user method."""
        # Mock service with with_user method
        mock_service = Mock()
        mock_scoped = Mock()
        mock_service.with_user = Mock(return_value=mock_scoped)
        
        MockService = Mock(return_value=mock_service)
        
        # Create user-scoped service
        service = jwt_middleware.create_user_scoped_service(
            MockService, user1_id, repo=Mock()
        )
        
        # Verify with_user was called
        mock_service.with_user.assert_called_with(user1_id)
        assert service == mock_scoped
    
    # ==================== Data Isolation Tests ====================
    
    def test_different_users_get_different_contexts(self, user1_id, user2_id):
        """Test that different users get different context managers."""
        # Create context managers for two users
        manager1 = UserContextManager(user1_id)
        manager2 = UserContextManager(user2_id)
        
        # Verify they have different user_ids
        assert manager1.user_id == user1_id
        assert manager2.user_id == user2_id
        
        # Verify they are different instances
        assert manager1 is not manager2
    
    def test_repositories_isolated_between_users(self, jwt_middleware, user1_id, user2_id, mock_db_session):
        """Test that repositories are properly isolated between users."""
        # Mock repository class
        class MockRepo:
            def __init__(self, session, user_id=None):
                self.session = session
                self.user_id = user_id
        
        # Create repositories for two users
        repo1 = jwt_middleware.create_user_scoped_repository(
            MockRepo, mock_db_session, user1_id
        )
        repo2 = jwt_middleware.create_user_scoped_repository(
            MockRepo, mock_db_session, user2_id
        )
        
        # Verify they have different user_ids
        assert repo1.user_id == user1_id
        assert repo2.user_id == user2_id
        
        # Verify they are different instances
        assert repo1 is not repo2
    
    def test_services_isolated_between_users(self, jwt_middleware, user1_id, user2_id):
        """Test that services are properly isolated between users."""
        # Mock service class
        class MockService:
            def __init__(self, repo, user_id=None):
                self.repo = repo
                self._user_id = user_id
        
        mock_repo = Mock()
        
        # Create services for two users
        service1 = jwt_middleware.create_user_scoped_service(
            MockService, user1_id, repo=mock_repo
        )
        service2 = jwt_middleware.create_user_scoped_service(
            MockService, user2_id, repo=mock_repo
        )
        
        # Verify they have different user_ids
        assert service1._user_id == user1_id
        assert service2._user_id == user2_id
        
        # Verify they are different instances
        assert service1 is not service2