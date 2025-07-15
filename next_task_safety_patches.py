"""
Comprehensive fixes for manage_task next action failures

Fixes applied:
1. File system permission issues - use project-relative paths
2. NoneType iteration issues - add comprehensive null safety
3. Priority calculation robustness - safe defaults and error handling
"""

import os
import tempfile
import logging
from typing import List, Optional, Any, Dict

logger = logging.getLogger(__name__)

class NextTaskSafetyPatches:
    """Safety patches for NextTaskUseCase to prevent common errors"""
    
    @staticmethod
    def safe_get_context_path(task_id: str, project_path: Optional[str] = None) -> str:
        """Get context path avoiding user home directory access"""
        try:
            if project_path and os.path.exists(project_path):
                context_dir = os.path.join(project_path, ".task_context")
            else:
                # Use current working directory
                context_dir = os.path.join(os.getcwd(), ".task_context")
                
            # Create directory with proper error handling
            try:
                os.makedirs(context_dir, exist_ok=True)
                # Test write access
                test_file = os.path.join(context_dir, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except (PermissionError, OSError):
                # Fall back to temp directory
                context_dir = tempfile.mkdtemp(prefix="task_context_")
                logger.warning(f"Using temp directory for context: {context_dir}")
                
            return os.path.join(context_dir, f"{task_id}.json")
            
        except Exception as e:
            logger.error(f"Context path error: {e}")
            # Ultimate fallback
            fd, path = tempfile.mkstemp(suffix=f"_{task_id}.json", prefix="ctx_")
            os.close(fd)
            return path
    
    @staticmethod
    def safe_filter_collection(items: Any, filter_func) -> List:
        """Safely filter a collection with null checks"""
        if not items:
            return []
            
        # Convert to list if needed
        if not isinstance(items, list):
            try:
                items = list(items)
            except (TypeError, AttributeError):
                logger.warning(f"Could not convert {type(items)} to list")
                return []
        
        try:
            return [item for item in items if filter_func(item)]
        except Exception as e:
            logger.warning(f"Filter error: {e}")
            return []
    
    @staticmethod
    def safe_attribute_check(obj: Any, attr: str, value: Any) -> bool:
        """Safely check if object attribute contains value"""
        try:
            if not obj or not hasattr(obj, attr):
                return False
                
            obj_value = getattr(obj, attr, None)
            if not obj_value:
                return False
                
            # Handle different collection types
            if isinstance(obj_value, (list, tuple)):
                return value in obj_value
            elif isinstance(obj_value, str):
                return value in obj_value or str(value) in obj_value
            else:
                return str(value) == str(obj_value)
                
        except Exception as e:
            logger.debug(f"Attribute check error for {attr}: {e}")
            return False
    
    @staticmethod
    def safe_priority_score(task: Any) -> int:
        """Calculate priority score with comprehensive safety"""
        default_score = 50
        
        try:
            if not task:
                return default_score
                
            # Get priority with multiple fallback attempts
            priority = None
            for attr in ['priority', 'Priority', '_priority']:
                if hasattr(task, attr):
                    priority = getattr(task, attr)
                    break
                    
            if not priority:
                return default_score
                
            # Extract priority value safely
            priority_value = None
            if hasattr(priority, 'value'):
                priority_value = priority.value
            elif hasattr(priority, 'name'):
                priority_value = priority.name
            else:
                priority_value = str(priority)
                
            if not priority_value:
                return default_score
                
            # Normalize and score
            priority_str = str(priority_value).lower().strip()
            
            priority_scores = {
                'critical': 100,
                'urgent': 80,
                'high': 60,
                'medium': 50,
                'normal': 50,
                'low': 20,
                'minimal': 10
            }
            
            return priority_scores.get(priority_str, default_score)
            
        except Exception as e:
            logger.debug(f"Priority calculation error: {e}")
            return default_score

# Patch functions for the NextTaskUseCase
def apply_safety_patches():
    """Apply all safety patches to prevent common errors"""
    import sys
    
    # Only apply if not already applied
    if hasattr(apply_safety_patches, '_applied'):
        return
        
    try:
        # Import the actual use case
        from fastmcp.task_management.application.use_cases.next_task import NextTaskUseCase
        
        # Store original methods
        if not hasattr(NextTaskUseCase, '_original_apply_filters'):
            NextTaskUseCase._original_apply_filters = NextTaskUseCase._apply_filters
            NextTaskUseCase._original_sort_tasks_by_priority = NextTaskUseCase._sort_tasks_by_priority
        
        # Patch _apply_filters method
        def safe_apply_filters(self, tasks, assignee=None, project_id=None, labels=None):
            """Patched version with null safety"""
            try:
                if not tasks:
                    return []
                    
                filtered_tasks = list(tasks)
                patches = NextTaskSafetyPatches()
                
                # Safe assignee filtering
                if assignee:
                    filtered_tasks = patches.safe_filter_collection(
                        filtered_tasks,
                        lambda task: patches.safe_attribute_check(task, 'assignees', assignee)
                    )
                
                # Safe label filtering
                if labels:
                    label_list = labels if isinstance(labels, list) else [labels]
                    for label in label_list:
                        filtered_tasks = patches.safe_filter_collection(
                            filtered_tasks,
                            lambda task: patches.safe_attribute_check(task, 'labels', label)
                        )
                
                return filtered_tasks
                
            except Exception as e:
                logger.error(f"Filter error, returning empty list: {e}")
                return []
        
        # Patch _sort_tasks_by_priority method  
        def safe_sort_tasks_by_priority(self, tasks):
            """Patched version with null safety"""
            try:
                if not tasks:
                    return []
                    
                patches = NextTaskSafetyPatches()
                
                def safe_sort_key(task):
                    try:
                        priority_score = patches.safe_priority_score(task)
                        
                        # Status score (todo=0, in_progress=1, others=2)
                        status_score = 2  # default
                        if hasattr(task, 'status'):
                            status = getattr(task.status, 'value', str(task.status)).lower()
                            if status == 'todo':
                                status_score = 0
                            elif status == 'in_progress':
                                status_score = 1
                                
                        # Return inverted priority (higher priority = lower number for ascending sort)
                        return (100 - priority_score, status_score)
                    except Exception as e:
                        logger.debug(f"Sort key error for task: {e}")
                        return (50, 2)  # default sort position
                
                return sorted(tasks, key=safe_sort_key)
                
            except Exception as e:
                logger.error(f"Sort error, returning original list: {e}")
                return list(tasks) if tasks else []
        
        # Apply patches
        NextTaskUseCase._apply_filters = safe_apply_filters
        NextTaskUseCase._sort_tasks_by_priority = safe_sort_tasks_by_priority
        
        # Mark as applied
        apply_safety_patches._applied = True
        logger.info("NextTaskUseCase safety patches applied successfully")
        
    except ImportError as e:
        logger.info(f"Could not import NextTaskUseCase for patching: {e}")
    except Exception as e:
        logger.error(f"Error applying safety patches: {e}")

# Apply patches on import
apply_safety_patches()
