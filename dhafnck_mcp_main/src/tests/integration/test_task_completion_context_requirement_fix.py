"""Test for task completion context requirement issue.

This test reproduces and verifies the fix for the issue where task completion
fails with "Task completion requires hierarchical context to be created first"
even though auto-context creation should handle this automatically.
"""

import pytest
import uuid
from datetime import datetime, timezone

from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects import TaskStatus, Priority, TaskId
from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task as TaskModel, 
    GlobalContext as GlobalContextModel
)


class TestTaskCompletionContextRequirement:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Test that task completion works without manual context creation."""
    
    @pytest.fixture
    def setup_minimal_test_data(self):
        """Set up minimal test database with project, branch, and task - NO contexts."""
        with get_session() as session:
            # Ensure global context exists (required by system)
            global_context = session.get(GlobalContextModel, "global_singleton")
            if not global_context:
                global_context = GlobalContextModel(
                    id="global_singleton",
                    organization_id="default_org",
                    autonomous_rules={},
                    security_policies={},
                    coding_standards={},
                    workflow_templates={},
                    delegation_rules={},
                    version=1
                )
                session.add(global_context)
                session.commit()
            
            # Generate UUIDs for test entities
            project_id = str(uuid.uuid4())
            branch_id = str(uuid.uuid4())
            task_id = str(uuid.uuid4())
            
            # Create test project (NO project context)
            project = Project(
                id=project_id,
                name="Test Project Context Fix",
                description="Test project for context requirement fix",
                user_id="test_user",
                status="active"
            )
            session.add(project)
            
            # Create test branch (NO branch context)
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project_id,
                name="main",
                description="Main branch for testing"
            )
            session.add(branch)
            
            # Create test task WITHOUT context_id (this is the key issue)
            task = TaskModel(
                id=task_id,
                git_branch_id=branch_id,
                title="Test Task Context Fix",
                description="This task should complete without manual context creation",
                status="todo",
                priority="medium",
                context_id=None  # This is the problem - no context_id
            )
            session.add(task)
            
            session.commit()
            
            return {
                "project_id": project_id,
                "branch_id": branch_id,
                "task_id": task_id
            }
    
    def test_task_completion_with_no_existing_contexts(self, setup_minimal_test_data):
        """Test that completing a task works when NO contexts exist.
        
        This reproduces the issue:
        1. Create task with NO context_id
        2. Try to complete it 
        3. Should auto-create hierarchy and succeed (NOT fail with context error)
        """
        task_id = setup_minimal_test_data["task_id"]
        
        # Create repositories
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
        from fastmcp.task_management.infrastructure.repositories.task_context_repository import TaskContextRepository
        
        task_repo = ORMTaskRepository(git_branch_id=setup_minimal_test_data["branch_id"], user_id="test_user")
        subtask_repo = ORMSubtaskRepository()
        from fastmcp.task_management.infrastructure.database.database_config import get_session
        context_repo = TaskContextRepository(get_session)
        
        # Create use case
        use_case = CompleteTaskUseCase(
            task_repository=task_repo,
            subtask_repository=subtask_repo,
            task_context_repository=context_repo
        )
        
        # Verify task exists and has NO context_id
        task_entity = task_repo.find_by_id(task_id)
        assert task_entity is not None, "Task should exist"
        assert task_entity.context_id is None, "Task should have no context_id initially"
        
        # Verify NO contexts exist yet (this is the failing scenario)
        initial_context = context_repo.get(task_id)
        assert initial_context is None, "Context should not exist before completion"
        
        # THIS IS THE CRITICAL TEST: Complete the task without any pre-existing contexts
        # The system should auto-create the entire hierarchy and succeed
        result = use_case.execute(
            task_id=task_id,
            completion_summary="Task completed successfully with auto-created context hierarchy",
            testing_notes="Verified auto hierarchy creation works"
        )
        
        # Verify completion succeeded (this should NOT fail with context error)
        print(f"Task completion result: {result}")
        assert result["success"] is True, f"Task completion should succeed: {result.get('message', result.get('error'))}"
        assert result["status"] == "done"
        assert f"task {task_id} done, can next_task" in result["message"]
        
        # Verify the task was updated with context_id  
        updated_task = task_repo.find_by_id(task_id)
        assert updated_task.context_id is not None, "Task should have context_id after completion"
        assert updated_task.context_id == task_id, "Context_id should match task_id"
        
        # Verify context was auto-created
        created_context = context_repo.get(task_id)
        assert created_context is not None, "Context should have been auto-created"
    
    def test_task_completion_with_context_creation_failure(self, setup_minimal_test_data):
        """Test task completion when context creation fails (edge case).
        
        This tests the scenario where auto-context creation fails for some reason.
        The completion should either retry or handle the failure gracefully.
        """
        task_id = setup_minimal_test_data["task_id"]
        
        # Create repositories with mock context repo that fails
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
        from unittest.mock import Mock
        
        task_repo = ORMTaskRepository(git_branch_id=setup_minimal_test_data["branch_id"], user_id="test_user")
        subtask_repo = ORMSubtaskRepository()
        
        # Mock context repository that always returns None (simulates context creation failure)
        mock_context_repo = Mock()
        mock_context_repo.get.return_value = None  # No existing context
        # Note: create method is not mocked, so UnifiedContextFacade will be used
        
        # Create use case
        use_case = CompleteTaskUseCase(
            task_repository=task_repo,
            subtask_repository=subtask_repo,
            task_context_repository=mock_context_repo
        )
        
        # Complete the task - should handle context creation failure gracefully
        result = use_case.execute(
            task_id=task_id,
            completion_summary="Task completed despite context issues",
            testing_notes="Testing graceful context failure handling"
        )
        
        # The completion should still succeed even if context operations have issues
        # The key is that it should NOT fail with "Context must be updated before completing task"
        assert result["success"] is True, f"Task completion should succeed even with context issues: {result}"
        assert result["status"] == "done"
        
        # Verify context check was attempted
        mock_context_repo.get.assert_called_with(task_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])