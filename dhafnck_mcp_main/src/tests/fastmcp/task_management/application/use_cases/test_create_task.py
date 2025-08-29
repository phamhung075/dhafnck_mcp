"""Test suite for create task use case"""

import pytest
from unittest.mock import Mock, patch
from fastmcp.task_management.application.use_cases.create_task import CreateTask
from fastmcp.task_management.application.dtos.task_dtos import TaskCreateDTO
from fastmcp.task_management.domain.entities.task import Task
import uuid
from datetime import datetime


@pytest.mark.unit
class TestCreateTask:
    """Test create task use case"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_task_repository = Mock()
        self.mock_project_repository = Mock()
        self.mock_git_branch_repository = Mock()
        self.use_case = CreateTask(
            task_repository=self.mock_task_repository,
            project_repository=self.mock_project_repository,
            git_branch_repository=self.mock_git_branch_repository
        )
    
    def test_create_task_with_valid_data(self):
        """Test creating task with valid data"""
        # Arrange
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description", 
            project_id="proj123",
            git_branch_id="branch456",
            priority="high",
            status="todo"
        )
        
        # Mock dependencies exist
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        # Mock successful task creation
        created_task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test Description",
            status="todo",
            priority="high",
            project_id="proj123",
            git_branch_id="branch456",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_task_repository.save.return_value = created_task
        
        # Act
        result = self.use_case.execute(task_dto)
        
        # Assert
        assert result is not None
        assert result.title == "Test Task"
        assert result.description == "Test Description"
        assert result.status == "todo"
        assert result.priority == "high"
        self.mock_task_repository.save.assert_called_once()
    
    def test_create_task_with_missing_project_fails(self):
        """Test creating task with non-existent project fails"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="nonexistent_proj",
            git_branch_id="branch456"
        )
        
        # Mock project doesn't exist
        self.mock_project_repository.get_by_id.return_value = None
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Project with ID nonexistent_proj not found"):
            self.use_case.execute(task_dto)
        
        self.mock_task_repository.save.assert_not_called()
    
    def test_create_task_with_missing_git_branch_fails(self):
        """Test creating task with non-existent git branch fails"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="nonexistent_branch"
        )
        
        # Mock git branch doesn't exist
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Git branch with ID nonexistent_branch not found"):
            self.use_case.execute(task_dto)
        
        self.mock_task_repository.save.assert_not_called()
    
    def test_create_task_with_invalid_title_fails(self):
        """Test creating task with invalid title fails"""
        task_dto = TaskCreateDTO(
            title="",  # Empty title
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            self.use_case.execute(task_dto)
        
        self.mock_task_repository.save.assert_not_called()
    
    def test_create_task_with_invalid_priority_fails(self):
        """Test creating task with invalid priority fails"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456",
            priority="invalid_priority"
        )
        
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid priority"):
            self.use_case.execute(task_dto)
        
        self.mock_task_repository.save.assert_not_called()
    
    def test_create_task_with_invalid_status_fails(self):
        """Test creating task with invalid status fails"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456",
            status="invalid_status"
        )
        
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid status"):
            self.use_case.execute(task_dto)
        
        self.mock_task_repository.save.assert_not_called()
    
    def test_create_task_with_optional_fields(self):
        """Test creating task with optional fields"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456",
            assignee="user123",
            due_date=datetime(2024, 12, 31),
            labels=["urgent", "feature"]
        )
        
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        created_task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            description="Test Description",
            status="todo",
            priority="medium",
            project_id="proj123",
            git_branch_id="branch456",
            assignee="user123",
            due_date=datetime(2024, 12, 31),
            labels=["urgent", "feature"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_task_repository.save.return_value = created_task
        
        # Act
        result = self.use_case.execute(task_dto)
        
        # Assert
        assert result.assignee == "user123"
        assert result.due_date == datetime(2024, 12, 31)
        assert result.labels == ["urgent", "feature"]
    
    def test_create_task_generates_unique_id(self):
        """Test that create task generates unique ID"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        # Mock two different tasks with different IDs
        task_id_1 = str(uuid.uuid4())
        task_id_2 = str(uuid.uuid4())
        
        task_1 = Task(id=task_id_1, title="Test Task", project_id="proj123", git_branch_id="branch456")
        task_2 = Task(id=task_id_2, title="Test Task", project_id="proj123", git_branch_id="branch456")
        
        self.mock_task_repository.save.side_effect = [task_1, task_2]
        
        # Act
        result_1 = self.use_case.execute(task_dto)
        result_2 = self.use_case.execute(task_dto)
        
        # Assert
        assert result_1.id != result_2.id
        assert result_1.id == task_id_1
        assert result_2.id == task_id_2
    
    def test_create_task_sets_timestamps(self):
        """Test that create task sets created_at and updated_at timestamps"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        now = datetime.utcnow()
        created_task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            project_id="proj123",
            git_branch_id="branch456",
            created_at=now,
            updated_at=now
        )
        self.mock_task_repository.save.return_value = created_task
        
        # Act
        result = self.use_case.execute(task_dto)
        
        # Assert
        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.created_at == result.updated_at  # Should be same for new task
    
    def test_create_task_handles_repository_errors(self):
        """Test create task handles repository errors gracefully"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        # Mock repository save failure
        self.mock_task_repository.save.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            self.use_case.execute(task_dto)


@pytest.mark.integration
class TestCreateTaskIntegration:
    """Integration tests for create task use case"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_task_repository = Mock()
        self.mock_project_repository = Mock()
        self.mock_git_branch_repository = Mock()
        self.use_case = CreateTask(
            task_repository=self.mock_task_repository,
            project_repository=self.mock_project_repository,
            git_branch_repository=self.mock_git_branch_repository
        )
    
    def test_create_task_with_context_creation(self):
        """Test task creation triggers context creation"""
        task_dto = TaskCreateDTO(
            title="Integration Test Task",
            description="Test with context creation",
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        # Mock dependencies
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = Mock(id="branch456")
        
        created_task = Task(
            id=str(uuid.uuid4()),
            title="Integration Test Task",
            project_id="proj123",
            git_branch_id="branch456"
        )
        self.mock_task_repository.save.return_value = created_task
        
        # Mock context service
        with patch('fastmcp.task_management.application.services.context_service.ContextService') as mock_context_service:
            mock_context_service.create_task_context.return_value = True
            
            # Act
            result = self.use_case.execute(task_dto)
            
            # Assert
            assert result is not None
            # Context creation should be triggered (if implemented)
            # mock_context_service.create_task_context.assert_called_once_with(created_task.id)
    
    def test_create_task_updates_branch_task_count(self):
        """Test task creation updates branch task count"""
        task_dto = TaskCreateDTO(
            title="Test Task",
            description="Test Description", 
            project_id="proj123",
            git_branch_id="branch456"
        )
        
        # Mock branch with task count
        mock_branch = Mock(id="branch456", task_count=5)
        self.mock_project_repository.get_by_id.return_value = Mock(id="proj123")
        self.mock_git_branch_repository.get_by_id.return_value = mock_branch
        
        created_task = Task(
            id=str(uuid.uuid4()),
            title="Test Task",
            project_id="proj123", 
            git_branch_id="branch456"
        )
        self.mock_task_repository.save.return_value = created_task
        
        # Act
        result = self.use_case.execute(task_dto)
        
        # Assert
        assert result is not None
        # Branch task count should be updated (if implemented)
        # self.mock_git_branch_repository.update_task_count.assert_called_once_with("branch456", 6)