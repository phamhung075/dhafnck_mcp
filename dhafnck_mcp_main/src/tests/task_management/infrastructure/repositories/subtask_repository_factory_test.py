"""
Test cases for Subtask Repository Factory.

This module tests the SubtaskRepositoryFactory which creates repository instances
with proper user scoping and database backend selection.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os

from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import (
    SubtaskRepositoryFactory,
    _find_project_root
)
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.infrastructure.repositories.mock_repository_factory import MockSubtaskRepository


class TestFindProjectRoot:
    """Test cases for the _find_project_root helper function."""
    
    def test_find_project_root_from_current_directory(self):
        """Test finding project root when dhafnck_mcp_main exists in parent directories."""
        with patch('pathlib.Path.resolve') as mock_resolve:
            with patch('pathlib.Path.exists') as mock_exists:
                # Mock the path hierarchy
                test_path = Path("/home/user/project/dhafnck_mcp_main/src/repositories")
                parent_path = Path("/home/user/project")
                
                mock_resolve.return_value = test_path
                # Configure exists to return True for project root
                mock_exists.side_effect = lambda: self.name == "dhafnck_mcp_main"
                
                with patch('pathlib.Path.__new__') as mock_path_new:
                    # Mock path traversal
                    mock_path_new.side_effect = [
                        test_path,
                        test_path.parent,
                        test_path.parent.parent,
                        parent_path
                    ]
                    
                    # Mock parent attribute
                    test_path.parent = test_path.parent
                    parent_path.parent = parent_path  # Stop condition
                    
                    with patch.object(Path, '__truediv__', return_value=Mock(exists=Mock(return_value=True))):
                        result = _find_project_root()
                        assert isinstance(result, Path)
    
    def test_find_project_root_from_cwd(self):
        """Test finding project root from current working directory."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            with patch('pathlib.Path.exists') as mock_exists:
                cwd_path = Path("/home/user/project")
                mock_cwd.return_value = cwd_path
                
                # First check (walking up) fails, second check (cwd) succeeds
                mock_exists.side_effect = [False, False, True]
                
                with patch('pathlib.Path.resolve') as mock_resolve:
                    mock_resolve.return_value = Path("/some/other/path")
                    
                    result = _find_project_root()
                    assert result == cwd_path
    
    def test_find_project_root_fallback_to_data_path(self):
        """Test fallback to environment variable data path."""
        with patch('os.environ.get') as mock_env_get:
            with patch('os.path.exists') as mock_exists:
                with patch('pathlib.Path.exists', return_value=False):
                    mock_env_get.return_value = '/custom/data/path'
                    mock_exists.return_value = True
                    
                    result = _find_project_root()
                    assert result == Path('/custom/data/path')
    
    def test_find_project_root_fallback_to_tmp(self):
        """Test final fallback to tmp directory."""
        with patch('os.environ.get', return_value='/nonexistent'):
            with patch('os.path.exists', return_value=False):
                with patch('pathlib.Path.exists', return_value=False):
                    result = _find_project_root()
                    assert result == Path('/tmp/dhafnck_project')


