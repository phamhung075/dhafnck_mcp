"""Task Workflow Operations Handler"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastmcp.task_management.infrastructure.factories.task_facade_factory import TaskFacadeFactory

logger = logging.getLogger(__name__)


class TaskWorkflowHandler:
    """Handler for task workflow operations"""
    
    def __init__(self, task_repository_factory, subtask_repository_factory):
        """
        Initialize handler with repository factories.
        
        Args:
            task_repository_factory: Factory for task repositories
            subtask_repository_factory: Factory for subtask repositories
        """
        self.task_repository_factory = task_repository_factory
        self.subtask_repository_factory = subtask_repository_factory
    
    def complete_task(self, task_id: str, completion_summary: str, 
                     testing_notes: Optional[str], user_id: str, session) -> Dict[str, Any]:
        """
        Complete a task.
        
        Args:
            task_id: Task identifier
            completion_summary: Summary of completion
            testing_notes: Optional testing notes
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Completion result
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
            
            # Delegate to facade
            result = task_facade.complete_task(
                task_id=task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            
            logger.info(f"Task {task_id} completed successfully for user {user_id}")
            
            return {
                "success": True,
                "task": result.get("task"),
                "message": "Task completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error completing task {task_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to complete task"
            }