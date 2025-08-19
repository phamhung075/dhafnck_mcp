"""
Project Context Repository with User Isolation.

Project contexts are scoped to both project AND user.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from contextlib import contextmanager
import logging

from ...domain.entities.context import ProjectContext
from ...infrastructure.database.models import ProjectContext as ProjectContextModel
from .base_user_scoped_repository import BaseUserScopedRepository

logger = logging.getLogger(__name__)


class ProjectContextRepository(BaseUserScopedRepository):
    """
    Repository for project context operations with user isolation.
    
    Project contexts are tied to both a project and a user, ensuring
    users only see contexts for their own projects.
    """
    
    def __init__(self, session_factory, user_id: Optional[str] = None):
        """
        Initialize with session factory and user context.
        
        Args:
            session_factory: Factory for creating database sessions
            user_id: ID of the user whose project contexts to access
        """
        session = session_factory()
        super().__init__(session, user_id)
        self.session_factory = session_factory
        self.model_class = ProjectContextModel
        
        if user_id:
            logger.info(f"ProjectContextRepository initialized for user: {user_id}")
    
    @contextmanager
    def get_db_session(self):
        """Get database session with proper transaction handling."""
        if hasattr(self, '_session') and self._session:
            yield self._session
        else:
            session = self.session_factory()
            try:
                yield session
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                session.close()
    
    def create(self, project_id: str, context_data: Dict[str, Any]) -> ProjectContext:
        """
        Create a new project context for the current user.
        
        Args:
            project_id: ID of the project
            context_data: Context data to store
            
        Returns:
            Created ProjectContext entity
        """
        with self.get_db_session() as session:
            # Check if context already exists for this project and user
            if self.user_id:
                existing = session.query(ProjectContextModel).filter(
                    and_(
                        ProjectContextModel.project_id == project_id,
                        ProjectContextModel.user_id == self.user_id
                    )
                ).first()
            else:
                existing = session.query(ProjectContextModel).filter(
                    ProjectContextModel.project_id == project_id
                ).first()
            
            if existing:
                raise ValueError(f"Project context already exists for project {project_id}")
            
            # Create new project context with user_id
            db_model = ProjectContextModel(
                project_id=project_id,
                context_data=context_data,
                user_id=self.user_id,  # Set user_id for isolation
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Log access for audit
            self.log_access("create", "project_context", project_id)
            
            session.add(db_model)
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def get(self, project_id: str) -> Optional[ProjectContext]:
        """
        Get project context by project ID, filtered by user.
        
        Args:
            project_id: ID of the project
            
        Returns:
            ProjectContext if found, None otherwise
        """
        with self.get_db_session() as session:
            # Build query with user filter
            query = session.query(ProjectContextModel).filter(
                ProjectContextModel.project_id == project_id
            )
            
            # Apply user filter
            query = self.apply_user_filter(query)
            
            db_model = query.first()
            
            if db_model:
                self.log_access("read", "project_context", project_id)
            else:
                logger.debug(f"Project context not found for user {self.user_id}: {project_id}")
            
            return self._to_entity(db_model) if db_model else None
    
    def update(self, project_id: str, context_data: Dict[str, Any]) -> ProjectContext:
        """
        Update project context for the current user.
        
        Args:
            project_id: ID of the project
            context_data: New context data
            
        Returns:
            Updated ProjectContext entity
        """
        with self.get_db_session() as session:
            # Build query with user filter
            query = session.query(ProjectContextModel).filter(
                ProjectContextModel.project_id == project_id
            )
            
            # Apply user filter
            query = self.apply_user_filter(query)
            
            db_model = query.first()
            
            if not db_model:
                raise ValueError(f"Project context not found for user {self.user_id}: {project_id}")
            
            # Ensure user ownership before update
            self.ensure_user_ownership(db_model)
            
            # Update context data
            db_model.context_data = context_data
            db_model.updated_at = datetime.now(timezone.utc)
            
            # Log access for audit
            self.log_access("update", "project_context", project_id)
            
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def delete(self, project_id: str) -> bool:
        """
        Delete project context for the current user.
        
        Args:
            project_id: ID of the project
            
        Returns:
            True if deleted, False if not found
        """
        with self.get_db_session() as session:
            # Build query with user filter
            query = session.query(ProjectContextModel).filter(
                ProjectContextModel.project_id == project_id
            )
            
            # Apply user filter
            query = self.apply_user_filter(query)
            
            db_model = query.first()
            
            if not db_model:
                return False
            
            # Ensure user ownership before delete
            self.ensure_user_ownership(db_model)
            
            # Log access for audit
            self.log_access("delete", "project_context", project_id)
            
            session.delete(db_model)
            return True
    
    def list_by_user(self) -> List[ProjectContext]:
        """
        List all project contexts for the current user.
        
        Returns:
            List of ProjectContext entities
        """
        with self.get_db_session() as session:
            # Start with base query
            query = session.query(ProjectContextModel)
            
            # Apply user filter - CRITICAL for isolation
            query = self.apply_user_filter(query)
            
            db_models = query.all()
            
            # Log access for audit
            self.log_access("list", "project_context", f"count={len(db_models)}")
            
            return [self._to_entity(model) for model in db_models]
    
    def list_by_project_ids(self, project_ids: List[str]) -> List[ProjectContext]:
        """
        List project contexts for specific projects, filtered by user.
        
        Args:
            project_ids: List of project IDs to fetch contexts for
            
        Returns:
            List of ProjectContext entities
        """
        with self.get_db_session() as session:
            # Build query for specific projects
            query = session.query(ProjectContextModel).filter(
                ProjectContextModel.project_id.in_(project_ids)
            )
            
            # Apply user filter
            query = self.apply_user_filter(query)
            
            db_models = query.all()
            
            # Log access for audit
            self.log_access("list", "project_context", f"projects={len(project_ids)}, found={len(db_models)}")
            
            return [self._to_entity(model) for model in db_models]
    
    def merge_context(self, project_id: str, additional_data: Dict[str, Any]) -> ProjectContext:
        """
        Merge additional data into existing project context.
        
        Args:
            project_id: ID of the project
            additional_data: Data to merge into existing context
            
        Returns:
            Updated ProjectContext entity
        """
        existing = self.get(project_id)
        
        if existing:
            # Merge data
            merged_data = existing.context_data.copy()
            merged_data.update(additional_data)
            return self.update(project_id, merged_data)
        else:
            # Create new context
            return self.create(project_id, additional_data)
    
    def count_user_project_contexts(self) -> int:
        """
        Count the number of project contexts for the current user.
        
        Returns:
            Number of project contexts for the user
        """
        with self.get_db_session() as session:
            query = session.query(ProjectContextModel)
            query = self.apply_user_filter(query)
            return query.count()
    
    def _to_entity(self, db_model: ProjectContextModel) -> ProjectContext:
        """Convert database model to domain entity."""
        metadata = {
            "created_at": db_model.created_at.isoformat() if db_model.created_at else None,
            "updated_at": db_model.updated_at.isoformat() if db_model.updated_at else None,
            "user_id": db_model.user_id  # Include user_id in metadata
        }
        
        return ProjectContext(
            id=db_model.id,
            project_id=db_model.project_id,
            context_data=db_model.context_data or {},
            metadata=metadata
        )
    
    def get_inherited_context(self, project_id: str) -> Dict[str, Any]:
        """
        Get inherited context for a project (from global context).
        
        Args:
            project_id: ID of the project
            
        Returns:
            Merged context data including inherited global context
        """
        # Get project's own context
        project_context = self.get(project_id)
        result = project_context.context_data if project_context else {}
        
        # Get user's global context (if we have access to global repo)
        # This would need to be injected or accessed through a service
        # For now, just return project context
        
        return result
    
    def migrate_to_user_scoped(self) -> int:
        """
        Migrate existing project contexts to user-scoped contexts.
        Assigns existing contexts to the system user.
        
        Returns:
            Number of contexts migrated
        """
        system_user_id = "00000000-0000-0000-0000-000000000000"
        migrated = 0
        
        with self.get_db_session() as session:
            # Find contexts without user_id
            contexts_to_migrate = session.query(ProjectContextModel).filter(
                ProjectContextModel.user_id == None
            ).all()
            
            for context in contexts_to_migrate:
                context.user_id = system_user_id
                migrated += 1
                logger.info(f"Migrated project context for project {context.project_id} to system user")
            
            if migrated > 0:
                session.commit()
                logger.info(f"Migrated {migrated} project contexts to user-scoped")
        
        return migrated