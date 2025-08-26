"""
Tests for MCP JWT Authentication Integration

This module tests the integration between JWT authentication and MCP server,
including token validation, user context, and repository filtering.
"""

import pytest
import os
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import jwt

from fastmcp.auth.mcp_integration.jwt_auth_backend import (
    JWTAuthBackend,
    MCPUserContext,
    create_jwt_auth_backend
)
from fastmcp.auth.middleware.request_context_middleware import (
    RequestContextMiddleware as UserContextMiddleware,  # Alias for backward compatibility
    get_current_user_context,
    get_current_user_id,
    current_user_context
)
from fastmcp.auth.mcp_integration.repository_filter import (
    UserFilteredTaskRepository,
    UserFilteredProjectRepository,
    UserFilteredContextRepository
)
from fastmcp.auth.domain.services.jwt_service import JWTService
from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole
from fastmcp.auth.domain.value_objects import UserId


class TestJWTAuthBackend:
    """Test JWT authentication backend for MCP"""
    
    @pytest.fixture
    def jwt_service(self):
        """Create JWT service with test secret"""
        return JWTService(
            secret_key="test-secret-key-for-testing-only",
            issuer="test-issuer"
        )
    
    @pytest.fixture
    def mock_user_repository(self):
        """Create mock user repository"""
        repo = Mock()
        
        # Configure find_by_id to return a user for any UUID
        def find_user_by_id(user_id):
            test_user = User(
                email="test@example.com",
                username="testuser",
                password_hash="hashed_password"
            )
            test_user.id = user_id  # Use the provided ID
            test_user.status = UserStatus.ACTIVE
            test_user.roles = [UserRole.USER, UserRole.DEVELOPER]
            return test_user
        
        repo.find_by_id.side_effect = find_user_by_id
        return repo
    
    @pytest.fixture
    def jwt_backend(self, jwt_service, mock_user_repository):
        """Create JWT backend with mocks"""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-key-for-testing-only"}):
            return JWTAuthBackend(
                jwt_service=jwt_service,
                user_repository=mock_user_repository,
                required_scopes=["mcp:access"]
            )
    
    @pytest.mark.asyncio
    async def test_load_valid_access_token(self, jwt_backend, jwt_service):
        """Test loading valid access token"""
        # Create valid token
        user_id = str(uuid.uuid4())
        token = jwt_service.create_access_token(
            user_id=user_id,
            email="test@example.com",
            roles=["user", "developer"],
            additional_claims={"scopes": ["read", "write"]}
        )
        
        # Load token (using new verify_token method)
        access_token = await jwt_backend.verify_token(token)
        
        # Verify
        assert access_token is not None
        assert access_token.client_id == user_id
        assert "mcp:access" in access_token.scopes
        assert "mcp:read" in access_token.scopes  # From developer role
        assert "mcp:write" in access_token.scopes  # From developer role
    
    @pytest.mark.asyncio
    async def test_reject_invalid_token(self, jwt_backend):
        """Test rejection of invalid token"""
        invalid_token = "invalid.jwt.token"
        
        access_token = await jwt_backend.verify_token(invalid_token)
        
        assert access_token is None
    
    @pytest.mark.asyncio
    async def test_reject_refresh_token(self, jwt_backend, jwt_service):
        """Test rejection of refresh token (only access tokens allowed)"""
        # Create refresh token
        user_id = str(uuid.uuid4())
        refresh_token, _ = jwt_service.create_refresh_token(
            user_id=user_id,
            token_family="family-456"
        )
        
        access_token = await jwt_backend.verify_token(refresh_token)
        
        assert access_token is None
    
    @pytest.mark.asyncio
    async def test_user_context_caching(self, jwt_backend, mock_user_repository):
        """Test that user context is cached"""
        user_id = str(uuid.uuid4())
        
        # Get context twice
        context1 = await jwt_backend._get_user_context(user_id)
        context2 = await jwt_backend._get_user_context(user_id)
        
        # Should only call repository once due to caching
        assert mock_user_repository.find_by_id.call_count == 1
        assert context1 == context2
    
    def test_role_to_scope_mapping(self, jwt_backend):
        """Test role to MCP scope mapping"""
        # Admin role
        admin_scopes = jwt_backend._map_roles_to_scopes(["admin"])
        assert "mcp:admin" in admin_scopes
        assert "mcp:write" in admin_scopes
        assert "mcp:read" in admin_scopes
        assert "mcp:access" in admin_scopes
        
        # Developer role
        dev_scopes = jwt_backend._map_roles_to_scopes(["developer"])
        assert "mcp:admin" not in dev_scopes
        assert "mcp:write" in dev_scopes
        assert "mcp:read" in dev_scopes
        assert "mcp:access" in dev_scopes
        
        # User role
        user_scopes = jwt_backend._map_roles_to_scopes(["user"])
        assert "mcp:admin" not in user_scopes
        assert "mcp:write" not in user_scopes
        assert "mcp:read" in user_scopes
        assert "mcp:access" in user_scopes


