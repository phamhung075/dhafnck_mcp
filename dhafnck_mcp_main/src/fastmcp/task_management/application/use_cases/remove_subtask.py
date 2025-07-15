"""Remove Subtask Use Case"""

from typing import Union, Any, Dict
from ...domain import TaskRepository, TaskId, TaskNotFoundError
from ...domain.repositories.subtask_repository import SubtaskRepository

class RemoveSubtaskUseCase:
    def __init__(self, task_repository: TaskRepository, subtask_repository: SubtaskRepository = None):
        self._task_repository = task_repository
        self._subtask_repository = subtask_repository

    def execute(self, task_id: Union[str, int], id: Union[str, int]) -> Dict[str, Any]:
        subtask = self._subtask_repository.find_by_id(id)
        if not subtask:
            raise ValueError(f"Subtask {id} not found in task {task_id}")
        success = self._subtask_repository.remove_subtask(task_id, id)
        return {
            "success": success,
            "subtask": {"id": str(id)},
        }

    def _convert_to_task_id(self, task_id: Union[str, int]) -> TaskId:
        if isinstance(task_id, int):
            return TaskId.from_int(task_id)
        else:
            return TaskId.from_string(str(task_id)) 