class TestSubtaskRepositoryFactory:
    """Test cases for SubtaskRepositoryFactory class."""
    
    @pytest.fixture
    def factory(self):
        """Create a factory instance for testing."""
        with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory._find_project_root') as mock_find:
            mock_find.return_value = Path('/test/project')
            return SubtaskRepositoryFactory(default_user_id="default-user")
    
    def test_factory_initialization(self):
        """Test factory initialization with custom parameters."""
        project_root = Path('/custom/project')
        base_path = '/custom/base/path'
        
        factory = SubtaskRepositoryFactory(
            base_path=base_path,
            default_user_id="custom-user",
            project_root=project_root
        )
        
        assert factory.project_root == project_root
        assert factory.base_path == base_path
        assert factory.default_user_id == "custom-user"
    
    def test_factory_initialization_defaults(self):
        """Test factory initialization with default values."""
        with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory._find_project_root') as mock_find:
            mock_project_root = Path('/found/project')
            mock_find.return_value = mock_project_root
            
            factory = SubtaskRepositoryFactory()
            
            assert factory.project_root == mock_project_root
            assert factory.base_path == str(mock_project_root / ".cursor" / "rules" / "subtasks")
            assert factory.default_user_id is None
    
    def test_static_create_method(self):
        """Test the static create method."""
        with patch.object(SubtaskRepositoryFactory, 'create_subtask_repository') as mock_create:
            mock_repo = Mock()
            mock_create.return_value = mock_repo
            
            result = SubtaskRepositoryFactory.create(
                project_id="test-project",
                git_branch_name="feature-branch",
                user_id="test-user"
            )
            
            assert result == mock_repo
            mock_create.assert_called_once_with("test-project", "feature-branch", "test-user")
    
    def test_create_subtask_repository_with_orm(self, factory):
        """Test creating ORM repository when database is available."""
        mock_db_config = Mock()
        mock_db_config.engine = Mock()  # Has engine, so DB is available
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config') as mock_get_config:
            mock_get_config.return_value = mock_db_config
            
            with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.ORMSubtaskRepository') as mock_orm:
                mock_orm_instance = Mock()
                mock_orm.return_value = mock_orm_instance
                
                result = factory.create_subtask_repository(
                    project_id="test-project",
                    git_branch_name="main",
                    user_id="test-user"
                )
                
                assert result == mock_orm_instance
                mock_orm.assert_called_once_with(user_id="test-user")
    
    def test_create_subtask_repository_fallback_to_mock(self, factory):
        """Test fallback to mock repository when database is not available."""
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config') as mock_get_config:
            mock_get_config.side_effect = Exception("Database not available")
            
            with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.MockSubtaskRepository') as mock_mock:
                mock_mock_instance = Mock()
                mock_mock.return_value = mock_mock_instance
                
                result = factory.create_subtask_repository(
                    project_id="test-project",
                    git_branch_name="main",
                    user_id="test-user"
                )
                
                assert result == mock_mock_instance
                mock_mock.assert_called_once_with()
    
    def test_create_subtask_repository_no_project_id(self, factory):
        """Test error when project_id is not provided."""
        with pytest.raises(ValueError, match="project_id is required"):
            factory.create_subtask_repository(
                project_id=None,
                git_branch_name="main",
                user_id="test-user"
            )
    
    def test_create_subtask_repository_default_values(self, factory):
        """Test default values for git_branch_name and user_id."""
        mock_db_config = Mock()
        mock_db_config.engine = Mock()
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config') as mock_get_config:
            mock_get_config.return_value = mock_db_config
            
            with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.ORMSubtaskRepository') as mock_orm:
                # Test with no git_branch_name
                factory.create_subtask_repository(
                    project_id="test-project",
                    git_branch_name=None,
                    user_id="test-user"
                )
                mock_orm.assert_called_with(user_id="test-user")
                
                # Test with no user_id (uses default)
                factory.create_subtask_repository(
                    project_id="test-project",
                    git_branch_name="main",
                    user_id=None
                )
                mock_orm.assert_called_with(user_id="default-user")
    
    def test_create_sqlite_subtask_repository(self, factory):
        """Test create_sqlite_subtask_repository method (legacy compatibility)."""
        mock_db_config = Mock()
        mock_db_config.engine = Mock()
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config') as mock_get_config:
            mock_get_config.return_value = mock_db_config
            
            with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.ORMSubtaskRepository') as mock_orm:
                mock_orm_instance = Mock()
                mock_orm.return_value = mock_orm_instance
                
                result = factory.create_sqlite_subtask_repository(
                    project_id="test-project",
                    git_branch_name="main",
                    user_id="test-user",
                    db_path="/custom/db/path"  # This parameter is ignored for ORM
                )
                
                assert result == mock_orm_instance
                mock_orm.assert_called_once_with(user_id="test-user")
    
    def test_create_orm_subtask_repository(self, factory):
        """Test create_orm_subtask_repository method."""
        with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.ORMSubtaskRepository') as mock_orm:
            mock_orm_instance = Mock()
            mock_orm.return_value = mock_orm_instance
            
            # Test with user_id
            result = factory.create_orm_subtask_repository(user_id="test-user")
            assert result == mock_orm_instance
            mock_orm.assert_called_once_with(user_id="test-user")
            
            # Test without user_id (uses default)
            mock_orm.reset_mock()
            result = factory.create_orm_subtask_repository(user_id=None)
            mock_orm.assert_called_once_with(user_id="default-user")
    
    def test_validate_user_project_tree(self, factory):
        """Test validate_user_project_tree method."""
        # Always returns True for ORM repositories
        assert factory.validate_user_project_tree(
            project_id="test-project",
            git_branch_name="main",
            user_id="test-user"
        ) is True
        
        # Test with default user_id
        assert factory.validate_user_project_tree(
            project_id="test-project",
            git_branch_name="main",
            user_id=None
        ) is True
    
    def test_get_subtask_db_path_with_env_variable(self, factory):
        """Test get_subtask_db_path with environment variable."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = "/env/db/path.db"
            
            result = factory.get_subtask_db_path(
                project_id="test-project",
                git_branch_name="main",
                user_id="test-user"
            )
            
            assert result == "/env/db/path.db"
    
    def test_get_subtask_db_path_without_env_variable(self, factory):
        """Test get_subtask_db_path without environment variable."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            result = factory.get_subtask_db_path(
                project_id="test-project",
                git_branch_name="main",
                user_id="test-user"
            )
            
            expected_path = str(factory.project_root / "dhafnck_mcp_main" / "database" / "data" / "dhafnck_mcp.db")
            assert result == expected_path
    
    def test_get_subtask_db_path_with_default_user(self, factory):
        """Test get_subtask_db_path with default user_id."""
        with patch('os.getenv', return_value=None):
            result = factory.get_subtask_db_path(
                project_id="test-project",
                git_branch_name="main",
                user_id=None
            )
            
            # Should still work with default user
            assert "dhafnck_mcp.db" in result


