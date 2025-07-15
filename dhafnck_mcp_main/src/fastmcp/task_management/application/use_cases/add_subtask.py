"""Add Subtask Use Case"""

from typing import Union
from ...application.dtos.subtask.add_subtask_request import AddSubtaskRequest
from ...application.dtos.subtask.subtask_response import SubtaskResponse

from ...domain import TaskRepository, TaskId, TaskNotFoundError
from ...domain.repositories.subtask_repository import SubtaskRepository
from ...domain.entities.subtask import Subtask
import logging

class AddSubtaskUseCase:
    def __init__(self, task_repository: TaskRepository, subtask_repository: SubtaskRepository = None):
        self._task_repository = task_repository
        self._subtask_repository = subtask_repository

    def execute(self, request: AddSubtaskRequest) -> SubtaskResponse:
        task_id = self._convert_to_task_id(request.task_id)
        task = self._task_repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {request.task_id} not found")
        
        # Create subtask using the new domain entity
        if self._subtask_repository:
            # Use dedicated subtask repository if available
            subtask_id = self._subtask_repository.get_next_id(task_id)
            subtask = Subtask.create(
                id=subtask_id,
                title=request.title,
                description=request.description,
                parent_task_id=task_id,
                assignees=request.assignees
            )
            self._subtask_repository.create_new(subtask)
            added_subtask = subtask.to_dict()
        else:
            # Fallback to existing task entity method for backward compatibility
            subtask = {
                "title": request.title,
                "description": request.description,
                "completed": False,
                "assignees": request.assignees
            }
            added_subtask = task.add_subtask(subtask)
            self._task_repository.save(task)
        
        logging.debug(f"[AddSubtask] Creating subtask for task_id={task_id} (following clean relationship chain)")
        
        return SubtaskResponse(
            task_id=str(request.task_id),
            subtask=added_subtask,
            progress=task.get_subtask_progress()
        )

    def _convert_to_task_id(self, task_id: Union[str, int]) -> TaskId:
        if isinstance(task_id, int):
            return TaskId.from_int(task_id)
        else:
            return TaskId.from_string(str(task_id)) 