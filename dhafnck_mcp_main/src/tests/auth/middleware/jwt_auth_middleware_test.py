"""
Tests for JWT Authentication Middleware

This module tests the JWTAuthMiddleware class functionality including:
- JWT token extraction and validation
- User-scoped repository creation
- User-scoped service creation
- Authentication decorator
- User context management
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
import logging

from fastmcp.auth.middleware.jwt_auth_middleware import (
    JWTAuthMiddleware,
    UserContextManager,
    create_auth_middleware
)


class TestJWTAuthMiddleware:
    """Test suite for JWTAuthMiddleware"""
    
    @pytest.fixture
    def secret_key(self):
        """Test secret key"""
        return "test-secret-key-12345"
    
    @pytest.fixture
    def middleware(self, secret_key):
        """Create middleware instance"""
        return JWTAuthMiddleware(secret_key)
    
    @pytest.fixture
    def valid_token(self, secret_key):
        """Create a valid JWT token"""
        payload = {
            "sub": "test-user-123",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @pytest.fixture
    def valid_token_with_user_id(self, secret_key):
        """Create a valid JWT token with user_id claim"""
        payload = {
            "user_id": "test-user-456",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    @pytest.fixture
    def expired_token(self, secret_key):
        """Create an expired JWT token"""
        payload = {
            "sub": "test-user-789",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    def test_extract_user_from_valid_token(self, middleware, valid_token):
        """Test extracting user from valid token"""
        user_id = middleware.extract_user_from_token(valid_token)
        assert user_id == "test-user-123"
    
    def test_extract_user_from_bearer_token(self, middleware, valid_token):
        """Test extracting user from token with Bearer prefix"""
        bearer_token = f"Bearer {valid_token}"
        user_id = middleware.extract_user_from_token(bearer_token)
        assert user_id == "test-user-123"
    
    def test_extract_user_from_token_with_user_id_claim(self, middleware, valid_token_with_user_id):
        """Test extracting user from token with user_id claim"""
        user_id = middleware.extract_user_from_token(valid_token_with_user_id)
        assert user_id == "test-user-456"
    
    def test_extract_user_from_expired_token(self, middleware, expired_token):
        """Test extracting user from expired token returns None"""
        user_id = middleware.extract_user_from_token(expired_token)
        assert user_id is None
    
    def test_extract_user_from_invalid_token(self, middleware):
        """Test extracting user from invalid token returns None"""
        user_id = middleware.extract_user_from_token("invalid-token")
        assert user_id is None
    
    def test_extract_user_from_token_missing_user_claim(self, middleware, secret_key):
        """Test extracting user from token without user claim returns None"""
        payload = {"exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        user_id = middleware.extract_user_from_token(token)
        assert user_id is None
    
    def test_create_user_scoped_repository_with_user_id_in_constructor(self, middleware):
        """Test creating repository that accepts user_id in constructor"""
        # Mock repository class with user_id in __init__
        MockRepo = Mock()
        MockRepo.__init__ = Mock(return_value=None)
        MockRepo.__init__.__code__ = Mock(co_varnames=('self', 'session', 'user_id'))
        
        session = Mock(spec=Session)
        user_id = "test-user-123"
        
        repo = middleware.create_user_scoped_repository(MockRepo, session, user_id)
        
        MockRepo.assert_called_once_with(session=session, user_id=user_id)
    
    def test_create_user_scoped_repository_with_with_user_method(self, middleware):
        """Test creating repository with with_user method"""
        # Mock repository instance
        mock_repo = Mock()
        mock_scoped_repo = Mock()
        mock_repo.with_user.return_value = mock_scoped_repo
        
        # Mock repository class
        MockRepo = Mock(return_value=mock_repo)
        MockRepo.__init__ = Mock(return_value=None)
        MockRepo.__init__.__code__ = Mock(co_varnames=('self', 'session'))
        
        session = Mock(spec=Session)
        user_id = "test-user-123"
        
        repo = middleware.create_user_scoped_repository(MockRepo, session, user_id)
        
        MockRepo.assert_called_once_with(session=session)
        mock_repo.with_user.assert_called_once_with(user_id)
        assert repo == mock_scoped_repo
    
    def test_create_user_scoped_repository_with_user_id_property(self, middleware):
        """Test creating repository with user_id property"""
        # Mock repository instance
        mock_repo = Mock()
        mock_repo.user_id = None
        
        # Mock repository class
        MockRepo = Mock(return_value=mock_repo)
        MockRepo.__init__ = Mock(return_value=None)
        MockRepo.__init__.__code__ = Mock(co_varnames=('self', 'session'))
        
        session = Mock(spec=Session)
        user_id = "test-user-123"
        
        repo = middleware.create_user_scoped_repository(MockRepo, session, user_id)
        
        MockRepo.assert_called_once_with(session=session)
        assert mock_repo.user_id == user_id
        assert repo == mock_repo
    
    def test_create_user_scoped_repository_without_user_support(self, middleware):
        """Test creating repository that doesn't support user scoping"""
        # Mock repository instance
        mock_repo = Mock()
        
        # Mock repository class
        MockRepo = Mock(return_value=mock_repo)
        MockRepo.__init__ = Mock(return_value=None)
        MockRepo.__init__.__code__ = Mock(co_varnames=('self', 'session'))
        
        session = Mock(spec=Session)
        user_id = "test-user-123"
        
        with patch('fastmcp.auth.middleware.jwt_auth_middleware.logger') as mock_logger:
            repo = middleware.create_user_scoped_repository(MockRepo, session, user_id)
            
            MockRepo.assert_called_once_with(session=session)
            assert repo == mock_repo
            mock_logger.warning.assert_called_once()
    
    def test_create_user_scoped_service_with_user_id_in_constructor(self, middleware):
        """Test creating service that accepts user_id in constructor"""
        # Mock service class with user_id in __init__
        MockService = Mock()
        MockService.__init__ = Mock(return_value=None)
        MockService.__init__.__code__ = Mock(co_varnames=('self', 'user_id', 'repo'))
        
        user_id = "test-user-123"
        repo = Mock()
        
        service = middleware.create_user_scoped_service(MockService, user_id, repo=repo)
        
        MockService.assert_called_once_with(user_id=user_id, repo=repo)
    
    def test_create_user_scoped_service_with_with_user_method(self, middleware):
        """Test creating service with with_user method"""
        # Mock service instance
        mock_service = Mock()
        mock_scoped_service = Mock()
        mock_service.with_user.return_value = mock_scoped_service
        
        # Mock service class
        MockService = Mock(return_value=mock_service)
        MockService.__init__ = Mock(return_value=None)
        MockService.__init__.__code__ = Mock(co_varnames=('self', 'repo'))
        
        user_id = "test-user-123"
        repo = Mock()
        
        service = middleware.create_user_scoped_service(MockService, user_id, repo=repo)
        
        MockService.assert_called_once_with(repo=repo)
        mock_service.with_user.assert_called_once_with(user_id)
        assert service == mock_scoped_service
    
    def test_create_user_scoped_service_with_user_id_property(self, middleware):
        """Test creating service with _user_id property"""
        # Mock service instance
        mock_service = Mock()
        mock_service._user_id = None
        
        # Mock service class
        MockService = Mock(return_value=mock_service)
        MockService.__init__ = Mock(return_value=None)
        MockService.__init__.__code__ = Mock(co_varnames=('self', 'repo'))
        
        user_id = "test-user-123"
        repo = Mock()
        
        service = middleware.create_user_scoped_service(MockService, user_id, repo=repo)
        
        MockService.assert_called_once_with(repo=repo)
        assert mock_service._user_id == user_id
        assert service == mock_service
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_success(self, middleware, valid_token):
        """Test require_auth decorator with valid token"""
        # Mock request
        request = Mock()
        request.headers = {"Authorization": f"Bearer {valid_token}"}
        
        # Mock route handler
        async def route_handler(request, *args, **kwargs):
            return {"user_id": kwargs.get("user_id")}
        
        # Apply decorator
        decorated = middleware.require_auth(route_handler)
        
        # Call decorated function
        result = await decorated(request)
        
        assert result == {"user_id": "test-user-123"}
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_missing_header(self, middleware):
        """Test require_auth decorator with missing authorization header"""
        # Mock request
        request = Mock()
        request.headers = {}
        
        # Mock route handler
        async def route_handler(request, *args, **kwargs):
            return {"success": True}
        
        # Apply decorator
        decorated = middleware.require_auth(route_handler)
        
        # Call decorated function
        result = await decorated(request)
        
        assert result == ({"error": "Authorization header missing"}, 401)
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_invalid_token(self, middleware):
        """Test require_auth decorator with invalid token"""
        # Mock request
        request = Mock()
        request.headers = {"Authorization": "Bearer invalid-token"}
        
        # Mock route handler
        async def route_handler(request, *args, **kwargs):
            return {"success": True}
        
        # Apply decorator
        decorated = middleware.require_auth(route_handler)
        
        # Call decorated function
        result = await decorated(request)
        
        assert result == ({"error": "Invalid or expired token"}, 401)


