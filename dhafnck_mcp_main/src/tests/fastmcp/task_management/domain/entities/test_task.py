"""Test suite for Task domain entity"""

import pytest
from fastmcp.task_management.domain.entities.task import Task
from datetime import datetime, timezone
import uuid


@pytest.mark.unit
class TestTaskEntity:
    """Test Task domain entity"""
    
    def test_task_creation_with_required_fields(self):
        """Test creating task with only required fields"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.project_id == "proj123"
        assert task.git_branch_id == "branch456"
        assert task.status == "todo"  # Default value
        assert task.priority == "medium"  # Default value
        assert task.created_at is not None
        assert task.updated_at is not None
    
    def test_task_creation_with_all_fields(self):
        """Test creating task with all fields"""
        due_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        task = Task(
            id=str(uuid.uuid4()),
            title="Complete Task",
            description="Comprehensive task description",
            project_id="proj123",
            git_branch_id="branch456", 
            status="in_progress",
            priority="high",
            assignee="user123",
            due_date=due_date,
            labels=["urgent", "feature"],
            completion_summary="Task completed successfully",
            testing_notes="All tests passed",
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert task.status == "in_progress"
        assert task.priority == "high"
        assert task.assignee == "user123"
        assert task.due_date == due_date
        assert task.labels == ["urgent", "feature"]
        assert task.completion_summary == "Task completed successfully"
        assert task.testing_notes == "All tests passed"
        assert task.created_at == created_at
        assert task.updated_at == updated_at
    
    def test_task_status_validation(self):
        """Test task status validation"""
        valid_statuses = ["todo", "in_progress", "blocked", "completed", "cancelled"]
        
        for status in valid_statuses:
            task = Task(
                id=str(uuid.uuid4()),
                title="Test Task",
                description="Test",
                project_id="proj123",
                git_branch_id="branch456",
                status=status
            )
            assert task.status == status
        
        # Test invalid status
        with pytest.raises(ValueError, match="Invalid task status"):
            Task(
                id=str(uuid.uuid4()),
                title="Test Task",
                description="Test",
                project_id="proj123",
                git_branch_id="branch456",
                status="invalid_status"
            )
    
    def test_task_priority_validation(self):
        """Test task priority validation"""
        valid_priorities = ["low", "medium", "high", "critical"]
        
        for priority in valid_priorities:
            task = Task(
                id=str(uuid.uuid4()),
                title="Test Task",
                description="Test",
                project_id="proj123",
                git_branch_id="branch456",
                priority=priority
            )
            assert task.priority == priority
        
        # Test invalid priority
        with pytest.raises(ValueError, match="Invalid task priority"):
            Task(
                id=str(uuid.uuid4()),
                title="Test Task",
                description="Test",
                project_id="proj123",
                git_branch_id="branch456",
                priority="invalid_priority"
            )
    
    def test_task_title_validation(self):
        """Test task title validation"""
        # Valid title
        task = Task(
            id=str(uuid.uuid4()),
            title="Valid Task Title",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456"
        )
        assert task.title == "Valid Task Title"
        
        # Empty title should raise error
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id=str(uuid.uuid4()),
                title="",
                description="Test",
                project_id="proj123",
                git_branch_id="branch456"
            )
        
        # None title should raise error
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(
                id=str(uuid.uuid4()),
                title=None,
                description="Test",
                project_id="proj123",
                git_branch_id="branch456"
            )
    
    def test_task_id_validation(self):
        """Test task ID validation"""
        # Valid UUID
        valid_id = str(uuid.uuid4())
        task = Task(
            id=valid_id,
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456"
        )
        assert task.id == valid_id
        
        # Invalid UUID format
        with pytest.raises(ValueError, match="Invalid task ID format"):
            Task(
                id="invalid_uuid",
                title="Test Task",
                description="Test",
                project_id="proj123",
                git_branch_id="branch456"
            )
    
    def test_task_update_status(self):
        """Test task status update method"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            status="todo"
        )
        
        original_updated_at = task.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        task.update_status("in_progress")
        
        assert task.status == "in_progress"
        assert task.updated_at > original_updated_at
    
    def test_task_complete_method(self):
        """Test task completion method"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            status="in_progress"
        )
        
        completion_summary = "Task completed successfully"
        testing_notes = "All tests passed"
        
        task.complete(completion_summary, testing_notes)
        
        assert task.status == "completed"
        assert task.completion_summary == completion_summary
        assert task.testing_notes == testing_notes
        assert task.updated_at is not None
    
    def test_task_assign_method(self):
        """Test task assignment method"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        assignee = "user123"
        task.assign(assignee)
        
        assert task.assignee == assignee
        assert task.updated_at is not None
    
    def test_task_add_label(self):
        """Test adding label to task"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            labels=["existing_label"]
        )
        
        task.add_label("new_label")
        
        assert "existing_label" in task.labels
        assert "new_label" in task.labels
        assert len(task.labels) == 2
    
    def test_task_remove_label(self):
        """Test removing label from task"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            labels=["label1", "label2", "label3"]
        )
        
        task.remove_label("label2")
        
        assert "label1" in task.labels
        assert "label2" not in task.labels
        assert "label3" in task.labels
        assert len(task.labels) == 2
    
    def test_task_is_overdue(self):
        """Test checking if task is overdue"""
        # Task with future due date
        future_date = datetime.now(timezone.utc).replace(year=2025)
        task_future = Task(
            id=str(uuid.uuid4()),
            title="Future Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            due_date=future_date
        )
        assert not task_future.is_overdue()
        
        # Task with past due date
        past_date = datetime.now(timezone.utc).replace(year=2020)
        task_past = Task(
            id=str(uuid.uuid4()),
            title="Past Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            due_date=past_date
        )
        assert task_past.is_overdue()
        
        # Task without due date
        task_no_due = Task(
            id=str(uuid.uuid4()),
            title="No Due Date Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456"
        )
        assert not task_no_due.is_overdue()
    
    def test_task_is_completed(self):
        """Test checking if task is completed"""
        # Completed task
        completed_task = Task(
            id=str(uuid.uuid4()),
            title="Completed Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            status="completed"
        )
        assert completed_task.is_completed()
        
        # Non-completed task
        todo_task = Task(
            id=str(uuid.uuid4()),
            title="Todo Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456",
            status="todo"
        )
        assert not todo_task.is_completed()
    
    def test_task_equality(self):
        """Test task equality comparison"""
        task_id = str(uuid.uuid4())
        
        task1 = Task(
            id=task_id,
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        task2 = Task(
            id=task_id,
            title="Different Title",  # Different title but same ID
            description="Test",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        task3 = Task(
            id=str(uuid.uuid4()),  # Different ID
            title="Test Task",
            description="Test",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        # Tasks with same ID should be equal
        assert task1 == task2
        # Tasks with different ID should not be equal
        assert task1 != task3
    
    def test_task_string_representation(self):
        """Test task string representation"""
        task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456",
            status="in_progress",
            priority="high"
        )
        
        str_repr = str(task)
        assert "Test Task" in str_repr
        assert "in_progress" in str_repr
        assert "high" in str_repr
    
    def test_task_dictionary_conversion(self):
        """Test converting task to dictionary"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456",
            status="todo",
            priority="medium",
            assignee="user123",
            labels=["test", "feature"]
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["id"] == task_id
        assert task_dict["title"] == "Test Task"
        assert task_dict["description"] == "Test Description"
        assert task_dict["project_id"] == "proj123"
        assert task_dict["git_branch_id"] == "branch456"
        assert task_dict["status"] == "todo"
        assert task_dict["priority"] == "medium"
        assert task_dict["assignee"] == "user123"
        assert task_dict["labels"] == ["test", "feature"]
        assert "created_at" in task_dict
        assert "updated_at" in task_dict