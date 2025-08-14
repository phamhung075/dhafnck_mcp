"""
Integration test to verify that tasks return subtask IDs correctly.
This test verifies the fix for the issue where backend was returning 
empty subtasks array instead of subtask IDs.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestTaskSubtaskIdsFix:
    
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

    """Test that tasks correctly return subtask IDs instead of empty arrays."""
    
    def test_task_repository_returns_subtask_ids_not_empty_array(self):
        """Test that task repository returns subtask IDs in the subtasks field."""
        # Setup - get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        from fastmcp.task_management.infrastructure.database.database_config import get_session
        
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
            
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Test Task with Subtasks",
            description="A task that should have subtask IDs",
            priority="high"
        )
        
        # Create subtasks for the task
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 1",
            description="First subtask",
            parent_task_id=task.id,
            status=TaskStatus("todo"),
            priority=Priority("medium")
        )
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Subtask 2", 
            description="Second subtask",
            parent_task_id=task.id,
            status=TaskStatus("todo"),
            priority=Priority("low")
        )
        
        # Save subtasks
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # Retrieve the task and check subtasks
        retrieved_task = task_repo.get_task(str(task.id))
        
        # Assertions
        assert retrieved_task is not None
        assert retrieved_task.subtasks is not None
        assert isinstance(retrieved_task.subtasks, list)
        assert len(retrieved_task.subtasks) == 2
        
        # Check that subtasks are string IDs, not empty or objects
        assert str(subtask1.id) in retrieved_task.subtasks
        assert str(subtask2.id) in retrieved_task.subtasks
        
        # Check that all subtasks are strings
        for subtask_id in retrieved_task.subtasks:
            assert isinstance(subtask_id, str)
            assert len(subtask_id) > 0  # Not empty strings
            
        print(f"✅ Task subtasks field contains IDs: {retrieved_task.subtasks}")
        
    def test_task_to_dict_serialization_includes_subtask_ids(self):
        """Test that task.to_dict() includes subtask IDs in the serialized output."""
        # Setup - get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        from fastmcp.task_management.infrastructure.database.database_config import get_session
        
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
            
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Test Task Serialization",
            description="Test task serialization with subtasks",
            priority="high"
        )
        
        # Create a subtask
        subtask = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Test Subtask",
            description="A test subtask",
            parent_task_id=task.id,
            status=TaskStatus("todo"),
            priority=Priority("medium")
        )
        
        # Save subtask
        subtask_repo.save(subtask)
        
        # Retrieve the task
        retrieved_task = task_repo.get_task(str(task.id))
        
        # Serialize to dict
        task_dict = retrieved_task.to_dict()
        
        # Assertions
        assert 'subtasks' in task_dict
        assert isinstance(task_dict['subtasks'], list)
        assert len(task_dict['subtasks']) == 1
        assert str(subtask.id) in task_dict['subtasks']
        assert isinstance(task_dict['subtasks'][0], str)
        
        print(f"✅ Task.to_dict() subtasks field: {task_dict['subtasks']}")
        
    def test_task_without_subtasks_has_empty_list(self):
        """Test that tasks without subtasks have empty list, not None."""
        # Setup - get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        from fastmcp.task_management.infrastructure.database.database_config import get_session
        
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
            
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        
        # Create a task without subtasks
        task = task_repo.create_task(
            title="Task Without Subtasks",
            description="A task with no subtasks",
            priority="medium"
        )
        
        # Retrieve the task
        retrieved_task = task_repo.get_task(str(task.id))
        
        # Assertions
        assert retrieved_task is not None
        assert retrieved_task.subtasks is not None
        assert isinstance(retrieved_task.subtasks, list)
        assert len(retrieved_task.subtasks) == 0
        
        # Check serialization
        task_dict = retrieved_task.to_dict()
        assert 'subtasks' in task_dict
        assert isinstance(task_dict['subtasks'], list)
        assert len(task_dict['subtasks']) == 0
        
        print(f"✅ Task without subtasks has empty list: {task_dict['subtasks']}")