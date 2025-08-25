"""
Unified Context Facade Factory

Factory for creating UnifiedContextFacade instances with proper dependency injection.
"""

import logging
from typing import Optional

from ..facades.unified_context_facade import UnifiedContextFacade
from ..services.unified_context_service import UnifiedContextService
from ...infrastructure.repositories.global_context_repository_user_scoped import GlobalContextRepository
from ...infrastructure.repositories.project_context_repository_user_scoped import ProjectContextRepository
from ...infrastructure.repositories.branch_context_repository import BranchContextRepository
from ...infrastructure.repositories.task_context_repository import TaskContextRepository
from ..services.context_cache_service import ContextCacheService
from ..services.context_inheritance_service import ContextInheritanceService
from ..services.context_delegation_service import ContextDelegationService
from ..services.context_validation_service import ContextValidationService
from ...infrastructure.database.database_config import get_db_config
from ...infrastructure.database.models import GLOBAL_SINGLETON_UUID

logger = logging.getLogger(__name__)


class UnifiedContextFacadeFactory:
    """
    Factory for creating UnifiedContextFacade instances.
    
    Manages dependency injection and ensures proper initialization
    of all required services and repositories.
    
    Implements singleton pattern to avoid expensive repeated initialization.
    """
    
    # Class-level singleton instance
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls, session_factory=None):
        """
        Get the singleton instance of the factory.
        
        This is the preferred way to get the factory instance.
        
        Args:
            session_factory: Optional session factory (only used on first call)
            
        Returns:
            UnifiedContextFacadeFactory: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls(session_factory)
        return cls._instance
    
    def __init__(self, session_factory=None):
        """
        Initialize factory with optional session factory.
        
        Args:
            session_factory: SQLAlchemy session factory for database access
        """
        # Skip initialization if already done (singleton pattern)
        if self._initialized:
            return
            
        self.session_factory = None
        self.unified_service = None
        
        # Try to get database config, but handle unavailability
        if session_factory is None:
            try:
                db_config = get_db_config()
                session_factory = db_config.SessionLocal
            except Exception as e:
                logger.warning(f"Database not available, using mock context service: {e}")
                # Create a minimal mock unified service
                self._create_mock_service()
                # Mark as initialized even with mock service
                UnifiedContextFacadeFactory._initialized = True
                return
        
        self.session_factory = session_factory
        
        try:
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
            
            logger.info("UnifiedContextFacadeFactory initialized with database")
            # Mark as initialized for singleton pattern
            UnifiedContextFacadeFactory._initialized = True
        except Exception as e:
            logger.warning(f"Failed to initialize with database, using mock service: {e}")
            self._create_mock_service()
            # Mark as initialized even with mock service
            UnifiedContextFacadeFactory._initialized = True
    
    def _create_mock_service(self):
        """Create a mock unified service for database-less operation"""
        from ..services.mock_unified_context_service import MockUnifiedContextService
        self.unified_service = MockUnifiedContextService()
        logger.warning("Using MockUnifiedContextService - context operations will have limited functionality")
    
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
        # Create user-scoped service if user_id is provided
        if user_id:
            scoped_service = self.unified_service.with_user(user_id)
        else:
            scoped_service = self.unified_service
            
        return UnifiedContextFacade(
            unified_service=scoped_service,
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
                existing_context = self.global_repo.get(GLOBAL_SINGLETON_UUID)
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
                context_id=GLOBAL_SINGLETON_UUID,
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