"""Task Dependency Operations Handler"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TaskDependencyHandler:
    """Handler for task dependency operations"""
    
    def __init__(self, task_repository_factory, subtask_repository_factory):
        """
        Initialize handler with repository factories.
        
        Args:
            task_repository_factory: Factory for task repositories
            subtask_repository_factory: Factory for subtask repositories
        """
        self.task_repository_factory = task_repository_factory
        self.subtask_repository_factory = subtask_repository_factory
    
    # Dependency operations would go here if needed
    # Currently handled by dependency_mcp_controller