class TestUserContextManager:
    """Test suite for UserContextManager"""
    
    @pytest.fixture
    def user_id(self):
        """Test user ID"""
        return "test-user-123"
    
    @pytest.fixture
    def context_manager(self, user_id):
        """Create context manager instance"""
        return UserContextManager(user_id)
    
    def test_get_repository_creates_scoped_repo(self, context_manager, user_id):
        """Test getting repository creates user-scoped version"""
        # Mock repository class
        MockRepo = Mock()
        session = Mock(spec=Session)
        
        with patch.object(JWTAuthMiddleware, 'create_user_scoped_repository') as mock_create:
            mock_repo = Mock()
            mock_create.return_value = mock_repo
            
            # Get repository
            repo = context_manager.get_repository(MockRepo, session)
            
            # Verify creation
            assert mock_create.called
            args = mock_create.call_args[0]
            assert args[0] == MockRepo
            assert args[1] == session
            assert args[2] == user_id
            
            # Verify caching
            repo2 = context_manager.get_repository(MockRepo, session)
            assert repo == repo2
            assert mock_create.call_count == 1
    
    def test_get_service_creates_scoped_service(self, context_manager, user_id):
        """Test getting service creates user-scoped version"""
        # Mock service class
        MockService = Mock()
        repo = Mock()
        
        with patch.object(JWTAuthMiddleware, 'create_user_scoped_service') as mock_create:
            mock_service = Mock()
            mock_create.return_value = mock_service
            
            # Get service
            service = context_manager.get_service(MockService, repo=repo)
            
            # Verify creation
            assert mock_create.called
            args = mock_create.call_args[0]
            assert args[0] == MockService
            assert args[1] == user_id
            assert mock_create.call_args[1] == {'repo': repo}
            
            # Verify caching
            service2 = context_manager.get_service(MockService, repo=repo)
            assert service == service2
            assert mock_create.call_count == 1
    
    def test_clear_cache(self, context_manager):
        """Test clearing cache"""
        # Mock repository and service
        MockRepo = Mock()
        MockService = Mock()
        session = Mock(spec=Session)
        
        with patch.object(JWTAuthMiddleware, 'create_user_scoped_repository') as mock_create_repo:
            with patch.object(JWTAuthMiddleware, 'create_user_scoped_service') as mock_create_service:
                mock_create_repo.return_value = Mock()
                mock_create_service.return_value = Mock()
                
                # Get repository and service
                context_manager.get_repository(MockRepo, session)
                context_manager.get_service(MockService)
                
                # Clear cache
                context_manager.clear_cache()
                
                # Get again - should create new instances
                context_manager.get_repository(MockRepo, session)
                context_manager.get_service(MockService)
                
                assert mock_create_repo.call_count == 2
                assert mock_create_service.call_count == 2


