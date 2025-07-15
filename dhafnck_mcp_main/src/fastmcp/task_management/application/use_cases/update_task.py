"""Update Task Use Case"""

from typing import Optional, Union
import logging

from ...application.dtos.task import (
    UpdateTaskRequest,
    UpdateTaskResponse,
    TaskResponse
)

from ...domain import TaskRepository, TaskId, TaskStatus, Priority, TaskNotFoundError
from ...domain.events import TaskUpdated

logger = logging.getLogger(__name__)


class UpdateTaskUseCase:
    """Use case for updating an existing task"""
    
    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository
    
    def execute(self, request: UpdateTaskRequest) -> UpdateTaskResponse:
        """Execute the update task use case"""
        # Convert to domain value object with proper type handling
        domain_task_id = self._convert_to_task_id(request.task_id)
        
        # Find the task
        task = self._task_repository.find_by_id(domain_task_id)
        if not task:
            raise TaskNotFoundError(f"Task {request.task_id} not found")
        
        # Update task fields if provided
        if request.title is not None:
            task.update_title(request.title)
        
        if request.description is not None:
            task.update_description(request.description)
        
        if request.status is not None:
            new_status = TaskStatus(request.status)
            task.update_status(new_status)
        
        if request.priority is not None:
            new_priority = Priority(request.priority)
            task.update_priority(new_priority)
        
        if request.details is not None:
            task.update_details(request.details)
        
        if request.estimated_effort is not None:
            task.update_estimated_effort(request.estimated_effort)
        
        if request.assignees is not None:
            task.update_assignees(request.assignees)
        
        if request.labels is not None:
            task.update_labels(request.labels)
        
        if request.due_date is not None:
            task.update_due_date(request.due_date)
        
        # IMPORTANT: Set context_id LAST, after all other updates that might clear it
        if request.context_id is not None:
            logger.info(f"Setting context_id to: {request.context_id}")
            task.set_context_id(request.context_id)
            logger.info(f"Task context_id after set: {task.context_id}")
        
        # Save the updated task
        self._task_repository.save(task)
        
        # Check context_id after save
        logger.info(f"Task context_id after save: {task.context_id}")
        
        # Handle domain events
        events = task.get_events()
        for event in events:
            if isinstance(event, TaskUpdated):
                # Could trigger notifications, logging, etc.
                pass
        
        # Convert to response DTO
        task_response = TaskResponse.from_domain(task)
        return UpdateTaskResponse.success_response(task_response)
    
    def _convert_to_task_id(self, task_id: Union[str, int, TaskId]) -> TaskId:
        """Convert task_id to TaskId domain object"""
        if isinstance(task_id, TaskId):
            return task_id
        # Always convert to string and use from_string method
        return TaskId.from_string(str(task_id)) 