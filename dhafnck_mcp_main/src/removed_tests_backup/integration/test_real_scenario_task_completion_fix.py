"""Test the real scenario where task completion fails with subtasks"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.git_branch_repository import ORMGitBranchRepository
from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.infrastructure.database.database_config import get_session


class TestRealScenarioTaskCompletion:
    
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

    """Test the actual scenario that causes the AttributeError"""
    
    def test_complete_task_with_subtasks_in_repository(self, module_test_db):
        """
        Reproduce the real scenario:
        1. Create a task with no internal subtasks
        2. Create subtasks in the SubtaskRepository
        3. Try to complete the task
        """
        # Get the existing git branch from the database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories with a git branch id
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Task with Subtasks",
            description="A task that has subtasks in the repository",
            priority="medium",
            assignee_ids=["user1"],
            label_names=["test"],
        )
        
        # Update task to have context_id (simulating that context was created)
        task.context_id = str(uuid4())
        task_repo.save(task)
        
        # Create subtasks in the repository
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 1",
            description="First subtask",
            parent_task_id=task.id,
            status=TaskStatus.done(),
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 2", 
            description="Second subtask",
            parent_task_id=task.id,
            status=TaskStatus.done(),
            priority=Priority.medium()
        )
        
        # Save subtasks
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # Create the use case with subtask repository
        complete_task_use_case = CompleteTaskUseCase(task_repo, subtask_repo)
        
        # Try to complete the task
        result = complete_task_use_case.execute(
            task_id=task.id.value,
            completion_summary="All subtasks completed successfully",
            testing_notes="Tested the fix for subtask handling"
        )
        
        # Should succeed without AttributeError
        assert result['success'] is True
        assert result['status'] == 'done'
        assert 'subtask_summary' in result
        assert result['subtask_summary']['total'] == 2
        assert result['subtask_summary']['completed'] == 2
    
    def test_complete_task_with_incomplete_subtasks(self, module_test_db):
        """Test that incomplete subtasks are properly detected"""
        # Get the existing git branch from the database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories with a git branch id
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Task with Incomplete Subtasks",
            description="A task that has incomplete subtasks",
            priority="high",
        )
        
        # Update task to have context_id
        task.context_id = str(uuid4())
        task_repo.save(task)
        
        # Create subtasks with one incomplete
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Completed Subtask",
            description="This one is done",
            parent_task_id=task.id,
            status=TaskStatus.done(),
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Incomplete Subtask", 
            description="This one is not done",
            parent_task_id=task.id,
            status=TaskStatus.in_progress(),
            priority=Priority.high()
        )
        
        # Save subtasks
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # Create the use case
        complete_task_use_case = CompleteTaskUseCase(task_repo, subtask_repo)
        
        # Try to complete the task - should fail
        result = complete_task_use_case.execute(
            task_id=task.id.value,
            completion_summary="Trying to complete with incomplete subtasks"
        )
        
        # Should fail with proper error message
        assert result['success'] is False
        assert "1 of 2 subtasks are incomplete" in result['message']
        assert "Incomplete Subtask" in result['message']
    
    def test_task_with_no_subtasks_completes_successfully(self, module_test_db):
        """Test that a task with no subtasks can be completed"""
        # Get the existing git branch from the database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories with a git branch id
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Simple Task",
            description="A task without any subtasks",
            priority="low",
        )
        
        # Update task to have context_id
        task.context_id = str(uuid4())
        task_repo.save(task)
        
        # Create the use case
        complete_task_use_case = CompleteTaskUseCase(task_repo, subtask_repo)
        
        # Complete the task
        result = complete_task_use_case.execute(
            task_id=task.id.value,
            completion_summary="Simple task completed",
            testing_notes="No subtasks to worry about"
        )
        
        # Should succeed
        assert result['success'] is True
        assert result['status'] == 'done'
        if 'subtask_summary' in result:
            assert result['subtask_summary']['total'] == 0
            assert result['subtask_summary']['can_complete_parent'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])