"""
Tests for Agent Repository Factory

This module tests the AgentRepositoryFactory functionality including:
- Factory pattern implementation for repository creation
- Multi-user repository management and caching
- Environment configuration and authentication handling
- Repository type registration and fallback mechanisms
- Configuration validation and error handling
- Global repository management and lifecycle
"""

import pytest
import os
import unittest.mock
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from fastmcp.task_management.infrastructure.repositories.agent_repository_factory import (
    AgentRepositoryFactory,
    AgentRepositoryType,
    AgentRepositoryConfig,
    GlobalAgentRepositoryManager,
    create_agent_repository,
    get_sqlite_agent_repository,
    get_orm_agent_repository,
    get_default_agent_repository,
    get_user_agent_repository,
    create_agent_repository_factory
)
from fastmcp.task_management.domain.repositories.agent_repository import AgentRepository
from fastmcp.task_management.infrastructure.repositories.orm.agent_repository import ORMAgentRepository
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)


class TestAgentRepositoryFactory:
    """Test cases for AgentRepositoryFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear factory cache before each test
        AgentRepositoryFactory.clear_cache()
        GlobalAgentRepositoryManager.clear_all()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clear factory cache after each test
        AgentRepositoryFactory.clear_cache()
        GlobalAgentRepositoryManager.clear_all()
    
    def test_agent_repository_type_enum(self):
        """Test AgentRepositoryType enum values."""
        assert AgentRepositoryType.ORM.value == "orm"
        assert AgentRepositoryType.IN_MEMORY.value == "in_memory"
        assert AgentRepositoryType.MOCK.value == "mock"
        
        # Test enum iteration
        types = list(AgentRepositoryType)
        assert len(types) >= 3
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.validate_user_id')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AuthConfig')
    def test_create_repository_success(self, mock_auth_config, mock_validate):
        """Test successful repository creation with valid user."""
        mock_validate.return_value = "test-user-123"
        mock_auth_config.is_default_user_allowed.return_value = False
        
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository') as mock_orm:
            mock_instance = Mock(spec=AgentRepository)
            mock_orm.return_value = mock_instance
            
            result = AgentRepositoryFactory.create(
                repository_type=AgentRepositoryType.ORM,
                user_id="test-user-123"
            )
            
            assert result == mock_instance
            mock_validate.assert_called_once_with("test-user-123", "Agent repository creation")
            mock_orm.assert_called_once_with(user_id="test-user-123")
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AuthConfig')
    def test_create_repository_no_user_id_compatibility_mode(self, mock_auth_config):
        """Test repository creation without user ID in compatibility mode."""
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "fallback-user"
        
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository') as mock_orm:
            mock_instance = Mock(spec=AgentRepository)
            mock_orm.return_value = mock_instance
            
            result = AgentRepositoryFactory.create(user_id=None)
            
            assert result == mock_instance
            mock_auth_config.is_default_user_allowed.assert_called_once()
            mock_auth_config.get_fallback_user_id.assert_called_once()
            mock_auth_config.log_authentication_bypass.assert_called_once_with(
                "Agent repository creation", "compatibility mode"
            )
            mock_orm.assert_called_once_with(user_id="fallback-user")
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AuthConfig')
    def test_create_repository_no_user_id_no_compatibility(self, mock_auth_config):
        """Test repository creation without user ID when compatibility is disabled."""
        mock_auth_config.is_default_user_allowed.return_value = False
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            AgentRepositoryFactory.create(user_id=None)
        
        assert "Agent repository creation" in str(exc_info.value)
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.validate_user_id')
    def test_create_repository_with_prohibited_user_id(self, mock_validate):
        """Test repository creation with prohibited user ID."""
        mock_validate.side_effect = DefaultUserProhibitedError()
        
        with pytest.raises(DefaultUserProhibitedError):
            AgentRepositoryFactory.create(user_id="default_id")
    
    def test_create_repository_caching(self):
        """Test that repositories are cached properly."""
        user_id = "test-user-123"
        
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository') as mock_orm:
            mock_instance = Mock(spec=AgentRepository)
            mock_orm.return_value = mock_instance
            
            # Create repository twice
            result1 = AgentRepositoryFactory.create(
                repository_type=AgentRepositoryType.ORM,
                user_id=user_id
            )
            result2 = AgentRepositoryFactory.create(
                repository_type=AgentRepositoryType.ORM,
                user_id=user_id
            )
            
            # Should return same instance
            assert result1 is result2
            # Should only create once
            mock_orm.assert_called_once()
    
    def test_create_repository_different_cache_keys(self):
        """Test that different parameters create different cache entries."""
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository') as mock_orm:
            mock_orm.side_effect = lambda **kwargs: Mock(spec=AgentRepository)
            
            # Create with different user IDs
            result1 = AgentRepositoryFactory.create(user_id="user1")
            result2 = AgentRepositoryFactory.create(user_id="user2")
            
            # Should be different instances
            assert result1 is not result2
            # Should create twice
            assert mock_orm.call_count == 2
    
    @patch.dict(os.environ, {'MCP_AGENT_REPOSITORY_TYPE': 'mock'})
    def test_get_default_type_from_environment(self):
        """Test getting default repository type from environment."""
        default_type = AgentRepositoryFactory._get_default_type()
        assert default_type == AgentRepositoryType.MOCK
    
    @patch.dict(os.environ, {'MCP_AGENT_REPOSITORY_TYPE': 'invalid'})
    def test_get_default_type_invalid_environment(self):
        """Test fallback when environment has invalid repository type."""
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.logger') as mock_logger:
            default_type = AgentRepositoryFactory._get_default_type()
            
            assert default_type == AgentRepositoryType.ORM
            mock_logger.warning.assert_called_once()
    
    def test_get_default_type_no_environment(self):
        """Test default repository type when no environment variable set."""
        with patch.dict(os.environ, {}, clear=True):
            default_type = AgentRepositoryFactory._get_default_type()
            assert default_type == AgentRepositoryType.ORM
    
    def test_generate_cache_key(self):
        """Test cache key generation."""
        cache_key = AgentRepositoryFactory._generate_cache_key(
            AgentRepositoryType.ORM,
            "user-123",
            "/path/to/db"
        )
        
        assert cache_key == "agent:orm:user-123:/path/to/db"
        
        # Test with None db_path
        cache_key_default = AgentRepositoryFactory._generate_cache_key(
            AgentRepositoryType.ORM,
            "user-123",
            None
        )
        
        assert cache_key_default == "agent:orm:user-123:default"
    
    def test_create_instance_orm_type(self):
        """Test creating ORM repository instance."""
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository') as mock_orm:
            mock_instance = Mock(spec=AgentRepository)
            mock_orm.return_value = mock_instance
            
            result = AgentRepositoryFactory._create_instance(
                AgentRepositoryType.ORM,
                "user-123",
                None
            )
            
            assert result == mock_instance
            mock_orm.assert_called_once_with(user_id="user-123")
    
    def test_create_instance_unsupported_type(self):
        """Test creating instance with unsupported repository type."""
        # Create a mock enum value that's not in _repository_types
        unsupported_type = Mock()
        unsupported_type.value = "unsupported"
        
        with pytest.raises(ValueError) as exc_info:
            AgentRepositoryFactory._create_instance(
                unsupported_type,
                "user-123",
                None
            )
        
        assert "Unsupported agent repository type" in str(exc_info.value)
    
    def test_create_instance_with_fallback(self):
        """Test fallback to ORM when repository creation fails."""
        # Mock a repository type that will fail
        mock_failing_repo = Mock()
        mock_failing_repo.side_effect = Exception("Creation failed")
        
        AgentRepositoryFactory._repository_types[AgentRepositoryType.MOCK] = mock_failing_repo
        
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository') as mock_orm:
            mock_instance = Mock(spec=AgentRepository)
            mock_orm.return_value = mock_instance
            
            result = AgentRepositoryFactory._create_instance(
                AgentRepositoryType.MOCK,
                "user-123",
                None
            )
            
            assert result == mock_instance
            mock_orm.assert_called_once_with(user_id="user-123")
    
    def test_create_instance_orm_fallback_fails(self):
        """Test when both primary and ORM fallback fail."""
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository') as mock_orm:
            mock_orm.side_effect = Exception("ORM creation failed")
            
            with pytest.raises(Exception) as exc_info:
                AgentRepositoryFactory._create_instance(
                    AgentRepositoryType.ORM,
                    "user-123",
                    None
                )
            
            assert "ORM creation failed" in str(exc_info.value)
    
    def test_register_type(self):
        """Test registering new repository type."""
        mock_repo_class = Mock()
        new_type = Mock()
        new_type.value = "custom"
        
        AgentRepositoryFactory.register_type(new_type, mock_repo_class)
        
        assert AgentRepositoryFactory._repository_types[new_type] == mock_repo_class
    
    def test_clear_cache(self):
        """Test clearing repository cache."""
        # Create some cached repositories
        with patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository'):
            AgentRepositoryFactory.create(user_id="user1")
            AgentRepositoryFactory.create(user_id="user2")
            
            assert len(AgentRepositoryFactory._instances) == 2
            
            AgentRepositoryFactory.clear_cache()
            
            assert len(AgentRepositoryFactory._instances) == 0
    
    def test_get_info(self):
        """Test getting factory information."""
        info = AgentRepositoryFactory.get_info()
        
        assert "available_types" in info
        assert "cached_instances" in info
        assert "default_type" in info
        assert "environment" in info
        
        assert isinstance(info["available_types"], list)
        assert isinstance(info["cached_instances"], int)
        assert info["default_type"] in ["orm", "in_memory", "mock"]


class TestAgentRepositoryConfig:
    """Test cases for AgentRepositoryConfig."""
    
    def test_config_initialization_default(self):
        """Test config initialization with default values."""
        config = AgentRepositoryConfig()
        
        assert config.repository_type == AgentRepositoryType.ORM
        assert config.user_id is None
        assert config.db_path is None
        assert config.kwargs == {}
    
    def test_config_initialization_custom(self):
        """Test config initialization with custom values."""
        config = AgentRepositoryConfig(
            repository_type="mock",
            user_id="test-user",
            db_path="/custom/path",
            custom_param="value"
        )
        
        assert config.repository_type == AgentRepositoryType.MOCK
        assert config.user_id == "test-user"
        assert config.db_path == "/custom/path"
        assert config.kwargs == {"custom_param": "value"}
    
    def test_config_validate_type_invalid(self):
        """Test config validation with invalid repository type."""
        config = AgentRepositoryConfig(repository_type="invalid")
        
        assert config.repository_type == AgentRepositoryType.ORM
    
    def test_config_create_repository(self):
        """Test creating repository from config."""
        config = AgentRepositoryConfig(
            repository_type="orm",
            user_id="test-user"
        )
        
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=AgentRepository)
            mock_create.return_value = mock_repository
            
            result = config.create_repository()
            
            assert result == mock_repository
            mock_create.assert_called_once_with(
                repository_type=AgentRepositoryType.ORM,
                user_id="test-user",
                db_path=None
            )
    
    @patch.dict(os.environ, {
        'MCP_AGENT_REPOSITORY_TYPE': 'mock',
        'MCP_USER_ID': 'env-user',
        'MCP_DB_PATH': '/env/path'
    })
    def test_config_from_environment(self):
        """Test creating config from environment variables."""
        config = AgentRepositoryConfig.from_environment()
        
        assert config.repository_type == AgentRepositoryType.MOCK
        assert config.user_id == "env-user"
        assert config.db_path == "/env/path"


class TestGlobalAgentRepositoryManager:
    """Test cases for GlobalAgentRepositoryManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        GlobalAgentRepositoryManager.clear_all()
    
    def teardown_method(self):
        """Clean up after each test."""
        GlobalAgentRepositoryManager.clear_all()
    
    def test_get_default(self):
        """Test getting default repository."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=AgentRepository)
            mock_create.return_value = mock_repository
            
            result = GlobalAgentRepositoryManager.get_default()
            
            assert result == mock_repository
            mock_create.assert_called_once_with()
    
    def test_get_default_cached(self):
        """Test that default repository is cached."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=AgentRepository)
            mock_create.return_value = mock_repository
            
            result1 = GlobalAgentRepositoryManager.get_default()
            result2 = GlobalAgentRepositoryManager.get_default()
            
            assert result1 is result2
            mock_create.assert_called_once()
    
    def test_get_for_user(self):
        """Test getting repository for specific user."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=AgentRepository)
            mock_create.return_value = mock_repository
            
            result = GlobalAgentRepositoryManager.get_for_user("user-123")
            
            assert result == mock_repository
            mock_create.assert_called_once_with(user_id="user-123")
    
    def test_get_for_user_cached(self):
        """Test that user repositories are cached."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=AgentRepository)
            mock_create.return_value = mock_repository
            
            result1 = GlobalAgentRepositoryManager.get_for_user("user-123")
            result2 = GlobalAgentRepositoryManager.get_for_user("user-123")
            
            assert result1 is result2
            mock_create.assert_called_once()
    
    def test_get_for_different_users(self):
        """Test getting repositories for different users."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_create.side_effect = lambda **kwargs: Mock(spec=AgentRepository)
            
            result1 = GlobalAgentRepositoryManager.get_for_user("user1")
            result2 = GlobalAgentRepositoryManager.get_for_user("user2")
            
            assert result1 is not result2
            assert mock_create.call_count == 2
    
    def test_clear_all(self):
        """Test clearing all managed repositories."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_create.return_value = Mock(spec=AgentRepository)
            
            # Create some repositories
            GlobalAgentRepositoryManager.get_default()
            GlobalAgentRepositoryManager.get_for_user("user1")
            
            GlobalAgentRepositoryManager.clear_all()
            
            assert GlobalAgentRepositoryManager._default_repository is None
            assert len(GlobalAgentRepositoryManager._user_repositories) == 0
    
    def test_get_status(self):
        """Test getting manager status."""
        status = GlobalAgentRepositoryManager.get_status()
        
        assert "default_repository" in status
        assert "user_repositories" in status
        assert "cached_users" in status
        assert "factory_info" in status


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def test_create_agent_repository(self):
        """Test create_agent_repository convenience function."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=AgentRepository)
            mock_create.return_value = mock_repository
            
            result = create_agent_repository(
                user_id="user-123",
                repository_type="orm"
            )
            
            assert result == mock_repository
            mock_create.assert_called_once_with(
                repository_type=AgentRepositoryType.ORM,
                user_id="user-123"
            )
    
    def test_get_sqlite_agent_repository(self):
        """Test get_sqlite_agent_repository convenience function."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ORMAgentRepository)
            mock_create.return_value = mock_repository
            
            result = get_sqlite_agent_repository(user_id="user-123")
            
            assert result == mock_repository
            mock_create.assert_called_once_with(
                repository_type=AgentRepositoryType.ORM,
                user_id="user-123"
            )
    
    def test_get_orm_agent_repository(self):
        """Test get_orm_agent_repository convenience function."""
        with patch.object(AgentRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ORMAgentRepository)
            mock_create.return_value = mock_repository
            
            result = get_orm_agent_repository(
                user_id="user-123",
                project_id="project-456"
            )
            
            assert result == mock_repository
            mock_create.assert_called_once_with(
                repository_type=AgentRepositoryType.ORM,
                user_id="user-123",
                project_id="project-456"
            )
    
    def test_get_default_agent_repository(self):
        """Test get_default_agent_repository convenience function."""
        with patch.object(GlobalAgentRepositoryManager, 'get_default') as mock_get_default:
            mock_repository = Mock(spec=AgentRepository)
            mock_get_default.return_value = mock_repository
            
            result = get_default_agent_repository()
            
            assert result == mock_repository
            mock_get_default.assert_called_once()
    
    def test_get_user_agent_repository(self):
        """Test get_user_agent_repository convenience function."""
        with patch.object(GlobalAgentRepositoryManager, 'get_for_user') as mock_get_for_user:
            mock_repository = Mock(spec=AgentRepository)
            mock_get_for_user.return_value = mock_repository
            
            result = get_user_agent_repository("user-123")
            
            assert result == mock_repository
            mock_get_for_user.assert_called_once_with("user-123")
    
    def test_create_agent_repository_factory(self):
        """Test create_agent_repository_factory convenience function."""
        result = create_agent_repository_factory()
        
        assert isinstance(result, AgentRepositoryFactory)


