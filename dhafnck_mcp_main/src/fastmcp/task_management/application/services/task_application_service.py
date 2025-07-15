"""Task Application Service (task operations only)"""

from typing import Optional, Any

from ...application.dtos.task import (
    CreateTaskRequest,
    CreateTaskResponse,
    TaskResponse,
    UpdateTaskRequest,
    ListTasksRequest,
    TaskListResponse,
    SearchTasksRequest
)
from ...domain.exceptions.task_exceptions import TaskNotFoundError
from ...domain.repositories.task_repository import TaskRepository
from ..use_cases.create_task import CreateTaskUseCase
from ..use_cases.get_task import GetTaskUseCase
from ..use_cases.update_task import UpdateTaskUseCase
from ..use_cases.list_tasks import ListTasksUseCase
from ..use_cases.search_tasks import SearchTasksUseCase
from ..use_cases.delete_task import DeleteTaskUseCase
from ..use_cases.complete_task import CompleteTaskUseCase


class TaskApplicationService:
    """Application service for task CRUD, search, and completion"""
    def __init__(self, task_repository: TaskRepository, context_service: Optional[Any] = None):
        from ...infrastructure.repositories.hierarchical_context_repository_factory import HierarchicalContextRepositoryFactory
        from ...application.services.hierarchical_context_service import HierarchicalContextService
        self._task_repository = task_repository
        # Initialize hierarchical context service
        factory = HierarchicalContextRepositoryFactory()
        repository = factory.create_hierarchical_context_repository()
        self._hierarchical_context_service = HierarchicalContextService(repository=repository)
        self._context_service = context_service
        self._create_task_use_case = CreateTaskUseCase(task_repository)
        self._get_task_use_case = GetTaskUseCase(task_repository, context_service)
        self._update_task_use_case = UpdateTaskUseCase(task_repository)
        self._list_tasks_use_case = ListTasksUseCase(task_repository)
        self._search_tasks_use_case = SearchTasksUseCase(task_repository)
        self._delete_task_use_case = DeleteTaskUseCase(task_repository)
        self._complete_task_use_case = CompleteTaskUseCase(task_repository)

    async def create_task(self, request: CreateTaskRequest) -> CreateTaskResponse:
        response = self._create_task_use_case.execute(request)
        if getattr(response, 'success', False) and hasattr(response, 'task') and response.task:
            task = response.task
            # Create task context in hierarchical system
            self._hierarchical_context_service.create_context(
                level="task",
                context_id=str(task.id.value if hasattr(task.id, 'value') else task.id),
                data={
                    "task_data": {
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                        "assignees": task.assignees,
                        "labels": task.labels,
                        "estimated_effort": task.estimated_effort,
                        "due_date": task.due_date.isoformat() if task.due_date else None
                    }
                }
            )
        return response

    async def get_task(self, task_id: str, generate_rules: bool = True, force_full_generation: bool = False,
                      include_context: bool = False, user_id: str = "default_id", 
                      project_id: str = "", git_branch_name: str = "main") -> Optional[TaskResponse]:
        try:
            return await self._get_task_use_case.execute(
                task_id,
                generate_rules=generate_rules,
                force_full_generation=force_full_generation,
                include_context=include_context
            )
        except TaskNotFoundError:
            return None

    async def update_task(self, request: UpdateTaskRequest) -> Optional[TaskResponse]:
        response = self._update_task_use_case.execute(request)
        if getattr(response, 'success', False) and hasattr(response, 'task') and response.task:
            task = response.task
            # Update task context in hierarchical system
            self._hierarchical_context_service.update_context(
                level="task",
                context_id=str(task.id.value if hasattr(task.id, 'value') else task.id),
                changes={
                    "task_data": {
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
                        "assignees": task.assignees,
                        "labels": task.labels,
                        "estimated_effort": task.estimated_effort,
                        "due_date": task.due_date.isoformat() if task.due_date else None
                    }
                }
            )
        return response

    async def list_tasks(self, request: ListTasksRequest) -> TaskListResponse:
        return await self._list_tasks_use_case.execute(request)

    async def search_tasks(self, request: SearchTasksRequest) -> TaskListResponse:
        return await self._search_tasks_use_case.execute(request)

    async def delete_task(self, task_id: str, user_id: str = 'default_id', project_id: str = '', git_branch_name: str = 'main') -> bool:
        result = self._delete_task_use_case.execute(task_id)
        if result:
            # Delete task context from hierarchical system
            self._hierarchical_context_service.delete_context("task", task_id)
        return result

    async def complete_task(self, task_id: str) -> dict:
        return await self._complete_task_use_case.execute(task_id)

    async def get_all_tasks(self) -> TaskListResponse:
        request = ListTasksRequest()
        return await self.list_tasks(request)

    async def get_tasks_by_status(self, status: str) -> TaskListResponse:
        request = ListTasksRequest(status=status)
        return await self.list_tasks(request)

    async def get_tasks_by_assignee(self, assignee: str) -> TaskListResponse:
        request = ListTasksRequest(assignees=[assignee])
        return await self.list_tasks(request) 