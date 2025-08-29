"""Task Search and Statistics Handler"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastmcp.task_management.infrastructure.factories.task_facade_factory import TaskFacadeFactory

logger = logging.getLogger(__name__)


class TaskSearchHandler:
    """Handler for task search and statistics operations"""
    
    def __init__(self, task_repository_factory, subtask_repository_factory):
        """
        Initialize handler with repository factories.
        
        Args:
            task_repository_factory: Factory for task repositories
            subtask_repository_factory: Factory for subtask repositories
        """
        self.task_repository_factory = task_repository_factory
        self.subtask_repository_factory = subtask_repository_factory
    
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
            
            # Get statistics using repository
            task_repository = self.task_repository_factory.create_repository()
            
            stats = {
                "total_tasks": task_repository.count_tasks({"user_id": user_id}),
                "todo_tasks": task_repository.count_tasks({"user_id": user_id, "status": "todo"}),
                "in_progress_tasks": task_repository.count_tasks({"user_id": user_id, "status": "in_progress"}),
                "completed_tasks": task_repository.count_tasks({"user_id": user_id, "status": "done"}),
                "blocked_tasks": task_repository.count_tasks({"user_id": user_id, "status": "blocked"}),
            }
            
            logger.info(f"Retrieved task statistics for user {user_id}")
            
            return {
                "success": True,
                "statistics": stats
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
        Count tasks matching filters.
        
        Args:
            filters: Task filters
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task count
        """
        try:
            # Add user_id to filters for security
            filters["user_id"] = user_id
            
            # Get count using repository
            task_repository = self.task_repository_factory.create_repository()
            count = task_repository.count_tasks(filters)
            
            logger.info(f"Counted {count} tasks for user {user_id} with filters {filters}")
            
            return {
                "success": True,
                "count": count,
                "filters": filters
            }
            
        except Exception as e:
            logger.error(f"Error counting tasks for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to count tasks"
            }
    
    def list_tasks_summary(self, filters: Dict[str, Any], offset: int, limit: int, 
                          user_id: str, session) -> Dict[str, Any]:
        """
        List task summaries with pagination.
        
        Args:
            filters: Task filters
            offset: Pagination offset
            limit: Pagination limit
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Task summaries
        """
        try:
            # Add user_id to filters for security
            filters["user_id"] = user_id
            
            # Get tasks using repository
            task_repository = self.task_repository_factory.create_repository()
            tasks = task_repository.find_with_pagination(filters, offset, limit)
            
            # Convert to summary format
            summaries = [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
                for task in tasks
            ]
            
            logger.info(f"Listed {len(summaries)} task summaries for user {user_id}")
            
            return {
                "success": True,
                "tasks": summaries,
                "offset": offset,
                "limit": limit,
                "total": task_repository.count_tasks(filters)
            }
            
        except Exception as e:
            logger.error(f"Error listing task summaries for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list task summaries"
            }
    
    def get_full_task(self, task_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Get full task details including subtasks and dependencies.
        
        Args:
            task_id: Task identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Full task details
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
            
            # Get task with all relations
            task = task_facade.get_task(task_id)
            
            if not task:
                return {
                    "success": False,
                    "error": "Task not found",
                    "message": "Task not found or access denied"
                }
            
            # Get subtasks
            subtask_repository = self.subtask_repository_factory.create_repository()
            subtasks = subtask_repository.find_by_task_id(task_id)
            
            # Add subtasks to response
            task["subtasks"] = [
                {
                    "id": subtask.id,
                    "title": subtask.title,
                    "status": subtask.status,
                    "progress": subtask.progress
                }
                for subtask in subtasks
            ]
            
            logger.info(f"Retrieved full task {task_id} for user {user_id}")
            
            return {
                "success": True,
                "task": task
            }
            
        except Exception as e:
            logger.error(f"Error getting full task {task_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get full task"
            }