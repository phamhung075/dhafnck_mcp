"""
Debug test to inspect the actual context update structure
"""

import pytest
from unittest.mock import Mock, patch
from fastmcp.task_management.application.use_cases.complete_task import CompleteTaskUseCase
from fastmcp.task_management.domain.repositories.task_repository import TaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from datetime import datetime
import uuid


class TestContextStructureDebug:
    """Debug test to inspect actual context structure"""

    @pytest.fixture
    def mock_task_repository(self):
        repo = Mock(spec=TaskRepository)
        return repo

    @pytest.fixture
    def mock_task(self):
        task = Mock(spec=Task)
        task.task_id = str(uuid.uuid4())
        task.git_branch_id = str(uuid.uuid4())
        task.title = "Test Task"
        task.status = TaskStatus.todo()
        task.priority = Priority.medium()
        task.created_at = datetime.now()
        task.get_subtask_progress.return_value = {"total": 0, "completed": 0}
        
        def mock_complete_task(completion_summary, context_updated_at=None):
            task.status = TaskStatus.done()
            task.completion_summary = completion_summary
            return task
        
        task.complete_task = mock_complete_task
        return task

    @pytest.fixture
    def complete_task_use_case(self, mock_task_repository):
        return CompleteTaskUseCase(mock_task_repository)

    def test_debug_context_update_structure(self, complete_task_use_case, mock_task_repository, mock_task):
        """Debug test to see the actual context update structure"""
        # Arrange
        mock_task_repository.find_by_id.return_value = mock_task
        mock_task_repository.save.return_value = mock_task
        
        completion_summary = "Task completed"
        testing_notes = "Tests passed"
        
        # Mock the UnifiedContextFacade to capture the context update
        with patch('fastmcp.task_management.application.factories.unified_context_facade_factory.UnifiedContextFacadeFactory') as mock_factory:
            mock_facade = Mock()
            mock_factory.return_value.create_facade.return_value = mock_facade
            
            # Make get_context return a proper mock structure
            mock_facade.get_context.return_value = {"success": True, "context": {"data": {}}}
            
            # Execute
            result = complete_task_use_case.execute(
                task_id=mock_task.task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            
            # Debug: Print the actual call arguments
            print("\n=== CONTEXT UPDATE DEBUG ===")
            print(f"update_context called: {mock_facade.update_context.called}")
            
            if mock_facade.update_context.called:
                call_args = mock_facade.update_context.call_args
                print(f"Call args: {call_args}")
                print(f"Positional args: {call_args[0] if call_args[0] else 'None'}")
                print(f"Keyword args: {call_args[1] if call_args[1] else 'None'}")
                
                if call_args[1] and "data" in call_args[1]:
                    context_data = call_args[1]["data"]
                    print(f"Context data structure: {context_data}")
                    
                    if "progress" in context_data:
                        print(f"Progress data: {context_data['progress']}")
                        
                        progress_data = context_data["progress"]
                        print(f"Has current_session_summary: {'current_session_summary' in progress_data}")
                        print(f"Has completion_percentage: {'completion_percentage' in progress_data}")
                        
                        if "current_session_summary" in progress_data:
                            print(f"current_session_summary value: {progress_data['current_session_summary']}")
                        if "completion_percentage" in progress_data:
                            print(f"completion_percentage value: {progress_data['completion_percentage']}")
                            
            print("=== END DEBUG ===\n")
            
            # Simple assertion to verify the test runs
            assert result["success"] is True