"""
Protected Task Routes with OAuth2 Authentication

This module provides OAuth2-protected versions of task-related endpoints
for use with the auth bridge pattern. These routes can be used for REST API
access while MCP protocol continues using its native authentication.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import logging
import json

# Import OAuth2 dependencies
from fastmcp.auth.interface.fastapi_auth import get_current_active_user
from fastmcp.auth.domain.entities.user import User

# Import API controllers for proper DDD architecture
from fastmcp.task_management.interface.api_controllers.task_api_controller import TaskAPIController
from fastmcp.task_management.interface.api_controllers.context_api_controller import ContextAPIController
from fastmcp.task_management.interface.api_controllers.subtask_api_controller import SubtaskAPIController
from fastmcp.auth.interface.fastapi_auth import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Define the missing function using the imported one
get_current_user_from_bridge = get_current_active_user

# Create router with OAuth2 protection
router = APIRouter(
    prefix="/api/tasks",
    tags=["Protected Tasks"],
    dependencies=[Depends(get_current_user_from_bridge)]  # Protect all routes
)

# Initialize API controllers
task_controller = TaskAPIController()
context_controller = ContextAPIController()
subtask_controller = SubtaskAPIController()


@router.get("/summaries")
async def get_task_summaries(
    git_branch_id: str = Query(..., description="Git branch UUID"),
    include_subtasks: bool = Query(False, description="Include subtask summaries"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_bridge),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get lightweight task summaries for list views with OAuth2 protection.
    
    This endpoint provides only essential task information for initial page load,
    dramatically improving performance for large task lists.
    """
    try:
        # Create list request for API controller
        from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
        
        list_request = ListTasksRequest(
            git_branch_id=git_branch_id,
            # Add user filtering from auth
            status=None,  # No status filter for summaries
            priority=None,  # No priority filter for summaries
            limit=100,  # Default limit for summaries
            offset=0
        )
        
        # Get user ID from current_user (OAuth2 format may be different than User entity)
        user_id = current_user.get("user_id") or current_user.get("id") or str(current_user)
        
        # Use API controller to list tasks
        result = task_controller.list_tasks(list_request, user_id, db)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch tasks")
            )
        
        tasks_data = result.get("tasks", [])
        
        # Transform to summary format
        summaries = []
        for task_data in tasks_data:
            summary = {
                "id": task_data.get("id"),
                "title": task_data.get("title"),
                "status": task_data.get("status"),
                "priority": task_data.get("priority"),
                "progress_percentage": task_data.get("progress_percentage", 0),
                "assignees": task_data.get("assignees", []),
                "labels": task_data.get("labels", []),
                "subtask_count": len(task_data.get("subtasks", [])),
                "has_context": bool(task_data.get("context_id")),
                "created_at": task_data.get("created_at"),
                "updated_at": task_data.get("updated_at")
            }
            
            # Optionally include subtask summaries
            if include_subtasks and task_data.get("subtasks"):
                summary["subtasks"] = [
                    {
                        "id": subtask.get("id"),
                        "title": subtask.get("title"),
                        "status": subtask.get("status"),
                        "progress": subtask.get("progress_percentage", 0)
                    }
                    for subtask in task_data.get("subtasks", [])
                ]
            
            summaries.append(summary)
        
        return {
            "success": True,
            "data": summaries,
            "count": len(summaries),
            "user": current_user.get("email", "unknown"),
            "auth_method": current_user.get("auth_method", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting task summaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subtask-summaries/{task_id}")
async def get_subtask_summaries(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_bridge),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get lightweight subtask summaries for a specific task with OAuth2 protection.
    
    Provides only essential subtask information for UI rendering.
    """
    try:
        # Get user ID from current_user
        user_id = current_user.get("user_id") or current_user.get("id") or str(current_user)
        
        # Use SubtaskAPIController to list subtasks
        result = subtask_controller.list_subtasks(task_id, user_id, db)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch subtasks")
            )
        
        subtasks_data = result.get("subtasks", [])
        
        # Transform to summary format
        summaries = [
            {
                "id": subtask_data.get("id"),
                "title": subtask_data.get("title"),
                "status": subtask_data.get("status"),
                "priority": subtask_data.get("priority"),
                "assignees": subtask_data.get("assignees", []),
                "progress": subtask_data.get("progress_percentage", 0),
                "created_at": subtask_data.get("created_at"),
                "updated_at": subtask_data.get("updated_at")
            }
            for subtask_data in subtasks_data
        ]
        
        # Calculate aggregate progress
        total_progress = sum(s["progress"] for s in summaries)
        avg_progress = total_progress / len(summaries) if summaries else 0
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "subtasks": summaries,
                "count": len(summaries),
                "average_progress": avg_progress,
                "completed_count": sum(1 for s in summaries if s["status"] == "done")
            },
            "user": current_user.get("email", "unknown"),
            "auth_method": current_user.get("auth_method", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting subtask summaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/branch-statistics/{git_branch_id}")
async def get_branch_statistics(
    git_branch_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_bridge),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get statistics for a git branch with OAuth2 protection.
    
    Provides task counts, progress metrics, and other statistics.
    """
    try:
        # Create list request for API controller
        from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
        
        list_request = ListTasksRequest(
            git_branch_id=git_branch_id,
            status=None,  # Get all statuses for statistics
            priority=None,  # Get all priorities
            limit=1000,  # High limit for statistics
            offset=0
        )
        
        # Get user ID from current_user
        user_id = current_user.get("user_id") or current_user.get("id") or str(current_user)
        
        # Use API controller to list tasks
        result = task_controller.list_tasks(list_request, user_id, db)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to fetch tasks")
            )
        
        tasks_data = result.get("tasks", [])
        
        # Calculate statistics
        total_tasks = len(tasks_data)
        completed_tasks = sum(1 for t in tasks_data if t.get("status") == "done")
        in_progress_tasks = sum(1 for t in tasks_data if t.get("status") == "in_progress")
        todo_tasks = sum(1 for t in tasks_data if t.get("status") == "todo")
        blocked_tasks = sum(1 for t in tasks_data if t.get("status") == "blocked")
        
        # Calculate average progress
        total_progress = sum(t.get("progress_percentage", 0) for t in tasks_data)
        avg_progress = total_progress / total_tasks if total_tasks > 0 else 0
        
        # Priority breakdown
        priority_breakdown = {
            "critical": sum(1 for t in tasks_data if t.get("priority") == "critical"),
            "high": sum(1 for t in tasks_data if t.get("priority") == "high"),
            "medium": sum(1 for t in tasks_data if t.get("priority") == "medium"),
            "low": sum(1 for t in tasks_data if t.get("priority") == "low")
        }
        
        return {
            "success": True,
            "data": {
                "git_branch_id": git_branch_id,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "todo_tasks": todo_tasks,
                "blocked_tasks": blocked_tasks,
                "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "average_progress": avg_progress,
                "priority_breakdown": priority_breakdown
            },
            "user": current_user.get("email", "unknown"),
            "auth_method": current_user.get("auth_method", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting branch statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router for mounting
__all__ = ["router"]