class TestCreateAuthMiddleware:
    """Test suite for create_auth_middleware factory function"""
    
    def test_create_auth_middleware(self):
        """Test creating middleware instance"""
        secret_key = "test-secret"
        algorithm = "HS512"
        
        middleware = create_auth_middleware(secret_key, algorithm)
        
        assert isinstance(middleware, JWTAuthMiddleware)
        assert middleware.secret_key == secret_key
        assert middleware.algorithm == algorithm
    
    def test_create_auth_middleware_default_algorithm(self):
        """Test creating middleware with default algorithm"""
        secret_key = "test-secret"
        
        middleware = create_auth_middleware(secret_key)
        
        assert isinstance(middleware, JWTAuthMiddleware)
        assert middleware.secret_key == secret_key
        assert middleware.algorithm == "HS256"


class TestJWTAuthMiddlewareLogging:
    """Test suite for enhanced JWT middleware logging"""
    
    @pytest.fixture
    def secret_key(self):
        """Test secret key"""
        return "test-secret-key-12345"
    
    @pytest.fixture
    def middleware(self, secret_key):
        """Create middleware instance"""
        return JWTAuthMiddleware(secret_key)
    
    def test_initialization_logging(self, caplog):
        """Test initialization logs secret key info"""
        secret_key = "my-test-secret-key-for-testing"
        
        with caplog.at_level(logging.DEBUG):  # Changed to DEBUG level to capture debug logs
            middleware = JWTAuthMiddleware(secret_key)
            
        # Check that secret length is logged
        assert "🔐 JWTAuthMiddleware initialized with secret length: 30 chars" in caplog.text
        assert "🔐 JWTAuthMiddleware secret (first 10 chars): my-test-se..." in caplog.text
    
    def test_initialization_warning_for_default_secret(self, caplog):
        """Test warning logged for default secret key"""
        default_secret = "default-secret-key-change-in-production"
        
        with caplog.at_level(logging.WARNING):
            middleware = JWTAuthMiddleware(default_secret)
            
        assert "⚠️ JWTAuthMiddleware using default fallback secret key!" in caplog.text
    
    def test_token_decode_success_logging(self, middleware, secret_key, caplog):
        """Test successful token decode logging"""
        payload = {
            "sub": "test-user-123",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        with caplog.at_level(logging.DEBUG):
            user_id = middleware.extract_user_from_token(token)
            
        assert "🔍 JWTAuthMiddleware attempting token decode" in caplog.text
        assert f"🔍 Token length: {len(token)} chars" in caplog.text
        assert "✅ JWTAuthMiddleware successfully decoded token" in caplog.text
        assert "Extracted user_id test-user-123 from JWT token" in caplog.text
    
    def test_token_decode_failure_logging(self, middleware, caplog):
        """Test failed token decode logging"""
        invalid_token = "this-is-not-a-valid-jwt-token"
        
        with caplog.at_level(logging.ERROR):
            user_id = middleware.extract_user_from_token(invalid_token)
            
        assert "❌ JWTAuthMiddleware - Invalid JWT token" in caplog.text
        assert f"❌ Using secret length: {len(middleware.secret_key)}, algorithm: HS256" in caplog.text
        assert "❌ Token (first 50 chars): this-is-not-a-valid-jwt-token" in caplog.text
        assert user_id is None
    
    def test_bearer_prefix_handling_logging(self, middleware, secret_key, caplog):
        """Test Bearer prefix removal logging"""
        payload = {
            "sub": "test-user-456",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        bearer_token = f"Bearer {token}"
        
        with caplog.at_level(logging.DEBUG):
            user_id = middleware.extract_user_from_token(bearer_token)
            
        # Should see token length after Bearer removal
        assert f"🔍 Token length: {len(token)} chars" in caplog.text
        assert user_id == "test-user-456"
    
    def test_missing_user_claim_logging(self, middleware, secret_key, caplog):
        """Test logging when user claim is missing"""
        payload = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "some_other_claim": "value"
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        with caplog.at_level(logging.WARNING):
            user_id = middleware.extract_user_from_token(token)
            
        assert "JWT token missing user_id/sub claim" in caplog.text
        assert user_id is None
    
    def test_expired_token_logging(self, middleware, secret_key, caplog):
        """Test logging for expired token"""
        payload = {
            "sub": "test-user-789",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        with caplog.at_level(logging.ERROR):
            user_id = middleware.extract_user_from_token(token)
            
        assert "❌ JWTAuthMiddleware - Invalid JWT token" in caplog.text
        assert "Signature has expired" in caplog.text
        assert user_id is None
    
    def test_general_exception_logging(self, middleware, caplog):
        """Test logging for general exceptions"""
        # Create a mock that raises an exception
        with patch('jwt.decode', side_effect=Exception("Unexpected error")):
            with caplog.at_level(logging.ERROR):
                user_id = middleware.extract_user_from_token("some-token")
                
        assert "❌ JWTAuthMiddleware - Error extracting user from token: Unexpected error" in caplog.text
        assert user_id is None