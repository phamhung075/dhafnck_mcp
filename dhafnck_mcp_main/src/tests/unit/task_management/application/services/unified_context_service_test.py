"""
Tests for UnifiedContextService

Tests the complete unified context service functionality including CRUD operations,
user scoping, hierarchy validation, and service integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from fastmcp.task_management.application.services.unified_context_service import UnifiedContextService
from fastmcp.task_management.domain.value_objects.context_enums import ContextLevel
from fastmcp.task_management.infrastructure.database.models import GLOBAL_SINGLETON_UUID


class TestUnifiedContextService:
    """Test suite for UnifiedContextService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_global_repo = Mock()
        self.mock_project_repo = Mock()
        self.mock_branch_repo = Mock()
        self.mock_task_repo = Mock()
        self.mock_cache_service = Mock()
        self.mock_inheritance_service = Mock()
        self.mock_delegation_service = Mock()
        self.mock_validation_service = Mock()
        self.user_id = "test-user-123"
        
        self.service = UnifiedContextService(
            global_context_repository=self.mock_global_repo,
            project_context_repository=self.mock_project_repo,
            branch_context_repository=self.mock_branch_repo,
            task_context_repository=self.mock_task_repo,
            cache_service=self.mock_cache_service,
            inheritance_service=self.mock_inheritance_service,
            delegation_service=self.mock_delegation_service,
            validation_service=self.mock_validation_service,
            user_id=self.user_id
        )

    def test_initialization_with_all_services(self):
        """Test service initialization with all provided services"""
        # Assert
        assert self.service._user_id == self.user_id
        assert self.service.repositories[ContextLevel.GLOBAL] == self.mock_global_repo
        assert self.service.repositories[ContextLevel.PROJECT] == self.mock_project_repo
        assert self.service.repositories[ContextLevel.BRANCH] == self.mock_branch_repo
        assert self.service.repositories[ContextLevel.TASK] == self.mock_task_repo
        assert self.service.cache_service == self.mock_cache_service
        assert self.service.inheritance_service == self.mock_inheritance_service
        assert self.service.delegation_service == self.mock_delegation_service
        assert self.service.validation_service == self.mock_validation_service

    def test_initialization_with_default_services(self):
        """Test service initialization creates default services when not provided"""
        # Act
        service = UnifiedContextService(
            global_context_repository=self.mock_global_repo,
            project_context_repository=self.mock_project_repo,
            branch_context_repository=self.mock_branch_repo,
            task_context_repository=self.mock_task_repo
        )
        
        # Assert
        assert service.cache_service is not None
        assert service.inheritance_service is not None
        assert service.delegation_service is not None
        assert service.validation_service is not None
        assert service.hierarchy_validator is not None

    def test_with_user_creates_scoped_service(self):
        """Test with_user creates a new service instance with user-scoped repositories"""
        # Arrange
        new_user_id = "new-user-456"
        
        # Mock repository with_user methods
        mock_scoped_global = Mock()
        mock_scoped_project = Mock()
        mock_scoped_branch = Mock()
        mock_scoped_task = Mock()
        
        self.mock_global_repo.with_user = Mock(return_value=mock_scoped_global)
        self.mock_project_repo.with_user = Mock(return_value=mock_scoped_project)
        self.mock_branch_repo.with_user = Mock(return_value=mock_scoped_branch)
        self.mock_task_repo.with_user = Mock(return_value=mock_scoped_task)
        
        # Act
        scoped_service = self.service.with_user(new_user_id)
        
        # Assert
        assert scoped_service._user_id == new_user_id
        assert scoped_service != self.service
        self.mock_global_repo.with_user.assert_called_once_with(new_user_id)
        self.mock_project_repo.with_user.assert_called_once_with(new_user_id)
        self.mock_branch_repo.with_user.assert_called_once_with(new_user_id)
        self.mock_task_repo.with_user.assert_called_once_with(new_user_id)

    def test_get_user_scoped_repository_with_user_method(self):
        """Test _get_user_scoped_repository when repository has with_user method"""
        # Arrange
        mock_repo = Mock()
        mock_scoped_repo = Mock()
        mock_repo.with_user = Mock(return_value=mock_scoped_repo)
        
        # Act
        result = self.service._get_user_scoped_repository(mock_repo)
        
        # Assert
        assert result == mock_scoped_repo
        mock_repo.with_user.assert_called_once_with(self.user_id)

    def test_get_user_scoped_repository_without_user_method(self):
        """Test _get_user_scoped_repository when repository doesn't have with_user method"""
        # Arrange
        mock_repo = Mock()
        del mock_repo.with_user  # Ensure with_user doesn't exist
        
        # Act
        result = self.service._get_user_scoped_repository(mock_repo)
        
        # Assert
        assert result == mock_repo

    def test_get_user_scoped_repository_without_user_id(self):
        """Test _get_user_scoped_repository when service has no user_id"""
        # Arrange
        service_no_user = UnifiedContextService(
            global_context_repository=self.mock_global_repo,
            project_context_repository=self.mock_project_repo,
            branch_context_repository=self.mock_branch_repo,
            task_context_repository=self.mock_task_repo,
            user_id=None
        )
        mock_repo = Mock()
        mock_repo.with_user = Mock()
        
        # Act
        result = service_no_user._get_user_scoped_repository(mock_repo)
        
        # Assert
        assert result == mock_repo
        mock_repo.with_user.assert_not_called()

    def test_create_context_global_level(self):
        """Test creating a global context"""
        # Arrange
        context_id = GLOBAL_SINGLETON_UUID
        data = {"autonomous_rules": {}}
        
        mock_context = Mock()
        self.mock_global_repo.create.return_value = mock_context
        self.mock_validation_service.validate_context_data.return_value = (True, None)
        
        # Act
        result = self.service.create_context("global", context_id, data)
        
        # Assert
        assert result["success"] is True
        assert result["context"] == mock_context
        self.mock_validation_service.validate_context_data.assert_called_once()
        self.mock_global_repo.create.assert_called_once()

    def test_create_context_with_validation_failure(self):
        """Test creating context with validation failure"""
        # Arrange
        context_id = "test-context"
        data = {"invalid": "data"}
        
        validation_error = "Invalid context data"
        self.mock_validation_service.validate_context_data.return_value = (False, validation_error)
        
        # Act
        result = self.service.create_context("project", context_id, data)
        
        # Assert
        assert result["success"] is False
        assert validation_error in result["error"]

    def test_create_context_with_hierarchy_validation_failure(self):
        """Test creating context with hierarchy validation failure"""
        # Arrange
        context_id = "test-project"
        data = {}
        
        self.mock_validation_service.validate_context_data.return_value = (True, None)
        
        # Mock hierarchy validator to fail
        with patch.object(self.service.hierarchy_validator, 'validate_hierarchy_requirements') as mock_validate:
            mock_validate.return_value = (False, "Global context required", {"error": "Global context missing"})
            
            # Act
            result = self.service.create_context("project", context_id, data)
            
            # Assert
            assert result["success"] is False
            assert "Global context required" in result["error"]
            assert result["guidance"]["error"] == "Global context missing"

    def test_get_context_from_cache(self):
        """Test getting context from cache"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        cached_context = {"id": context_id, "data": {"cached": True}}
        
        cache_key = f"{level}:{context_id}"
        self.mock_cache_service.get.return_value = cached_context
        
        # Act
        result = self.service.get_context(level, context_id)
        
        # Assert
        assert result["success"] is True
        assert result["context"] == cached_context
        assert result["from_cache"] is True
        self.mock_cache_service.get.assert_called_once_with(cache_key)

    def test_get_context_from_repository_when_not_cached(self):
        """Test getting context from repository when not in cache"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        mock_context = Mock()
        
        self.mock_cache_service.get.return_value = None
        self.mock_task_repo.get.return_value = mock_context
        
        # Act
        result = self.service.get_context(level, context_id)
        
        # Assert
        assert result["success"] is True
        assert result["context"] == mock_context
        assert result.get("from_cache", False) is False
        self.mock_task_repo.get.assert_called_once_with(context_id)
        self.mock_cache_service.set.assert_called_once()

    def test_get_context_with_inheritance(self):
        """Test getting context with inheritance enabled"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        mock_context = Mock()
        inherited_data = {"inherited": "data"}
        
        self.mock_cache_service.get.return_value = None
        self.mock_task_repo.get.return_value = mock_context
        self.mock_inheritance_service.get_inherited_context.return_value = inherited_data
        
        # Act
        result = self.service.get_context(level, context_id, include_inherited=True)
        
        # Assert
        assert result["success"] is True
        assert result["context"] == mock_context
        assert result["inherited_context"] == inherited_data
        self.mock_inheritance_service.get_inherited_context.assert_called_once()

    def test_get_context_not_found(self):
        """Test getting context that doesn't exist"""
        # Arrange
        level = "task"
        context_id = "nonexistent-task"
        
        self.mock_cache_service.get.return_value = None
        self.mock_task_repo.get.return_value = None
        
        # Act
        result = self.service.get_context(level, context_id)
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_update_context_success(self):
        """Test successful context update"""
        # Arrange
        level = "project"
        context_id = "test-project-123"
        update_data = {"updated": True}
        updated_context = Mock()
        
        self.mock_project_repo.update.return_value = updated_context
        self.mock_validation_service.validate_context_data.return_value = (True, None)
        
        # Act
        result = self.service.update_context(level, context_id, update_data)
        
        # Assert
        assert result["success"] is True
        assert result["context"] == updated_context
        self.mock_project_repo.update.assert_called_once_with(context_id, update_data)
        self.mock_cache_service.invalidate.assert_called_once()

    def test_update_context_with_propagation(self):
        """Test context update with change propagation"""
        # Arrange
        level = "branch"
        context_id = "test-branch-123"
        update_data = {"propagate": True}
        updated_context = Mock()
        
        self.mock_branch_repo.update.return_value = updated_context
        self.mock_validation_service.validate_context_data.return_value = (True, None)
        
        # Act
        result = self.service.update_context(level, context_id, update_data, propagate_changes=True)
        
        # Assert
        assert result["success"] is True
        # Verify propagation was called (implementation specific)
        # This would depend on how propagation is implemented

    def test_delete_context_success(self):
        """Test successful context deletion"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        
        self.mock_task_repo.delete.return_value = True
        
        # Act
        result = self.service.delete_context(level, context_id)
        
        # Assert
        assert result["success"] is True
        self.mock_task_repo.delete.assert_called_once_with(context_id)
        self.mock_cache_service.invalidate.assert_called_once()

    def test_delete_context_not_found(self):
        """Test deleting context that doesn't exist"""
        # Arrange
        level = "task"
        context_id = "nonexistent-task"
        
        self.mock_task_repo.delete.return_value = False
        
        # Act
        result = self.service.delete_context(level, context_id)
        
        # Assert
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_resolve_context_with_full_inheritance(self):
        """Test resolving context with full inheritance chain"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        mock_context = Mock()
        full_resolved_data = {"resolved": "data", "inheritance_chain": []}
        
        self.mock_cache_service.get.return_value = None
        self.mock_task_repo.get.return_value = mock_context
        self.mock_inheritance_service.resolve_full_context.return_value = full_resolved_data
        
        # Act
        result = self.service.resolve_context(level, context_id)
        
        # Assert
        assert result["success"] is True
        assert result["resolved_context"] == full_resolved_data
        self.mock_inheritance_service.resolve_full_context.assert_called_once()

    def test_delegate_context_success(self):
        """Test successful context delegation"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        delegate_to = "project"
        delegate_data = {"pattern": "reusable_pattern"}
        delegation_reason = "Reusable across project"
        
        delegation_result = {"delegated": True, "target_id": "delegated-id"}
        self.mock_delegation_service.delegate.return_value = delegation_result
        
        # Act
        result = self.service.delegate_context(
            level, context_id, delegate_to, delegate_data, delegation_reason
        )
        
        # Assert
        assert result["success"] is True
        assert result["delegation_result"] == delegation_result
        self.mock_delegation_service.delegate.assert_called_once_with(
            level, context_id, delegate_to, delegate_data, delegation_reason
        )

    def test_add_insight_success(self):
        """Test successfully adding insight to context"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        content = "Important discovery about optimization"
        category = "performance"
        importance = "high"
        agent = "test-agent"
        
        updated_context = Mock()
        self.mock_task_repo.add_insight = Mock(return_value=updated_context)
        
        # Act
        result = self.service.add_insight(level, context_id, content, category, importance, agent)
        
        # Assert
        assert result["success"] is True
        assert result["context"] == updated_context
        self.mock_task_repo.add_insight.assert_called_once_with(
            context_id, content, category, importance, agent
        )

    def test_add_progress_success(self):
        """Test successfully adding progress update"""
        # Arrange
        level = "branch"
        context_id = "test-branch-123"
        content = "Completed authentication module"
        agent = "coding-agent"
        
        updated_context = Mock()
        self.mock_branch_repo.add_progress = Mock(return_value=updated_context)
        
        # Act
        result = self.service.add_progress(level, context_id, content, agent)
        
        # Assert
        assert result["success"] is True
        assert result["context"] == updated_context
        self.mock_branch_repo.add_progress.assert_called_once_with(
            context_id, content, agent
        )

    def test_list_contexts_success(self):
        """Test successfully listing contexts"""
        # Arrange
        level = "project"
        filters = {"status": "active"}
        mock_contexts = [Mock(), Mock()]
        
        self.mock_project_repo.list.return_value = mock_contexts
        
        # Act
        result = self.service.list_contexts(level, filters)
        
        # Assert
        assert result["success"] is True
        assert result["contexts"] == mock_contexts
        assert result["count"] == len(mock_contexts)
        self.mock_project_repo.list.assert_called_once_with(filters)

    def test_context_level_enum_conversion(self):
        """Test that string context levels are properly converted to ContextLevel enum"""
        # Test that the service properly handles string level parameters
        # This tests the internal conversion logic
        
        # Arrange
        string_levels = ["global", "project", "branch", "task"]
        
        for level_str in string_levels:
            # The service should handle string levels by converting to enum
            level_enum = ContextLevel(level_str.upper())
            assert level_enum in self.service.repositories

    def test_exception_handling_in_operations(self):
        """Test proper exception handling in service operations"""
        # Arrange
        level = "task"
        context_id = "test-task-123"
        
        # Mock repository to raise exception
        self.mock_task_repo.get.side_effect = Exception("Database error")
        
        # Act
        result = self.service.get_context(level, context_id)
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Database error" in result["error"]


# Integration and user scoping tests
class TestUnifiedContextServiceUserScoping:
    """Test user scoping functionality"""

    def setup_method(self):
        """Set up test fixtures for user scoping tests"""
        self.mock_repos = {
            'global': Mock(),
            'project': Mock(),
            'branch': Mock(),
            'task': Mock()
        }
        
        # Set up with_user methods on repositories
        for repo in self.mock_repos.values():
            repo.with_user = Mock(return_value=Mock())

    def test_service_with_user_preserves_services(self):
        """Test that with_user preserves other services"""
        # Arrange
        original_cache = Mock()
        original_inheritance = Mock()
        original_delegation = Mock()
        original_validation = Mock()
        
        service = UnifiedContextService(
            global_context_repository=self.mock_repos['global'],
            project_context_repository=self.mock_repos['project'],
            branch_context_repository=self.mock_repos['branch'],
            task_context_repository=self.mock_repos['task'],
            cache_service=original_cache,
            inheritance_service=original_inheritance,
            delegation_service=original_delegation,
            validation_service=original_validation
        )
        
        # Act
        scoped_service = service.with_user("test-user")
        
        # Assert
        assert scoped_service.cache_service == original_cache
        assert scoped_service.inheritance_service == original_inheritance
        assert scoped_service.delegation_service == original_delegation
        assert scoped_service.validation_service == original_validation

    def test_get_user_scoped_repository_for_user(self):
        """Test getting user-scoped repository for specific user"""
        # Arrange
        service = UnifiedContextService(
            global_context_repository=self.mock_repos['global'],
            project_context_repository=self.mock_repos['project'],
            branch_context_repository=self.mock_repos['branch'],
            task_context_repository=self.mock_repos['task']
        )
        
        user_id = "specific-user-123"
        mock_scoped_repo = Mock()
        self.mock_repos['global'].with_user.return_value = mock_scoped_repo
        
        # Act
        result = service._get_user_scoped_repository_for_user(
            self.mock_repos['global'], user_id
        )
        
        # Assert
        assert result == mock_scoped_repo
        self.mock_repos['global'].with_user.assert_called_once_with(user_id)

    def test_repository_without_with_user_method(self):
        """Test handling repositories that don't support user scoping"""
        # Arrange
        service = UnifiedContextService(
            global_context_repository=self.mock_repos['global'],
            project_context_repository=self.mock_repos['project'],
            branch_context_repository=self.mock_repos['branch'],
            task_context_repository=self.mock_repos['task']
        )
        
        repo_without_scoping = Mock()
        del repo_without_scoping.with_user  # Remove with_user method
        
        # Act
        result = service._get_user_scoped_repository_for_user(repo_without_scoping, "user-123")
        
        # Assert
        assert result == repo_without_scoping


