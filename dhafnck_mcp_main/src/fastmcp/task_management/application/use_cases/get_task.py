"""Get Task Use Case"""

import logging
from typing import Optional, Union, Any
from datetime import datetime

from ...application.dtos.task import TaskResponse
from ...application.dtos.context import GetContextRequest

from ...domain import TaskRepository, TaskId
from ...domain.exceptions.task_exceptions import TaskNotFoundError
from ...domain.events import TaskRetrieved
from ...infrastructure.services.agent_doc_generator import generate_agent_docs, generate_docs_for_assignees

logger = logging.getLogger(__name__)


class GetTaskUseCase:
    """Use case for retrieving a task by ID with optional context data"""
    
    def __init__(self, task_repository: TaskRepository, context_service: Optional[Any] = None):
        """
        Initialize the GetTaskUseCase with required dependencies.
        
        Args:
            task_repository: Repository for task data access
            context_service: Optional context service for fetching context data
        """
        self._task_repository = task_repository
        self._context_service = context_service
    
    async def execute(self, task_id: str, generate_rules: bool = True, force_full_generation: bool = False,
                     include_context: bool = False) -> Optional[TaskResponse]:
        """
        Execute the get task use case following clean relationship chain.
        
        Args:
            task_id: The ID of the task to retrieve (contains all necessary context via relationships)
            generate_rules: Whether to generate agent rules
            force_full_generation: Whether to force full rule generation
            include_context: Whether to include full context data
            
        Returns:
            TaskResponse with optional context data or None if task not found
            
        Raises:
            TaskNotFoundError: If the task is not found
        """
        try:
            # Get the task from repository
            domain_task_id = TaskId(task_id)
            task = self._task_repository.find_by_id(domain_task_id)
            
            if not task:
                raise TaskNotFoundError(f"Task with ID {task_id} not found")
            
            # Generate agent documentation if requested
            if generate_rules:
                generate_docs_for_assignees(task.assignees, clear_all=force_full_generation)
            
            # Fetch context data if requested
            context_data = None
            
            if include_context:
                try:
                    # Try to get context using only task_id (follows clean relationship chain)
                    if self._context_service:
                        # Use task_id only - the repository will derive other context from task relationships
                        get_context_request = GetContextRequest(task_id=task_id)
                        
                        context_response = await self._context_service.get_context(get_context_request)
                        
                        if context_response.success and context_response.context:
                            # Convert context to dict if it has to_dict method
                            if hasattr(context_response.context, 'to_dict'):
                                context_data = context_response.context.to_dict()
                            else:
                                context_data = context_response.context
                            logger.debug(f"Context data fetched for task {task_id}")
                        elif context_response.success and context_response.data:
                            # Fallback to data field if context field is not present
                            context_data = context_response.data
                            logger.debug(f"Context data fetched for task {task_id} from data field")
                        else:
                            logger.debug(f"No context data found for task {task_id}")
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch context data for task {task_id}: {e}")
            
            # Publish domain event
            _event = TaskRetrieved(
                task_id=task.id,
                task_data=task.to_dict() if hasattr(task, 'to_dict') else {},
                retrieved_at=datetime.now()
            )
            # Note: Event publishing would be handled by an event dispatcher in a full implementation
            
            # Convert domain task to response DTO with context data
            return TaskResponse.from_domain(task, context_data=context_data)
            
        except TaskNotFoundError:
            logger.warning(f"Task not found: {task_id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving task {task_id}: {e}")
            raise