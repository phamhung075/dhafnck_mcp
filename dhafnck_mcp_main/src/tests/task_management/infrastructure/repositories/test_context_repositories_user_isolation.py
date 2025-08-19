"""
Test all context repositories (global, project, branch, task) with user isolation.
Critical: Even GLOBAL contexts must be user-scoped.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

from fastmcp.task_management.infrastructure.repositories.global_context_repository import GlobalContextRepository
from fastmcp.task_management.infrastructure.repositories.project_context_repository import ProjectContextRepository
from fastmcp.task_management.infrastructure.repositories.branch_context_repository import BranchContextRepository
from fastmcp.task_management.infrastructure.repositories.task_context_repository import TaskContextRepository


class TestContextRepositoriesUserIsolation:
    """Test suite ensuring ALL context levels respect user boundaries."""
    
    @pytest.fixture
    def mock_db_adapter(self):
        """Create a mock database adapter."""
        adapter = Mock()
        adapter.execute_query = Mock()
        adapter.fetch_one = Mock()
        adapter.fetch_all = Mock()
        return adapter
    
    @pytest.fixture
    def user_id(self):
        """Generate a test user ID."""
        return str(uuid4())
    
    @pytest.fixture
    def other_user_id(self):
        """Generate another user ID for cross-user testing."""
        return str(uuid4())
    
    # ==================== Global Context Tests ====================
    
    def test_global_context_requires_user_id(self, mock_db_adapter):
        """Test that GlobalContextRepository requires user_id."""
        with pytest.raises(TypeError):
            GlobalContextRepository(db_adapter=mock_db_adapter)
    
    def test_global_context_is_user_scoped(self, mock_db_adapter, user_id):
        """Test that global contexts are scoped to users, not truly global."""
        repository = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        # Create a global context
        context_data = {
            "key": "api_settings",
            "value": {"endpoint": "https://api.example.com"},
            "description": "User's API settings"
        }
        
        repository.create_global_context(context_data)
        
        # Verify user_id was included
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert user_id in query
        assert "user_id" in query
    
    def test_users_have_separate_global_contexts(self, mock_db_adapter, user_id, other_user_id):
        """Test that each user has their own 'global' context space."""
        # Create repositories for two users
        user1_repo = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        user2_repo = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=other_user_id)
        
        # Mock return values
        mock_db_adapter.fetch_all.return_value = []
        
        # User 1 gets global contexts
        user1_repo.get_all_global_contexts()
        user1_call = mock_db_adapter.execute_query.call_args
        
        # Reset mock
        mock_db_adapter.execute_query.reset_mock()
        
        # User 2 gets global contexts
        user2_repo.get_all_global_contexts()
        user2_call = mock_db_adapter.execute_query.call_args
        
        # Verify different user_ids
        assert user_id in str(user1_call)
        assert other_user_id not in str(user1_call)
        
        assert other_user_id in str(user2_call)
        assert user_id not in str(user2_call)
    
    def test_global_context_update_respects_user_boundaries(self, mock_db_adapter, user_id):
        """Test that global context updates only affect user's context."""
        repository = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        context_id = str(uuid4())
        update_data = {"value": {"new_setting": "value"}}
        
        repository.update_global_context(context_id, update_data)
        
        # Verify both context_id and user_id in query
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert context_id in query
        assert user_id in query
        assert "user_id" in query
    
    def test_global_context_delete_respects_user_boundaries(self, mock_db_adapter, user_id):
        """Test that global context deletes only affect user's context."""
        repository = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        context_id = str(uuid4())
        
        repository.delete_global_context(context_id)
        
        # Verify both context_id and user_id in query
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert context_id in query
        assert user_id in query
        assert "user_id" in query
    
    # ==================== Project Context Tests ====================
    
    def test_project_context_requires_user_id(self, mock_db_adapter):
        """Test that ProjectContextRepository requires user_id."""
        with pytest.raises(TypeError):
            ProjectContextRepository(db_adapter=mock_db_adapter)
    
    def test_project_context_filters_by_user(self, mock_db_adapter, user_id):
        """Test that project contexts are filtered by user_id."""
        repository = ProjectContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        project_id = str(uuid4())
        
        repository.get_project_context(project_id)
        
        # Verify user_id in query
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert project_id in query
        assert user_id in query
        assert "user_id" in query
    
    def test_project_context_create_adds_user_id(self, mock_db_adapter, user_id):
        """Test that creating project context adds user_id."""
        repository = ProjectContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        context_data = {
            "project_id": str(uuid4()),
            "data": {"project_settings": "value"}
        }
        
        repository.create_project_context(context_data)
        
        # Verify user_id was added
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert user_id in query
        assert "user_id" in query
    
    # ==================== Branch Context Tests ====================
    
    def test_branch_context_requires_user_id(self, mock_db_adapter):
        """Test that BranchContextRepository requires user_id."""
        with pytest.raises(TypeError):
            BranchContextRepository(db_adapter=mock_db_adapter)
    
    def test_branch_context_filters_by_user(self, mock_db_adapter, user_id):
        """Test that branch contexts are filtered by user_id."""
        repository = BranchContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        branch_id = str(uuid4())
        
        repository.get_branch_context(branch_id)
        
        # Verify user_id in query
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert branch_id in query
        assert user_id in query
        assert "user_id" in query
    
    def test_branch_context_inheritance_respects_user_boundaries(self, mock_db_adapter, user_id):
        """Test that branch context inheritance stays within user boundaries."""
        repository = BranchContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        branch_id = str(uuid4())
        project_id = str(uuid4())
        
        # Mock the inheritance chain queries
        mock_db_adapter.fetch_one.return_value = None
        mock_db_adapter.fetch_all.return_value = []
        
        repository.get_inherited_context(branch_id, project_id)
        
        # All queries should include user_id
        all_calls = mock_db_adapter.execute_query.call_args_list
        for call in all_calls:
            query = str(call)
            assert user_id in query
    
    # ==================== Task Context Tests ====================
    
    def test_task_context_requires_user_id(self, mock_db_adapter):
        """Test that TaskContextRepository requires user_id."""
        with pytest.raises(TypeError):
            TaskContextRepository(db_adapter=mock_db_adapter)
    
    def test_task_context_filters_by_user(self, mock_db_adapter, user_id):
        """Test that task contexts are filtered by user_id."""
        repository = TaskContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        task_id = str(uuid4())
        
        repository.get_task_context(task_id)
        
        # Verify user_id in query
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert task_id in query
        assert user_id in query
        assert "user_id" in query
    
    def test_task_context_auto_creation_adds_user_id(self, mock_db_adapter, user_id):
        """Test that auto-created task contexts include user_id."""
        repository = TaskContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        task_id = str(uuid4())
        task_data = {
            "title": "Test Task",
            "status": "completed",
            "completion_summary": "Task completed successfully"
        }
        
        repository.create_task_context_from_completion(task_id, task_data)
        
        # Verify user_id was included
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert user_id in query
        assert "user_id" in query
    
    # ==================== Context Inheritance Tests ====================
    
    def test_context_inheritance_stays_within_user_boundary(self, mock_db_adapter, user_id):
        """Test that context inheritance doesn't leak across users."""
        # Create repositories for task context (lowest level)
        task_repo = TaskContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        task_id = str(uuid4())
        branch_id = str(uuid4())
        project_id = str(uuid4())
        
        # Mock the inheritance chain
        mock_db_adapter.fetch_one.return_value = None
        mock_db_adapter.fetch_all.return_value = []
        
        # Get full inherited context
        task_repo.get_full_inherited_context(task_id, branch_id, project_id)
        
        # Every query in the chain should include user_id
        all_calls = mock_db_adapter.execute_query.call_args_list
        assert len(all_calls) > 0  # Should make multiple queries
        
        for call in all_calls:
            query = str(call)
            assert user_id in query
            assert "user_id" in query
    
    def test_context_delegation_respects_user_boundaries(self, mock_db_adapter, user_id):
        """Test that context delegation stays within user boundaries."""
        repository = TaskContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        # Attempt to delegate context upward
        task_id = str(uuid4())
        delegation_data = {
            "from_level": "task",
            "to_level": "branch",
            "data": {"shared_setting": "value"}
        }
        
        repository.delegate_context(task_id, delegation_data)
        
        # Verify user_id is maintained in delegation
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert user_id in query
        assert "user_id" in query
    
    # ==================== Cross-User Isolation Tests ====================
    
    def test_users_cannot_share_contexts(self, mock_db_adapter, user_id, other_user_id):
        """Test that users cannot access each other's contexts at any level."""
        # Create global context for user 1
        user1_global = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        user1_global.create_global_context({"key": "setting", "value": "user1_value"})
        
        # Create global context for user 2
        user2_global = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=other_user_id)
        user2_global.create_global_context({"key": "setting", "value": "user2_value"})
        
        # Verify queries used different user_ids
        calls = mock_db_adapter.execute_query.call_args_list
        
        user1_query = str(calls[0])
        user2_query = str(calls[1])
        
        assert user_id in user1_query
        assert other_user_id not in user1_query
        
        assert other_user_id in user2_query
        assert user_id not in user2_query
    
    def test_context_search_filters_by_user(self, mock_db_adapter, user_id):
        """Test that context searches are filtered by user."""
        repository = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        search_params = {"key": "api_settings"}
        
        repository.search_contexts(search_params)
        
        # Verify user_id in search query
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert user_id in query
        assert "user_id" in query
    
    # ==================== Special Cases ====================
    
    def test_system_user_contexts(self, mock_db_adapter):
        """Test that system user can have its own contexts."""
        system_user_id = "00000000-0000-0000-0000-000000000000"
        
        # Create all levels of context repositories for system user
        global_repo = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=system_user_id)
        project_repo = ProjectContextRepository(db_adapter=mock_db_adapter, user_id=system_user_id)
        branch_repo = BranchContextRepository(db_adapter=mock_db_adapter, user_id=system_user_id)
        task_repo = TaskContextRepository(db_adapter=mock_db_adapter, user_id=system_user_id)
        
        # System user creates contexts at all levels
        global_repo.create_global_context({"key": "system_setting"})
        project_repo.create_project_context({"project_id": str(uuid4())})
        branch_repo.create_branch_context({"branch_id": str(uuid4())})
        task_repo.create_task_context({"task_id": str(uuid4())})
        
        # Verify all used system_user_id
        calls = mock_db_adapter.execute_query.call_args_list
        
        for call in calls:
            query = str(call)
            assert system_user_id in query
    
    def test_context_count_by_user(self, mock_db_adapter, user_id):
        """Test that context counts are per user."""
        repository = GlobalContextRepository(db_adapter=mock_db_adapter, user_id=user_id)
        
        mock_db_adapter.fetch_one.return_value = {"count": 5}
        
        count = repository.get_context_count()
        
        # Verify count query includes user_id
        call_args = mock_db_adapter.execute_query.call_args
        query = str(call_args)
        
        assert user_id in query
        assert "user_id" in query
        assert count == 5