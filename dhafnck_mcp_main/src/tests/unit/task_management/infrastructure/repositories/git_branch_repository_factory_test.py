"""
Tests for Git Branch Repository Factory

This module tests the GitBranchRepositoryFactory functionality including:
- Factory pattern implementation for git branch repository creation
- Repository type registration and environment configuration
- Caching mechanisms and instance management
- Fallback strategies and error handling
- Convenience functions and legacy compatibility
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory import (
    GitBranchRepositoryFactory,
    GitBranchRepositoryType,
    get_default_repository,
    get_sqlite_repository,
    get_orm_repository
)
from fastmcp.task_management.domain.repositories.git_branch_repository import GitBranchRepository


class TestGitBranchRepositoryType:
    """Test suite for GitBranchRepositoryType enum"""
    
    def test_enum_values(self):
        """Test enum values are correctly defined"""
        assert GitBranchRepositoryType.JSON.value == "json"
        assert GitBranchRepositoryType.ORM.value == "orm"
        assert GitBranchRepositoryType.MEMORY.value == "memory"
    
    def test_enum_membership(self):
        """Test enum membership checks"""
        assert GitBranchRepositoryType.ORM in GitBranchRepositoryType
        assert GitBranchRepositoryType.JSON in GitBranchRepositoryType
        assert GitBranchRepositoryType.MEMORY in GitBranchRepositoryType


class TestGitBranchRepositoryFactory:
    """Test suite for GitBranchRepositoryFactory"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        # Clear factory cache before each test
        GitBranchRepositoryFactory.clear_cache()
        yield
        # Clear factory cache after each test
        GitBranchRepositoryFactory.clear_cache()
    
    @pytest.fixture
    def mock_orm_repository(self):
        """Create a mock ORM repository"""
        repo = Mock(spec=GitBranchRepository)
        repo.user_id = "test-user"
        return repo
    
    def test_factory_initialization(self):
        """Test factory class initialization and default state"""
        # Test class attributes
        assert isinstance(GitBranchRepositoryFactory._instances, dict)
        assert len(GitBranchRepositoryFactory._instances) == 0
        assert isinstance(GitBranchRepositoryFactory._repository_types, dict)
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_create_orm_repository_success(self, mock_orm_class, mock_orm_repository):
        """Test successful ORM repository creation"""
        mock_orm_class.return_value = mock_orm_repository
        
        repository = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="test_user"
        )
        
        assert repository == mock_orm_repository
        mock_orm_class.assert_called_once_with(user_id="test_user")
    
    def test_create_json_repository_not_implemented(self):
        """Test that JSON repository raises NotImplementedError"""
        with pytest.raises(NotImplementedError, match="JSON repository type not yet implemented"):
            GitBranchRepositoryFactory.create(
                repository_type=GitBranchRepositoryType.JSON,
                user_id="test_user"
            )
    
    def test_create_memory_repository_not_implemented(self):
        """Test that Memory repository raises NotImplementedError"""
        with pytest.raises(NotImplementedError, match="Memory repository type not yet implemented"):
            GitBranchRepositoryFactory.create(
                repository_type=GitBranchRepositoryType.MEMORY,
                user_id="test_user"
            )
    
    def test_create_unsupported_repository_type(self):
        """Test creation with unsupported repository type"""
        unsupported_type = Mock()
        unsupported_type.value = "unsupported"
        
        with pytest.raises(ValueError, match="Unsupported repository type"):
            GitBranchRepositoryFactory.create(
                repository_type=unsupported_type,
                user_id="test_user"
            )
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_create_caching_behavior(self, mock_orm_class, mock_orm_repository):
        """Test repository caching behavior"""
        mock_orm_class.return_value = mock_orm_repository
        
        # Create repository twice with same parameters
        repository1 = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="cache_user"
        )
        repository2 = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="cache_user"
        )
        
        # Should return same instance
        assert repository1 == repository2
        # Repository should be created only once
        mock_orm_class.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_create_different_cache_keys(self, mock_orm_class):
        """Test that different parameters create different cache entries"""
        mock_orm_class.side_effect = lambda **kwargs: Mock(spec=GitBranchRepository)
        
        # Create with different user IDs
        repo1 = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="user1"
        )
        repo2 = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="user2"
        )
        
        # Should be different instances
        assert repo1 is not repo2
        # Should create twice
        assert mock_orm_class.call_count == 2
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.get_db_config')
    def test_get_default_type_with_database_available(self, mock_get_db_config):
        """Test getting default type when database is available"""
        # Mock database config as available
        mock_config = Mock()
        mock_config.engine = Mock()
        mock_get_db_config.return_value = mock_config
        
        default_type = GitBranchRepositoryFactory._get_default_type()
        assert default_type == GitBranchRepositoryType.ORM
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.get_db_config')
    def test_get_default_type_database_unavailable(self, mock_get_db_config):
        """Test getting default type when database is unavailable"""
        # Mock database config as unavailable
        mock_get_db_config.side_effect = Exception("Database unavailable")
        
        with patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.logger') as mock_logger:
            default_type = GitBranchRepositoryFactory._get_default_type()
            assert default_type == GitBranchRepositoryType.MEMORY
            mock_logger.warning.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.get_db_config')
    def test_get_default_type_no_engine(self, mock_get_db_config):
        """Test getting default type when database config has no engine"""
        # Mock database config without engine
        mock_config = Mock()
        mock_config.engine = None
        mock_get_db_config.return_value = mock_config
        
        default_type = GitBranchRepositoryFactory._get_default_type()
        assert default_type == GitBranchRepositoryType.MEMORY
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_create_with_default_type(self, mock_orm_class, mock_orm_repository):
        """Test repository creation with default type"""
        mock_orm_class.return_value = mock_orm_repository
        
        with patch.object(GitBranchRepositoryFactory, '_get_default_type', return_value=GitBranchRepositoryType.ORM):
            repository = GitBranchRepositoryFactory.create(user_id="default_user")
            
            assert repository == mock_orm_repository
            mock_orm_class.assert_called_once_with(user_id="default_user")
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_create_with_kwargs(self, mock_orm_class, mock_orm_repository):
        """Test repository creation with additional kwargs"""
        mock_orm_class.return_value = mock_orm_repository
        
        repository = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="kwargs_user",
            project_id="project123",
            branch_name="feature/test"
        )
        
        assert repository == mock_orm_repository
        mock_orm_class.assert_called_once_with(
            user_id="kwargs_user",
            project_id="project123",
            branch_name="feature/test"
        )
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_create_orm_repository_exception(self, mock_orm_class):
        """Test ORM repository creation with exception"""
        mock_orm_class.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            GitBranchRepositoryFactory.create(
                repository_type=GitBranchRepositoryType.ORM,
                user_id="error_user"
            )
    
    def test_register_type(self):
        """Test registering new repository type"""
        # Create mock type and class
        mock_type = Mock()
        mock_type.value = "custom"
        mock_class = Mock()
        
        # Register type
        GitBranchRepositoryFactory.register_type(mock_type, mock_class)
        
        # Verify registration
        assert mock_type in GitBranchRepositoryFactory._repository_types
        assert GitBranchRepositoryFactory._repository_types[mock_type] == mock_class
        
        # Clean up
        del GitBranchRepositoryFactory._repository_types[mock_type]
    
    def test_clear_cache(self):
        """Test clearing factory cache"""
        # Add some dummy entries to cache
        GitBranchRepositoryFactory._instances["test1"] = Mock()
        GitBranchRepositoryFactory._instances["test2"] = Mock()
        
        # Clear cache
        GitBranchRepositoryFactory.clear_cache()
        
        # Verify cache is empty
        assert len(GitBranchRepositoryFactory._instances) == 0
    
    @patch.dict(os.environ, {"MCP_GIT_BRANCH_REPOSITORY_TYPE": "orm"})
    def test_get_info(self):
        """Test getting factory information"""
        info = GitBranchRepositoryFactory.get_info()
        
        assert "available_types" in info
        assert "cached_instances" in info
        assert "default_type" in info
        assert "environment" in info
        
        assert isinstance(info["available_types"], list)
        assert isinstance(info["cached_instances"], int)
        assert info["environment"]["MCP_GIT_BRANCH_REPOSITORY_TYPE"] == "orm"
    
    def test_get_info_no_environment(self):
        """Test getting factory information without environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            info = GitBranchRepositoryFactory.get_info()
            
            assert info["environment"]["MCP_GIT_BRANCH_REPOSITORY_TYPE"] is None


class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        GitBranchRepositoryFactory.clear_cache()
        yield
        GitBranchRepositoryFactory.clear_cache()
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.GitBranchRepositoryFactory')
    def test_get_default_repository(self, mock_factory):
        """Test get_default_repository convenience function"""
        mock_repo = Mock()
        mock_factory.create.return_value = mock_repo
        
        result = get_default_repository(user_id="default_user")
        
        assert result == mock_repo
        mock_factory.create.assert_called_once_with(user_id="default_user")
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.GitBranchRepositoryFactory')
    def test_get_sqlite_repository(self, mock_factory):
        """Test get_sqlite_repository convenience function"""
        mock_repo = Mock()
        mock_factory.create.return_value = mock_repo
        
        result = get_sqlite_repository(
            user_id="sqlite_user",
            db_path="/test/path"
        )
        
        assert result == mock_repo
        mock_factory.create.assert_called_once_with(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="sqlite_user",
            db_path="/test/path"
        )
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.GitBranchRepositoryFactory')
    def test_get_orm_repository(self, mock_factory):
        """Test get_orm_repository convenience function"""
        mock_repo = Mock()
        mock_factory.create.return_value = mock_repo
        
        result = get_orm_repository(
            user_id="orm_user",
            project_id="project123"
        )
        
        assert result == mock_repo
        mock_factory.create.assert_called_once_with(
            repository_type=GitBranchRepositoryType.ORM,
            user_id="orm_user",
            project_id="project123"
        )


class TestGitBranchRepositoryFactoryIntegration:
    """Test suite for integration scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        GitBranchRepositoryFactory.clear_cache()
        yield
        GitBranchRepositoryFactory.clear_cache()
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.get_db_config')
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_end_to_end_repository_creation(self, mock_orm_class, mock_get_db_config):
        """Test complete repository creation workflow"""
        # Setup database config
        mock_config = Mock()
        mock_config.engine = Mock()
        mock_get_db_config.return_value = mock_config
        
        # Setup repository creation
        mock_repo = Mock()
        mock_orm_class.return_value = mock_repo
        
        # Create repository using factory
        repository = GitBranchRepositoryFactory.create(user_id="integration_user")
        
        # Verify repository was created correctly
        assert repository == mock_repo
        mock_orm_class.assert_called_once_with(user_id="integration_user")
        
        # Verify caching works
        repository2 = GitBranchRepositoryFactory.create(user_id="integration_user")
        assert repository2 == repository
        # ORM class should still be called only once due to caching
        mock_orm_class.assert_called_once()
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.get_db_config')
    def test_fallback_to_memory_when_database_unavailable(self, mock_get_db_config):
        """Test fallback to memory repository when database is unavailable"""
        # Mock database as unavailable
        mock_get_db_config.side_effect = Exception("Database connection failed")
        
        # Attempt to create repository with default type
        with pytest.raises(NotImplementedError, match="Memory repository type not yet implemented"):
            GitBranchRepositoryFactory.create(user_id="fallback_user")
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.MockGitBranchRepository')
    def test_memory_repository_registration(self, mock_memory_class):
        """Test that memory repository is properly registered"""
        # Verify memory repository is registered
        assert GitBranchRepositoryType.MEMORY in GitBranchRepositoryFactory._repository_types
        memory_class = GitBranchRepositoryFactory._repository_types[GitBranchRepositoryType.MEMORY]
        
        # Should be MockGitBranchRepository
        from fastmcp.task_management.infrastructure.repositories.mock_repository_factory import MockGitBranchRepository
        assert memory_class == MockGitBranchRepository


