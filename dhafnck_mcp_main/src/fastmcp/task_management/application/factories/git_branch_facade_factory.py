"""Git Branch Facade Factory

Factory for creating git branch application facades with proper dependency injection following DDD patterns.
"""

import logging
from typing import Optional, Dict
from ..facades.git_branch_application_facade import GitBranchApplicationFacade
from ...domain.repositories.git_branch_repository import GitBranchRepository
from ...infrastructure.repositories.git_branch_repository_factory import GitBranchRepositoryFactory

logger = logging.getLogger(__name__)


class GitBranchFacadeFactory:
    """
    Factory for creating git branch application facades with proper DDD dependency injection.
    
    This factory ensures proper layering and dependency direction:
    - Creates facades with injected repositories
    - Repositories handle data persistence
    """
    
    def __init__(self, git_branch_repository_factory: Optional[GitBranchRepositoryFactory] = None):
        """
        Initialize the git branch facade factory.
        
        Args:
            git_branch_repository_factory: Optional factory for creating git branch repositories
        """
        self._git_branch_repository_factory = git_branch_repository_factory
        self._facades_cache: Dict[str, GitBranchApplicationFacade] = {}
        logger.info("GitBranchFacadeFactory initialized")
    
    def create_git_branch_facade(self, 
                                project_id: str = "default_project") -> GitBranchApplicationFacade:
        """
        Create a git branch application facade with proper dependency injection.
        
        Args:
            project_id: Project identifier for scoping
            
        Returns:
            GitBranchApplicationFacade instance with injected dependencies
        """
        # Create cache key
        cache_key = f"{project_id}"
        
        # Check cache first
        if cache_key in self._facades_cache:
            logger.debug(f"Returning cached git branch facade for {cache_key}")
            return self._facades_cache[cache_key]
        
        # Create TaskTreeService - it will get its own project repository
        from ..services.task_tree_service import TaskTreeService
        task_tree_service = TaskTreeService()
        
        # Create facade with service and project_id
        facade = GitBranchApplicationFacade(task_tree_service=task_tree_service, project_id=project_id)
        
        # Cache the facade
        self._facades_cache[cache_key] = facade
        
        logger.info(f"Created new git branch facade for {cache_key}")
        return facade
    
    def clear_cache(self):
        """Clear the facades cache."""
        self._facades_cache.clear()
        logger.info("Git branch facades cache cleared")
    
    def get_cached_facade(self, project_id: str) -> Optional[GitBranchApplicationFacade]:
        """
        Get a cached facade if available.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Cached facade or None
        """
        cache_key = f"{project_id}"
        return self._facades_cache.get(cache_key)