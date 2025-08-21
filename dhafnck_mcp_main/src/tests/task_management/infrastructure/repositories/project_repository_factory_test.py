"""Test suite for ProjectRepositoryFactory.

Tests the project repository factory including:
- Repository creation with authentication
- Type detection and fallbacks
- Database availability checks
- Caching mechanisms
- Error handling and recovery
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from fastmcp.task_management.infrastructure.repositories.project_repository_factory import (
    ProjectRepositoryFactory,
    RepositoryType,
    RepositoryConfig,
    GlobalRepositoryManager,
    create_project_repository,
    get_sqlite_repository,
    get_default_repository,
    get_user_repository
)
from fastmcp.task_management.domain.repositories.project_repository import ProjectRepository
from fastmcp.task_management.infrastructure.repositories.orm.project_repository import ORMProjectRepository
from fastmcp.task_management.infrastructure.repositories.mock_repository_factory import MockProjectRepository
from fastmcp.task_management.domain.exceptions.authentication_exceptions import (
    UserAuthenticationRequiredError,
    DefaultUserProhibitedError
)


class TestProjectRepositoryFactory:
    """Test cases for ProjectRepositoryFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear factory cache before each test
        ProjectRepositoryFactory.clear_cache()
        GlobalRepositoryManager.clear_all()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clear factory cache after each test
        ProjectRepositoryFactory.clear_cache()
        GlobalRepositoryManager.clear_all()
    
    def test_repository_type_enum(self):
        """Test RepositoryType enum values."""
        assert RepositoryType.ORM.value == "orm"
        assert RepositoryType.IN_MEMORY.value == "in_memory"
        assert RepositoryType.MOCK.value == "mock"
        
        # Test enum iteration
        types = list(RepositoryType)
        assert len(types) >= 3
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.validate_user_id')
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.AuthConfig')
    def test_create_repository_success(self, mock_auth_config, mock_validate):
        """Test successful repository creation with valid user."""
        mock_validate.return_value = "test-user-123"
        mock_auth_config.is_default_user_allowed.return_value = False
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            mock_instance = Mock(spec=ProjectRepository)
            mock_orm.return_value = mock_instance
            
            result = ProjectRepositoryFactory.create(
                repository_type=RepositoryType.ORM,
                user_id="test-user-123"
            )
            
            assert result == mock_instance
            mock_validate.assert_called_once_with("test-user-123", "Project repository creation")
            mock_orm.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.AuthConfig')
    def test_create_repository_compatibility_mode(self, mock_auth_config):
        """Test repository creation in compatibility mode."""
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "fallback-user"
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            mock_instance = Mock(spec=ProjectRepository)
            mock_orm.return_value = mock_instance
            
            result = ProjectRepositoryFactory.create(user_id=None)
            
            assert result == mock_instance
            mock_auth_config.is_default_user_allowed.assert_called_once()
            mock_auth_config.get_fallback_user_id.assert_called_once()
            mock_auth_config.log_authentication_bypass.assert_called_once_with(
                "Project repository creation", "compatibility mode"
            )
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.AuthConfig')
    @patch('os.getenv')
    def test_create_repository_no_user_id_no_compatibility(self, mock_getenv, mock_auth_config):
        """Test repository creation without user ID when compatibility is disabled."""
        mock_auth_config.is_default_user_allowed.return_value = False
        mock_getenv.return_value = 'production'  # Not in development
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            ProjectRepositoryFactory.create(user_id=None)
        
        assert "Project repository creation" in str(exc_info.value)
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.AuthConfig')
    @patch('os.getenv')
    def test_create_repository_dev_environment_temporary_fix(self, mock_getenv, mock_auth_config):
        """Test temporary development environment fix for git branch authentication."""
        mock_auth_config.is_default_user_allowed.return_value = False
        mock_auth_config.log_authentication_bypass = Mock()
        
        # Test with different development environment values
        dev_environments = ['development', 'dev', '']  # Empty string for local dev
        
        for env_value in dev_environments:
            mock_getenv.return_value = env_value
            
            with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
                mock_instance = Mock(spec=ProjectRepository)
                mock_orm.return_value = mock_instance
                
                # Should use compatibility-default-user even when compatibility mode is disabled
                result = ProjectRepositoryFactory.create(user_id=None)
                
                assert result == mock_instance
                mock_auth_config.log_authentication_bypass.assert_called_with(
                    "Project repository creation", 
                    "forced compatibility mode for git branch fix"
                )
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.logger')
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.AuthConfig')
    @patch('os.getenv')
    def test_create_repository_dev_environment_logs_warning(self, mock_getenv, mock_auth_config, mock_logger):
        """Test that temporary dev fix logs appropriate warning."""
        mock_auth_config.is_default_user_allowed.return_value = False
        mock_getenv.return_value = 'development'
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository'):
            ProjectRepositoryFactory.create(user_id=None)
            
            # Should log warning about temporary fix
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if "TEMPORARY FIX" in str(call)]
            assert len(warning_calls) > 0
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.validate_user_id')
    def test_create_repository_prohibited_user_id(self, mock_validate):
        """Test repository creation with prohibited user ID."""
        mock_validate.side_effect = DefaultUserProhibitedError()
        
        with pytest.raises(DefaultUserProhibitedError):
            ProjectRepositoryFactory.create(user_id="default_id")
    
    def test_create_repository_caching(self):
        """Test that repositories are cached properly."""
        user_id = "test-user-123"
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            mock_instance = Mock(spec=ProjectRepository)
            mock_orm.return_value = mock_instance
            
            # Create repository twice
            result1 = ProjectRepositoryFactory.create(
                repository_type=RepositoryType.ORM,
                user_id=user_id
            )
            result2 = ProjectRepositoryFactory.create(
                repository_type=RepositoryType.ORM,
                user_id=user_id
            )
            
            # Should return same instance
            assert result1 is result2
            # Should only create once
            mock_orm.assert_called_once()
    
    def test_create_repository_different_users(self):
        """Test that different users get different repository instances."""
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            mock_orm.side_effect = lambda **kwargs: Mock(spec=ProjectRepository)
            
            # Create with different user IDs
            result1 = ProjectRepositoryFactory.create(user_id="user1")
            result2 = ProjectRepositoryFactory.create(user_id="user2")
            
            # Should be different instances
            assert result1 is not result2
            # Should create twice
            assert mock_orm.call_count == 2
    
    def test_create_repository_fallback_to_mock(self):
        """Test fallback to mock repository when ORM creation fails."""
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            mock_orm.side_effect = Exception("Database connection failed")
            
            with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.MockProjectRepository') as mock_mock:
                mock_instance = Mock(spec=ProjectRepository)
                mock_mock.return_value = mock_instance
                
                result = ProjectRepositoryFactory.create(
                    repository_type=RepositoryType.ORM,
                    user_id="user-123"
                )
                
                # Should fallback to mock
                assert result == mock_instance
                mock_mock.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.get_db_config')
    def test_get_default_type_database_available(self, mock_get_db_config):
        """Test default type selection when database is available."""
        mock_db_config = Mock()
        mock_db_config.engine = Mock()
        mock_get_db_config.return_value = mock_db_config
        
        default_type = ProjectRepositoryFactory._get_default_type()
        
        assert default_type == RepositoryType.ORM
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.get_db_config')
    def test_get_default_type_database_unavailable(self, mock_get_db_config):
        """Test default type selection when database is unavailable."""
        mock_get_db_config.side_effect = Exception("Database not available")
        
        default_type = ProjectRepositoryFactory._get_default_type()
        
        assert default_type == RepositoryType.MOCK
    
    @patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.get_db_config')
    def test_get_default_type_no_engine(self, mock_get_db_config):
        """Test default type selection when database config has no engine."""
        mock_db_config = Mock()
        mock_db_config.engine = None
        mock_get_db_config.return_value = mock_db_config
        
        default_type = ProjectRepositoryFactory._get_default_type()
        
        assert default_type == RepositoryType.MOCK
    
    def test_generate_cache_key(self):
        """Test cache key generation."""
        cache_key = ProjectRepositoryFactory._generate_cache_key(
            RepositoryType.ORM,
            "user-123",
            "/path/to/db"
        )
        
        assert cache_key == "orm:user-123:/path/to/db"
        
        # Test with None db_path
        cache_key_default = ProjectRepositoryFactory._generate_cache_key(
            RepositoryType.ORM,
            "user-123",
            None
        )
        
        assert cache_key_default == "orm:user-123:default"
    
    def test_generate_cache_key_enum_compatibility(self):
        """Test cache key generation with different enum formats."""
        # Test with mock enum that has value attribute
        mock_enum = Mock()
        mock_enum.value = "test_type"
        
        cache_key = ProjectRepositoryFactory._generate_cache_key(
            mock_enum,
            "user-123",
            None
        )
        
        assert cache_key == "test_type:user-123:default"
        
        # Test with object that doesn't have value attribute
        mock_object = "string_type"
        
        cache_key = ProjectRepositoryFactory._generate_cache_key(
            mock_object,
            "user-123",
            None
        )
        
        assert cache_key == "string_type:user-123:default"
    
    def test_create_instance_orm_type(self):
        """Test creating ORM repository instance."""
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            mock_instance = Mock(spec=ProjectRepository)
            mock_orm.return_value = mock_instance
            
            result = ProjectRepositoryFactory._create_instance(
                RepositoryType.ORM,
                "user-123",
                None
            )
            
            assert result == mock_instance
            mock_orm.assert_called_once()
    
    def test_create_instance_orm_with_db_path(self):
        """Test creating ORM repository with custom database path."""
        custom_db_path = "/custom/db/path"
        
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.close_db') as mock_close_db:
                with patch.dict(os.environ, {}, clear=True):
                    mock_instance = Mock(spec=ProjectRepository)
                    mock_orm.return_value = mock_instance
                    
                    result = ProjectRepositoryFactory._create_instance(
                        RepositoryType.ORM,
                        "user-123",
                        custom_db_path
                    )
                    
                    assert result == mock_instance
                    assert os.environ.get('MCP_DB_PATH') != custom_db_path  # Should be restored
                    mock_close_db.assert_called_once()
    
    def test_create_instance_mock_type(self):
        """Test creating mock repository instance."""
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.MockProjectRepository') as mock_mock:
            mock_instance = Mock(spec=ProjectRepository)
            mock_mock.return_value = mock_instance
            
            result = ProjectRepositoryFactory._create_instance(
                RepositoryType.MOCK,
                "user-123",
                None
            )
            
            assert result == mock_instance
            mock_mock.assert_called_once()
    
    def test_create_instance_unsupported_type(self):
        """Test creating instance with unsupported repository type."""
        unsupported_type = Mock()
        unsupported_type.value = "unsupported"
        
        with pytest.raises(ValueError) as exc_info:
            ProjectRepositoryFactory._create_instance(
                unsupported_type,
                "user-123",
                None
            )
        
        assert "Unsupported repository type" in str(exc_info.value)
    
    def test_create_instance_orm_fallback_to_mock(self):
        """Test fallback to mock when ORM creation fails."""
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.ORMProjectRepository') as mock_orm:
            mock_orm.side_effect = Exception("ORM creation failed")
            
            with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.MockProjectRepository') as mock_mock:
                mock_instance = Mock(spec=ProjectRepository)
                mock_mock.return_value = mock_instance
                
                result = ProjectRepositoryFactory._create_instance(
                    RepositoryType.ORM,
                    "user-123",
                    None
                )
                
                assert result == mock_instance
                mock_mock.assert_called_once()
    
    def test_register_type(self):
        """Test registering new repository type."""
        mock_repo_class = Mock()
        
        ProjectRepositoryFactory.register_type(RepositoryType.IN_MEMORY, mock_repo_class)
        
        assert ProjectRepositoryFactory._repository_types[RepositoryType.IN_MEMORY] == mock_repo_class
    
    def test_clear_cache(self):
        """Test clearing repository cache."""
        # Create some cached repositories
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.MockProjectRepository'):
            ProjectRepositoryFactory.create(user_id="user1")
            ProjectRepositoryFactory.create(user_id="user2")
            
            assert len(ProjectRepositoryFactory._instances) == 2
            
            ProjectRepositoryFactory.clear_cache()
            
            assert len(ProjectRepositoryFactory._instances) == 0
    
    def test_get_info(self):
        """Test getting factory information."""
        info = ProjectRepositoryFactory.get_info()
        
        assert "available_types" in info
        assert "cached_instances" in info
        assert "default_type" in info
        assert "environment" in info
        
        assert isinstance(info["available_types"], list)
        assert isinstance(info["cached_instances"], int)
        assert info["default_type"] in ["orm", "mock"]