class TestAgentRepositoryFactoryIntegration:
    """Test suite for integration scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        AgentRepositoryFactory.clear_cache()
        GlobalAgentRepositoryManager.clear_all()
        yield
        AgentRepositoryFactory.clear_cache()
        GlobalAgentRepositoryManager.clear_all()
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AuthConfig')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.validate_user_id')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository')
    def test_end_to_end_repository_creation(self, mock_orm_class, mock_validate_user, mock_auth_config):
        """Test complete repository creation workflow"""
        # Setup mocks
        mock_validate_user.return_value = "integration_user"
        mock_repo = Mock()
        mock_orm_class.return_value = mock_repo
        
        # Create repository through factory
        repository = AgentRepositoryFactory.create(
            repository_type=AgentRepositoryType.ORM,
            user_id="integration_user"
        )
        
        # Verify repository was created correctly
        assert repository == mock_repo
        mock_validate_user.assert_called_once_with("integration_user", "Agent repository creation")
        mock_orm_class.assert_called_once_with(user_id="integration_user")
        
        # Verify caching works
        repository2 = AgentRepositoryFactory.create(
            repository_type=AgentRepositoryType.ORM,
            user_id="integration_user"
        )
        assert repository2 == repository
        # ORM class should still be called only once due to caching
        mock_orm_class.assert_called_once()
    
    @patch.dict(os.environ, {
        "MCP_AGENT_REPOSITORY_TYPE": "orm",
        "MCP_USER_ID": "env_integration_user"
    })
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.validate_user_id')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository')
    def test_environment_based_creation(self, mock_orm_class, mock_validate_user):
        """Test repository creation using environment configuration"""
        mock_validate_user.return_value = "env_integration_user"
        mock_repo = Mock()
        mock_orm_class.return_value = mock_repo
        
        # Create config from environment
        config = AgentRepositoryConfig.from_environment()
        
        # Create repository from config
        repository = config.create_repository()
        
        # Verify correct configuration was used
        assert repository == mock_repo
        assert config.repository_type == AgentRepositoryType.ORM
        assert config.user_id == "env_integration_user"
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AgentRepositoryFactory')
    def test_global_manager_integration(self, mock_factory):
        """Test integration with global repository manager"""
        mock_repo1 = Mock()
        mock_repo2 = Mock()
        mock_factory.create.side_effect = [mock_repo1, mock_repo2]
        
        # Get default repository
        default_repo = get_default_agent_repository()
        assert default_repo == mock_repo1
        
        # Get user-specific repository
        user_repo = get_user_agent_repository("specific_user")
        assert user_repo == mock_repo2
        
        # Verify factory calls
        expected_calls = [
            unittest.mock.call(),  # Default repository call
            unittest.mock.call(user_id="specific_user")  # User-specific call
        ]
        mock_factory.create.assert_has_calls(expected_calls)


class TestAgentRepositoryFactoryErrorHandling:
    """Test suite for error handling scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        AgentRepositoryFactory.clear_cache()
        yield
        AgentRepositoryFactory.clear_cache()
    
    def test_invalid_repository_type_creation(self):
        """Test error handling for invalid repository type"""
        invalid_type = Mock()
        invalid_type.value = "nonexistent"
        
        with pytest.raises(ValueError, match="Unsupported agent repository type"):
            AgentRepositoryFactory._create_instance(invalid_type, "test_user", None)
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AuthConfig')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.validate_user_id')
    def test_authentication_validation_error(self, mock_validate_user, mock_auth_config):
        """Test error handling for authentication validation failure"""
        mock_validate_user.side_effect = UserAuthenticationRequiredError("Invalid user")
        
        with pytest.raises(UserAuthenticationRequiredError, match="Invalid user"):
            AgentRepositoryFactory.create(user_id="invalid_user")
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AuthConfig')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.validate_user_id')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository')
    def test_repository_creation_failure_with_fallback(self, mock_orm_class, mock_validate_user, mock_auth_config):
        """Test repository creation failure and fallback mechanism"""
        mock_validate_user.return_value = "test_user"
        
        # First attempt fails, second succeeds (fallback)
        mock_orm_class.side_effect = [Exception("Creation failed"), Mock()]
        
        # Register a custom type that will fail
        custom_type = Mock()
        custom_type.value = "custom"
        failed_class = Mock(side_effect=Exception("Custom creation failed"))
        AgentRepositoryFactory.register_type(custom_type, failed_class)
        
        try:
            repository = AgentRepositoryFactory.create(
                repository_type=custom_type,
                user_id="test_user"
            )
            assert repository is not None
        finally:
            # Clean up
            del AgentRepositoryFactory._repository_types[custom_type]
    
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.AuthConfig')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.validate_user_id')
    @patch('fastmcp.task_management.infrastructure.repositories.agent_repository_factory.ORMAgentRepository')
    def test_orm_fallback_also_fails(self, mock_orm_class, mock_validate_user, mock_auth_config):
        """Test when both primary and fallback repository creation fail"""
        mock_validate_user.return_value = "test_user"
        mock_orm_class.side_effect = Exception("ORM creation failed")
        
        with pytest.raises(Exception, match="ORM creation failed"):
            AgentRepositoryFactory.create(
                repository_type=AgentRepositoryType.ORM,
                user_id="test_user"
            )