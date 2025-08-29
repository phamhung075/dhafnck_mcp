"""
Subtask API Controller

This controller handles frontend subtask management operations following proper DDD architecture.
It serves as the interface layer, delegating business logic to application facades.
"""

import logging
from typing import Dict, Any, Optional

from ...application.facades.subtask_application_facade import SubtaskApplicationFacade
from fastmcp.task_management.infrastructure.factories.task_facade_factory import TaskFacadeFactory
from ...infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from ...infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory

logger = logging.getLogger(__name__)


class SubtaskAPIController:
    """
    API Controller for subtask management operations.
    
    This controller provides a clean interface between frontend routes and
    application services, ensuring proper separation of concerns.
    """
    
    def __init__(self):
        """Initialize the controller"""
        self.task_repository_factory = TaskRepositoryFactory()
        self.subtask_repository_factory = SubtaskRepositoryFactory()
    
    def create_subtask(self, task_id: str, title: str, description: Optional[str], user_id: str, session) -> Dict[str, Any]:
        """
        Create a new subtask.
        
        Args:
            task_id: Parent task identifier
            title: Subtask title
            description: Optional subtask description
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Subtask creation result
        """
        try:
            # Create subtask facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,  # Will be determined by parent task
                user_id=user_id
            )
            
            # Create subtask request data
            subtask_data = {
                "task_id": task_id,
                "title": title,
                "description": description or "",
                "status": "todo",
                "priority": "medium"
            }
            
            # Delegate to facade
            result = task_facade.create_subtask(subtask_data)
            
            logger.info(f"Subtask created successfully for user {user_id}: {result.get('subtask', {}).get('id')}")
            
            return {
                "success": True,
                "subtask": result.get("subtask"),
                "message": "Subtask created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating subtask for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create subtask"
            }
    
    def list_subtasks(self, task_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        List subtasks for a parent task.
        
        Args:
            task_id: Parent task identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            List of subtasks
        """
        try:
            # Create subtask facade with proper user context
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
            result = task_facade.list_subtasks_summary(
                parent_task_id=task_id,
                include_counts=True
            )
            
            logger.info(f"Listed {len(result.get('subtasks', []))} subtasks for task {task_id} by user {user_id}")
            
            return {
                "success": True,
                "subtasks": result.get("subtasks", []),
                "count": len(result.get("subtasks", [])),
                "parent_task_id": task_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error listing subtasks for task {task_id} by user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list subtasks"
            }
    
    def get_subtask(self, task_id: str, subtask_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Get a specific subtask.
        
        Args:
            task_id: Parent task identifier
            subtask_id: Subtask identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Subtask details
        """
        try:
            # Create subtask facade with proper user context
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
            subtask = task_facade.get_subtask(task_id, subtask_id)
            
            if not subtask:
                return {
                    "success": False,
                    "error": "Subtask not found",
                    "message": "Subtask not found or access denied"
                }
            
            logger.info(f"Retrieved subtask {subtask_id} for user {user_id}")
            
            return {
                "success": True,
                "subtask": subtask
            }
            
        except Exception as e:
            logger.error(f"Error getting subtask {subtask_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get subtask"
            }
    
    def update_subtask(self, task_id: str, subtask_id: str, update_data: Dict[str, Any], user_id: str, session) -> Dict[str, Any]:
        """
        Update a subtask.
        
        Args:
            task_id: Parent task identifier
            subtask_id: Subtask identifier
            update_data: Subtask update data
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Updated subtask details
        """
        try:
            # Create subtask facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # First check if subtask exists
            existing_subtask = task_facade.get_subtask(task_id, subtask_id)
            if not existing_subtask:
                return {
                    "success": False,
                    "error": "Subtask not found",
                    "message": "Subtask not found or access denied"
                }
            
            # Prepare update data
            update_request = {
                "task_id": task_id,
                "subtask_id": subtask_id,
                **update_data
            }
            
            # Delegate to facade
            updated_subtask = task_facade.update_subtask(update_request)
            
            logger.info(f"Updated subtask {subtask_id} for user {user_id}")
            
            return {
                "success": True,
                "subtask": updated_subtask,
                "message": "Subtask updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating subtask {subtask_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update subtask"
            }
    
    def delete_subtask(self, task_id: str, subtask_id: str, user_id: str, session) -> Dict[str, Any]:
        """
        Delete a subtask.
        
        Args:
            task_id: Parent task identifier
            subtask_id: Subtask identifier
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Deletion result
        """
        try:
            # Create subtask facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # First check if subtask exists
            existing_subtask = task_facade.get_subtask(task_id, subtask_id)
            if not existing_subtask:
                return {
                    "success": False,
                    "error": "Subtask not found",
                    "message": "Subtask not found or access denied"
                }
            
            # Delegate to facade
            task_facade.delete_subtask(task_id, subtask_id)
            
            logger.info(f"Deleted subtask {subtask_id} for user {user_id}")
            
            return {
                "success": True,
                "message": "Subtask deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting subtask {subtask_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete subtask"
            }
    
    def complete_subtask(self, task_id: str, subtask_id: str, completion_summary: str, user_id: str, session) -> Dict[str, Any]:
        """
        Complete a subtask.
        
        Args:
            task_id: Parent task identifier
            subtask_id: Subtask identifier
            completion_summary: Summary of work completed
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Subtask completion result
        """
        try:
            # Create subtask facade with proper user context
            task_facade_factory = TaskFacadeFactory(
                self.task_repository_factory,
                self.subtask_repository_factory
            )
            
            task_facade = task_facade_factory.create_task_facade(
                project_id="default_project",
                git_branch_id=None,
                user_id=user_id
            )
            
            # First check if subtask exists
            existing_subtask = task_facade.get_subtask(task_id, subtask_id)
            if not existing_subtask:
                return {
                    "success": False,
                    "error": "Subtask not found",
                    "message": "Subtask not found or access denied"
                }
            
            # Prepare completion data
            completion_data = {
                "task_id": task_id,
                "subtask_id": subtask_id,
                "completion_summary": completion_summary
            }
            
            # Delegate to facade
            completed_subtask = task_facade.complete_subtask(completion_data)
            
            logger.info(f"Completed subtask {subtask_id} for user {user_id}")
            
            return {
                "success": True,
                "subtask": completed_subtask,
                "message": "Subtask completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error completing subtask {subtask_id} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to complete subtask"
            }
    
    def list_subtasks_summary(self, parent_task_id: str, include_counts: bool, user_id: str, session) -> Dict[str, Any]:
        """
        List subtasks with summary data for performance optimization.
        
        Args:
            parent_task_id: Parent task identifier
            include_counts: Whether to include counts
            user_id: Authenticated user ID
            session: Database session
            
        Returns:
            Subtask summary list result
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
            
            # Get subtask summaries
            result = task_facade.list_subtasks_summary(
                parent_task_id=parent_task_id,
                include_counts=include_counts
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing subtask summaries for task {parent_task_id} by user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "subtasks": []
            }