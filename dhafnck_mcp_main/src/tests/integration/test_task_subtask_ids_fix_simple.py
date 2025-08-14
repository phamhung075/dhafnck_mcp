"""
Simple test to verify that tasks return subtask IDs correctly.
This test verifies the fix for the issue where backend was returning 
empty subtasks array instead of subtask IDs.
"""

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from datetime import datetime
import uuid


class TestTaskSubtaskIdsSerialization:
    
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

    """Test that tasks correctly serialize subtask IDs."""
    
    def test_task_with_subtask_ids_serializes_correctly(self):
        """Test that Task entity with subtask IDs serializes correctly to dict."""
        # Create a task with subtask IDs
        task = Task(
            id=TaskId(str(uuid.uuid4())),
            title="Test Task",
            description="A test task",
            status=TaskStatus("todo"),
            priority=Priority("medium"),
            subtasks=["subtask-id-1", "subtask-id-2", "subtask-id-3"],  # List of IDs
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Convert to dict
        task_dict = task.to_dict()
        
        # Assertions
        assert 'subtasks' in task_dict
        assert isinstance(task_dict['subtasks'], list)
        assert len(task_dict['subtasks']) == 3
        assert task_dict['subtasks'] == ["subtask-id-1", "subtask-id-2", "subtask-id-3"]
        
        # Check that all subtasks are strings
        for subtask_id in task_dict['subtasks']:
            assert isinstance(subtask_id, str)
            assert len(subtask_id) > 0
            
        print(f"✅ Task.to_dict() subtasks field: {task_dict['subtasks']}")
        
    def test_task_without_subtasks_serializes_correctly(self):
        """Test that Task entity without subtasks serializes correctly to dict."""
        # Create a task without subtasks
        task = Task(
            id=TaskId(str(uuid.uuid4())),
            title="Test Task",
            description="A test task",
            status=TaskStatus("todo"),
            priority=Priority("medium"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Convert to dict
        task_dict = task.to_dict()
        
        # Assertions
        assert 'subtasks' in task_dict
        assert isinstance(task_dict['subtasks'], list)
        assert len(task_dict['subtasks']) == 0
        
        print(f"✅ Task without subtasks serializes as empty list: {task_dict['subtasks']}")
        
    def test_task_entity_subtask_field_type(self):
        """Test that Task entity subtasks field is list of strings."""
        # Create a task with subtask IDs
        task = Task(
            id=TaskId(str(uuid.uuid4())),
            title="Test Task",
            description="A test task",
            status=TaskStatus("todo"),
            priority=Priority("medium"),
            subtasks=["subtask-id-1", "subtask-id-2"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Check the subtasks field directly
        assert isinstance(task.subtasks, list)
        assert len(task.subtasks) == 2
        assert all(isinstance(subtask_id, str) for subtask_id in task.subtasks)
        
        print(f"✅ Task.subtasks field is list of strings: {task.subtasks}")
        
    def test_task_entity_subtasks_field_is_not_none(self):
        """Test that Task entity subtasks field is never None."""
        # Create a task with default subtasks
        task = Task(
            id=TaskId(str(uuid.uuid4())),
            title="Test Task",
            description="A test task",
            status=TaskStatus("todo"),
            priority=Priority("medium"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Check the subtasks field
        assert task.subtasks is not None
        assert isinstance(task.subtasks, list)
        assert len(task.subtasks) == 0  # Default empty list
        
        print(f"✅ Task.subtasks field defaults to empty list: {task.subtasks}")