# Error handling and edge cases
class TestUnifiedContextServiceErrorHandling:
    """Test error handling and edge cases"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_repos = Mock()
        self.service = UnifiedContextService(
            global_context_repository=Mock(),
            project_context_repository=Mock(),
            branch_context_repository=Mock(),
            task_context_repository=Mock()
        )

    def test_invalid_context_level(self):
        """Test handling of invalid context level"""
        # Act & Assert
        with pytest.raises(ValueError):
            self.service.get_context("invalid_level", "context-id")

    def test_none_context_id(self):
        """Test handling of None context ID"""
        # Act
        result = self.service.get_context("task", None)
        
        # Assert
        assert result["success"] is False
        assert "Context ID is required" in result["error"]

    def test_empty_context_id(self):
        """Test handling of empty context ID"""
        # Act
        result = self.service.get_context("task", "")
        
        # Assert
        assert result["success"] is False
        assert "Context ID is required" in result["error"]

    def test_repository_method_not_available(self):
        """Test handling when repository method is not available"""
        # Arrange
        mock_repo = Mock()
        del mock_repo.add_insight  # Remove method
        self.service.repositories[ContextLevel.TASK] = mock_repo
        
        # Act
        result = self.service.add_insight("task", "task-123", "insight")
        
        # Assert
        assert result["success"] is False
        assert "not supported" in result["error"] or "error" in result