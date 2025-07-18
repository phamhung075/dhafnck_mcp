"""Complete Task Use Case"""

from typing import Union, Dict, Any, Optional, List
import logging
from datetime import datetime, timezone

from ...domain.repositories.task_repository import TaskRepository
from ...domain.repositories.subtask_repository import SubtaskRepository
from ...domain.value_objects.task_id import TaskId
from ...domain.exceptions import TaskNotFoundError
from ...domain.exceptions.task_exceptions import TaskCompletionError
from ...domain.exceptions.vision_exceptions import MissingCompletionSummaryError
from ...domain.services.task_completion_service import TaskCompletionService
from ...domain.events import TaskUpdated
from ...interface.utils.error_handler import UserFriendlyErrorHandler
from ..services.hierarchical_context_service import HierarchicalContextService
# from ..services.context_validation_service import ContextValidationService  # TODO: Fix circular import

# Module-level logger
logger = logging.getLogger(__name__)

class CompleteTaskUseCase:
    """Use case for completing a task (marking all subtasks as completed and task status as done)"""
    
    def __init__(self, task_repository: TaskRepository, subtask_repository: Optional[SubtaskRepository] = None, 
                 hierarchical_context_service: Optional[HierarchicalContextService] = None):
        self._task_repository = task_repository
        self._subtask_repository = subtask_repository
        self._hierarchical_context_service = hierarchical_context_service
        # Only create completion service if both required dependencies are provided
        self._completion_service = TaskCompletionService(subtask_repository, hierarchical_context_service) if (subtask_repository and hierarchical_context_service) else None
        # Vision System validation service
        # self._validation_service = ContextValidationService()  # TODO: Fix circular import
        self._validation_service = None
    
    def execute(self, task_id: Union[str, int], 
                completion_summary: Optional[str] = None,
                testing_notes: Optional[str] = None,
                next_recommendations: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the complete task use case.
        
        Args:
            task_id: ID of the task to complete
            completion_summary: Summary of what was accomplished (REQUIRED by Vision System)
            testing_notes: Optional testing notes
            next_recommendations: Optional recommendations for next steps
            
        Returns:
            Dict with success status and details
        """
        # Convert to domain value object (handle both int and str)
        domain_task_id = TaskId.from_string(str(task_id))
        
        # Find the task
        task = self._task_repository.find_by_id(domain_task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")
        
        # Check if task is already completed
        if task.status.is_done():
            return {
                "success": False,
                "task_id": str(task_id),
                "message": f"Task {task_id} is already completed",
                "status": str(task.status)
            }
        
        try:
            # Validate task completion using domain service (if available)
            if self._completion_service:
                self._completion_service.validate_task_completion(task)
            elif self._subtask_repository:
                # Fallback validation: Check subtasks directly when completion service is not available
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
                        
                        return {
                            "success": False,
                            "task_id": str(task_id),
                            "message": error_msg,
                            "status": str(task.status)
                        }
            
            # Get context timestamp to validate context is newer than task
            # Only validate context timing if task has context_id (hasn't been updated after context creation)
            context_updated_at = None
            if task.context_id:  # Only check context timestamp if task has context_id
                try:
                    # Get context for the task using hierarchical context facade
                    import asyncio
                    from ..factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory
                    
                    # Use the hierarchical context facade to get context
                    hierarchical_facade = HierarchicalContextFacadeFactory().create_facade()
                    context_result = hierarchical_facade.get_context("task", str(task_id))
                    
                    if context_result.get("success") and "context" in context_result:
                        context = context_result["context"]
                        # Get updated_at timestamp from context
                        if "updated_at" in context:
                            # Parse the timestamp - it's in format "2025-07-13 01:14:22"
                            # Make it timezone-aware (UTC) to match task.updated_at
                            context_updated_at = datetime.strptime(context["updated_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                            logger.info(f"Context updated at: {context_updated_at}, Task updated at: {task.updated_at}")
                            logger.info(f"Validation check: context_updated_at <= task.updated_at? {context_updated_at <= task.updated_at}")
                        else:
                            logger.warning(f"No 'updated_at' field found in context: {context}")
                    else:
                        logger.warning(f"Context retrieval failed or no context field: {context_result}")
                except Exception as e:
                    logger.warning(f"Could not get context timestamp for task {task_id}: {e}")
                    import traceback
                    logger.warning(f"Traceback: {traceback.format_exc()}")
            
            # Complete the task (will complete all subtasks and set status to done)
            # Vision System requires completion_summary
            # Pass context_updated_at only if task has context_id (to avoid validation when context_id is cleared)
            task.complete_task(completion_summary=completion_summary, 
                             context_updated_at=context_updated_at if task.context_id else None)
            
            # Update context with completion information using hierarchical context
            if completion_summary:
                try:
                    from ..factories.hierarchical_context_facade_factory import HierarchicalContextFacadeFactory
                    
                    # Use the hierarchical context facade to update context
                    hierarchical_facade = HierarchicalContextFacadeFactory().create_facade()
                    
                    # Update context with completion summary
                    context_update = {
                        "progress": {
                            "completion_summary": completion_summary,
                            "testing_notes": testing_notes,
                            "next_recommendations": next_recommendations,
                            "completion_percentage": 100.0
                        }
                    }
                    
                    # Merge update into task context
                    hierarchical_facade.merge_context("task", str(task_id), context_update)
                except Exception as e:
                    logger.warning(f"Could not update context with completion summary: {e}")
            
        except MissingCompletionSummaryError as e:
            # Vision System enforcement - provide helpful error message
            return {
                "success": False,
                "task_id": str(task_id),
                "message": str(e),
                "status": str(task.status),
                "hint": "Use the 'complete_task_with_context' action or provide 'completion_summary' parameter"
            }
        except TaskCompletionError as e:
            return {
                "success": False,
                "task_id": str(task_id),
                "message": str(e),
                "status": str(task.status)
            }
        except ValueError as e:
            # Handle context validation errors from task.complete_task()
            error_response = UserFriendlyErrorHandler.handle_error(
                e, 
                "task completion",
                {"task_id": str(task_id), "project_id": "dhafnck_mcp"}
            )
            
            # Merge the error response with task-specific information
            error_response.update({
                "task_id": str(task_id),
                "status": str(task.status)
            })
            
            return error_response
        
        # Save the task
        self._task_repository.save(task)
        
        # Update dependent tasks (tasks that depend on this completed task)
        self._update_dependent_tasks(task)
        
        # Handle domain events
        events = task.get_events()
        for event in events:
            if isinstance(event, TaskUpdated):
                # Could trigger notifications, logging, etc.
                pass
        
        # Get subtask progress for the response (both legacy and new subtasks)
        legacy_progress = task.get_subtask_progress()
        new_subtask_summary = None
        if self._completion_service:
            new_subtask_summary = self._completion_service.get_subtask_completion_summary(task)
        elif self._subtask_repository:
            # Fallback: Create subtask summary directly from repository when completion service is not available
            try:
                subtasks = self._subtask_repository.find_by_parent_task_id(task.id)
                if subtasks:
                    total = len(subtasks)
                    completed = sum(1 for subtask in subtasks if subtask.is_completed)
                    incomplete = total - completed
                    completion_percentage = round((completed / total) * 100, 1) if total > 0 else 0
                    
                    new_subtask_summary = {
                        "total": total,
                        "completed": completed,
                        "incomplete": incomplete,
                        "completion_percentage": completion_percentage,
                        "can_complete_parent": incomplete == 0
                    }
                else:
                    # No subtasks case
                    new_subtask_summary = {
                        "total": 0,
                        "completed": 0,
                        "incomplete": 0,
                        "completion_percentage": 100,  # No subtasks = 100% complete
                        "can_complete_parent": True
                    }
            except Exception as e:
                logger.warning(f"Error generating fallback subtask summary for task {task_id}: {e}")
        
        # Return success response with required message format
        response = {
            "success": True,
            "task_id": str(task_id),
            "status": str(task.status),
            "subtask_progress": legacy_progress,
            "message": f"task {task_id} done, can next_task"
        }
        
        # Add subtask summary if available
        if new_subtask_summary:
            response["subtask_summary"] = new_subtask_summary
            
        return response
    
    def _update_dependent_tasks(self, completed_task):
        """
        Update tasks that depend on the completed task.
        
        This method finds all tasks that have the completed task as a dependency
        and updates their status if all their dependencies are now satisfied.
        
        Args:
            completed_task: The task that was just completed
        """
        try:
            logger.info(f"Updating dependent tasks for completed task {completed_task.id}")
            
            # Find all tasks that might depend on this completed task
            # We need to search through all tasks to find dependencies
            all_tasks = self._task_repository.find_all()
            
            dependent_tasks = []
            for task in all_tasks:
                if hasattr(task, 'dependencies') and task.dependencies:
                    # Check if this task depends on the completed task
                    for dependency in task.dependencies:
                        dependency_id = str(dependency) if hasattr(dependency, 'value') else str(dependency)
                        if dependency_id == str(completed_task.id):
                            dependent_tasks.append(task)
                            break
                elif hasattr(task, 'get_dependency_ids') and task.get_dependency_ids():
                    # Alternative way to check dependencies
                    if str(completed_task.id) in task.get_dependency_ids():
                        dependent_tasks.append(task)
            
            logger.info(f"Found {len(dependent_tasks)} tasks dependent on {completed_task.id}")
            
            # Update each dependent task
            for dependent_task in dependent_tasks:
                self._update_single_dependent_task(dependent_task, completed_task, all_tasks)
                
        except Exception as e:
            logger.error(f"Error updating dependent tasks for {completed_task.id}: {e}")
            # Don't fail the entire completion operation for this
    
    def _update_single_dependent_task(self, dependent_task, completed_task, all_tasks):
        """
        Update a single dependent task based on the completion of a dependency.
        
        Args:
            dependent_task: The task that depends on the completed task
            completed_task: The task that was just completed
            all_tasks: List of all tasks (for dependency checking)
        """
        try:
            # Check if all dependencies of the dependent task are now satisfied
            all_dependencies_complete = self._check_all_dependencies_complete(dependent_task, all_tasks)
            
            original_status = str(dependent_task.status)
            
            # If all dependencies are complete and task is blocked, unblock it
            if all_dependencies_complete and hasattr(dependent_task.status, 'value'):
                if dependent_task.status.value == 'blocked':
                    # Unblock the task - set to todo
                    from ...domain.value_objects.task_status import TaskStatus
                    dependent_task.status = TaskStatus.todo()
                    
                    # Save the updated task
                    self._task_repository.save(dependent_task)
                    
                    logger.info(f"Task {dependent_task.id} unblocked: all dependencies completed")
                    logger.info(f"Status changed from {original_status} to {dependent_task.status}")
                elif dependent_task.status.value == 'todo':
                    logger.info(f"Task {dependent_task.id} ready to start: all dependencies completed")
                else:
                    logger.debug(f"Task {dependent_task.id} status is {dependent_task.status.value} - no change needed")
            else:
                logger.debug(f"Task {dependent_task.id} still has incomplete dependencies")
                
        except Exception as e:
            logger.error(f"Error updating dependent task {dependent_task.id}: {e}")
    
    def _check_all_dependencies_complete(self, task, all_tasks: List) -> bool:
        """
        Check if all dependencies of a task are completed.
        
        Args:
            task: The task to check
            all_tasks: List of all tasks
            
        Returns:
            True if all dependencies are completed, False otherwise
        """
        try:
            # Get task dependencies
            dependency_ids = []
            
            if hasattr(task, 'dependencies') and task.dependencies:
                dependency_ids = [str(dep) if hasattr(dep, 'value') else str(dep) for dep in task.dependencies]
            elif hasattr(task, 'get_dependency_ids'):
                dependency_ids = task.get_dependency_ids()
            
            if not dependency_ids:
                return True  # No dependencies means all are satisfied
            
            # Check each dependency
            for dep_id in dependency_ids:
                # Find the dependency task
                dep_task = None
                for t in all_tasks:
                    if str(t.id) == dep_id:
                        dep_task = t
                        break
                
                if not dep_task:
                    logger.warning(f"Dependency task {dep_id} not found for task {task.id}")
                    return False  # Missing dependency means not all complete
                
                # Check if dependency is completed
                if hasattr(dep_task.status, 'is_done') and not dep_task.status.is_done():
                    return False  # Found incomplete dependency
                elif hasattr(dep_task.status, 'value') and dep_task.status.value != 'done':
                    return False  # Found incomplete dependency
            
            return True  # All dependencies are completed
            
        except Exception as e:
            logger.error(f"Error checking dependencies for task {task.id}: {e}")
            return False 