class TestRepositoryConfig:
    """Test cases for RepositoryConfig."""
    
    def test_config_initialization_default(self):
        """Test config initialization with default values."""
        config = RepositoryConfig()
        
        assert config.repository_type == RepositoryType.ORM
        assert config.user_id is None
        assert config.db_path is None
        assert config.kwargs == {}
    
    def test_config_initialization_custom(self):
        """Test config initialization with custom values."""
        config = RepositoryConfig(
            repository_type="mock",
            user_id="test-user",
            db_path="/custom/path",
            custom_param="value"
        )
        
        assert config.repository_type == RepositoryType.MOCK
        assert config.user_id == "test-user"
        assert config.db_path == "/custom/path"
        assert config.kwargs == {"custom_param": "value"}
    
    def test_config_validate_type_invalid(self):
        """Test config validation with invalid repository type."""
        with patch('fastmcp.task_management.infrastructure.repositories.project_repository_factory.logger') as mock_logger:
            config = RepositoryConfig(repository_type="invalid")
            
            assert config.repository_type == RepositoryType.ORM
            mock_logger.warning.assert_called_once()
    
    def test_config_create_repository(self):
        """Test creating repository from config."""
        config = RepositoryConfig(
            repository_type="orm",
            user_id="test-user"
        )
        
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ProjectRepository)
            mock_create.return_value = mock_repository
            
            result = config.create_repository()
            
            assert result == mock_repository
            mock_create.assert_called_once_with(
                repository_type=RepositoryType.ORM,
                user_id="test-user",
                db_path=None
            )
    
    @patch.dict(os.environ, {
        'MCP_PROJECT_REPOSITORY_TYPE': 'mock',
        'MCP_USER_ID': 'env-user',
        'MCP_DB_PATH': '/env/path'
    })
    def test_config_from_environment(self):
        """Test creating config from environment variables."""
        config = RepositoryConfig.from_environment()
        
        assert config.repository_type == RepositoryType.MOCK
        assert config.user_id == "env-user"
        assert config.db_path == "/env/path"


