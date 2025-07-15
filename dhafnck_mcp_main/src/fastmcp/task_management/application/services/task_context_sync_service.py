from typing import Optional, Any
import logging

from ...infrastructure.repositories.hierarchical_context_repository_factory import HierarchicalContextRepositoryFactory
from ...application.services.hierarchical_context_service import HierarchicalContextService
from ...domain.repositories.task_repository import TaskRepository
from ...domain.value_objects.task_id import TaskId
from ..use_cases.get_task import GetTaskUseCase

logger = logging.getLogger(__name__)


class TaskContextSyncService:
    """Application-level service that ensures a freshly-created or updated Task
    has an up-to-date Context and returns the complete TaskResponse (including
    context data).
    
    This keeps infrastructure-heavy orchestration out of facades / use-cases and
    out of the Domain layer while remaining easily testable.
    """

    def __init__(self, task_repository: TaskRepository, context_service: Optional[Any] = None):
        self._task_repository = task_repository
        # Initialize hierarchical context service
        factory = HierarchicalContextRepositoryFactory()
        repository = factory.create_hierarchical_context_repository()
        self._hierarchical_context_service = HierarchicalContextService(repository=repository)
        self._get_task_use_case = GetTaskUseCase(task_repository, context_service)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def sync_context_and_get_task(
        self,
        task_id: str,
        *,
        user_id: str = "default_id",
        project_id: str = "",
        git_branch_name: str = "main",
    ) -> Optional[Any]:
        """Ensure context exists for *task_id* and return TaskResponse with context.

        Returns None if the task cannot be found or any step fails. The caller
        can decide how to handle fallback behaviour.
        """
        try:
            # ------------------------------------------------------------------
            # 1. Reload domain task and create/update its context
            # ------------------------------------------------------------------
            task_id_obj = TaskId.from_string(task_id)
            domain_task = self._task_repository.find_by_id(task_id_obj)
            if domain_task is None:
                logger.warning("[TaskContextSyncService] Task %s not found while syncing context", task_id)
                return None

            # Create or update task context in hierarchical system
            task_id_str = str(domain_task.id.value if hasattr(domain_task.id, 'value') else domain_task.id)
            
            # Try to get existing context first
            context_result = self._hierarchical_context_service.get_context(
                level="task",
                context_id=task_id_str
            )
            
            # Prepare task data
            task_data = {
                "task_data": {
                    "title": domain_task.title,
                    "description": domain_task.description,
                    "status": domain_task.status.value if hasattr(domain_task.status, 'value') else str(domain_task.status),
                    "priority": domain_task.priority.value if hasattr(domain_task.priority, 'value') else str(domain_task.priority),
                    "assignees": domain_task.assignees,
                    "labels": domain_task.labels,
                    "estimated_effort": domain_task.estimated_effort,
                    "due_date": domain_task.due_date.isoformat() if domain_task.due_date else None
                }
            }
            
            if not context_result:
                # Create new context
                self._hierarchical_context_service.create_context(
                    level="task",
                    context_id=task_id_str,
                    data=task_data
                )
            else:
                # Update existing context
                self._hierarchical_context_service.update_context(
                    level="task",
                    context_id=task_id_str,
                    data=task_data
                )

            # ------------------------------------------------------------------
            # 2. Retrieve TaskResponse *with* context data
            # ------------------------------------------------------------------
            task_response = await self._get_task_use_case.execute(
                task_id,
                generate_rules=False,
                force_full_generation=False,
                include_context=True,
            )
            return task_response
        except Exception as exc:
            logger.error("[TaskContextSyncService] Failed to sync context for task %s: %s", task_id, exc)
            return None 