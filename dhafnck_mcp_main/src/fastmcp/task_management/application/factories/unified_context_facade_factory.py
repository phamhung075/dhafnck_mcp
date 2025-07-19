"""
Unified Context Facade Factory

Factory for creating UnifiedContextFacade instances with proper dependency injection.
"""

import logging
from typing import Optional

from ..facades.unified_context_facade import UnifiedContextFacade
from ..services.unified_context_service import UnifiedContextService
from ...infrastructure.repositories.global_context_repository import GlobalContextRepository
from ...infrastructure.repositories.project_context_repository import ProjectContextRepository
from ...infrastructure.repositories.branch_context_repository import BranchContextRepository
from ...infrastructure.repositories.task_context_repository import TaskContextRepository
from ..services.context_cache_service import ContextCacheService
from ..services.context_inheritance_service import ContextInheritanceService
from ..services.context_delegation_service import ContextDelegationService
from ..services.context_validation_service import ContextValidationService
from ...infrastructure.database.database_config import get_db_config

logger = logging.getLogger(__name__)


class UnifiedContextFacadeFactory:
    """
    Factory for creating UnifiedContextFacade instances.
    
    Manages dependency injection and ensures proper initialization
    of all required services and repositories.
    """
    
    def __init__(self, session_factory=None):
        """
        Initialize factory with optional session factory.
        
        Args:
            session_factory: SQLAlchemy session factory for database access
        """
        if session_factory is None:
            db_config = get_db_config()
            session_factory = db_config.SessionLocal
        
        self.session_factory = session_factory
        
        # Initialize repositories
        self.global_repo = GlobalContextRepository(session_factory)
        self.project_repo = ProjectContextRepository(session_factory)
        self.branch_repo = BranchContextRepository(session_factory)
        self.task_repo = TaskContextRepository(session_factory)
        
        # Initialize services
        self.cache_service = ContextCacheService()
        
        # Repository map for services
        repo_map = {
            "global": self.global_repo,
            "project": self.project_repo,
            "branch": self.branch_repo,
            "task": self.task_repo
        }
        
        self.inheritance_service = ContextInheritanceService(repo_map)
        self.delegation_service = ContextDelegationService(repo_map)
        self.validation_service = ContextValidationService()
        
        # Initialize unified service
        self.unified_service = UnifiedContextService(
            global_context_repository=self.global_repo,
            project_context_repository=self.project_repo,
            branch_context_repository=self.branch_repo,
            task_context_repository=self.task_repo,
            cache_service=self.cache_service,
            inheritance_service=self.inheritance_service,
            delegation_service=self.delegation_service,
            validation_service=self.validation_service
        )
        
        logger.info("UnifiedContextFacadeFactory initialized")
    
    def create_facade(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        git_branch_id: Optional[str] = None
    ) -> UnifiedContextFacade:
        """
        Create a UnifiedContextFacade instance.
        
        Args:
            user_id: User identifier for context scoping
            project_id: Project identifier for context scoping
            git_branch_id: Git branch UUID for context scoping
            
        Returns:
            UnifiedContextFacade instance configured with the provided scope
        """
        return UnifiedContextFacade(
            unified_service=self.unified_service,
            user_id=user_id,
            project_id=project_id,
            git_branch_id=git_branch_id
        )
    
    def create_unified_service(self) -> UnifiedContextService:
        """
        Get the unified context service directly.
        
        Returns:
            UnifiedContextService instance
        """
        return self.unified_service
    
    # Backward compatibility methods
    def create_hierarchical_context_repository(self):
        """
        Legacy method for backward compatibility.
        Returns the unified service instead of a repository.
        """
        return self.unified_service
        
    def create_service(self, user_id: str = None, project_id: str = None, git_branch_id: str = None):
        """
        Legacy method for backward compatibility.
        Alias for create_facade.
        """
        return self.create_facade(user_id=user_id, project_id=project_id, git_branch_id=git_branch_id)
    
    def create_context_facade(self, user_id: str = None, project_id: str = None, git_branch_id: str = None):
        """
        Legacy method for backward compatibility.
        Alias for create_facade.
        """
        return self.create_facade(user_id=user_id, project_id=project_id, git_branch_id=git_branch_id)
    
    def auto_create_global_context(self) -> bool:
        """
        Auto-create global context if it doesn't exist.
        
        This method ensures the global singleton context exists for the hierarchical
        context system to function properly. It's safe to call multiple times.
        
        Returns:
            bool: True if global context was created or already exists, False if creation failed
        """
        try:
            # Check if global context already exists
            try:
                existing_context = self.global_repo.get("global_singleton")
                if existing_context:
                    logger.info("Global context already exists")
                    return True
            except Exception:
                # Context doesn't exist, continue with creation
                pass
            
            # Create default global context
            default_global_data = {
                "organization_name": "Default Organization",
                "global_settings": {
                    "autonomous_rules": {},
                    "security_policies": {},
                    "coding_standards": {},
                    "workflow_templates": {},
                    "delegation_rules": {}
                }
            }
            
            # Create facade and use it to create global context
            facade = self.create_facade()
            result = facade.create_context(
                level="global",
                context_id="global_singleton",
                data=default_global_data
            )
            
            if result.get("success", False):
                logger.info("Global context auto-created successfully")
                return True
            else:
                logger.warning(f"Failed to auto-create global context: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.warning(f"Exception during global context auto-creation: {e}")
            return False