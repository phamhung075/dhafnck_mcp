"""Context ID Type Detector

This module provides utilities to detect whether a given ID is a project ID, 
git branch ID, or task ID by checking against the database.
"""

import logging
from typing import Tuple, Optional
from ...infrastructure.database.session_manager import get_session_manager
from sqlalchemy import text

logger = logging.getLogger(__name__)


class ContextIDDetector:
    """Detects the type of a given ID by checking against database tables"""
    
    @staticmethod
    def detect_id_type(context_id: str) -> Tuple[str, Optional[str]]:
        """
        Detect whether the given ID is a project, git branch, or task ID.
        
        Args:
            context_id: The ID to check
            
        Returns:
            Tuple of (id_type, project_id) where:
            - id_type is one of: "project", "git_branch", "task", "unknown"
            - project_id is the associated project ID (None for unknown)
        """
        try:
            session_manager = get_session_manager()
            with session_manager.get_session() as session:
                # Check if it's a project ID
                result = session.execute(
                    text('SELECT id FROM projects WHERE id = :context_id'),
                    {'context_id': context_id}
                ).fetchone()
                
                if result:
                    logger.debug(f"ID {context_id} identified as project ID")
                    return ("project", context_id)
                
                # Check if it's a git branch ID (stored in project_task_trees)
                result = session.execute(
                    text('SELECT project_id FROM project_task_trees WHERE id = :context_id'),
                    {'context_id': context_id}
                ).fetchone()
                
                if result:
                    project_id = result[0]
                    logger.debug(f"ID {context_id} identified as git branch ID with project {project_id}")
                    return ("git_branch", project_id)
                
                # Check if it's a task ID
                result = session.execute(
                    text('''
                    SELECT t.id, pt.project_id 
                    FROM tasks t
                    JOIN project_task_trees pt ON t.git_branch_id = pt.id
                    WHERE t.id = :context_id
                    '''),
                    {'context_id': context_id}
                ).fetchone()
                
                if result:
                    project_id = result[1]
                    logger.debug(f"ID {context_id} identified as task ID with project {project_id}")
                    return ("task", project_id)
                
                # ID not found in any table
                logger.warning(f"ID {context_id} not found in any table")
                return ("unknown", None)
                
        except Exception as e:
            logger.error(f"Error detecting ID type for {context_id}: {e}")
            return ("unknown", None)
    
    @staticmethod
    def get_context_level_for_id(context_id: str) -> str:
        """
        Get the appropriate context level for a given ID.
        
        Args:
            context_id: The ID to check
            
        Returns:
            The context level: "project", "task", or "task" (default)
        """
        id_type, _ = ContextIDDetector.detect_id_type(context_id)
        
        # Map ID types to context levels
        if id_type == "project":
            return "project"
        elif id_type in ["git_branch", "task"]:
            return "task"  # Both git branches and tasks use task-level contexts
        else:
            # Default to task level for unknown IDs
            logger.warning(f"Unknown ID type for {context_id}, defaulting to task level")
            return "task"