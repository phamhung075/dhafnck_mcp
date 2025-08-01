"""Task Facade Factory

Application layer factory for creating task facades with proper dependency injection.
"""

# NOTE: Importing inside method to avoid circular import with TaskApplicationFacade
from ...infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from ...infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory
from .unified_context_facade_factory import UnifiedContextFacadeFactory as ContextServiceFactory


class TaskFacadeFactory:
    """
    Factory for creating task application facades with proper DDD dependency injection.
    
    This factory encapsulates the creation logic for task facades, ensuring
    proper dependency injection and separation of concerns.
    """
    
    def __init__(self, repository_factory: TaskRepositoryFactory, subtask_repository_factory: SubtaskRepositoryFactory = None):
        """
        Initialize the task facade factory.
        
        Args:
            repository_factory: Factory for creating task repositories
            subtask_repository_factory: Factory for creating subtask repositories (optional)
        """
        self._repository_factory = repository_factory
        self._subtask_repository_factory = subtask_repository_factory
        self._context_service_factory = ContextServiceFactory()
    
    from typing import TYPE_CHECKING, Any
    if TYPE_CHECKING:
        from ..facades.task_application_facade import TaskApplicationFacade as _TaskApplicationFacade

    def create_task_facade(self, project_id: str, git_branch_id: str = None, user_id: str = "default_id") -> object:
        """
        Create a task application facade with proper dependency injection.
        
        This method demonstrates how to properly construct application facades
        with all required dependencies using dependency injection.
        
        Args:
            project_id: Project identifier for repository creation
            git_branch_id: Git branch UUID (if None, will use default branch)
            user_id: User identifier
            
        Returns:
            Configured task application facade
        """
        # Create task repository for facade construction
        # For now, use "main" as branch name since we're transitioning to UUIDs
        task_repository = self._repository_factory.create_repository(project_id, "main", user_id)
        
        # Create subtask repository if factory is available
        subtask_repository = None
        if self._subtask_repository_factory:
            subtask_repository = self._subtask_repository_factory.create_subtask_repository(project_id)
        
        # Create context service for context integration
        context_service = self._context_service_factory.create_facade(
            user_id=user_id,
            project_id=project_id,
            git_branch_id=git_branch_id
        )
        
        # Create and return facade with all repositories and services
        # The facade will create its own use cases internally
        from ..facades.task_application_facade import TaskApplicationFacade
        return TaskApplicationFacade(task_repository, subtask_repository, context_service)

    def create_task_facade_with_git_branch_id(self, project_id: str, git_branch_name: str, user_id: str, git_branch_id: str) -> object:
        """
        Create a task application facade with a specific git_branch_id.
        
        This method creates a facade where the task repository is initialized with
        the git_branch_id directly, bypassing the need for context resolution.
        
        Args:
            project_id: Project identifier for repository creation
            git_branch_name: Task tree identifier
            user_id: User identifier
            git_branch_id: Specific git branch ID to use
            
        Returns:
            Configured task application facade
        """
        # Create task repository with git_branch_id directly
        task_repository = self._repository_factory.create_repository_with_git_branch_id(project_id, git_branch_name, user_id, git_branch_id)
        
        # Create subtask repository if factory is available
        subtask_repository = None
        if self._subtask_repository_factory:
            subtask_repository = self._subtask_repository_factory.create_subtask_repository(project_id)
        
        # Create context service for context integration
        context_service = self._context_service_factory.create_facade(
            user_id=user_id,
            project_id=project_id,
            git_branch_id=git_branch_id
        )
        
        # Create and return facade with all repositories and services
        from ..facades.task_application_facade import TaskApplicationFacade
        return TaskApplicationFacade(task_repository, subtask_repository, context_service)