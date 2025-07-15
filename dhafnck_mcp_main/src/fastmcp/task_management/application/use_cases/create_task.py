"""Create Task Use Case"""

from typing import Optional

from ...application.dtos.task import (
    CreateTaskRequest,
    CreateTaskResponse,
    TaskResponse
)
from ...domain.entities.task import Task
from ...domain.repositories.task_repository import TaskRepository
from ...domain.value_objects import TaskStatus, Priority
from ...domain.value_objects.task_status import TaskStatusEnum
from ...domain.value_objects.priority import PriorityLevel
from ...domain.events import TaskCreated


class CreateTaskUseCase:
    """Use case for creating a new task"""
    
    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository
    
    def execute(self, request: CreateTaskRequest) -> CreateTaskResponse:
        """Execute the create task use case following clean relationship chain"""
        try:
            # Generate new task ID
            task_id = self._task_repository.get_next_id()
            
            # Create domain value objects. Let ValueError propagate for invalid inputs.
            status = TaskStatus(request.status or TaskStatusEnum.TODO.value)
            priority = Priority(request.priority or PriorityLevel.MEDIUM.label)
            
            # Handle very long content gracefully by truncating
            title = request.title
            if title and len(title) > 200:
                title = title[:200]
            
            description = request.description
            if description and len(description) > 1000:
                description = description[:1000]           

            
            # Create domain entity using git_branch_id from request (follows clean relationship chain)
            task = Task.create(
                id=task_id,
                title=title,
                description=description,
                status=status,
                priority=priority,
                git_branch_id=request.git_branch_id,  # Use git_branch_id instead of project_id
                details=request.details,
                estimated_effort=request.estimated_effort,
                assignees=request.assignees,
                labels=request.labels,
                due_date=request.due_date,
            )
            
            # Add dependencies if provided
            if hasattr(request, 'dependencies') and request.dependencies:
                from ...domain.value_objects.task_id import TaskId
                for dep_id in request.dependencies:
                    if dep_id and dep_id.strip():
                        try:
                            task.add_dependency(TaskId(dep_id))
                        except ValueError as e:
                            # Log but don't fail creation if dependency is invalid
                            import logging
                            logging.warning(f"Skipping invalid dependency {dep_id}: {e}")
            
            # Create the task (with duplicate detection)
            self._task_repository.create_new(task)
            
            # Handle domain events
            events = task.get_events()
            for event in events:
                if isinstance(event, TaskCreated):
                    # Could trigger notifications, logging, etc.
                    pass
            
            # Convert to response DTO
            task_response = TaskResponse.from_domain(task)
            return CreateTaskResponse.success_response(task_response)
            
        except ValueError as e:
            # Re-raise validation errors so they can be handled by the caller
            raise e
        except Exception as e:
            # Handle any other errors during task creation
            import logging
            import traceback
            logging.error(f"Failed to create task: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return CreateTaskResponse.error_response(f"Failed to create task: {str(e)}") 