class TestDatabaseAvailabilityHandling:
    """Test cases for database availability scenarios."""
    
    def test_db_config_none(self):
        """Test when get_db_config returns None."""
        factory = SubtaskRepositoryFactory(default_user_id="test-user")
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config') as mock_get_config:
            mock_get_config.return_value = None  # No DB config
            
            with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.MockSubtaskRepository') as mock_mock:
                mock_mock_instance = Mock()
                mock_mock.return_value = mock_mock_instance
                
                result = factory.create_subtask_repository(
                    project_id="test-project",
                    git_branch_name="main",
                    user_id="test-user"
                )
                
                assert result == mock_mock_instance
    
    def test_db_config_no_engine(self):
        """Test when db_config exists but has no engine."""
        factory = SubtaskRepositoryFactory(default_user_id="test-user")
        
        mock_db_config = Mock()
        mock_db_config.engine = None  # No engine
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config') as mock_get_config:
            mock_get_config.return_value = mock_db_config
            
            with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.MockSubtaskRepository') as mock_mock:
                mock_mock_instance = Mock()
                mock_mock.return_value = mock_mock_instance
                
                result = factory.create_subtask_repository(
                    project_id="test-project",
                    git_branch_name="main", 
                    user_id="test-user"
                )
                
                assert result == mock_mock_instance
    
    def test_logging_on_fallback(self):
        """Test that warning is logged when falling back to mock repository."""
        factory = SubtaskRepositoryFactory(default_user_id="test-user")
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_db_config') as mock_get_config:
            mock_get_config.side_effect = RuntimeError("Connection failed")
            
            with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.logger') as mock_logger:
                with patch('fastmcp.task_management.infrastructure.repositories.subtask_repository_factory.MockSubtaskRepository'):
                    factory.create_subtask_repository(
                        project_id="test-project",
                        git_branch_name="main",
                        user_id="test-user"
                    )
                    
                    mock_logger.warning.assert_called_once()
                    warning_message = mock_logger.warning.call_args[0][0]
                    assert "Database not available" in warning_message
                    assert "using mock repository" in warning_message


if __name__ == "__main__":
    pytest.main([__file__])