class TestGitBranchRepositoryFactoryErrorHandling:
    """Test suite for error handling scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        GitBranchRepositoryFactory.clear_cache()
        yield
        GitBranchRepositoryFactory.clear_cache()
    
    def test_invalid_repository_type_creation(self):
        """Test error handling for invalid repository type"""
        invalid_type = Mock()
        invalid_type.value = "nonexistent"
        
        with pytest.raises(ValueError, match="Unsupported repository type"):
            GitBranchRepositoryFactory.create(
                repository_type=invalid_type,
                user_id="test_user"
            )
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_orm_repository_creation_failure(self, mock_orm_class):
        """Test ORM repository creation failure"""
        mock_orm_class.side_effect = Exception("ORM creation failed")
        
        with pytest.raises(Exception, match="ORM creation failed"):
            GitBranchRepositoryFactory.create(
                repository_type=GitBranchRepositoryType.ORM,
                user_id="test_user"
            )
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.get_db_config')
    def test_database_config_import_error(self, mock_get_db_config):
        """Test handling of database config import errors"""
        mock_get_db_config.side_effect = ImportError("Database module not available")
        
        with patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.logger') as mock_logger:
            default_type = GitBranchRepositoryFactory._get_default_type()
            assert default_type == GitBranchRepositoryType.MEMORY
            mock_logger.warning.assert_called_once()
    
    def test_cache_key_generation_with_none_user(self):
        """Test cache key generation with None user ID"""
        cache_key_1 = f"{GitBranchRepositoryType.ORM.value}_None"
        cache_key_2 = f"{GitBranchRepositoryType.ORM.value}_None"
        
        # Cache keys should be consistent
        assert cache_key_1 == cache_key_2
    
    @patch('fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory.ORMGitBranchRepository')
    def test_repository_creation_with_none_user(self, mock_orm_class):
        """Test repository creation with None user ID"""
        mock_repo = Mock()
        mock_orm_class.return_value = mock_repo
        
        repository = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.ORM,
            user_id=None
        )
        
        assert repository == mock_repo
        mock_orm_class.assert_called_once_with(user_id=None)


class TestGitBranchRepositoryFactoryRegistration:
    """Test suite for repository type registration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        GitBranchRepositoryFactory.clear_cache()
        yield
        GitBranchRepositoryFactory.clear_cache()
    
    def test_default_repository_types_registered(self):
        """Test that default repository types are registered"""
        # Check that memory repository is registered
        assert GitBranchRepositoryType.MEMORY in GitBranchRepositoryFactory._repository_types
        
        # Check that ORM repository is registered if available
        try:
            from fastmcp.task_management.infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
            assert GitBranchRepositoryType.ORM in GitBranchRepositoryFactory._repository_types
        except ImportError:
            # ORM repository may not be available in test environment
            pass
    
    def test_custom_repository_registration(self):
        """Test registering custom repository type"""
        # Create custom type and class
        custom_type = Mock()
        custom_type.value = "custom_test"
        custom_class = Mock()
        
        # Register custom type
        GitBranchRepositoryFactory.register_type(custom_type, custom_class)
        
        try:
            # Verify registration
            assert custom_type in GitBranchRepositoryFactory._repository_types
            assert GitBranchRepositoryFactory._repository_types[custom_type] == custom_class
        finally:
            # Clean up
            if custom_type in GitBranchRepositoryFactory._repository_types:
                del GitBranchRepositoryFactory._repository_types[custom_type]
    
    def test_overriding_existing_repository_type(self):
        """Test overriding existing repository type"""
        # Create new implementation for memory type
        new_memory_class = Mock()
        
        # Store original class
        original_class = GitBranchRepositoryFactory._repository_types.get(GitBranchRepositoryType.MEMORY)
        
        try:
            # Override memory repository
            GitBranchRepositoryFactory.register_type(GitBranchRepositoryType.MEMORY, new_memory_class)
            
            # Verify override
            assert GitBranchRepositoryFactory._repository_types[GitBranchRepositoryType.MEMORY] == new_memory_class
        finally:
            # Restore original class
            if original_class:
                GitBranchRepositoryFactory._repository_types[GitBranchRepositoryType.MEMORY] = original_class