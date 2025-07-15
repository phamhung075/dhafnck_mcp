"""Cached Task Repository Implementation

This module demonstrates how to add caching to the task repository
for improved performance.
"""

import logging
from typing import List, Optional, Dict, Any

from .task_repository import TaskRepository
from ...cache import cached, cached_method, CachedRepository
from ....domain.entities import Task

logger = logging.getLogger(__name__)


class CachedTaskRepository(CachedRepository, TaskRepository):
    """
    Task repository with caching support.
    
    This implementation adds caching to frequently accessed methods
    while ensuring cache invalidation on updates.
    """
    
    def __init__(self, db_path: Optional[str] = None, git_branch_id: Optional[str] = None):
        """Initialize cached task repository"""
        # Initialize with a specific cache name
        super().__init__(
            db_path=db_path,
            git_branch_id=git_branch_id,
            cache_name='task_repository_cache'
        )
        logger.info(f"Initialized CachedTaskRepository with cache")
    
    @cached_method(ttl=300)  # Cache for 5 minutes
    def find_by_id(self, task_id: str) -> Optional[Task]:
        """
        Find task by ID with caching.
        
        Cache hit rate should be high for this method as tasks
        are often accessed multiple times in a workflow.
        """
        return super().find_by_id(task_id)
    
    @cached_method(ttl=60)  # Cache for 1 minute (lists change more frequently)
    def find_all(self) -> List[Task]:
        """Find all tasks with caching"""
        return super().find_all()
    
    @cached_method(ttl=120)  # Cache for 2 minutes
    def find_by_criteria(self, criteria: Dict[str, Any], limit: Optional[int] = None) -> List[Task]:
        """Find tasks by criteria with caching"""
        return super().find_by_criteria(criteria, limit)
    
    def save(self, task: Task) -> Task:
        """
        Save task and invalidate related cache entries.
        
        This ensures cache consistency when tasks are modified.
        """
        # Save the task
        result = super().save(task)
        
        # Invalidate cache entries
        self._invalidate_task_cache(str(task.id))
        
        # If task has a parent, invalidate parent cache too
        if hasattr(task, 'parent_task_id') and task.parent_task_id:
            self._invalidate_task_cache(str(task.parent_task_id))
        
        return result
    
    def update(self, task: Task) -> Task:
        """Update task and invalidate cache"""
        result = super().update(task)
        self._invalidate_task_cache(str(task.id))
        return result
    
    def delete(self, task_id: str) -> bool:
        """Delete task and invalidate cache"""
        # Get task first to check for parent
        task = self.find_by_id(task_id)
        
        result = super().delete(task_id)
        
        if result:
            self._invalidate_task_cache(task_id)
            
            # Invalidate parent cache if exists
            if task and hasattr(task, 'parent_task_id') and task.parent_task_id:
                self._invalidate_task_cache(str(task.parent_task_id))
        
        return result
    
    def _invalidate_task_cache(self, task_id: str):
        """
        Invalidate all cache entries related to a task.
        
        This includes:
        - Direct task lookups
        - List operations (since task might be in the list)
        - Criteria searches (task might match criteria)
        """
        # Invalidate specific task lookup
        self.invalidate_cache(f"find_by_id:{task_id}")
        
        # Invalidate list operations (conservative approach)
        self.invalidate_cache("find_all")
        self.invalidate_cache("find_by_criteria")
        
        logger.debug(f"Invalidated cache for task {task_id}")
    
    def warmup_cache(self, task_ids: List[str]):
        """
        Pre-populate cache with frequently accessed tasks.
        
        This can be called during application startup or after
        cache clear to improve initial performance.
        
        Args:
            task_ids: List of task IDs to preload
        """
        logger.info(f"Warming up cache with {len(task_ids)} tasks")
        
        for task_id in task_ids:
            try:
                # This will populate the cache
                self.find_by_id(task_id)
            except Exception as e:
                logger.warning(f"Failed to warmup cache for task {task_id}: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get repository performance statistics including cache stats"""
        stats = {
            'repository': self.__class__.__name__,
            'cache_stats': self.get_cache_stats()
        }
        
        # Add repository-specific stats if available
        if hasattr(super(), 'get_stats'):
            stats['repository_stats'] = super().get_stats()
        
        return stats


# Decorator for standalone functions
@cached(ttl=300, cache_name='task_cache')
def get_task_with_full_relations(repository: TaskRepository, task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get task with all relations loaded.
    
    This is an expensive operation that benefits from caching.
    """
    task = repository.find_by_id(task_id)
    if not task:
        return None
    
    # Load additional relations (example)
    return {
        'task': task,
        'subtasks': repository.find_subtasks(task_id) if hasattr(repository, 'find_subtasks') else [],
        'parent': repository.find_by_id(task.parent_task_id) if hasattr(task, 'parent_task_id') and task.parent_task_id else None
    }


# Cache configuration for different environments
def configure_task_cache(environment: str = 'production'):
    """
    Configure cache settings based on environment.
    
    Args:
        environment: 'development', 'staging', or 'production'
    """
    cache = get_cache('task_repository_cache')
    
    if environment == 'development':
        # Shorter TTL for development
        cache._default_ttl = 60  # 1 minute
        cache._max_size = 100
    elif environment == 'staging':
        cache._default_ttl = 180  # 3 minutes
        cache._max_size = 500
    else:  # production
        cache._default_ttl = 300  # 5 minutes
        cache._max_size = 1000
    
    logger.info(f"Configured task cache for {environment} environment")