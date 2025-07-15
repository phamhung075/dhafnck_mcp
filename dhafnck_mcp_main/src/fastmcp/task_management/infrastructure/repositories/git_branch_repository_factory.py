"""Git Branch Repository Factory

Factory for creating git branch repositories with proper dependency injection.
"""

import os
import logging
from typing import Dict, Any, Optional, Type
from enum import Enum

from ...domain.repositories.git_branch_repository import GitBranchRepository

logger = logging.getLogger(__name__)


class GitBranchRepositoryType(Enum):
    """Available git branch repository types"""
    JSON = "json"
    SQLITE = "sqlite"
    MEMORY = "memory"


class GitBranchRepositoryFactory:
    """Factory for creating git branch repositories"""
    
    _repository_types: Dict[GitBranchRepositoryType, Type[GitBranchRepository]] = {}
    _instances: Dict[str, GitBranchRepository] = {}
    
    @classmethod
    def create(
        cls,
        repository_type: Optional[GitBranchRepositoryType] = None,
        user_id: str = "default_id",
        **kwargs
    ) -> GitBranchRepository:
        """
        Create a git branch repository instance.
        
        Args:
            repository_type: Type of repository to create
            user_id: User identifier for repository isolation
            **kwargs: Additional configuration parameters
            
        Returns:
            GitBranchRepository instance
        """
        if repository_type is None:
            repository_type = cls._get_default_type()
        
        # Create cache key
        cache_key = f"{repository_type.value}_{user_id}"
        
        # Return cached instance if available
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Create repository instance based on type
        try:
            if repository_type == GitBranchRepositoryType.SQLITE:
                from .sqlite.git_branch_repository import SQLiteGitBranchRepository
                repository = SQLiteGitBranchRepository(
                    user_id=user_id,
                    **kwargs
                )
            elif repository_type == GitBranchRepositoryType.JSON:
                # JSON repository not implemented yet
                raise NotImplementedError(f"JSON repository type not yet implemented")
            elif repository_type == GitBranchRepositoryType.MEMORY:
                # Memory repository not implemented yet
                raise NotImplementedError(f"Memory repository type not yet implemented")
            else:
                raise ValueError(f"Unsupported repository type: {repository_type}")
            
            # Cache the instance
            cls._instances[cache_key] = repository
            logger.info(f"Created git branch repository: {repository_type.value} for user: {user_id}")
            
            return repository
            
        except Exception as e:
            logger.error(f"Failed to create git branch repository {repository_type.value}: {e}")
            raise
    
    @classmethod
    def _get_default_type(cls) -> GitBranchRepositoryType:
        """Get default repository type from environment or fallback"""
        env_type = os.getenv("MCP_GIT_BRANCH_REPOSITORY_TYPE", "sqlite").lower()
        
        try:
            return GitBranchRepositoryType(env_type)
        except ValueError:
            logger.warning(f"Unknown repository type in environment: {env_type}, using SQLITE")
            return GitBranchRepositoryType.SQLITE
    
    @classmethod
    def register_type(
        cls,
        repository_type: GitBranchRepositoryType,
        repository_class: Type[GitBranchRepository]
    ) -> None:
        """Register a new repository type"""
        cls._repository_types[repository_type] = repository_class
        logger.info(f"Registered git branch repository type: {repository_type.value}")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached instances"""
        cls._instances.clear()
        logger.info("Git branch repository cache cleared")
    
    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get factory information"""
        return {
            "available_types": [rt.value for rt in cls._repository_types.keys()],
            "cached_instances": len(cls._instances),
            "default_type": cls._get_default_type().value,
            "environment": {
                "MCP_GIT_BRANCH_REPOSITORY_TYPE": os.getenv("MCP_GIT_BRANCH_REPOSITORY_TYPE"),
            }
        }


# Register default repository types
try:
    from .sqlite.git_branch_repository import SQLiteGitBranchRepository
    GitBranchRepositoryFactory.register_type(GitBranchRepositoryType.SQLITE, SQLiteGitBranchRepository)
except ImportError:
    logger.warning("SQLiteGitBranchRepository not available")




# Convenience functions
def get_default_repository(user_id: str = "default_id") -> GitBranchRepository:
    """Get default git branch repository"""
    return GitBranchRepositoryFactory.create(user_id=user_id)


def get_sqlite_repository(user_id: str = "default_id", **kwargs) -> GitBranchRepository:
    """Get SQLite git branch repository"""
    return GitBranchRepositoryFactory.create(
        repository_type=GitBranchRepositoryType.SQLITE,
        user_id=user_id,
        **kwargs
    )