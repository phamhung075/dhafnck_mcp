"""
User-Scoped Task Routes with Authentication

This module demonstrates how to implement user-based data isolation
in API routes using JWT authentication and user-scoped repositories.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...auth.interface.fastapi_auth import get_db
# Use Supabase authentication for V2 routes
try:
    from ...auth.interface.supabase_fastapi_auth import get_current_user
except ImportError:
    # Fallback to local JWT if Supabase auth not available
    from ...auth.interface.fastapi_auth import get_current_user
from ...auth.domain.entities.user import User
from ...task_management.application.facades.task_application_facade import TaskApplicationFacade
from ...task_management.infrastructure.repositories.orm.task_repository import TaskRepository
from ...task_management.infrastructure.repositories.orm.project_repository import ProjectRepository
from ...task_management.infrastructure.repositories.orm.agent_repository import AgentRepository
from ...task_management.application.dtos.task.create_task_request import CreateTaskRequest
from ...task_management.application.dtos.task.update_task_request import UpdateTaskRequest
from ...task_management.application.dtos.task.list_tasks_request import ListTasksRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/tasks", tags=["User-Scoped Tasks"])


class UserScopedRepositoryFactory:
    """Factory for creating user-scoped repository instances"""
    
    @staticmethod
    def create_task_repository(session: Session, user_id: str) -> TaskRepository:
        """Create a user-scoped task repository"""
        # Assuming TaskRepository has been updated to inherit from BaseUserScopedRepository
        return TaskRepository(session).with_user(user_id)
    
    @staticmethod
    def create_project_repository(session: Session, user_id: str) -> ProjectRepository:
        """Create a user-scoped project repository"""
        return ProjectRepository(session).with_user(user_id)
    
    @staticmethod
    def create_agent_repository(session: Session, user_id: str) -> AgentRepository:
        """Create a user-scoped agent repository"""
        return AgentRepository(session).with_user(user_id)


@router.post("/", response_model=dict)
async def create_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new task for the authenticated user.
    
    The task will be automatically associated with the current user,
    ensuring data isolation.
    """
    try:
        # Create user-scoped repositories
        task_repo = UserScopedRepositoryFactory.create_task_repository(db, current_user.id)
        project_repo = UserScopedRepositoryFactory.create_project_repository(db, current_user.id)
        
        # Create facade with user context
        facade = TaskApplicationFacade(
            task_repository=task_repo,
            git_branch_repository=None,  # Will be initialized as needed
            context_service=None  # Will be initialized as needed
        )
        
        # Log the access for audit
        logger.info(f"User {current_user.email} creating task: {request.title}")
        
        # Create the task - will automatically be scoped to the user
        result = facade.create_task(request)
        
        return {
            "success": True,
            "task": result,
            "message": f"Task created successfully for user {current_user.email}"
        }
        
    except Exception as e:
        logger.error(f"Error creating task for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get("/", response_model=dict)
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all tasks for the authenticated user.
    
    Only returns tasks that belong to the current user,
    ensuring data isolation.
    """
    try:
        # Create user-scoped repository
        task_repo = UserScopedRepositoryFactory.create_task_repository(db, current_user.id)
        
        # Create facade with user context
        facade = TaskApplicationFacade(task_repository=task_repo)
        
        # Build request
        list_request = ListTasksRequest(
            status=status,
            priority=priority,
            limit=limit
        )
        
        # Get user's tasks only
        tasks = facade.list_tasks(list_request)
        
        logger.info(f"User {current_user.email} retrieved {len(tasks)} tasks")
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks),
            "user": current_user.email
        }
        
    except Exception as e:
        logger.error(f"Error listing tasks for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tasks"
        )


@router.get("/{task_id}", response_model=dict)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific task for the authenticated user.
    
    Returns 404 if the task doesn't exist or doesn't belong to the user.
    """
    try:
        # Create user-scoped repository
        task_repo = UserScopedRepositoryFactory.create_task_repository(db, current_user.id)
        
        # Create facade with user context
        facade = TaskApplicationFacade(task_repository=task_repo)
        
        # Get the task - will automatically check user ownership
        task = facade.get_task(task_id)
        
        if not task:
            logger.warning(f"User {current_user.email} attempted to access non-existent or unauthorized task {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        logger.info(f"User {current_user.email} accessed task {task_id}")
        
        return {
            "success": True,
            "task": task
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task"
        )


@router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a task for the authenticated user.
    
    Only allows updating tasks that belong to the current user.
    """
    try:
        # Create user-scoped repository
        task_repo = UserScopedRepositoryFactory.create_task_repository(db, current_user.id)
        
        # Create facade with user context
        facade = TaskApplicationFacade(task_repository=task_repo)
        
        # First check if task exists and belongs to user
        existing_task = facade.get_task(task_id)
        if not existing_task:
            logger.warning(f"User {current_user.email} attempted to update non-existent or unauthorized task {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update the task
        updated_task = facade.update_task(task_id, request)
        
        logger.info(f"User {current_user.email} updated task {task_id}")
        
        return {
            "success": True,
            "task": updated_task,
            "message": "Task updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


@router.delete("/{task_id}", response_model=dict)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a task for the authenticated user.
    
    Only allows deleting tasks that belong to the current user.
    """
    try:
        # Create user-scoped repository
        task_repo = UserScopedRepositoryFactory.create_task_repository(db, current_user.id)
        
        # Create facade with user context
        facade = TaskApplicationFacade(task_repository=task_repo)
        
        # First check if task exists and belongs to user
        existing_task = facade.get_task(task_id)
        if not existing_task:
            logger.warning(f"User {current_user.email} attempted to delete non-existent or unauthorized task {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Delete the task
        facade.delete_task(task_id)
        
        logger.info(f"User {current_user.email} deleted task {task_id}")
        
        return {
            "success": True,
            "message": "Task deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )


@router.post("/{task_id}/complete", response_model=dict)
async def complete_task(
    task_id: str,
    completion_summary: str,
    testing_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a task as completed for the authenticated user.
    
    Only allows completing tasks that belong to the current user.
    """
    try:
        # Create user-scoped repository
        task_repo = UserScopedRepositoryFactory.create_task_repository(db, current_user.id)
        
        # Create facade with user context
        facade = TaskApplicationFacade(task_repository=task_repo)
        
        # First check if task exists and belongs to user
        existing_task = facade.get_task(task_id)
        if not existing_task:
            logger.warning(f"User {current_user.email} attempted to complete non-existent or unauthorized task {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Complete the task
        completed_task = facade.complete_task(
            task_id=task_id,
            completion_summary=completion_summary,
            testing_notes=testing_notes
        )
        
        logger.info(f"User {current_user.email} completed task {task_id}")
        
        return {
            "success": True,
            "task": completed_task,
            "message": "Task completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task {task_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete task"
        )


@router.get("/stats/summary", response_model=dict)
async def get_user_task_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get task statistics for the authenticated user.
    
    Returns summary statistics only for the user's own tasks.
    """
    try:
        # Create user-scoped repository
        task_repo = UserScopedRepositoryFactory.create_task_repository(db, current_user.id)
        
        # Get all user's tasks
        all_tasks = task_repo.find_all()
        
        # Calculate statistics
        stats = {
            "total_tasks": len(all_tasks),
            "completed_tasks": len([t for t in all_tasks if t.status == "done"]),
            "in_progress_tasks": len([t for t in all_tasks if t.status == "in_progress"]),
            "pending_tasks": len([t for t in all_tasks if t.status == "todo"]),
            "high_priority_tasks": len([t for t in all_tasks if t.priority == "high"]),
            "user": current_user.email
        }
        
        logger.info(f"User {current_user.email} retrieved task statistics")
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting task stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task statistics"
        )


# Register the router in your main app
# app.include_router(router)