class TestUserContextMiddleware:
    """Test user context middleware"""
    
    @pytest.fixture
    def jwt_service(self):
        """Create JWT service"""
        return JWTService(
            secret_key="test-secret-key",
            issuer="test-issuer"
        )
    
    @pytest.fixture
    def mock_jwt_backend(self):
        """Create mock JWT backend"""
        backend = AsyncMock(spec=JWTAuthBackend)
        
        # Mock access token
        test_user_id = str(uuid.uuid4())
        mock_token = Mock()
        mock_token.client_id = test_user_id
        mock_token.scopes = ["mcp:access", "mcp:read"]
        backend.load_access_token.return_value = mock_token
        
        # Mock user context
        mock_context = MCPUserContext(
            user_id=test_user_id,
            email="test@example.com",
            username="testuser",
            roles=["user"],
            scopes=["mcp:access", "mcp:read"]
        )
        backend._get_user_context.return_value = mock_context
        
        return backend
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock()
        request.headers = {"Authorization": "Bearer test-token"}
        request.state = Mock()
        return request
    
    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app"""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_extract_user_context(self, mock_app, mock_jwt_backend, mock_request):
        """Test extraction of user context from JWT"""
        middleware = UserContextMiddleware(mock_app, jwt_backend=mock_jwt_backend)
        
        # Mock call_next
        mock_response = Mock()
        async def call_next(request):
            # Check that context is set during request
            context = get_current_user_context()
            assert context is not None
            assert context.user_id == test_user_id
            return mock_response
        
        # Process request
        response = await middleware.dispatch(mock_request, call_next)
        
        # Verify
        assert response == mock_response
        assert mock_request.state.user_id == test_user_id
        assert mock_request.state.user_email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_no_token_provided(self, mock_app, mock_jwt_backend, mock_request):
        """Test middleware with no authorization header"""
        mock_request.headers = {}
        middleware = UserContextMiddleware(mock_app, jwt_backend=mock_jwt_backend)
        
        mock_response = Mock()
        async def call_next(request):
            # Context should be None
            context = get_current_user_context()
            assert context is None
            return mock_response
        
        response = await middleware.dispatch(mock_request, call_next)
        assert response == mock_response


class TestUserFilteredRepositories:
    """Test user-filtered repository wrappers"""
    
    @pytest.fixture
    def mock_base_repository(self):
        """Create mock base repository"""
        return Mock()
    
    @pytest.fixture
    def set_user_context(self):
        """Set user context for testing"""
        test_user_id = str(uuid.uuid4())
        context = MCPUserContext(
            user_id=test_user_id,
            email="test@example.com",
            username="testuser",
            roles=["user"],
            scopes=["mcp:access"]
        )
        token = current_user_context.set(context)
        yield
        current_user_context.reset(token)
    
    def test_task_repository_filter_by_user(self, mock_base_repository, set_user_context):
        """Test task repository filters by user"""
        filtered_repo = UserFilteredTaskRepository(mock_base_repository)
        
        # Get user_id from context
        user_id = get_current_user_id()
        
        # Mock tasks
        task1 = Mock(id="task-1", user_id=user_id)
        task2 = Mock(id="task-2", user_id="user-456")
        task3 = Mock(id="task-3", user_id=user_id)
        
        mock_base_repository.find_all.return_value = [task1, task2, task3]
        
        # Find all should filter by user
        result = filtered_repo.find_all()
        
        # Verify user filter was added
        mock_base_repository.find_all.assert_called_with(user_id=user_id)
    
    def test_task_repository_find_by_id_access_control(self, mock_base_repository, set_user_context):
        """Test task repository access control on find_by_id"""
        filtered_repo = UserFilteredTaskRepository(mock_base_repository)
        
        # Get user_id from context
        user_id = get_current_user_id()
        
        # Task belonging to current user
        user_task = Mock(id="task-1", user_id=user_id)
        mock_base_repository.find_by_id.return_value = user_task
        
        result = filtered_repo.find_by_id("task-1")
        assert result == user_task
        
        # Task belonging to another user
        other_task = Mock(id="task-2", user_id="user-456")
        mock_base_repository.find_by_id.return_value = other_task
        
        result = filtered_repo.find_by_id("task-2")
        assert result is None  # Should not return other user's task
    
    def test_project_repository_save_sets_user_id(self, mock_base_repository, set_user_context):
        """Test project repository sets user_id on save"""
        filtered_repo = UserFilteredProjectRepository(mock_base_repository)
        
        # New project without ID
        new_project = Mock(id=None, spec=["id", "user_id"])
        mock_base_repository.save.return_value = new_project
        
        result = filtered_repo.save(new_project)
        
        # Get user_id from context
        user_id = get_current_user_id()
        
        # Should set user_id
        assert new_project.user_id == user_id
        mock_base_repository.save.assert_called_with(new_project)
    
    def test_context_repository_allows_global_context(self, mock_base_repository, set_user_context):
        """Test context repository allows access to global contexts"""
        filtered_repo = UserFilteredContextRepository(mock_base_repository)
        
        # Global context (no user_id)
        global_context = Mock(id="ctx-1", user_id=None, level="global")
        mock_base_repository.find_by_id.return_value = global_context
        
        result = filtered_repo.find_by_id("ctx-1")
        assert result == global_context  # Should allow access to global context
        
        # Get user_id from context
        user_id = get_current_user_id()
        
        # User context
        user_context = Mock(id="ctx-2", user_id=user_id, level="task")
        mock_base_repository.find_by_id.return_value = user_context
        
        result = filtered_repo.find_by_id("ctx-2")
        assert result == user_context  # Should allow access to own context
    
    def test_repository_without_user_context_raises_error(self, mock_base_repository):
        """Test repository raises error when no user context"""
        # No user context set
        filtered_repo = UserFilteredTaskRepository(mock_base_repository)
        
        with pytest.raises(RuntimeError, match="No authenticated user"):
            filtered_repo.find_all()


class TestJWTBackendFactory:
    """Test JWT backend factory function"""
    
    def test_create_jwt_backend_without_database(self):
        """Test creating JWT backend without database"""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            backend = create_jwt_auth_backend()
            
            assert backend is not None
            assert isinstance(backend, JWTAuthBackend)
            assert backend._user_repository is None
    
    def test_create_jwt_backend_with_database(self):
        """Test creating JWT backend with database"""
        mock_session_factory = Mock()
        
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret"}):
            backend = create_jwt_auth_backend(
                database_session_factory=mock_session_factory
            )
            
            assert backend is not None
            assert backend._user_repository is not None
    
    def test_create_jwt_backend_requires_secret(self):
        """Test that JWT backend requires secret key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
                create_jwt_auth_backend()


