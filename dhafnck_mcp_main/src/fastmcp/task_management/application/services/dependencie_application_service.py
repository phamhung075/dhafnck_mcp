"""Dependencie Application Service"""

from typing import Any, Dict, TYPE_CHECKING

from ...application.dtos.dependency import (
    AddDependencyRequest,
    DependencyResponse
)

from ...domain import TaskRepository

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ..use_cases import (
        AddDependencyUseCase,
        RemoveDependencyUseCase,
        GetDependenciesUseCase,
        ClearDependenciesUseCase,
        GetBlockingTasksUseCase
    )

class DependencieApplicationService:
    """Application service for dependency operations"""
    def __init__(self, task_repository: TaskRepository):
        self._task_repository = task_repository
        # Lazy initialization of use cases to avoid circular imports
        self._add_dependency_use_case = None
        self._remove_dependency_use_case = None
        self._get_dependencies_use_case = None
        self._clear_dependencies_use_case = None
        self._get_blocking_tasks_use_case = None

    def add_dependency(self, request: AddDependencyRequest) -> DependencyResponse:
        if self._add_dependency_use_case is None:
            from ..use_cases.add_dependency import AddDependencyUseCase
            self._add_dependency_use_case = AddDependencyUseCase(self._task_repository)
        return self._add_dependency_use_case.execute(request)

    def remove_dependency(self, task_id: str, dependency_id: str) -> DependencyResponse:
        if self._remove_dependency_use_case is None:
            from ..use_cases.remove_dependency import RemoveDependencyUseCase
            self._remove_dependency_use_case = RemoveDependencyUseCase(self._task_repository)
        return self._remove_dependency_use_case.execute(task_id, dependency_id)

    def get_dependencies(self, task_id: str) -> Dict[str, Any]:
        if self._get_dependencies_use_case is None:
            from ..use_cases.get_dependencies import GetDependenciesUseCase
            self._get_dependencies_use_case = GetDependenciesUseCase(self._task_repository)
        return self._get_dependencies_use_case.execute(task_id)

    def clear_dependencies(self, task_id: str) -> DependencyResponse:
        if self._clear_dependencies_use_case is None:
            from ..use_cases.clear_dependencies import ClearDependenciesUseCase
            self._clear_dependencies_use_case = ClearDependenciesUseCase(self._task_repository)
        return self._clear_dependencies_use_case.execute(task_id)

    def get_blocking_tasks(self, task_id: str) -> Dict[str, Any]:
        if self._get_blocking_tasks_use_case is None:
            from ..use_cases.get_blocking_tasks import GetBlockingTasksUseCase
            self._get_blocking_tasks_use_case = GetBlockingTasksUseCase(self._task_repository)
        return self._get_blocking_tasks_use_case.execute(task_id) 