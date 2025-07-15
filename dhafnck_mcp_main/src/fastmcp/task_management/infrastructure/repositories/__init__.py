"""Infrastructure Repositories"""

# Legacy imports (commented out)
# from .json_task_repository import JsonTaskRepository, InMemoryTaskRepository

# Project repositories
from .sqlite.project_repository import SQLiteProjectRepository
from .project_repository_factory import ProjectRepositoryFactory, create_project_repository, get_default_repository

# Agent repositories
from .sqlite.agent_repository import SQLiteAgentRepository
from .agent_repository_factory import AgentRepositoryFactory, create_agent_repository, get_default_agent_repository

# Context repositories
from .sqlite.hierarchical_context_repository import SQLiteHierarchicalContextRepository
# Alias for backward compatibility
SQLiteContextRepository = SQLiteHierarchicalContextRepository

# Agent coordination repositories
from .sqlite.agent_coordination_repository import AgentCoordinationRepository

__all__ = [
    # Project repositories
    "SQLiteProjectRepository",
    "ProjectRepositoryFactory", 
    "create_project_repository",
    "get_default_repository",
    
    # Agent repositories
    "SQLiteAgentRepository", 
    "AgentRepositoryFactory",
    "create_agent_repository",
    "get_default_agent_repository",
    
    # Context repositories
    "SQLiteContextRepository",
    
    # Agent coordination repositories
    "AgentCoordinationRepository",
] 