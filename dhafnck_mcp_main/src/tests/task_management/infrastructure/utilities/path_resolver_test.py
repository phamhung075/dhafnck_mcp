"""
Test suite for PathResolver utility.

Tests the path resolution functionality including project root detection,
dynamic path resolution, and directory management operations.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

from fastmcp.task_management.infrastructure.utilities.path_resolver import (
    PathResolver,
    find_project_root,
    ensure_project_structure
)


class TestFindProjectRoot:
    """Test suite for find_project_root function."""

    def test_find_project_root_with_git(self, tmp_path):
        """Test finding project root with .git directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        result = find_project_root(tmp_path)
        
        assert result == tmp_path

    def test_find_project_root_with_pyproject_toml(self, tmp_path):
        """Test finding project root with pyproject.toml."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.touch()
        
        result = find_project_root(tmp_path)
        
        assert result == tmp_path

    def test_find_project_root_with_setup_py(self, tmp_path):
        """Test finding project root with setup.py."""
        setup_file = tmp_path / "setup.py"
        setup_file.touch()
        
        result = find_project_root(tmp_path)
        
        assert result == tmp_path

    def test_find_project_root_with_package_json(self, tmp_path):
        """Test finding project root with package.json."""
        package_file = tmp_path / "package.json"
        package_file.touch()
        
        result = find_project_root(tmp_path)
        
        assert result == tmp_path

    def test_find_project_root_traverses_up(self, tmp_path):
        """Test that find_project_root traverses up directory tree."""
        # Create nested directory structure
        nested_dir = tmp_path / "deep" / "nested" / "directory"
        nested_dir.mkdir(parents=True)
        
        # Put marker in parent directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        result = find_project_root(nested_dir)
        
        assert result == tmp_path

    def test_find_project_root_no_markers(self):
        """Test find_project_root with no markers (returns cwd)."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path('/mock/cwd')
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                result = find_project_root(tmp_dir)
                
                # Should return cwd when no markers found
                assert result == Path('/mock/cwd')

    def test_find_project_root_no_start_path(self):
        """Test find_project_root with no start path (uses cwd)."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path('/mock/cwd')
            
            result = find_project_root()
            
            # Should use cwd as start path
            assert str(result) == '/mock/cwd'


class TestEnsureProjectStructure:
    """Test suite for ensure_project_structure function."""

    def test_ensure_project_structure_creates_directories(self, tmp_path):
        """Test that ensure_project_structure creates required directories."""
        result = ensure_project_structure(tmp_path)
        
        expected_path = tmp_path / ".cursor" / "rules"
        assert result == expected_path
        assert expected_path.exists()
        assert expected_path.is_dir()

    def test_ensure_project_structure_existing_directories(self, tmp_path):
        """Test ensure_project_structure with existing directories."""
        # Pre-create directories
        cursor_dir = tmp_path / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True)
        
        result = ensure_project_structure(tmp_path)
        
        assert result == cursor_dir
        assert cursor_dir.exists()


class TestPathResolver:
    """Test suite for PathResolver class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_project_root = Path("/test/project")

    @patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root')
    @patch('fastmcp.task_management.infrastructure.utilities.path_resolver.ensure_project_structure')
    def test_initialization(self, mock_ensure_structure, mock_find_root):
        """Test PathResolver initialization."""
        mock_find_root.return_value = self.test_project_root
        mock_cursor_dir = self.test_project_root / ".cursor" / "rules"
        mock_ensure_structure.return_value = mock_cursor_dir
        
        with patch.object(PathResolver, 'ensure_brain_dir'), \
             patch.object(PathResolver, '_ensure_projects_file'):
            
            resolver = PathResolver()
            
            assert resolver.project_root == self.test_project_root
            assert resolver.cursor_rules_dir == mock_cursor_dir
            mock_find_root.assert_called_once()
            mock_ensure_structure.assert_called_once_with(self.test_project_root)

    def test_resolve_path_absolute(self):
        """Test _resolve_path with absolute path."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                absolute_path = "/absolute/path"
                
                result = resolver._resolve_path(absolute_path)
                
                assert result == Path(absolute_path)

    def test_resolve_path_relative(self):
        """Test _resolve_path with relative path."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                relative_path = "relative/path"
                
                result = resolver._resolve_path(relative_path)
                
                assert result == self.test_project_root / relative_path

    @patch('os.makedirs')
    def test_ensure_brain_dir(self, mock_makedirs):
        """Test ensure_brain_dir method."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, '_ensure_projects_file'):
                resolver = PathResolver()
                resolver.brain_dir = Path("/test/brain/dir")
                
                resolver.ensure_brain_dir()
                
                mock_makedirs.assert_called_with(Path("/test/brain/dir"), exist_ok=True)

    def test_ensure_projects_file_creates_new(self):
        """Test _ensure_projects_file creates new file."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'):
                # Mock projects file that doesn't exist
                mock_projects_file = Mock()
                mock_projects_file.exists.return_value = False
                mock_projects_file.parent.mkdir = Mock()
                
                mock_file = mock_open()
                
                with patch('builtins.open', mock_file), \
                     patch('json.dump') as mock_json_dump:
                    
                    resolver = PathResolver()
                    resolver.projects_file = mock_projects_file
                    resolver._ensure_projects_file()
                    
                    mock_projects_file.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                    mock_file.assert_called_once()
                    mock_json_dump.assert_called_once()

    def test_ensure_projects_file_exists(self):
        """Test _ensure_projects_file when file already exists."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'):
                # Mock projects file that exists
                mock_projects_file = Mock()
                mock_projects_file.exists.return_value = True
                
                resolver = PathResolver()
                resolver.projects_file = mock_projects_file
                resolver._ensure_projects_file()
                
                # Should not try to create file
                mock_projects_file.parent.mkdir.assert_not_called()

    def test_ensure_projects_file_permission_error_fallback(self):
        """Test _ensure_projects_file handles permission errors with fallback."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'):
                # Mock projects file that doesn't exist
                mock_projects_file = Mock()
                mock_projects_file.exists.return_value = False
                mock_projects_file.parent.mkdir.side_effect = PermissionError("Permission denied")
                
                # Mock fallback file
                mock_fallback_file = Mock()
                mock_fallback_file.parent.mkdir = Mock()
                
                mock_file = mock_open()
                
                with patch('builtins.open', mock_file), \
                     patch('json.dump') as mock_json_dump, \
                     patch.object(Path, '__truediv__', return_value=mock_fallback_file):
                    
                    resolver = PathResolver()
                    resolver.projects_file = mock_projects_file
                    resolver._ensure_projects_file()
                    
                    # Should use fallback file
                    assert resolver.projects_file == mock_fallback_file
                    mock_fallback_file.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_tasks_json_path_hierarchical(self):
        """Test get_tasks_json_path with hierarchical structure."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                
                project_id = "test_project"
                git_branch_name = "feature/test"
                user_id = "test_user"
                
                with patch.object(Path, 'mkdir') as mock_mkdir:
                    result = resolver.get_tasks_json_path(project_id, git_branch_name, user_id)
                    
                    expected_path = self.test_project_root / ".cursor/rules/tasks/test_user/test_project/feature/test/tasks.json"
                    assert str(result) == str(expected_path)
                    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_tasks_json_path_legacy(self):
        """Test get_tasks_json_path with legacy fallback."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                
                with patch.object(Path, 'mkdir') as mock_mkdir:
                    result = resolver.get_tasks_json_path(project_id=None)
                    
                    expected_path = self.test_project_root / ".cursor/rules/tasks/tasks.json"
                    assert str(result) == str(expected_path)
                    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_legacy_tasks_json_path(self):
        """Test get_legacy_tasks_json_path method."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                
                result = resolver.get_legacy_tasks_json_path()
                
                expected_path = self.test_project_root / ".cursor/rules/tasks/tasks.json"
                assert result == expected_path

    def test_get_auto_rule_path(self):
        """Test get_auto_rule_path method."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                
                result = resolver.get_auto_rule_path()
                
                expected_path = self.test_project_root / ".cursor/rules/auto_rule.mdc"
                assert result == expected_path

    def test_get_auto_rule_path_with_env_var(self):
        """Test get_auto_rule_path with environment variable override."""
        with patch.dict(os.environ, {'AUTO_RULE_PATH': '/custom/auto_rule.mdc'}):
            with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
                mock_find_root.return_value = self.test_project_root
                
                with patch.object(PathResolver, 'ensure_brain_dir'), \
                     patch.object(PathResolver, '_ensure_projects_file'):
                    
                    resolver = PathResolver()
                    
                    result = resolver.get_auto_rule_path()
                    
                    assert result == Path('/custom/auto_rule.mdc')

    @patch('fastmcp.task_management.infrastructure.utilities.path_resolver.logger')
    def test_get_rules_directory_from_settings_exception_handling(self, mock_logger):
        """Test get_rules_directory_from_settings exception handling."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                
                # Mock import error
                with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.get_rules_directory', side_effect=ImportError("Module not found")):
                    # Should still work with fallback import
                    with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.get_rules_directory', return_value=Path("/fallback")):
                        result = resolver.get_rules_directory_from_settings()
                        
                        assert result == Path("/fallback")
                        mock_logger.warning.assert_called()

    def test_get_cursor_agent_dir_project_specific(self):
        """Test get_cursor_agent_dir with project-specific directory."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                
                project_agent_library = self.test_project_root / "agent-library"
                
                with patch.object(Path, 'exists', return_value=True):
                    result = resolver.get_cursor_agent_dir()
                    
                    assert str(result) == str(project_agent_library)

    def test_get_cursor_agent_dir_environment_variable(self):
        """Test get_cursor_agent_dir with environment variable."""
        with patch.dict(os.environ, {'AGENT_LIBRARY_DIR_PATH': '/env/agent/library'}):
            with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
                mock_find_root.return_value = self.test_project_root
                
                with patch.object(PathResolver, 'ensure_brain_dir'), \
                     patch.object(PathResolver, '_ensure_projects_file'):
                    
                    resolver = PathResolver()
                    
                    with patch.object(Path, 'exists', return_value=False):
                        result = resolver.get_cursor_agent_dir()
                        
                        assert result == Path('/env/agent/library')

    def test_get_cursor_agent_dir_fallback(self):
        """Test get_cursor_agent_dir with fallback path."""
        with patch('fastmcp.task_management.infrastructure.utilities.path_resolver.find_project_root') as mock_find_root:
            mock_find_root.return_value = self.test_project_root
            
            with patch.object(PathResolver, 'ensure_brain_dir'), \
                 patch.object(PathResolver, '_ensure_projects_file'):
                
                resolver = PathResolver()
                
                with patch.object(Path, 'exists', return_value=False), \
                     patch.dict(os.environ, {}, clear=True):
                    
                    result = resolver.get_cursor_agent_dir()
                    
                    expected_path = self.test_project_root / "dhafnck_mcp_main/agent-library"
                    assert str(result) == str(expected_path)