class TestIntegration:
    """Integration tests for complete auth flow"""
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self):
        """Test complete authentication flow from token to filtered repository"""
        # Setup
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "integration-test-secret"}):
            # Create services
            jwt_service = JWTService(secret_key="integration-test-secret")
            
            # Create user with valid UUID
            user_id = str(uuid.uuid4())
            test_user = User(
                email="integration@test.com",
                username="integrationuser",
                password_hash="hashed"
            )
            test_user.id = UserId(user_id)
            test_user.status = UserStatus.ACTIVE
            test_user.roles = [UserRole.DEVELOPER]
            
            # Mock repository
            mock_user_repo = Mock()
            mock_user_repo.find_by_id.return_value = test_user
            
            # Create backend
            jwt_backend = JWTAuthBackend(
                jwt_service=jwt_service,
                user_repository=mock_user_repo
            )
            
            # Create token
            token = jwt_service.create_access_token(
                user_id=user_id,
                email="integration@test.com",
                roles=["developer"],
                additional_claims={"scopes": ["read", "write"]}
            )
            
            # Validate token  
            access_token = await jwt_backend.verify_token(token)
            
            # Verify complete flow
            assert access_token is not None
            assert access_token.client_id == user_id
            assert "mcp:write" in access_token.scopes  # Developer role mapping
            
            # Set user context (simulating middleware)
            user_context = await jwt_backend._get_user_context(user_id)
            token_var = current_user_context.set(user_context)
            
            try:
                # Create filtered repository
                mock_task_repo = Mock()
                mock_task_repo.find_all.return_value = []
                
                filtered_repo = UserFilteredTaskRepository(mock_task_repo)
                
                # Use filtered repository
                tasks = filtered_repo.find_all(status="pending")
                
                # Verify user filter was applied
                mock_task_repo.find_all.assert_called_with(
                    status="pending",
                    user_id=user_id
                )
            finally:
                current_user_context.reset(token_var)