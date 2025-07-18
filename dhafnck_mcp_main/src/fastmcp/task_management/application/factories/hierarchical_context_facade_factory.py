"""Hierarchical Context Facade Factory

Factory for creating hierarchical context facades with proper dependency injection.
This replaces the old context facade factory for the new hierarchical system.
"""

import logging
from typing import Optional, Dict, Any
from ..facades.hierarchical_context_facade import HierarchicalContextFacade
from ..services.hierarchical_context_service import HierarchicalContextService
from ..services.context_inheritance_service import ContextInheritanceService
from ..services.context_delegation_service import ContextDelegationService
from ..services.context_cache_service import ContextCacheService
from ...infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository
from ...infrastructure.repositories.hierarchical_context_repository_factory import HierarchicalContextRepositoryFactory

logger = logging.getLogger(__name__)


class HierarchicalContextFacadeFactory:
    """
    Factory for creating hierarchical context facades with proper DDD dependency injection.
    
    This factory ensures proper layering and dependency direction:
    - Creates facades with injected services
    - Services are created with injected repositories
    - Repositories handle data persistence
    """
    
    def __init__(self, repository: Optional[ORMHierarchicalContextRepository] = None):
        """
        Initialize the hierarchical context facade factory.
        
        Args:
            repository: Optional hierarchical context repository instance
        """
        if repository is None:
            factory = HierarchicalContextRepositoryFactory()
            self._repository = factory.create_hierarchical_context_repository()
        else:
            self._repository = repository
        self._facades_cache: Dict[str, HierarchicalContextFacade] = {}
        logger.info("HierarchicalContextFacadeFactory initialized")
    
    def create_facade(self, 
                     user_id: str = "default_id",
                     project_id: str = "default_project",
                     git_branch_id: str = None) -> HierarchicalContextFacade:
        """
        Create a hierarchical context facade with proper dependency injection.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            git_branch_id: Git branch identifier (UUID) - required
            
        Returns:
            HierarchicalContextFacade instance with injected dependencies
        """
        if not git_branch_id:
            raise ValueError("git_branch_id is required for creating facade")
            
        # Create cache key
        cache_key = f"{user_id}:{project_id}:{git_branch_id}"
        
        # Check cache first
        if cache_key in self._facades_cache:
            logger.debug(f"Returning cached hierarchical facade for {cache_key}")
            return self._facades_cache[cache_key]
        
        # Create services with shared repository
        hierarchy_service = HierarchicalContextService(repository=self._repository)
        inheritance_service = ContextInheritanceService(repository=self._repository)
        delegation_service = ContextDelegationService(repository=self._repository)
        cache_service = ContextCacheService(repository=self._repository)
        
        # Create facade with services
        facade = HierarchicalContextFacade(
            hierarchy_service=hierarchy_service,
            inheritance_service=inheritance_service,
            delegation_service=delegation_service,
            cache_service=cache_service
        )
        
        # Cache the facade
        self._facades_cache[cache_key] = facade
        
        logger.info(f"Created new hierarchical context facade for {cache_key}")
        return facade
    
    def clear_cache(self):
        """Clear the facades cache."""
        self._facades_cache.clear()
        logger.info("Hierarchical context facades cache cleared")
    
    def get_cached_facade(self, user_id: str, project_id: str, git_branch_id: str) -> Optional[HierarchicalContextFacade]:
        """
        Get a cached facade if available.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            git_branch_id: Git branch identifier (UUID)
            
        Returns:
            Cached facade or None
        """
        cache_key = f"{user_id}:{project_id}:{git_branch_id}"
        return self._facades_cache.get(cache_key)

    def create_service(self, 
                      user_id: str = "default_id",
                      project_id: str = "default_project", 
                      git_branch_id: str = None) -> HierarchicalContextService:
        """
        Create a hierarchical context service.
        
        This method provides backward compatibility for code expecting create_service().
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            git_branch_id: Git branch identifier (UUID)
            
        Returns:
            HierarchicalContextService instance
        """
        return HierarchicalContextService(repository=self._repository)

    def create_context_facade(self, 
                             user_id: str = "default_id",
                             project_id: str = "default_project",
                             git_branch_id: str = None) -> HierarchicalContextFacade:
        """
        Create a hierarchical context facade.
        
        This method provides backward compatibility for code expecting create_context_facade().
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            git_branch_id: Git branch identifier (UUID) - required
            
        Returns:
            HierarchicalContextFacade instance
        """
        return self.create_facade(user_id=user_id, project_id=project_id, git_branch_id=git_branch_id)