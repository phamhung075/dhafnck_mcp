"""Subtask Application Service"""

from typing import Any, Dict

from ...application.dtos.subtask import (
    AddSubtaskRequest,
    UpdateSubtaskRequest,
    SubtaskResponse
)

from ...domain import TaskRepository
from ...domain.repositories.subtask_repository import SubtaskRepository
from ..use_cases.add_subtask import AddSubtaskUseCase
from ..use_cases.update_subtask import UpdateSubtaskUseCase
from ..use_cases.remove_subtask import RemoveSubtaskUseCase
from ..use_cases.complete_subtask import CompleteSubtaskUseCase
from ..use_cases.get_subtasks import GetSubtasksUseCase
from ..use_cases.get_subtask import GetSubtaskUseCase


class SubtaskApplicationService:
    """Application service for subtask operations with DDD support"""
    def __init__(self, task_repository: TaskRepository, subtask_repository: SubtaskRepository = None):
        self._task_repository = task_repository
        self._subtask_repository = subtask_repository
        
        # Initialize use cases with both repositories
        self._add_subtask_use_case = AddSubtaskUseCase(task_repository, subtask_repository)
        self._update_subtask_use_case = UpdateSubtaskUseCase(task_repository, subtask_repository)
        self._remove_subtask_use_case = RemoveSubtaskUseCase(task_repository, subtask_repository)
        self._complete_subtask_use_case = CompleteSubtaskUseCase(task_repository, subtask_repository)
        self._get_subtasks_use_case = GetSubtasksUseCase(task_repository, subtask_repository)
        self._get_subtask_use_case = GetSubtaskUseCase(task_repository, subtask_repository)

    def add_subtask(self, request: AddSubtaskRequest) -> SubtaskResponse:
        return self._add_subtask_use_case.execute(request)

    def remove_subtask(self, task_id: str, id: str) -> Dict[str, Any]:
        return self._remove_subtask_use_case.execute(task_id, id)

    def update_subtask(self, request: UpdateSubtaskRequest) -> SubtaskResponse:
        return self._update_subtask_use_case.execute(request)

    def complete_subtask(self, task_id: str, id: str) -> Dict[str, Any]:
        return self._complete_subtask_use_case.execute(task_id, id)

    def get_subtasks(self, task_id: str) -> Dict[str, Any]:
        return self._get_subtasks_use_case.execute(task_id)

    def get_subtask(self, task_id: str, id: str) -> Dict[str, Any]:
        """Get a single subtask by ID"""
        return self._get_subtask_use_case.execute(task_id, id)

    def manage_subtasks(self, task_id: str, action: str, subtask_data: dict) -> dict:
        """Manage subtasks with enhanced DDD support"""
        if action in ["add_subtask", "add"]:
            request = AddSubtaskRequest(
                task_id=task_id,
                title=subtask_data.get("title", ""),
                description=subtask_data.get("description", ""),
                assignee=subtask_data.get("assignee", "")
            )
            return self.add_subtask(request).__dict__
        elif action in ["complete_subtask", "complete"]:
            id = subtask_data.get("id")
            if id is None:
                raise ValueError("id is required for completing a subtask")
            return self.complete_subtask(task_id, id)
        elif action in ["update_subtask", "update"]:
            request = UpdateSubtaskRequest(
                task_id=task_id,
                id=subtask_data.get("id"),
                title=subtask_data.get("title"),
                description=subtask_data.get("description"),
                completed=subtask_data.get("completed"),
                assignee=subtask_data.get("assignee")
            )
            return self.update_subtask(request).__dict__
        elif action in ["remove_subtask", "remove"]:
            id = subtask_data.get("id")
            if id is None:
                raise ValueError("id is required for removing a subtask")
            return self.remove_subtask(task_id, id)
        elif action in ["get_subtask", "get"]:
            id = subtask_data.get("id")
            if id is None:
                raise ValueError("id is required for getting a subtask")
            return self.get_subtask(task_id, id)
        elif action in ["list_subtasks", "list"]:
            return self.get_subtasks(task_id)
        else:
            raise ValueError(f"Unknown subtask action: {action}") 