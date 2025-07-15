"""Task Completion Service - Domain Service for Task Completion Business Rules"""

import logging
from typing import Optional, Dict, Any

from ..entities.task import Task
from ..repositories.subtask_repository import SubtaskRepository
from ..value_objects.task_id import TaskId
from ..exceptions.task_exceptions import TaskCompletionError

logger = logging.getLogger(__name__)


class TaskCompletionService:
    """
    Domain service that enforces task completion business rules.
    
    This service implements the business logic for validating task completion,
    including checking subtask completion status and context requirements.
    """
    
    def __init__(self, subtask_repository: SubtaskRepository):
        """
        Initialize the task completion service.
        
        Args:
            subtask_repository: Repository for accessing subtask data
        """
        self._subtask_repository = subtask_repository
    
    def can_complete_task(self, task: Task) -> tuple[bool, Optional[str]]:
        """
        Check if a task can be completed based on business rules.
        
        Business Rules:
        1. Context validation handled by completion use case (context_id cleared on updates by design)
        2. All subtasks linked to the task must be completed
        
        Args:
            task: The task to validate for completion
            
        Returns:
            Tuple of (can_complete: bool, error_message: Optional[str])
        """
        try:
            error_messages = []
            # Rule 1: Check if task has a context (required for completion)
            if task.context_id is None:
                error_messages.append(
                    "Task completion requires context to be created first. "
                    "Use: manage_context(action='create', task_id='{}', data_title='{}', "
                    "data_description='Your work summary') to create context.".format(
                        task.id.value, task.title
                    )
                )
            
            # Rule 2: Check if all subtasks are completed
            subtasks = self._subtask_repository.find_by_parent_task_id(task.id)
            
            if subtasks:
                incomplete_subtasks = [
                    subtask for subtask in subtasks 
                    if not subtask.is_completed
                ]
                
                if incomplete_subtasks:
                    incomplete_count = len(incomplete_subtasks)
                    total_count = len(subtasks)
                    incomplete_titles = [st.title for st in incomplete_subtasks[:3]]  # Show first 3
                    
                    error_msg = f"Cannot complete task: {incomplete_count} of {total_count} subtasks are incomplete."
                    if incomplete_titles:
                        if len(incomplete_titles) < incomplete_count:
                            error_msg += f" Incomplete subtasks include: {', '.join(incomplete_titles)}, and {incomplete_count - len(incomplete_titles)} more."
                        else:
                            error_msg += f" Incomplete subtasks: {', '.join(incomplete_titles)}."
                    error_msg += " Complete all subtasks first."
                    
                    error_messages.append(error_msg)
            
            if error_messages:
                return False, " ".join(error_messages)
            
            # All rules passed
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating task completion for task {task.id}: {e}")
            return False, f"Internal error validating task completion: {str(e)}"
    
    def validate_task_completion(self, task: Task) -> None:
        """
        Validate that a task can be completed, raising an exception if not.
        
        Args:
            task: The task to validate for completion
            
        Raises:
            TaskCompletionError: If the task cannot be completed
        """
        can_complete, error_message = self.can_complete_task(task)
        
        if not can_complete:
            raise TaskCompletionError(error_message or "Task cannot be completed")
    
    def get_completion_blockers(self, task: Task) -> list[str]:
        """
        Get a list of reasons why a task cannot be completed.
        
        Args:
            task: The task to check
            
        Returns:
            List of blocking reasons (empty if task can be completed)
        """
        blockers = []
        
        try:
            # Check if task has a context (required for completion)
            if task.context_id is None:
                blockers.append(
                    "Task completion requires context to be created first. "
                    "Use: manage_context(action='create', task_id='{}', data_title='{}', "
                    "data_description='Your work summary') to create context.".format(
                        task.id.value, task.title
                    )
                )
            
            # Check subtask completion
            subtasks = self._subtask_repository.find_by_parent_task_id(task.id)
            
            if subtasks:
                incomplete_subtasks = [
                    subtask for subtask in subtasks 
                    if not subtask.is_completed
                ]
                
                if incomplete_subtasks:
                    incomplete_count = len(incomplete_subtasks)
                    total_count = len(subtasks)
                    
                    blocker_msg = f"{incomplete_count} of {total_count} subtasks are incomplete"
                    
                    incomplete_titles = [st.title for st in incomplete_subtasks[:3]]
                    if incomplete_titles:
                        blocker_msg += " (including: "
                        if len(incomplete_titles) < incomplete_count:
                            blocker_msg += f"{', '.join(incomplete_titles)}, and {incomplete_count - len(incomplete_titles)} more"
                        else:
                            blocker_msg += f"{', '.join(incomplete_titles)}"
                        blocker_msg += ")"
                    
                    blocker_msg += ". Complete all subtasks first."
                    blockers.append(blocker_msg)
        
        except Exception as e:
            logger.error(f"Error checking completion blockers for task {task.id}: {e}")
            blockers.append(f"Error checking completion status: {str(e)}")
        
        return blockers
    
    def _create_context_required_error(self, task: Task) -> Dict[str, Any]:
        """Create a user-friendly context required error message."""
        return {
            "error": "Task completion requires context to be created first.",
            "explanation": "Context stores task progress and is required before completing tasks. This ensures work history is preserved.",
            "recovery_instructions": [
                "Create context for this task first",
                "Update the context with your progress", 
                "Then try completing the task again"
            ],
            "step_by_step_fix": [
                {
                    "step": 1,
                    "action": "Create context",
                    "command": f"manage_context(action='create', task_id='{task.id.value}', project_id='dhafnck_mcp')"
                },
                {
                    "step": 2,
                    "action": "Update context status",
                    "command": f"manage_context(action='update', task_id='{task.id.value}', data_status='done')"
                },
                {
                    "step": 3,
                    "action": "Complete task",
                    "command": f"manage_task(action='complete', task_id='{task.id.value}', completion_summary='Your summary here')"
                }
            ]
        }
    
    def _create_incomplete_subtasks_error(self, task: Task, incomplete_subtasks: list) -> Dict[str, Any]:
        """Create a user-friendly incomplete subtasks error message."""
        incomplete_count = len(incomplete_subtasks)
        total_subtasks = len(self._subtask_repository.find_by_parent_task_id(task.id))
        
        return {
            "error": "Cannot complete task while subtasks remain incomplete.",
            "explanation": "All subtasks must be completed before the parent task can be marked as done.",
            "details": {
                "incomplete_count": incomplete_count,
                "total_subtasks": total_subtasks,
                "incomplete_subtask_titles": [st.title for st in incomplete_subtasks[:3]]
            },
            "recovery_instructions": [
                "List all subtasks to see which are incomplete",
                "Complete each remaining subtask",
                "Then try completing the parent task again"
            ],
            "step_by_step_fix": [
                {
                    "step": 1,
                    "action": "List subtasks",
                    "command": f"manage_subtask(action='list', task_id='{task.id.value}')"
                },
                {
                    "step": 2,
                    "action": "Complete each incomplete subtask",
                    "command": f"manage_subtask(action='complete', task_id='{task.id.value}', subtask_id='subtask-id', completion_summary='Subtask completed')"
                },
                {
                    "step": 3,
                    "action": "Complete parent task",
                    "command": f"manage_task(action='complete', task_id='{task.id.value}', completion_summary='All subtasks completed')"
                }
            ]
        }
    
    def get_subtask_completion_summary(self, task: Task) -> dict:
        """
        Get a summary of subtask completion status for a task.
        
        Args:
            task: The task to check
            
        Returns:
            Dictionary with completion statistics
        """
        try:
            subtasks = self._subtask_repository.find_by_parent_task_id(task.id)
            
            if not subtasks:
                return {
                    "total": 0,
                    "completed": 0,
                    "incomplete": 0,
                    "completion_percentage": 100,  # No subtasks = 100% complete
                    "can_complete_parent": True
                }
            
            total = len(subtasks)
            completed = sum(1 for subtask in subtasks if subtask.is_completed)
            incomplete = total - completed
            completion_percentage = round((completed / total) * 100, 1) if total > 0 else 0
            
            return {
                "total": total,
                "completed": completed,
                "incomplete": incomplete,
                "completion_percentage": completion_percentage,
                "can_complete_parent": incomplete == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting subtask completion summary for task {task.id}: {e}")
            return {
                "total": 0,
                "completed": 0,
                "incomplete": 0,
                "completion_percentage": 0,
                "can_complete_parent": False,
                "error": str(e)
            }