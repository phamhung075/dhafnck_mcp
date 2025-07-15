"""Project Repository Factory - Clean DDD Implementation"""

import os
import logging
from typing import Optional, Dict, Any, Type
from enum import Enum

from ...domain.repositories.project_repository import ProjectRepository
from .sqlite.project_repository import SQLiteProjectRepository

logger = logging.getLogger(__name__)


class RepositoryType(Enum):
    """Available repository implementation types"""
    SQLITE = "sqlite"
    IN_MEMORY = "in_memory"
    MOCK = "mock"


class ProjectRepositoryFactory:
    """Factory for creating project repository instances following DDD principles"""
    
    _instances: Dict[str, ProjectRepository] = {}
    _repository_types: Dict[RepositoryType, Type[ProjectRepository]] = {
        RepositoryType.SQLITE: SQLiteProjectRepository,
    }
    
    @classmethod
    def create(
        cls,
        repository_type: Optional[RepositoryType] = None,
        user_id: str = "default_id",
        db_path: Optional[str] = None,
        **kwargs
    ) -> ProjectRepository:
        """
        Create a project repository instance
        
        Args:
            repository_type: Type of repository to create
            user_id: User identifier for multi-user support
            db_path: Database path for SQLite repositories
            **kwargs: Additional repository-specific parameters
            
        Returns:
            ProjectRepository instance
        """
        # Use default repository type if not specified
        if repository_type is None:
            repository_type = cls._get_default_type()
        
        # Generate cache key
        cache_key = cls._generate_cache_key(repository_type, user_id, db_path)
        
        # Return cached instance if available
        if cache_key in cls._instances:
            logger.debug(f"Returning cached repository: {cache_key}")
            return cls._instances[cache_key]
        
        # Create new instance
        repository = cls._create_instance(repository_type, user_id, db_path, **kwargs)
        
        # Cache the instance
        cls._instances[cache_key] = repository
        
        logger.info(f"Created repository: {repository_type.value} for user: {user_id}")
        return repository
    
    @classmethod
    def _get_default_type(cls) -> RepositoryType:
        """Get default repository type from environment"""
        env_type = os.getenv("MCP_PROJECT_REPOSITORY_TYPE", "sqlite").lower()
        
        try:
            return RepositoryType(env_type)
        except ValueError:
            logger.warning(f"Invalid repository type '{env_type}', using SQLite")
            return RepositoryType.SQLITE
    
    @classmethod
    def _generate_cache_key(
        cls, 
        repository_type: RepositoryType, 
        user_id: str, 
        db_path: Optional[str]
    ) -> str:
        """Generate cache key for repository instance"""
        return f"{repository_type.value}:{user_id}:{db_path or 'default'}"
    
    @classmethod
    def _create_instance(
        cls,
        repository_type: RepositoryType,
        user_id: str,
        db_path: Optional[str],
        **kwargs
    ) -> ProjectRepository:
        """Create repository instance of specified type"""
        
        if repository_type not in cls._repository_types:
            raise ValueError(f"Unsupported repository type: {repository_type.value}")
        
        repository_class = cls._repository_types[repository_type]
        
        try:
            if repository_type == RepositoryType.SQLITE:
                return repository_class(db_path=db_path, user_id=user_id, **kwargs)
            else:
                return repository_class(user_id=user_id, **kwargs)
                
        except Exception as e:
            logger.error(f"Failed to create {repository_type.value} repository: {e}")
            # Fallback to SQLite if possible
            if repository_type != RepositoryType.SQLITE:
                logger.info("Falling back to SQLite repository")
                return SQLiteProjectRepository(db_path=db_path, user_id=user_id)
            raise
    
    @classmethod
    def register_type(
        cls,
        repository_type: RepositoryType,
        repository_class: Type[ProjectRepository]
    ) -> None:
        """Register a new repository type"""
        cls._repository_types[repository_type] = repository_class
        logger.info(f"Registered repository type: {repository_type.value}")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached instances"""
        cls._instances.clear()
        logger.info("Repository cache cleared")
    
    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get factory information"""
        return {
            "available_types": [rt.value for rt in cls._repository_types.keys()],
            "cached_instances": len(cls._instances),
            "default_type": cls._get_default_type().value,
            "environment": {
                "MCP_PROJECT_REPOSITORY_TYPE": os.getenv("MCP_PROJECT_REPOSITORY_TYPE"),
                "MCP_DB_PATH": os.getenv("MCP_DB_PATH")
            }
        }


