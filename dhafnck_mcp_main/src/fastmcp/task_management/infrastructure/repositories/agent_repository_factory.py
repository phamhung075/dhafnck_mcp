"""Agent Repository Factory - Clean DDD Implementation"""

import os
import logging
from typing import Optional, Dict, Any, Type
from enum import Enum

from ...domain.repositories.agent_repository import AgentRepository
from .orm.agent_repository import ORMAgentRepository

logger = logging.getLogger(__name__)


class AgentRepositoryType(Enum):
    """Available agent repository implementation types"""
    ORM = "orm"
    IN_MEMORY = "in_memory"
    MOCK = "mock"


class AgentRepositoryFactory:
    """Factory for creating agent repository instances following DDD principles"""
    
    _instances: Dict[str, AgentRepository] = {}
    _repository_types: Dict[AgentRepositoryType, Type[AgentRepository]] = {
        AgentRepositoryType.ORM: ORMAgentRepository,
    }
    
    @classmethod
    def create(
        cls,
        repository_type: Optional[AgentRepositoryType] = None,
        user_id: str = "default_id",
        db_path: Optional[str] = None,
        **kwargs
    ) -> AgentRepository:
        """
        Create an agent repository instance
        
        Args:
            repository_type: Type of repository to create
            user_id: User identifier for multi-user support
            db_path: Database path for SQLite repositories
            **kwargs: Additional repository-specific parameters
            
        Returns:
            AgentRepository instance
        """
        # Use default repository type if not specified
        if repository_type is None:
            repository_type = cls._get_default_type()
        
        # Generate cache key
        cache_key = cls._generate_cache_key(repository_type, user_id, db_path)
        
        # Return cached instance if available
        if cache_key in cls._instances:
            logger.debug(f"Returning cached agent repository: {cache_key}")
            return cls._instances[cache_key]
        
        # Create new instance
        repository = cls._create_instance(repository_type, user_id, db_path, **kwargs)
        
        # Cache the instance
        cls._instances[cache_key] = repository
        
        logger.info(f"Created agent repository: {repository_type.value} for user: {user_id}")
        return repository
    
    @classmethod
    def _get_default_type(cls) -> AgentRepositoryType:
        """Get default repository type from environment"""
        env_type = os.getenv("MCP_AGENT_REPOSITORY_TYPE", "orm").lower()
        
        try:
            return AgentRepositoryType(env_type)
        except ValueError:
            logger.warning(f"Invalid agent repository type '{env_type}', using orm")
            return AgentRepositoryType.ORM
    
    @classmethod
    def _generate_cache_key(
        cls, 
        repository_type: AgentRepositoryType, 
        user_id: str, 
        db_path: Optional[str]
    ) -> str:
        """Generate cache key for repository instance"""
        return f"agent:{repository_type.value}:{user_id}:{db_path or 'default'}"
    
    @classmethod
    def _create_instance(
        cls,
        repository_type: AgentRepositoryType,
        user_id: str,
        db_path: Optional[str],
        **kwargs
    ) -> AgentRepository:
        """Create repository instance of specified type"""
        
        if repository_type not in cls._repository_types:
            raise ValueError(f"Unsupported agent repository type: {repository_type.value}")
        
        repository_class = cls._repository_types[repository_type]
        
        try:
            if repository_type == AgentRepositoryType.ORM:
                return repository_class(user_id=user_id, **kwargs)
            else:
                return repository_class(user_id=user_id, **kwargs)
                
        except Exception as e:
            logger.error(f"Failed to create {repository_type.value} agent repository: {e}")
            # Fallback to ORM if possible
            if repository_type != AgentRepositoryType.ORM:
                logger.info("Falling back to ORM agent repository")
                return ORMAgentRepository(user_id=user_id)
            raise
    
    @classmethod
    def register_type(
        cls,
        repository_type: AgentRepositoryType,
        repository_class: Type[AgentRepository]
    ) -> None:
        """Register a new repository type"""
        cls._repository_types[repository_type] = repository_class
        logger.info(f"Registered agent repository type: {repository_type.value}")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached instances"""
        cls._instances.clear()
        logger.info("Agent repository cache cleared")
    
    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get factory information"""
        return {
            "available_types": [rt.value for rt in cls._repository_types.keys()],
            "cached_instances": len(cls._instances),
            "default_type": cls._get_default_type().value,
            "environment": {
                "MCP_AGENT_REPOSITORY_TYPE": os.getenv("MCP_AGENT_REPOSITORY_TYPE"),
                "MCP_DB_PATH": os.getenv("MCP_DB_PATH")
            }
        }


