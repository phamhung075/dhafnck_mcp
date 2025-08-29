"""
Task API Controller

This controller handles frontend task management operations following proper DDD architecture.
It serves as the interface layer, delegating business logic to application facades.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from ...application.facades.task_application_facade import TaskApplicationFacade
from ...application.dtos.task.create_task_request import CreateTaskRequest
from ...application.dtos.task.update_task_request import UpdateTaskRequest
from ...application.dtos.task.list_tasks_request import ListTasksRequest
from fastmcp.task_management.infrastructure.factories.task_facade_factory import TaskFacadeFactory
from ...infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from ...infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory

logger = logging.getLogger(__name__)


class TaskAPIController:
    """
    API Controller for task management operations.
    
    This controller provides a clean interface between frontend routes and
    application services, ensuring proper separation of concerns.
    """
    
    def __init__(self):
        """Initialize the controller"""
        self.task_repository_factory = TaskRepositoryFactory()
        self.subtask_repository_factory = SubtaskRepositoryFactory()
    
    def create_task(self, request: CreateTaskRequest, user_id: str, session) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            request: Task creation request data
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task creation result
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory, 
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",  # This should come from request
                git_branch_id=request.git_branch_id,
                user_id=user_id
            )
            
            # Delegate to facade
            result = task_facade.create_task(request)
            
            logger.info(f"Task created successfully for user {user_id}: {result.get('task', {}).get('id')}")
            
            return {
                "success": True,
                "task": result.get("task"),
                "message": "Task created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating task for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create task"
            }
    
    def list_tasks(self, request: ListTasksRequest, user_id: str, session) -> Dict[str, Any]:
        """
        List tasks for a user.
        
        Args:
            request: Task listing request
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            List of tasks
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory, 
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=request.git_branch_id,
                user_id=user_id
            )
            
            # Delegate to facade
            result = task_facade.list_tasks(request)
            
            logger.info(f"Listed {len(result.get('tasks', []))} tasks for user {user_id}")
            
            return {
                "success": True,
                "tasks": result.get("tasks", []),
                "count": len(result.get("tasks", [])),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list tasks"
            }
    
    def get_task(self, task_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Get a specific task.
        
        Args:
            task_id: Task identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task details
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory, 
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,  # Will be determined by task
                user_id=user_id
            )
            
            # Delegate to facade
            task = task_facade.get_task(task_id)
            
            if not task:
                return {
                    "success": False,
                    "error": "Task not found",
                    "message": "Task not found or access denied"
                }
            
            logger.info(f"Retrieved task {task_id} for user {user_id}")
            
            return {
                "success": True,
                "task": task
            }
            
        except Exception as e:
            logger.error(f"Error getting task {task_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get task"
            }
    
    def update_task(self, task_id: str, request: UpdateTaskRequest, user_id: str, session) -> Dict[str, Any]:
        """
        Update a task.
        
        Args:
            task_id: Task identifier
            request: Task update request
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Updated task details
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory, 
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # First check if task exists
            existing_task = task_facade.get_task(task_id)
            if not existing_task:
                return {
                    "success": False,
                    "error": "Task not found",
                    "message": "Task not found or access denied"
                }
            
            # Delegate to facade
            updated_task = task_facade.update_task(task_id, request)
            
            logger.info(f"Updated task {task_id} for user {user_id}")
            
            return {
                "success": True,
                "task": updated_task,
                "message": "Task updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating task {task_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update task"
            }
    
    def delete_task(self, task_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Delete a task.
        
        Args:
            task_id: Task identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Deletion result
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory, 
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # First check if task exists
            existing_task = task_facade.get_task(task_id)
            if not existing_task:
                return {
                    "success": False,
                    "error": "Task not found", 
                    "message": "Task not found or access denied"
                }
            
            # Delegate to facade
            task_facade.delete_task(task_id)
            
            logger.info(f"Deleted task {task_id} for user {user_id}")
            
            return {
                "success": True,
                "message": "Task deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete task"
            }
    
    def complete_task(self, task_id: str, completion_summary: str, testing_notes: Optional[str], user_id: str, session) -> Dict[str, Any]:
        """
        Complete a task.
        
        Args:
            task_id: Task identifier
            completion_summary: Summary of work completed
            testing_notes: Notes about testing performed
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task completion result
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory, 
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # First check if task exists
            existing_task = task_facade.get_task(task_id)
            if not existing_task:
                return {
                    "success": False,
                    "error": "Task not found",
                    "message": "Task not found or access denied"
                }
            
            # Delegate to facade
            completed_task = task_facade.complete_task(
                task_id=task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            
            logger.info(f"Completed task {task_id} for user {user_id}")
            
            return {
                "success": True,
                "task": completed_task,
                "message": "Task completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error completing task {task_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to complete task"
            }
    
    def get_task_statistics(self, user_id: str, session) -> Dict[str, Any]:
        """
        Get task statistics for a user.
        
        Args:
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task statistics
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # Get statistics from facade
            result = task_facade.get_user_task_statistics()
            
            return {
                "success": True,
                "stats": result.get("stats", {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "pending_tasks": 0,
                    "high_priority_tasks": 0,
                    "user_id": user_id
                }),
                "message": "Statistics retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting task statistics for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get task statistics"
            }
    
    def count_tasks(self, filters: Dict[str, Any], user_id: str, session) -> Dict[str, Any]:
        """
        Count tasks matching filters for performance optimization.
        
        Args:
            filters: Filter criteria
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task count result
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=filters.get("git_branch_id"),
                user_id=user_id
            )
            
            # Count tasks with filters
            result = task_facade.count_tasks(filters)
            
            return result
            
        except Exception as e:
            logger.error(f"Error counting tasks for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "count": 0
            }
    
    def list_tasks_summary(self, filters: Dict[str, Any], offset: int, limit: int, 
                          include_counts: bool, user_id: str, session) -> Dict[str, Any]:
        """
        List tasks with lightweight summary data for performance optimization.
        
        Args:
            filters: Filter criteria
            offset: Pagination offset
            limit: Pagination limit
            include_counts: Whether to include counts
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task summary list result
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=filters.get("git_branch_id"),
                user_id=user_id
            )
            
            # Get tasks summary
            result = task_facade.list_tasks_summary(
                filters=filters,
                offset=offset,
                limit=limit,
                include_counts=include_counts
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing task summaries for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tasks": []
            }
    
    def get_full_task(self, task_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Get full task data for lazy loading.
        
        Args:
            task_id: Task identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Full task data
        """
        try:
            # Create task facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # Get full task data
            result = task_facade.get_task(task_id, include_full_data=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting full task {task_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get full task data"
            }