class RepositoryConfig:
    """Configuration for repository creation"""
    
    def __init__(
        self,
        repository_type: Optional[str] = None,
        user_id: str = "default_id",
        db_path: Optional[str] = None,
        **kwargs
    ):
        self.repository_type = self._validate_type(repository_type)
        self.user_id = user_id
        self.db_path = db_path
        self.kwargs = kwargs
    
    def _validate_type(self, repository_type: Optional[str]) -> RepositoryType:
        """Validate and convert repository type"""
        if repository_type is None:
            return RepositoryType.SQLITE
        
        try:
            return RepositoryType(repository_type.lower())
        except ValueError:
            logger.warning(f"Invalid repository type '{repository_type}', using SQLite")
            return RepositoryType.SQLITE
    
    def create_repository(self) -> ProjectRepository:
        """Create repository from this configuration"""
        return ProjectRepositoryFactory.create(
            repository_type=self.repository_type,
            user_id=self.user_id,
            db_path=self.db_path,
            **self.kwargs
        )
    
    @classmethod
    def from_environment(cls) -> 'RepositoryConfig':
        """Create configuration from environment variables"""
        return cls(
            repository_type=os.getenv("MCP_PROJECT_REPOSITORY_TYPE"),
            user_id=os.getenv("MCP_USER_ID", "default_id"),
            db_path=os.getenv("MCP_DB_PATH")
        )


class GlobalRepositoryManager:
    """Global repository instance manager"""
    
    _default_repository: Optional[ProjectRepository] = None
    _user_repositories: Dict[str, ProjectRepository] = {}
    
    @classmethod
    def get_default(cls) -> ProjectRepository:
        """Get default global repository"""
        if cls._default_repository is None:
            cls._default_repository = ProjectRepositoryFactory.create()
        return cls._default_repository
    
    @classmethod
    def get_for_user(cls, user_id: str) -> ProjectRepository:
        """Get repository for specific user"""
        if user_id not in cls._user_repositories:
            cls._user_repositories[user_id] = ProjectRepositoryFactory.create(user_id=user_id)
        return cls._user_repositories[user_id]
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all managed repositories"""
        cls._default_repository = None
        cls._user_repositories.clear()
        ProjectRepositoryFactory.clear_cache()
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get manager status"""
        return {
            "has_default": cls._default_repository is not None,
            "user_count": len(cls._user_repositories),
            "factory_info": ProjectRepositoryFactory.get_info()
        }


# Convenience functions for clean API

def create_project_repository(
    user_id: str = "default_id",
    repository_type: Optional[str] = None,
    db_path: Optional[str] = None
) -> ProjectRepository:
    """Create a project repository instance"""
    repo_type = RepositoryType(repository_type) if repository_type else None
    return ProjectRepositoryFactory.create(
        repository_type=repo_type,
        user_id=user_id,
        db_path=db_path
    )


def get_sqlite_repository(
    user_id: str = "default_id",
    db_path: Optional[str] = None
) -> SQLiteProjectRepository:
    """Get SQLite project repository"""
    return ProjectRepositoryFactory.create(
        repository_type=RepositoryType.SQLITE,
        user_id=user_id,
        db_path=db_path
    )


def get_default_repository() -> ProjectRepository:
    """Get default global repository"""
    return GlobalRepositoryManager.get_default()


def get_user_repository(user_id: str) -> ProjectRepository:
    """Get repository for specific user"""
    return GlobalRepositoryManager.get_for_user(user_id)


# Export clean API
__all__ = [
    "ProjectRepositoryFactory",
    "RepositoryType", 
    "RepositoryConfig",
    "GlobalRepositoryManager",
    "create_project_repository",
    "get_sqlite_repository",
    "get_default_repository",
    "get_user_repository"
] 