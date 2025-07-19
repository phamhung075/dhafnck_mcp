"""Update Subtask Use Case"""

import logging
from typing import Union
from ...application.dtos.subtask import (
    UpdateSubtaskRequest,
    SubtaskResponse
)

from ...domain import TaskRepository, TaskId, TaskNotFoundError
from ...domain.repositories.subtask_repository import SubtaskRepository
from ...domain.entities.subtask import Subtask
from ...domain.value_objects.priority import Priority
from ...domain.value_objects.task_status import TaskStatus

logger = logging.getLogger(__name__)


class UpdateSubtaskUseCase:
    def __init__(self, task_repository: TaskRepository, subtask_repository: SubtaskRepository = None):
        self._task_repository = task_repository
        self._subtask_repository = subtask_repository

    def execute(self, request: UpdateSubtaskRequest) -> SubtaskResponse:
        task_id = self._convert_to_task_id(request.task_id)
        task = self._task_repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {request.task_id} not found")
        
        # Use dedicated subtask repository if available
        if self._subtask_repository:
            subtask = self._subtask_repository.find_by_id(request.id)
            if not subtask:
                raise ValueError(f"Subtask {request.id} not found in task {request.task_id}")
            
            # Update subtask using domain entity methods
            if request.title is not None:
                subtask.update_title(request.title)
            if request.description is not None:
                subtask.update_description(request.description)
            if request.status is not None:
                if request.status == "done":
                    subtask.complete()
                elif request.status == "todo":
                    subtask.reopen()
                else:
                    # For other statuses, update directly
                    status_obj = TaskStatus.from_string(request.status)
                    subtask.update_status(status_obj)
            if request.priority is not None:
                priority_obj = Priority.from_string(request.priority)
                subtask.update_priority(priority_obj)
            if request.assignees is not None:
                subtask.update_assignees(request.assignees)
            if request.progress_percentage is not None:
                # Update subtask progress percentage (0-100)
                if hasattr(subtask, 'progress_percentage'):
                    subtask.progress_percentage = request.progress_percentage
                else:
                    # Add progress_percentage as an attribute if it doesn't exist
                    setattr(subtask, 'progress_percentage', request.progress_percentage)
            
            self._subtask_repository.save(subtask)
            updated_subtask = subtask.to_dict()
            
            # Update parent task progress
            self._update_parent_task_progress(str(request.task_id))
        else:
            # Fallback to existing task entity method for backward compatibility
            updates = {}
            if request.title is not None:
                updates["title"] = request.title
            if request.description is not None:
                updates["description"] = request.description
            if request.status is not None:
                updates["status"] = request.status
            if request.priority is not None:
                updates["priority"] = request.priority
            if request.assignees is not None:
                updates["assignees"] = request.assignees
            
            success = task.update_subtask(request.id, updates)
            if not success:
                raise ValueError(f"Subtask {request.id} not found in task {request.task_id}")
            self._task_repository.save(task)
            updated_subtask = task.get_subtask(request.id)
        
        return SubtaskResponse(
            task_id=str(request.task_id),
            subtask=updated_subtask,
            progress=task.get_subtask_progress()
        )

    def _convert_to_task_id(self, task_id: Union[str, int]) -> TaskId:
        if isinstance(task_id, int):
            return TaskId.from_int(task_id)
        else:
            return TaskId.from_string(str(task_id))
    
    def _update_parent_task_progress(self, task_id: str) -> None:
        """Update parent task progress based on subtask completion."""
        try:
            from ..services.task_progress_service import TaskProgressService
            progress_service = TaskProgressService(self._task_repository, self._subtask_repository)
            progress_service.update_task_progress_from_subtasks(task_id)
        except Exception as e:
            logger.warning(f"Failed to update parent task progress: {e}") 