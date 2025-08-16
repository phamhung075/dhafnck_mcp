"""Unit tests for Unified Context Service"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid
import json

from fastmcp.task_management.application.services.unified_context_service import (
    UnifiedContextService
)


class TestUnifiedContextService:
    """Test suite for UnifiedContextService"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'global_context': Mock(),
            'project_context': Mock(),
            'branch_context': Mock(),
            'task_context': Mock()
        }
    
    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service"""
        cache = Mock()
        cache.get.return_value = None
        cache.set.return_value = None
        cache.invalidate.return_value = None
        return cache
    
    @pytest.fixture
    def mock_delegation_service(self):
        """Create mock delegation service"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_repositories, mock_cache_service, mock_delegation_service):
        """Create service instance with mocks"""
        with patch('fastmcp.task_management.application.services.unified_context_service.logger'):
            service = UnifiedContextService(
                global_repository=mock_repositories['global_context'],
                project_repository=mock_repositories['project_context'],
                branch_repository=mock_repositories['branch_context'],
                task_repository=mock_repositories['task_context']
            )
            service._cache_service = mock_cache_service
            service._delegation_service = mock_delegation_service
            return service
    
    def test_create_global_context(self, service, mock_repositories):
        """Test creating global context"""
        # Arrange
        context_data = {
            'patterns': ['auth_pattern'],
            'guidelines': ['Use JWT']
        }
        mock_repositories['global_context'].save.return_value = Mock(
            id='global_singleton',
            data=context_data
        )
        
        # Act
        result = service.create_context(
            level='global',
            context_id='global_singleton',
            data=context_data
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        mock_repositories['global_context'].save.assert_called_once()
    
    def test_create_project_context(self, service, mock_repositories):
        """Test creating project context"""
        # Arrange
        project_id = str(uuid.uuid4())
        context_data = {
            'project_name': 'Test Project',
            'tech_stack': ['Python', 'FastAPI']
        }
        mock_repositories['project_context'].save.return_value = Mock(
            id=project_id,
            data=context_data
        )
        
        # Act
        result = service.create_context(
            level='project',
            context_id=project_id,
            data=context_data
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        mock_repositories['project_context'].save.assert_called_once()
    
    def test_create_branch_context(self, service, mock_repositories):
        """Test creating branch context"""
        # Arrange
        branch_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        context_data = {
            'branch_name': 'feature/auth',
            'project_id': project_id
        }
        mock_repositories['branch_context'].save.return_value = Mock(
            id=branch_id,
            data=context_data,
            project_id=project_id
        )
        
        # Act
        result = service.create_context(
            level='branch',
            context_id=branch_id,
            data=context_data,
            project_id=project_id
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        mock_repositories['branch_context'].save.assert_called_once()
    
    def test_create_task_context(self, service, mock_repositories):
        """Test creating task context"""
        # Arrange
        task_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        context_data = {
            'task_title': 'Implement login',
            'branch_id': branch_id
        }
        mock_repositories['task_context'].save.return_value = Mock(
            id=task_id,
            data=context_data,
            git_branch_id=branch_id
        )
        
        # Act
        result = service.create_context(
            level='task',
            context_id=task_id,
            data=context_data,
            git_branch_id=branch_id
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        mock_repositories['task_context'].save.assert_called_once()
    
    def test_get_context_with_cache_hit(self, service, mock_cache_service):
        """Test getting context when cache has it"""
        # Arrange
        context_id = str(uuid.uuid4())
        cached_data = {'cached': True, 'data': 'test'}
        mock_cache_service.get.return_value = cached_data
        
        # Act
        result = service.get_context(
            level='task',
            context_id=context_id
        )
        
        # Assert
        assert result == cached_data
        mock_cache_service.get.assert_called_once()
    
    def test_get_context_with_cache_miss(self, service, mock_repositories, mock_cache_service):
        """Test getting context when cache misses"""
        # Arrange
        context_id = str(uuid.uuid4())
        mock_cache_service.get.return_value = None
        
        context = Mock(
            id=context_id,
            data={'fresh': True},
            to_dict=Mock(return_value={'id': context_id, 'data': {'fresh': True}})
        )
        mock_repositories['task_context'].find_by_id.return_value = context
        
        # Act
        result = service.get_context(
            level='task',
            context_id=context_id
        )
        
        # Assert
        assert result is not None
        assert result['id'] == context_id
        mock_cache_service.set.assert_called_once()
    
    def test_update_context(self, service, mock_repositories, mock_cache_service):
        """Test updating context"""
        # Arrange
        context_id = str(uuid.uuid4())
        existing_context = Mock(
            id=context_id,
            data={'old': 'data'},
            update=Mock()
        )
        mock_repositories['task_context'].find_by_id.return_value = existing_context
        mock_repositories['task_context'].save.return_value = existing_context
        
        new_data = {'new': 'data'}
        
        # Act
        result = service.update_context(
            level='task',
            context_id=context_id,
            data=new_data
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        existing_context.update.assert_called_once_with(new_data)
        mock_cache_service.invalidate.assert_called()
    
    def test_delete_context(self, service, mock_repositories, mock_cache_service):
        """Test deleting context"""
        # Arrange
        context_id = str(uuid.uuid4())
        mock_repositories['task_context'].delete.return_value = True
        
        # Act
        result = service.delete_context(
            level='task',
            context_id=context_id
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        mock_repositories['task_context'].delete.assert_called_once_with(context_id)
        mock_cache_service.invalidate.assert_called()
    
    def test_resolve_context_with_inheritance(self, service, mock_repositories):
        """Test resolving context with full inheritance chain"""
        # Arrange
        task_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        
        # Mock task context
        task_context = Mock(
            id=task_id,
            data={'task_data': 'value'},
            git_branch_id=branch_id,
            to_dict=Mock(return_value={
                'id': task_id,
                'data': {'task_data': 'value'},
                'git_branch_id': branch_id
            })
        )
        
        # Mock branch context
        branch_context = Mock(
            id=branch_id,
            data={'branch_data': 'value'},
            project_id=project_id,
            to_dict=Mock(return_value={
                'id': branch_id,
                'data': {'branch_data': 'value'},
                'project_id': project_id
            })
        )
        
        # Mock project context
        project_context = Mock(
            id=project_id,
            data={'project_data': 'value'},
            to_dict=Mock(return_value={
                'id': project_id,
                'data': {'project_data': 'value'}
            })
        )
        
        # Mock global context
        global_context = Mock(
            id='global_singleton',
            data={'global_data': 'value'},
            to_dict=Mock(return_value={
                'id': 'global_singleton',
                'data': {'global_data': 'value'}
            })
        )
        
        mock_repositories['task_context'].find_by_id.return_value = task_context
        mock_repositories['branch_context'].find_by_id.return_value = branch_context
        mock_repositories['project_context'].find_by_id.return_value = project_context
        mock_repositories['global_context'].find_by_id.return_value = global_context
        
        # Act
        result = service.resolve_context(
            level='task',
            context_id=task_id
        )
        
        # Assert
        assert result is not None
        assert 'resolved_data' in result
        assert 'inheritance_chain' in result
        assert len(result['inheritance_chain']) == 4
    
    def test_delegate_context_upward(self, service, mock_delegation_service):
        """Test delegating context to higher level"""
        # Arrange
        task_id = str(uuid.uuid4())
        delegate_data = {'pattern': 'reusable_auth'}
        
        mock_delegation_service.create_delegation.return_value = {
            'success': True,
            'delegation_id': str(uuid.uuid4())
        }
        
        # Act
        result = service.delegate_context(
            level='task',
            context_id=task_id,
            delegate_to='project',
            delegate_data=delegate_data,
            delegation_reason='Reusable pattern'
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        mock_delegation_service.create_delegation.assert_called_once()
    
    def test_add_insight_to_context(self, service, mock_repositories):
        """Test adding insight to context"""
        # Arrange
        context_id = str(uuid.uuid4())
        existing_context = Mock(
            id=context_id,
            data={'insights': []},
            update=Mock()
        )
        mock_repositories['task_context'].find_by_id.return_value = existing_context
        mock_repositories['task_context'].save.return_value = existing_context
        
        # Act
        result = service.add_insight(
            level='task',
            context_id=context_id,
            content='Found optimization opportunity',
            category='performance'
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        existing_context.update.assert_called_once()
    
    def test_add_progress_to_context(self, service, mock_repositories):
        """Test adding progress update to context"""
        # Arrange
        context_id = str(uuid.uuid4())
        existing_context = Mock(
            id=context_id,
            data={'progress_updates': []},
            update=Mock()
        )
        mock_repositories['task_context'].find_by_id.return_value = existing_context
        mock_repositories['task_context'].save.return_value = existing_context
        
        # Act
        result = service.add_progress(
            level='task',
            context_id=context_id,
            content='Completed authentication module'
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        existing_context.update.assert_called_once()
    
    def test_list_contexts_at_level(self, service, mock_repositories):
        """Test listing contexts at specific level"""
        # Arrange
        contexts = [
            Mock(id=str(uuid.uuid4()), to_dict=Mock(return_value={'id': str(uuid.uuid4())}))
            for _ in range(3)
        ]
        mock_repositories['project_context'].find_all.return_value = contexts
        
        # Act
        result = service.list_contexts(level='project')
        
        # Assert
        assert result is not None
        assert len(result['contexts']) == 3
        mock_repositories['project_context'].find_all.assert_called_once()
    
    def test_validate_hierarchy_levels(self, service):
        """Test validation of hierarchy levels"""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid context level"):
            service.create_context(
                level='invalid_level',
                context_id='test',
                data={}
            )
    
    def test_propagate_changes_downward(self, service, mock_repositories):
        """Test that changes propagate to dependent contexts"""
        # Arrange
        project_id = str(uuid.uuid4())
        project_context = Mock(
            id=project_id,
            data={'updated': True}
        )
        
        # Mock branches that depend on this project
        dependent_branches = [
            Mock(id=str(uuid.uuid4()), project_id=project_id)
            for _ in range(2)
        ]
        
        mock_repositories['project_context'].find_by_id.return_value = project_context
        mock_repositories['branch_context'].find_by_project.return_value = dependent_branches
        
        # Act
        result = service.update_context(
            level='project',
            context_id=project_id,
            data={'updated': True},
            propagate_changes=True
        )
        
        # Assert
        assert result is not None
        # Verify cache was invalidated for dependent contexts
        assert service._cache_service.invalidate.call_count >= 1
    
    def test_handle_json_string_data(self, service, mock_repositories):
        """Test handling JSON string data input"""
        # Arrange
        json_data = '{"key": "value", "nested": {"field": 123}}'
        mock_repositories['global_context'].save.return_value = Mock(
            id='global_singleton',
            data=json.loads(json_data)
        )
        
        # Act
        result = service.create_context(
            level='global',
            context_id='global_singleton',
            data=json_data
        )
        
        # Assert
        assert result is not None
        assert result['success'] is True
        # Verify JSON was parsed
        call_args = mock_repositories['global_context'].save.call_args
        assert isinstance(call_args[0][0].data, dict)
    
    def test_error_handling_for_missing_context(self, service, mock_repositories):
        """Test error handling when context not found"""
        # Arrange
        context_id = str(uuid.uuid4())
        mock_repositories['task_context'].find_by_id.return_value = None
        
        # Act
        result = service.get_context(
            level='task',
            context_id=context_id
        )
        
        # Assert
        assert result is None
    
    def test_performance_with_cache(self, service, mock_cache_service):
        """Test that cache improves performance"""
        # Arrange
        context_id = str(uuid.uuid4())
        cached_data = {'cached': True}
        
        # First call - cache miss
        mock_cache_service.get.return_value = None
        result1 = service.get_context('task', context_id)
        
        # Second call - cache hit
        mock_cache_service.get.return_value = cached_data
        result2 = service.get_context('task', context_id)
        
        # Assert
        assert mock_cache_service.get.call_count == 2
        assert result2 == cached_data