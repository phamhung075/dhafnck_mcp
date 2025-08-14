"""Project Facade Factory

Factory for creating project application facades with proper dependency injection following DDD patterns.
"""

import logging
from typing import Optional, Dict
from ..facades.project_application_facade import ProjectApplicationFacade
from ..services.project_management_service import ProjectManagementService
from ...infrastructure.repositories.project_repository_factory import (
    ProjectRepositoryFactory, 
    GlobalRepositoryManager
)

logger = logging.getLogger(__name__)


class ProjectFacadeFactory:
    """
    Factory for creating project application facades with proper DDD dependency injection.
    
    This factory ensures proper layering and dependency direction:
    - Creates facades with injected services
    - Services are created with injected repositories
    - Repositories handle data persistence
    """
    
    def __init__(self, project_repository_factory: Optional[ProjectRepositoryFactory] = None):
        """
        Initialize the project facade factory.
        
        Args:
            project_repository_factory: Optional factory for creating project repositories
        """
        self._project_repository_factory = project_repository_factory
        self._facades_cache: Dict[str, ProjectApplicationFacade] = {}
        logger.info("ProjectFacadeFactory initialized")
    
    def create_project_facade(self, 
                            user_id: str = "default_id") -> ProjectApplicationFacade:
        """
        Create a project application facade with proper dependency injection.
        
        Args:
            user_id: User identifier
            
        Returns:
            ProjectApplicationFacade instance with injected dependencies
        """
        # Create cache key
        cache_key = f"{user_id}"
        
        # Check cache first
        if cache_key in self._facades_cache:
            logger.debug(f"Returning cached project facade for {cache_key}")
            return self._facades_cache[cache_key]
        
        # Create repository
        if self._project_repository_factory:
            project_repository = self._project_repository_factory.create(
                user_id=user_id
            )
        else:
            # Use global repository manager if no factory provided
            project_repository = GlobalRepositoryManager.get_default()
        
        # Create service with repository
        project_service = ProjectManagementService(project_repo=project_repository)
        
        # Create facade with service
        facade = ProjectApplicationFacade(project_service=project_service)
        
        # Cache the facade
        self._facades_cache[cache_key] = facade
        
        logger.info(f"Created new project facade for {cache_key}")
        return facade
    
    def clear_cache(self):
        """Clear the facades cache."""
        self._facades_cache.clear()
        logger.info("Project facades cache cleared")
    
    def get_cached_facade(self, user_id: str) -> Optional[ProjectApplicationFacade]:
        """
        Get a cached facade if available.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cached facade or None
        """
        cache_key = f"{user_id}"
        return self._facades_cache.get(cache_key)