class AgentRepositoryConfig:
    """Configuration for agent repository creation"""
    
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
    
    def _validate_type(self, repository_type: Optional[str]) -> AgentRepositoryType:
        """Validate and convert repository type"""
        if repository_type is None:
            return AgentRepositoryType.ORM
        
        try:
            return AgentRepositoryType(repository_type.lower())
        except ValueError:
            logger.warning(f"Invalid agent repository type '{repository_type}', using orm")
            return AgentRepositoryType.ORM
    
    def create_repository(self) -> AgentRepository:
        """Create repository from this configuration"""
        return AgentRepositoryFactory.create(
            repository_type=self.repository_type,
            user_id=self.user_id,
            db_path=self.db_path,
            **self.kwargs
        )
    
    @classmethod
    def from_environment(cls) -> 'AgentRepositoryConfig':
        """Create configuration from environment variables"""
        return cls(
            repository_type=os.getenv("MCP_AGENT_REPOSITORY_TYPE"),
            user_id=os.getenv("MCP_USER_ID", "default_id"),
            db_path=os.getenv("MCP_DB_PATH")
        )


class GlobalAgentRepositoryManager:
    """Global agent repository instance manager"""
    
    _default_repository: Optional[AgentRepository] = None
    _user_repositories: Dict[str, AgentRepository] = {}
    
    @classmethod
    def get_default(cls) -> AgentRepository:
        """Get default agent repository instance"""
        if cls._default_repository is None:
            cls._default_repository = AgentRepositoryFactory.create()
        return cls._default_repository
    
    @classmethod
    def get_for_user(cls, user_id: str) -> AgentRepository:
        """Get agent repository for specific user"""
        if user_id not in cls._user_repositories:
            cls._user_repositories[user_id] = AgentRepositoryFactory.create(user_id=user_id)
        return cls._user_repositories[user_id]
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all cached repositories"""
        cls._default_repository = None
        cls._user_repositories.clear()
        AgentRepositoryFactory.clear_cache()
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get manager status"""
        return {
            "default_repository": cls._default_repository is not None,
            "user_repositories": len(cls._user_repositories),
            "cached_users": list(cls._user_repositories.keys()),
            "factory_info": AgentRepositoryFactory.get_info()
        }


# Convenience functions for easy repository creation
def create_agent_repository(
    user_id: str = "default_id",
    repository_type: Optional[str] = None,
    db_path: Optional[str] = None
) -> AgentRepository:
    """Create an agent repository with specified parameters"""
    repo_type = AgentRepositoryType(repository_type.lower()) if repository_type else None
    return AgentRepositoryFactory.create(
        repository_type=repo_type,
        user_id=user_id
    )


def get_sqlite_agent_repository(
    user_id: str = "default_id",
    db_path: Optional[str] = None
) -> ORMAgentRepository:
    """Get ORM agent repository instance (SQLite method deprecated)"""
    return AgentRepositoryFactory.create(
        repository_type=AgentRepositoryType.ORM,
        user_id=user_id
    )


def get_orm_agent_repository(
    user_id: str = "default_id",
    project_id: Optional[str] = None
) -> ORMAgentRepository:
    """Get ORM agent repository instance"""
    return AgentRepositoryFactory.create(
        repository_type=AgentRepositoryType.ORM,
        user_id=user_id,
        project_id=project_id
    )




def get_default_agent_repository() -> AgentRepository:
    """Get default agent repository instance"""
    return GlobalAgentRepositoryManager.get_default()


def get_user_agent_repository(user_id: str) -> AgentRepository:
    """Get agent repository for specific user"""
    return GlobalAgentRepositoryManager.get_for_user(user_id)


def create_agent_repository_factory() -> AgentRepositoryFactory:
    """Create agent repository factory instance"""
    return AgentRepositoryFactory() 