class TestGlobalRepositoryManager:
    """Test cases for GlobalRepositoryManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        GlobalRepositoryManager.clear_all()
    
    def teardown_method(self):
        """Clean up after each test."""
        GlobalRepositoryManager.clear_all()
    
    def test_get_default(self):
        """Test getting default repository."""
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ProjectRepository)
            mock_create.return_value = mock_repository
            
            result = GlobalRepositoryManager.get_default()
            
            assert result == mock_repository
            mock_create.assert_called_once_with()
    
    def test_get_default_cached(self):
        """Test that default repository is cached."""
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ProjectRepository)
            mock_create.return_value = mock_repository
            
            result1 = GlobalRepositoryManager.get_default()
            result2 = GlobalRepositoryManager.get_default()
            
            assert result1 is result2
            mock_create.assert_called_once()
    
    def test_get_for_user(self):
        """Test getting repository for specific user."""
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ProjectRepository)
            mock_create.return_value = mock_repository
            
            result = GlobalRepositoryManager.get_for_user("user-123")
            
            assert result == mock_repository
            mock_create.assert_called_once_with(user_id="user-123")
    
    def test_get_for_user_cached(self):
        """Test that user repositories are cached."""
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ProjectRepository)
            mock_create.return_value = mock_repository
            
            result1 = GlobalRepositoryManager.get_for_user("user-123")
            result2 = GlobalRepositoryManager.get_for_user("user-123")
            
            assert result1 is result2
            mock_create.assert_called_once()
    
    def test_clear_all(self):
        """Test clearing all managed repositories."""
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_create.return_value = Mock(spec=ProjectRepository)
            
            # Create some repositories
            GlobalRepositoryManager.get_default()
            GlobalRepositoryManager.get_for_user("user1")
            
            GlobalRepositoryManager.clear_all()
            
            assert GlobalRepositoryManager._default_repository is None
            assert len(GlobalRepositoryManager._user_repositories) == 0
    
    def test_get_status(self):
        """Test getting manager status."""
        status = GlobalRepositoryManager.get_status()
        
        assert "has_default" in status
        assert "user_count" in status
        assert "factory_info" in status


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def test_create_project_repository(self):
        """Test create_project_repository convenience function."""
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ProjectRepository)
            mock_create.return_value = mock_repository
            
            result = create_project_repository(
                user_id="user-123",
                repository_type="orm"
            )
            
            assert result == mock_repository
            mock_create.assert_called_once_with(
                repository_type=RepositoryType.ORM,
                user_id="user-123",
                db_path=None
            )
    
    def test_get_sqlite_repository(self):
        """Test get_sqlite_repository convenience function."""
        with patch.object(ProjectRepositoryFactory, 'create') as mock_create:
            mock_repository = Mock(spec=ORMProjectRepository)
            mock_create.return_value = mock_repository
            
            result = get_sqlite_repository(user_id="user-123")
            
            assert result == mock_repository
            mock_create.assert_called_once_with(
                repository_type=RepositoryType.ORM,
                user_id="user-123",
                db_path=None
            )
    
    def test_get_default_repository(self):
        """Test get_default_repository convenience function."""
        with patch.object(GlobalRepositoryManager, 'get_default') as mock_get_default:
            mock_repository = Mock(spec=ProjectRepository)
            mock_get_default.return_value = mock_repository
            
            result = get_default_repository()
            
            assert result == mock_repository
            mock_get_default.assert_called_once()
    
    def test_get_user_repository(self):
        """Test get_user_repository convenience function."""
        with patch.object(GlobalRepositoryManager, 'get_for_user') as mock_get_for_user:
            mock_repository = Mock(spec=ProjectRepository)
            mock_get_for_user.return_value = mock_repository
            
            result = get_user_repository("user-123")
            
            assert result == mock_repository
            mock_get_for_user.assert_called_once_with("user-123")