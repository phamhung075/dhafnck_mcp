"""Test suite for task application facade"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.dtos.task_dtos import TaskCreateDTO, TaskUpdateDTO
import uuid


@pytest.mark.unit
class TestTaskApplicationFacade:
    """Test task application facade functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.facade = TaskApplicationFacade()
    
    def test_facade_initialization(self):
        """Test facade initializes correctly"""
        assert self.facade is not None
    
    @pytest.mark.asyncio
    async def test_create_task_with_valid_data(self):
        """Test task creation with valid data"""
        task_data = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            project_id="proj123",
            git_branch_id="branch456",
            priority="high",
            status="todo"
        )
        
        expected_task = {
            "id": str(uuid.uuid4()),
            "title": "Test Task",
            "description": "Test Description",
            "status": "todo",
            "priority": "high"
        }
        
        with patch.object(self.facade, '_create_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = expected_task
            
            result = await self.facade.create_task(task_data)
            
        assert result == expected_task
        mock_use_case.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_task_with_valid_data(self):
        """Test task update with valid data"""
        task_id = str(uuid.uuid4())
        update_data = TaskUpdateDTO(
            title="Updated Task",
            description="Updated Description",
            status="in_progress"
        )
        
        expected_task = {
            "id": task_id,
            "title": "Updated Task",
            "description": "Updated Description",
            "status": "in_progress"
        }
        
        with patch.object(self.facade, '_update_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = expected_task
            
            result = await self.facade.update_task(task_id, update_data)
            
        assert result == expected_task
        mock_use_case.execute.assert_called_once_with(task_id, update_data)
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self):
        """Test getting task by ID"""
        task_id = str(uuid.uuid4())
        expected_task = {
            "id": task_id,
            "title": "Test Task",
            "status": "todo"
        }
        
        with patch.object(self.facade, '_get_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = expected_task
            
            result = await self.facade.get_task(task_id)
            
        assert result == expected_task
        mock_use_case.execute.assert_called_once_with(task_id)
    
    @pytest.mark.asyncio
    async def test_delete_task_by_id(self):
        """Test deleting task by ID"""
        task_id = str(uuid.uuid4())
        
        with patch.object(self.facade, '_delete_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = True
            
            result = await self.facade.delete_task(task_id)
            
        assert result is True
        mock_use_case.execute.assert_called_once_with(task_id)
    
    @pytest.mark.asyncio
    async def test_complete_task(self):
        """Test completing a task"""
        task_id = str(uuid.uuid4())
        completion_summary = "Task completed successfully"
        
        expected_task = {
            "id": task_id,
            "status": "completed",
            "completion_summary": completion_summary
        }
        
        with patch.object(self.facade, '_complete_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = expected_task
            
            result = await self.facade.complete_task(task_id, completion_summary)
            
        assert result == expected_task
        mock_use_case.execute.assert_called_once_with(task_id, completion_summary)
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self):
        """Test listing tasks with filters"""
        filters = {
            "status": "todo",
            "priority": "high",
            "project_id": "proj123"
        }
        
        expected_tasks = [
            {"id": str(uuid.uuid4()), "title": "Task 1", "status": "todo"},
            {"id": str(uuid.uuid4()), "title": "Task 2", "status": "todo"}
        ]
        
        with patch.object(self.facade, '_list_tasks_use_case') as mock_use_case:
            mock_use_case.execute.return_value = expected_tasks
            
            result = await self.facade.list_tasks(**filters)
            
        assert result == expected_tasks
        mock_use_case.execute.assert_called_once_with(**filters)
    
    @pytest.mark.asyncio
    async def test_search_tasks(self):
        """Test searching tasks by query"""
        query = "test search"
        expected_results = [
            {"id": str(uuid.uuid4()), "title": "Test Task 1"},
            {"id": str(uuid.uuid4()), "title": "Another Test Task"}
        ]
        
        with patch.object(self.facade, '_search_tasks_use_case') as mock_use_case:
            mock_use_case.execute.return_value = expected_results
            
            result = await self.facade.search_tasks(query)
            
        assert result == expected_results
        mock_use_case.execute.assert_called_once_with(query)
    
    @pytest.mark.asyncio
    async def test_get_next_task(self):
        """Test getting next task for assignment"""
        git_branch_id = str(uuid.uuid4())
        expected_task = {
            "id": str(uuid.uuid4()),
            "title": "Next Task",
            "priority": "high"
        }
        
        with patch.object(self.facade, '_next_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = expected_task
            
            result = await self.facade.get_next_task(git_branch_id)
            
        assert result == expected_task
        mock_use_case.execute.assert_called_once_with(git_branch_id)
    
    @pytest.mark.asyncio
    async def test_facade_handles_validation_errors(self):
        """Test facade handles validation errors appropriately"""
        invalid_task_data = TaskCreateDTO(
            title="",  # Invalid empty title
            description="Test",
            project_id="proj123"
        )
        
        with patch.object(self.facade, '_create_task_use_case') as mock_use_case:
            mock_use_case.execute.side_effect = ValueError("Title cannot be empty")
            
            with pytest.raises(ValueError, match="Title cannot be empty"):
                await self.facade.create_task(invalid_task_data)
    
    @pytest.mark.asyncio
    async def test_facade_handles_not_found_errors(self):
        """Test facade handles not found errors appropriately"""
        non_existent_id = str(uuid.uuid4())
        
        with patch.object(self.facade, '_get_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = None
            
            result = await self.facade.get_task(non_existent_id)
            
        assert result is None
    
    def test_facade_dependency_injection(self):
        """Test facade properly initializes dependencies"""
        with patch('fastmcp.task_management.application.use_cases.create_task.CreateTask') as mock_create, \
             patch('fastmcp.task_management.application.use_cases.update_task.UpdateTask') as mock_update:
            
            facade = TaskApplicationFacade()
            
            # Verify use cases are initialized
            assert hasattr(facade, '_create_task_use_case')
            assert hasattr(facade, '_update_task_use_case')


@pytest.mark.integration
class TestTaskApplicationFacadeIntegration:
    """Integration tests for task application facade"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.facade = TaskApplicationFacade()
    
    @pytest.mark.asyncio
    async def test_task_lifecycle_integration(self):
        """Test complete task lifecycle through facade"""
        # Create task
        task_data = TaskCreateDTO(
            title="Integration Test Task",
            description="Test task lifecycle",
            project_id="test_project",
            git_branch_id="test_branch"
        )
        
        with patch.object(self.facade, '_create_task_use_case') as mock_create, \
             patch.object(self.facade, '_update_task_use_case') as mock_update, \
             patch.object(self.facade, '_complete_task_use_case') as mock_complete:
            
            # Mock task creation
            created_task = {
                "id": str(uuid.uuid4()),
                "title": "Integration Test Task",
                "status": "todo"
            }
            mock_create.execute.return_value = created_task
            
            # Mock task update
            updated_task = {
                **created_task,
                "status": "in_progress"
            }
            mock_update.execute.return_value = updated_task
            
            # Mock task completion
            completed_task = {
                **updated_task,
                "status": "completed"
            }
            mock_complete.execute.return_value = completed_task
            
            # Execute lifecycle
            task = await self.facade.create_task(task_data)
            assert task["status"] == "todo"
            
            updated = await self.facade.update_task(
                task["id"], 
                TaskUpdateDTO(status="in_progress")
            )
            assert updated["status"] == "in_progress"
            
            completed = await self.facade.complete_task(task["id"], "Test completed")
            assert completed["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_facade_error_propagation(self):
        """Test facade properly propagates errors from use cases"""
        task_id = str(uuid.uuid4())
        
        with patch.object(self.facade, '_get_task_use_case') as mock_use_case:
            mock_use_case.execute.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception, match="Database connection failed"):
                await self.facade.get_task(task_id)
    
    @pytest.mark.asyncio
    async def test_facade_performance_with_multiple_operations(self):
        """Test facade performance with multiple concurrent operations"""
        import asyncio
        import time
        
        task_ids = [str(uuid.uuid4()) for _ in range(10)]
        
        with patch.object(self.facade, '_get_task_use_case') as mock_use_case:
            mock_use_case.execute.return_value = {"id": "test", "title": "test"}
            
            start_time = time.time()
            tasks = await asyncio.gather(*[
                self.facade.get_task(task_id) for task_id in task_ids
            ])
            end_time = time.time()
            
        # All operations should complete
        assert len(tasks) == 10
        # Should be reasonably fast (< 1 second for 10 operations)
        assert (end_time - start_time) < 1.0