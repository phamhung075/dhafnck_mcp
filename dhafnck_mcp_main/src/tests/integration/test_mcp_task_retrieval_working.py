"""
Integration test to verify that MCP task retrieval works correctly after the fix.

This test verifies that the AttributeError is fixed by using the actual MCP tools
to create and retrieve tasks with subtasks.
"""

import pytest
from uuid import uuid4

from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.infrastructure.database.database_config import get_session


class TestMCPTaskRetrievalWorking:
    """Test that MCP task retrieval works correctly after the fix."""
    
    def test_mcp_task_retrieval_with_subtasks_works(self, module_test_db):
        """Test that MCP task retrieval works with subtasks after the fix."""
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories and facades (like MCP tools do)
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
        
        task_repository = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repository = ORMSubtaskRepository()
        
        task_facade = TaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
        subtask_facade = SubtaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
        
        # Create a task using the facade
        from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
        
        task_request = CreateTaskRequest(
            title="MCP Test Task with Subtasks",
            git_branch_id=git_branch_id,
            description="This task tests MCP task retrieval with subtasks",
            priority="high"
        )
        
        task_result = task_facade.create_task(task_request)
        
        assert task_result['success'] is True
        
        # Extract task_id from the response
        task_id = task_result['task']['id']
        
        # Create subtasks using the facade
        subtask1_result = subtask_facade.handle_manage_subtask(
            action="create",
            task_id=task_id,
            subtask_data={
                "title": "MCP Subtask 1",
                "description": "First subtask via MCP"
            }
        )
        
        subtask2_result = subtask_facade.handle_manage_subtask(
            action="create",
            task_id=task_id,
            subtask_data={
                "title": "MCP Subtask 2",
                "description": "Second subtask via MCP"
            }
        )
        
        assert subtask1_result['success'] is True
        assert subtask2_result['success'] is True
        
        # NOW THE CRITICAL TEST: Retrieve the task via MCP
        # This should NOT cause AttributeError
        task_get_result = task_facade.get_task(task_id)
        
        # Verify the task was retrieved successfully
        assert task_get_result['success'] is True
        assert task_get_result['task']['id'] == task_id
        assert task_get_result['task']['title'] == "MCP Test Task with Subtasks"
        
        # Verify subtasks are present as string IDs
        assert 'subtasks' in task_get_result['task']
        subtasks = task_get_result['task']['subtasks']
        assert isinstance(subtasks, list)
        assert len(subtasks) == 2
        
        # Verify each subtask is a string ID
        for subtask_id in subtasks:
            assert isinstance(subtask_id, str)
            assert len(subtask_id) == 36  # UUID length
            
        print(f"✅ MCP task retrieval works correctly: {subtasks}")
        
    def test_mcp_task_list_with_subtasks_works(self, module_test_db):
        """Test that MCP task listing works with subtasks after the fix."""
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories and facades
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
        
        task_repository = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repository = ORMSubtaskRepository()
        
        task_facade = TaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
        subtask_facade = SubtaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
        
        # Create a task
        from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
        
        task_request = CreateTaskRequest(
            title="MCP List Test Task",
            git_branch_id=git_branch_id,
            description="This task tests MCP task listing with subtasks",
            priority="medium"
        )
        
        task_result = task_facade.create_task(task_request)
        
        assert task_result['success'] is True
        task_id = task_result['task']['id']
        
        # Create a subtask
        subtask_result = subtask_facade.handle_manage_subtask(
            action="create",
            task_id=task_id,
            subtask_data={
                "title": "MCP List Subtask",
                "description": "Subtask for list test"
            }
        )
        
        assert subtask_result['success'] is True
        
        # List tasks - this should NOT cause AttributeError
        from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
        
        list_request = ListTasksRequest(git_branch_id=git_branch_id)
        list_result = task_facade.list_tasks(list_request)
        
        assert list_result['success'] is True
        assert 'tasks' in list_result
        assert len(list_result['tasks']) > 0
        
        # Find our created task
        created_task = None
        for task in list_result['tasks']:
            if task['id'] == task_id:
                created_task = task
                break
        
        assert created_task is not None
        assert created_task['title'] == "MCP List Test Task"
        assert 'subtasks' in created_task
        assert isinstance(created_task['subtasks'], list)
        assert len(created_task['subtasks']) == 1
        assert isinstance(created_task['subtasks'][0], str)
        
        print(f"✅ MCP task listing works correctly: {created_task['subtasks']}")
        
    def test_mcp_task_completion_with_subtasks_works(self, module_test_db):
        """Test that MCP task completion works with subtasks after the fix."""
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories and facades
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
        
        task_repository = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repository = ORMSubtaskRepository()
        
        task_facade = TaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
        subtask_facade = SubtaskApplicationFacade(task_repository=task_repository, subtask_repository=subtask_repository)
        
        # Create a task
        from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
        
        task_request = CreateTaskRequest(
            title="MCP Completion Test Task",
            git_branch_id=git_branch_id,
            description="This task tests MCP task completion with subtasks",
            priority="high"
        )
        
        task_result = task_facade.create_task(task_request)
        
        assert task_result['success'] is True
        task_id = task_result['task']['id']
        
        # Add context to task (required for completion)
        from fastmcp.task_management.application.dtos.task.update_task_request import UpdateTaskRequest
        
        update_request = UpdateTaskRequest(
            task_id=task_id,
            context_id=str(uuid4())
        )
        task_facade.update_task(task_id, update_request)
        
        # Create subtasks
        subtask1_result = subtask_facade.handle_manage_subtask(
            action="create",
            task_id=task_id,
            subtask_data={
                "title": "Completion Subtask 1",
                "description": "First subtask for completion test"
            }
        )
        
        subtask2_result = subtask_facade.handle_manage_subtask(
            action="create",
            task_id=task_id,
            subtask_data={
                "title": "Completion Subtask 2",
                "description": "Second subtask for completion test"
            }
        )
        
        assert subtask1_result['success'] is True
        assert subtask2_result['success'] is True
        
        subtask1_id = subtask1_result['subtask']['id']
        subtask2_id = subtask2_result['subtask']['id']
        
        # Complete both subtasks
        subtask_facade.handle_manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_data={
                "subtask_id": subtask1_id,
                "completion_summary": "First subtask completed"
            }
        )
        
        subtask_facade.handle_manage_subtask(
            action="complete",
            task_id=task_id,
            subtask_data={
                "subtask_id": subtask2_id,
                "completion_summary": "Second subtask completed"
            }
        )
        
        # NOW THE CRITICAL TEST: Complete the task
        # This should NOT cause AttributeError when checking subtask completion
        completion_result = task_facade.complete_task(
            task_id=task_id,
            completion_summary="All subtasks completed successfully",
            testing_notes="Verified that MCP task completion works"
        )
        
        # Verify the task was completed successfully
        assert completion_result['success'] is True
        assert completion_result['status'] == 'done'
        assert 'subtask_summary' in completion_result
        assert completion_result['subtask_summary']['total'] == 2
        assert completion_result['subtask_summary']['completed'] == 2
        
        print(f"✅ MCP task completion works correctly: {completion_result['subtask_summary']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])