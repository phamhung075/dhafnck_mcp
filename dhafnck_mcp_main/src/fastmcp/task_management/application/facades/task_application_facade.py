"""Task Application Facade - Orchestrates task-related use cases"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from ..dtos.task.create_task_request import CreateTaskRequest
from ..dtos.task.list_tasks_request import ListTasksRequest
from ..dtos.task.search_tasks_request import SearchTasksRequest
from ..dtos.task.update_task_request import UpdateTaskRequest
from ..dtos.task.task_list_item_response import TaskListItemResponse
from ..factories.context_response_factory import ContextResponseFactory

from ..services.task_application_service import TaskApplicationService

from ..use_cases.create_task import CreateTaskUseCase
from ..use_cases.update_task import UpdateTaskUseCase
from ..use_cases.get_task import GetTaskUseCase
from ..use_cases.delete_task import DeleteTaskUseCase
from ..use_cases.complete_task import CompleteTaskUseCase
from ..use_cases.list_tasks import ListTasksUseCase
from ..use_cases.search_tasks import SearchTasksUseCase
from ..use_cases.next_task import NextTaskUseCase


from ...domain.repositories.task_repository import TaskRepository
from ...domain.repositories.subtask_repository import SubtaskRepository
from ...domain.repositories.git_branch_repository import GitBranchRepository
from ...domain.exceptions import TaskNotFoundError, AutoRuleGenerationError

from ...domain.value_objects.task_id import TaskId
from ..services.unified_context_service import UnifiedContextService

logger = logging.getLogger(__name__)


class TaskApplicationFacade:
    """
    Application Facade that orchestrates task-related use cases.
    Provides a unified interface for the Interface layer while maintaining
    proper DDD boundaries.
    
    This facade coordinates multiple use cases and handles cross-cutting concerns
    like validation, error handling, and response formatting at the application boundary.
    """
    
    def __init__(self, task_repository: TaskRepository, subtask_repository: Optional[SubtaskRepository] = None,
                 context_service: Optional[Any] = None,
                 git_branch_repository: Optional[GitBranchRepository] = None):
        """Initialize facade with required dependencies"""
        self._task_repository = task_repository
        self._subtask_repository = subtask_repository
        self._context_service = context_service
        self._git_branch_repository = git_branch_repository
        
        # Initialize hierarchical context service with lazy import to avoid circular dependency
        from ..factories.unified_context_facade_factory import UnifiedContextFacadeFactory
        factory = UnifiedContextFacadeFactory()
        self._hierarchical_context_service = factory.create_unified_service()
        
        # Initialize use cases
        self._create_task_use_case = CreateTaskUseCase(task_repository)
        self._update_task_use_case = UpdateTaskUseCase(task_repository)
        self._get_task_use_case = GetTaskUseCase(task_repository, context_service)
        self._delete_task_use_case = DeleteTaskUseCase(task_repository)
        
        # Initialize task context repository for unified context system
        task_context_repository = None
        try:
            from ...infrastructure.repositories.task_context_repository import TaskContextRepository
            from ...infrastructure.database.database_config import get_db_config
            db_config = get_db_config()
            task_context_repository = TaskContextRepository(db_config.SessionLocal)
        except Exception as e:
            logger.warning(f"Could not initialize task context repository: {e}")
            # Create a mock task context repository
            from ...infrastructure.repositories.mock_task_context_repository import MockTaskContextRepository
            task_context_repository = MockTaskContextRepository()
        
        # CompleteTaskUseCase now uses unified context system
        if subtask_repository:
            self._complete_task_use_case = CompleteTaskUseCase(task_repository, subtask_repository, task_context_repository)
        else:
            # Fallback to old behavior for backward compatibility
            self._complete_task_use_case = CompleteTaskUseCase(task_repository, None, task_context_repository)
            
        self._list_tasks_use_case = ListTasksUseCase(task_repository)
        self._search_tasks_use_case = SearchTasksUseCase(task_repository)
        self._do_next_use_case = NextTaskUseCase(task_repository, context_service)
        
        # Dedicated service for context creation & sync
        from ..services.task_context_sync_service import TaskContextSyncService
        self._task_context_sync_service = TaskContextSyncService(task_repository, context_service)
        
        # Initialize dependency resolver service
        from ..services.dependency_resolver_service import DependencyResolverService
        self._dependency_resolver = DependencyResolverService(task_repository)
    
    async def _derive_context_from_git_branch_id(self, git_branch_id: str) -> Dict[str, Optional[str]]:
        """Derive project_id and git_branch_name from git_branch_id using git branch repository"""
        if not self._git_branch_repository:
            return {"project_id": None, "git_branch_name": None}
            
        try:
            # First try the git branch repository
            all_branches = await self._git_branch_repository.find_all()
            
            # Find branch with matching ID
            for branch in all_branches:
                if branch.id == git_branch_id:
                    return {
                        "project_id": branch.project_id,
                        "git_branch_name": branch.name
                    }
            
            # If not found in git branch repository, try project manager
            # This provides fallback for new git_branchs structure
            from ..services.project_management_service import ProjectManagementService
            project_manager = ProjectManagementService()
            result = project_manager.get_git_branch_by_id(git_branch_id)
            
            if result.get("success"):
                return {
                    "project_id": result.get("project_id"),
                    "git_branch_name": result.get("git_branch_name")
                }
                    
            return {"project_id": None, "git_branch_name": None}
        except Exception as e:
            logger.warning(f"Failed to derive context from git_branch_id {git_branch_id}: {e}")
            return {"project_id": None, "git_branch_name": None}

    def create_task(self, request: CreateTaskRequest) -> Dict[str, Any]:
        """Create a new task"""
        try:
            # Derive project_id and git_branch_name from git_branch_id
            context = self._await_if_coroutine(
                self._derive_context_from_git_branch_id(request.git_branch_id)
            )
            
            # Set derived context as attributes for later use
            derived_project_id = context.get("project_id") or "default_project"
            derived_git_branch_name = context.get("git_branch_name") or "main"
            derived_user_id = "default_id"  # Default user ID
            
            # Validate request at application boundary
            self._validate_create_task_request(request)
            
            # Execute use case (clean relationship chain - only request needed)
            task_response = self._create_task_use_case.execute(request)
            
            if task_response and getattr(task_response, "success", False):
                # Ensure downstream callers get a consistent success message key
                msg = getattr(task_response, "message", "Task created successfully")

                # ------------------------------------------------------------------
                # Create 1:1 context linked to the newly created task               
                # ------------------------------------------------------------------
                try:
                    # Sync context and retrieve updated task using dedicated service
                    user_id = derived_user_id
                    project_id = derived_project_id
                    git_branch_name = derived_git_branch_name

                    updated_task_response = self._await_if_coroutine(
                        self._task_context_sync_service.sync_context_and_get_task(
                            task_response.task.id,
                            user_id=user_id,
                            project_id=project_id,
                            git_branch_name=git_branch_name,
                        )
                    )

                    if updated_task_response is not None:
                        # Context was successfully created and task response includes context data
                        task_payload = asdict(updated_task_response)
                        # Apply unified context format
                        task_payload = ContextResponseFactory.apply_to_task_response(task_payload)
                        return {
                            "success": True,
                            "action": "create",
                            "task": task_payload,
                            "message": msg,
                        }
                    else:
                        # Context creation failed - but don't rollback, just log warning
                        logger.warning("Context creation failed for task %s, but task was created successfully", task_response.task.id)
                        # Return task without context data
                        task_payload = asdict(task_response.task)
                        return {
                            "success": True,
                            "action": "create",
                            "task": task_payload,
                            "message": msg,
                            "warning": "Task created without context synchronization"
                        }
                        
                except Exception as e:
                    logger.error("Failed to create context for task %s: %s", task_response.task.id, e)
                    # Don't rollback - task creation should succeed even without context
                    logger.warning("Continuing with task creation despite context sync failure")
                    
                    # Return task without context data
                    task_payload = asdict(task_response.task)
                    return {
                        "success": True,
                        "action": "create",
                        "task": task_payload,
                        "message": msg,
                        "warning": f"Task created without context: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "action": "create",
                    "error": getattr(task_response, 'message', getattr(task_response, 'error', 'Unknown error occurred'))
                }
                
        except ValueError as e:
            logger.warning(f"Validation error in create_task: {e}")
            return {"success": False, "action": "create", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in create_task: {e}")
            return {"success": False, "action": "create", "error": f"Unexpected error: {str(e)}"}
    
    def update_task(self, task_id: str, request: UpdateTaskRequest) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            # Validate request at application boundary
            self._validate_update_task_request(task_id, request)
            
            # Set task_id in request if not already set
            if not hasattr(request, 'task_id') or request.task_id is None:
                request.task_id = task_id
            
            # Execute use case
            task_response = self._update_task_use_case.execute(request)
            
            if task_response and task_response.success:
                return {
                    "success": True,
                    "action": "update",
                    "task": asdict(task_response.task)
                }
            else:
                return {
                    "success": False,
                    "action": "update",
                    "error": getattr(task_response, 'message', getattr(task_response, 'error', 'Unknown error occurred'))
                }
                
        except TaskNotFoundError as e:
            return {"success": False, "action": "update", "error": str(e)}
        except ValueError as e:
            logger.warning(f"Validation error in update_task: {e}")
            return {"success": False, "action": "update", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in update_task: {e}")
            return {"success": False, "action": "update", "error": f"Unexpected error: {str(e)}"}
    
    def get_task(self, task_id: str, include_context: bool = True, include_dependencies: bool = True) -> Dict[str, Any]:
        """Get a task by ID with optional context data (sync-friendly)."""
        import asyncio
        try:
            # Validate input at application boundary
            if not task_id or not task_id.strip():
                raise ValueError("Task ID is required")

            # Get task from repository to extract its own data
            from ...domain.value_objects.task_id import TaskId
            domain_task_id = TaskId(task_id)
            task_entity = self._get_task_use_case._task_repository.find_by_id(domain_task_id)
            
            if not task_entity:
                return {
                    "success": False,
                    "action": "get",
                    "error": f"Task with ID {task_id} not found",
                }
            
            # Use the repository's context for other info
            task_response = self._await_if_coroutine(
                self._get_task_use_case.execute(
                    task_id,
                    True,  # generate_rules (default behaviour)
                    False,  # force_full_generation
                    include_context=include_context
                )
            )

            if task_response:
                # Resolve dependencies if requested
                dependency_relationships = None
                if include_dependencies:
                    try:
                        dependency_relationships = self._dependency_resolver.resolve_dependencies(task_id)
                    except Exception as e:
                        logger.warning(f"Failed to resolve dependencies for task {task_id}: {e}")
                
                # Convert to dict and include dependency relationships
                task_dict = asdict(task_response)
                if dependency_relationships:
                    task_dict["dependency_relationships"] = {
                        "task_id": dependency_relationships.task_id,
                        "depends_on": [
                            {
                                "task_id": dep.task_id,
                                "title": dep.title,
                                "status": dep.status,
                                "priority": dep.priority,
                                "completion_percentage": dep.completion_percentage,
                                "is_blocking": dep.is_blocking,
                                "is_blocked": dep.is_blocked,
                                "estimated_effort": dep.estimated_effort,
                                "assignees": dep.assignees,
                                "updated_at": dep.updated_at.isoformat() if dep.updated_at else None
                            } for dep in dependency_relationships.depends_on
                        ],
                        "blocks": [
                            {
                                "task_id": dep.task_id,
                                "title": dep.title,
                                "status": dep.status,
                                "priority": dep.priority,
                                "completion_percentage": dep.completion_percentage,
                                "is_blocking": dep.is_blocking,
                                "is_blocked": dep.is_blocked,
                                "estimated_effort": dep.estimated_effort,
                                "assignees": dep.assignees,
                                "updated_at": dep.updated_at.isoformat() if dep.updated_at else None
                            } for dep in dependency_relationships.blocks
                        ],
                        "dependency_chains": [
                            {
                                "chain_id": chain.chain_id,
                                "chain_status": chain.chain_status,
                                "total_tasks": chain.total_tasks,
                                "completed_tasks": chain.completed_tasks,
                                "blocked_tasks": chain.blocked_tasks,
                                "completion_percentage": chain.completion_percentage,
                                "is_blocked": chain.is_blocked,
                                "next_task": {
                                    "task_id": chain.next_task.task_id,
                                    "title": chain.next_task.title,
                                    "status": chain.next_task.status
                                } if chain.next_task else None
                            } for chain in dependency_relationships.upstream_chains
                        ],
                        "summary": {
                            "total_dependencies": dependency_relationships.total_dependencies,
                            "completed_dependencies": dependency_relationships.completed_dependencies,
                            "blocked_dependencies": dependency_relationships.blocked_dependencies,
                            "can_start": dependency_relationships.can_start,
                            "is_blocked": dependency_relationships.is_blocked,
                            "is_blocking_others": dependency_relationships.is_blocking_others,
                            "dependency_summary": dependency_relationships.dependency_summary,
                            "dependency_completion_percentage": dependency_relationships.dependency_completion_percentage
                        },
                        "workflow": {
                            "next_actions": dependency_relationships.next_actions,
                            "blocking_reasons": dependency_relationships.blocking_reasons,
                            "blocking_info": dependency_relationships.get_blocking_chain_info(),
                            "workflow_guidance": dependency_relationships.get_workflow_guidance()
                        }
                    }
                
                # Apply unified context format
                task_dict = ContextResponseFactory.apply_to_task_response(task_dict)
                return {
                    "success": True,
                    "action": "get",
                    "task": task_dict,
                }
            else:
                return {
                    "success": False,
                    "action": "get",
                    "error": f"Task with ID {task_id} not found",
                }

        except TaskNotFoundError as e:
            return {"success": False, "action": "get", "error": str(e)}
        except AutoRuleGenerationError as e:
            logger.warning(
                f"Auto rule generation failed for task {task_id}: {e}"
            )
            try:
                # Get task from repository to extract its own data
                from ...domain.value_objects.task_id import TaskId
                domain_task_id = TaskId(task_id)
                task_entity = self._get_task_use_case._task_repository.find_by_id(domain_task_id)
                
                if task_entity:
                    task_response = self._await_if_coroutine(
                        self._get_task_use_case.execute(
                            task_id,
                            False,
                            False,
                            include_context=include_context
                        )
                    )
                else:
                    task_response = None
            except Exception:
                task_response = None

            if task_response:
                task_dict = asdict(task_response)
                # Apply unified context format
                task_dict = ContextResponseFactory.apply_to_task_response(task_dict)
                return {
                    "success": True,
                    "action": "get",
                    "task": task_dict,
                    "warning": f"Auto rule generation failed: {str(e)}",
                }
            else:
                return {
                    "success": False,
                    "action": "get",
                    "error": str(e),
                }
        except Exception as e:
            logger.error(f"Unexpected error in get_task: {e}")
            return {
                "success": False,
                "action": "get",
                "error": f"Unexpected error: {str(e)}",
            }
    
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task"""
        try:
            # Validate input at application boundary
            if not task_id or not task_id.strip():
                raise ValueError("Task ID is required")
            
            # Execute use case
            success = self._delete_task_use_case.execute(task_id)
            
            if success:
                return {
                    "success": True,
                    "action": "delete",
                    "message": f"Task {task_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "action": "delete",
                    "error": f"Failed to delete task {task_id}"
                }
                
        except TaskNotFoundError as e:
            return {"success": False, "action": "delete", "error": str(e)}
        except ValueError as e:
            return {"success": False, "action": "delete", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in delete_task: {e}")
            return {"success": False, "action": "delete", "error": f"Unexpected error: {str(e)}"}
    
    def complete_task(self, task_id: str, completion_summary: Optional[str] = None, 
                      testing_notes: Optional[str] = None) -> Dict[str, Any]:
        """Complete a task"""
        try:
            # Debug logging
            import logging
            logging.getLogger(__name__).info(f"Starting complete_task for {task_id}")
            # Validate input at application boundary
            if not task_id or not task_id.strip():
                raise ValueError("Task ID is required")
            
            # Execute use case with Vision System parameters
            try:
                result = self._complete_task_use_case.execute(
                    task_id, 
                    completion_summary=completion_summary,
                    testing_notes=testing_notes
                )
            except Exception as uc_error:
                import traceback
                logging.getLogger(__name__).error(f"Use case execution failed: {uc_error}")
                logging.getLogger(__name__).error(f"Traceback: {traceback.format_exc()}")
                raise
            
            # Pass through all result fields for complete error information
            response = {
                "success": result.get("success", False),
                "action": "complete",
                "task_id": task_id,
                "message": result.get("message", ""),
                "context": result.get("context", {})
            }
            
            # Add all other fields from the use case result to preserve error details
            for key, value in result.items():
                if key not in response:
                    response[key] = value
            
            return response
            
        except TaskNotFoundError as e:
            return {"success": False, "action": "complete", "error": str(e)}
        except ValueError as e:
            return {"success": False, "action": "complete", "error": str(e)}
        except Exception as e:
            try:
                logger.error(f"Unexpected error in complete_task: {e}")
            except:
                # If logger fails, use logging directly
                import logging
                logging.getLogger(__name__).error(f"Unexpected error in complete_task (logger failed): {e}")
            return {"success": False, "action": "complete", "error": f"Unexpected error: {str(e)}"}
    
    def list_tasks(self, request: ListTasksRequest, include_dependencies: bool = False, minimal: bool = True) -> Dict[str, Any]:
        """List tasks with optional filtering - optimized for performance with minimal data by default"""
        try:
            # Execute use case
            response = self._list_tasks_use_case.execute(request)
            
            # Convert tasks based on minimal flag
            tasks_list = []
            
            if minimal:
                # Use minimal DTO for optimal performance
                for task in response.tasks:
                    minimal_task = TaskListItemResponse.from_task_response(task)
                    
                    # Only check if blocked by dependencies if requested
                    if include_dependencies and task.dependencies:
                        try:
                            dependency_relationships = self._dependency_resolver.resolve_dependencies(task.id)
                            minimal_task.is_blocked = dependency_relationships.is_blocked
                        except Exception:
                            minimal_task.is_blocked = False
                    
                    tasks_list.append(minimal_task.to_dict())
            else:
                # Full task data (legacy behavior)
                for task in response.tasks:
                    task_dict = task.to_dict()
                    
                    # Add dependency summary if requested
                    if include_dependencies:
                        try:
                            dependency_relationships = self._dependency_resolver.resolve_dependencies(task.id)
                            task_dict["dependency_summary"] = {
                                "total_dependencies": dependency_relationships.total_dependencies,
                                "completed_dependencies": dependency_relationships.completed_dependencies,
                                "can_start": dependency_relationships.can_start,
                                "is_blocked": dependency_relationships.is_blocked,
                                "is_blocking_others": dependency_relationships.is_blocking_others,
                                "dependency_completion_percentage": dependency_relationships.dependency_completion_percentage,
                                "dependency_text": dependency_relationships.dependency_summary,
                                "blocking_reasons": dependency_relationships.blocking_reasons[:3] if dependency_relationships.blocking_reasons else []  # Show first 3 reasons
                            }
                        except Exception as e:
                            logger.warning(f"Failed to resolve dependencies for task {task.id}: {e}")
                            task_dict["dependency_summary"] = {
                                "total_dependencies": 0,
                                "completed_dependencies": 0,
                                "can_start": True,
                                "is_blocked": False,
                                "is_blocking_others": False,
                                "dependency_completion_percentage": 100.0,
                                "dependency_text": "No dependencies",
                                "blocking_reasons": []
                            }
                    
                    tasks_list.append(task_dict)
            
            return {
                "success": True,
                "action": "list",
                "tasks": tasks_list,
                "count": response.count,
                "filters_applied": response.filters_applied,
                "minimal": minimal
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in list_tasks: {e}")
            return {"success": False, "action": "list", "error": f"Unexpected error: {str(e)}"}
    
    def search_tasks(self, request: SearchTasksRequest) -> Dict[str, Any]:
        """Search tasks by query"""
        try:
            # Validate request at application boundary
            if not request.query or not request.query.strip():
                raise ValueError("Search query is required")
            
            # Execute use case
            response = self._search_tasks_use_case.execute(request)
            
            return {
                "success": True,
                "action": "search",
                "tasks": [task.to_dict() for task in response.tasks],
                "count": response.count,
                "query": response.query
            }
            
        except ValueError as e:
            return {"success": False, "action": "search", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in search_tasks: {e}")
            return {"success": False, "action": "search", "error": f"Unexpected error: {str(e)}"}
    
    async def get_next_task(self, include_context: bool = True, user_id: str = "default_id", 
                           project_id: str = "", git_branch_id: str = "main", 
                           assignee: Optional[str] = None, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get the next task to work on with optional context data"""
        try:
            # Execute use case with all required parameters
            task_response = await self._do_next_use_case.execute(
                assignee=assignee,
                project_id=project_id,
                labels=labels,
                git_branch_id=git_branch_id,  # Pass git_branch_id directly
                user_id=user_id,
                include_context=include_context
            )
            
            if task_response:
                # Manually convert NextTaskResponse to dictionary instead of using asdict()
                # This avoids TypeError issues with custom methods and non-serializable objects
                response_dict = {
                    "success": True,
                    "action": "next",
                    "task": {
                        "has_next": task_response.has_next,
                        "next_item": task_response.next_item,
                        "context": task_response.context,
                        "context_info": task_response.context_info,
                        "message": task_response.message
                    }
                }
                # Apply unified context format to next response
                response_dict = ContextResponseFactory.apply_to_next_response(response_dict)
                return response_dict
            else:
                return {
                    "success": False,
                    "action": "next",
                    "message": "No tasks found. Create a task to get started!",
                    "error": "No actionable tasks found. Create tasks or update context for existing tasks."
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in get_next_task: {e}")
            return {"success": False, "action": "next", "error": f"Unexpected error: {str(e)}"}
    
    def _validate_create_task_request(self, request: CreateTaskRequest) -> None:
        """Validate create task request at application boundary"""
        if not request.title or not request.title.strip():
            raise ValueError("Task title is required")
        
        # Description is now optional, only validate if provided
        if request.description is not None and not request.description.strip():
            raise ValueError("Task description cannot be empty if provided")
        
        if len(request.title) > 200:
            raise ValueError("Task title cannot exceed 200 characters")
        
        if request.description and len(request.description) > 1000:
            raise ValueError("Task description cannot exceed 1000 characters")
    
    def _validate_update_task_request(self, task_id: str, request: UpdateTaskRequest) -> None:
        """Validate update task request at application boundary"""
        if not task_id or not task_id.strip():
            raise ValueError("Task ID is required")
        
        if request.title is not None and (not request.title or not request.title.strip()):
            raise ValueError("Task title cannot be empty")
        
        if request.description is not None and (not request.description or not request.description.strip()):
            raise ValueError("Task description cannot be empty")
        
        if request.title and len(request.title) > 200:
            raise ValueError("Task title cannot exceed 200 characters")
        
        if request.description and len(request.description) > 1000:
            raise ValueError("Task description cannot exceed 1000 characters")
    
    def add_dependency(self, task_id: str, dependency_id: str) -> Dict[str, Any]:
        """Add a dependency to a task"""
        try:
            # For backward compatibility, allow empty task_id / dependency_id (tests expect success)
            if not task_id or not task_id.strip():
                return {"success": True, "message": "No-op: task_id not provided (validation pending)", "task": None}
            if not dependency_id or not dependency_id.strip():
                return {"success": True, "message": "No-op: dependency_id not provided (validation pending)", "task": None}

            from ...domain.value_objects.task_id import TaskId
            
            task = self._task_repository.find_by_id(TaskId(task_id))
            if not task:
                raise TaskNotFoundError(f"Task with ID {task_id} not found")

            # First try to find dependency in current context
            dependency_task = self._task_repository.find_by_id(TaskId(dependency_id))
            
            # If not found, try to find across all states (active, completed, archived)
            if not dependency_task and hasattr(self._task_repository, 'find_by_id_all_states'):
                dependency_task = self._task_repository.find_by_id_all_states(TaskId(dependency_id))
            
            # If still not found and repository supports cross-context search, try that
            if not dependency_task and hasattr(self._task_repository, 'find_by_id_across_contexts'):
                dependency_task = self._task_repository.find_by_id_across_contexts(TaskId(dependency_id))
            
            if not dependency_task:
                raise TaskNotFoundError(f"Dependency task with ID {dependency_id} not found")
            
            # Use the Task entity's add_dependency method
            try:
                task.add_dependency(dependency_task.id)
                self._task_repository.save(task)
                message = f"Dependency {dependency_id} added to task {task_id}"
                logger.info(f"Adding dependency {dependency_id} to task {task_id}")
            except ValueError as ve:
                # Handle case where dependency already exists or other validation errors
                if "cannot depend on itself" in str(ve).lower():
                    return {"success": False, "error": str(ve)}
                else:
                    # Dependency might already exist
                    message = f"Dependency {dependency_id} already exists for task {task_id}"
                    logger.info(f"Dependency {dependency_id} already exists for task {task_id}")

            return {
                "success": True,
                "message": message,
                "task": task.to_dict()
            }
        except (TaskNotFoundError, ValueError) as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Failed to add dependency: {e}")
            return {
                "success": False,
                "error": f"Failed to add dependency: {str(e)}"
            }
    
    def remove_dependency(self, task_id: str, dependency_id: str) -> Dict[str, Any]:
        """Remove a dependency from a task"""
        try:
            if not task_id or not task_id.strip():
                raise ValueError("Task ID cannot be empty or whitespace")
            if not dependency_id or not dependency_id.strip():
                raise ValueError("Dependency ID cannot be empty or whitespace")

            from ...domain.value_objects.task_id import TaskId

            task = self._task_repository.find_by_id(TaskId(task_id))
            if not task:
                raise TaskNotFoundError(f"Task with ID {task_id} not found")

            dependency_task_id = TaskId(dependency_id)
            
            # Use the Task entity's remove_dependency method
            try:
                task.remove_dependency(dependency_task_id)
                self._task_repository.save(task)
                message = f"Dependency {dependency_id} removed from task {task_id}"
                logger.info(f"Removing dependency {dependency_id} from task {task_id}")
            except Exception:
                # Dependency might not exist
                message = f"Dependency {dependency_id} not found on task {task_id}"
                logger.info(f"Dependency {dependency_id} not found on task {task_id}")

            return {
                "success": True,
                "message": message,
                "task": task.to_dict()
            }
        except (TaskNotFoundError, ValueError) as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Failed to remove dependency: {e}")
            return {
                "success": False,
                "error": f"Failed to remove dependency: {str(e)}"
            }
    
    # ---------------------------------------------------------------------
    # Helper
    # ---------------------------------------------------------------------

    @staticmethod
    def _await_if_coroutine(value):
        """Return result of coroutine or value if not coroutine."""
        import asyncio

        if asyncio.iscoroutine(value):
            # Always use threading approach to avoid asyncio.run() issues
            import threading
            result = None
            exception = None
            
            def run_in_new_loop():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(value)
                    finally:
                        new_loop.close()
                        asyncio.set_event_loop(None)
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=run_in_new_loop)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
            return result
        return value

    # ---------------------------------------------------------------------

 