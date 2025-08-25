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
import uuid

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
    
    def create(self, entity: ProjectContext) -> ProjectContext:
        """
        Create a new project context for the current user.
        
        Args:
            entity: ProjectContext entity to create
            
        Returns:
            Created ProjectContext entity
        """
        with self.get_db_session() as session:
            # Extract project_id and data from entity
            # The entity.id is the project UUID for project contexts
            project_id = entity.id
            context_data = entity.dict()  # Convert entire entity to dict for context_data
            
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
            logger.info(f"Creating ProjectContextModel: project_id={project_id}, user_id={self.user_id}")
            db_model = ProjectContextModel(
                id=project_id,  # Set id field (primary key) to project_id
                project_id=project_id,
                data=context_data,  # Use 'data' field, not 'context_data'
                user_id=self.user_id,  # Set user_id for isolation
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Log access for audit
            self.log_access("create", "project_context", project_id)
            logger.info(f"Created ProjectContextModel with ID: {db_model.id}, user_id: {db_model.user_id}")
            
            session.add(db_model)
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def create_by_project_id(self, project_id: str, context_data: Dict[str, Any]) -> ProjectContext:
        """
        Legacy method for backward compatibility.
        Create a new project context by project ID and context data.
        
        Args:
            project_id: ID of the project
            context_data: Context data to store
            
        Returns:
            Created ProjectContext entity
        """
        # Create entity and call main create method
        entity = ProjectContext(
            id=project_id,  # Use project_id as the entity id
            project_name=context_data.get("project_name", f"Project-{project_id}"),
            project_settings=context_data.get("project_settings", {}),
            metadata=context_data.get("metadata", {})
        )
        return self.create(entity)
    
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
    
    def update(self, project_id: str, entity: ProjectContext) -> ProjectContext:
        """
        Update project context for the current user.
        
        Args:
            project_id: ID of the project
            entity: ProjectContext entity with updated data
            
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
            
            # Convert entity to dict for context data storage
            context_data = entity.dict()
            
            # Update context data
            db_model.data = context_data
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
            # Merge additional_data into existing project_settings
            merged_settings = existing.project_settings.copy()
            merged_settings.update(additional_data)
            
            # Create updated entity with merged settings
            updated_entity = ProjectContext(
                id=existing.id,
                project_name=existing.project_name,
                project_settings=merged_settings,
                metadata=existing.metadata
            )
            return self.update(project_id, updated_entity)
        else:
            # Create new context
            return self.create_by_project_id(project_id, additional_data)
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[ProjectContext]:
        """
        Generic list method that respects user isolation and filters.
        
        Args:
            filters: Optional filters to apply (user_id filter is automatically applied)
            
        Returns:
            List of ProjectContext entities for the current user
        """
        with self.get_db_session() as session:
            # Start with base query
            query = session.query(ProjectContextModel)
            
            # Log debug info
            logger.info(f"Starting list query for user_id={self.user_id}, filters={filters}")
            
            # Apply user filter - CRITICAL for isolation
            original_query = query
            query = self.apply_user_filter(query)
            logger.info(f"Applied user filter. Query changed: {query is not original_query}")
            
            # Apply additional filters if provided
            if filters:
                for key, value in filters.items():
                    if hasattr(ProjectContextModel, key) and key != 'user_id':  # Don't override user filter
                        query = query.filter(getattr(ProjectContextModel, key) == value)
                        logger.info(f"Applied filter: {key} = {value}")
            
            # Execute query and get results
            db_models = query.all()
            logger.info(f"Query returned {len(db_models)} results")
            
            # Debug: check if there are any records at all (without user filter)
            if len(db_models) == 0:
                total_records = session.query(ProjectContextModel).count()
                logger.info(f"Total project contexts in database (all users): {total_records}")
                
                # Check records for this specific user
                user_records = session.query(ProjectContextModel).filter(
                    ProjectContextModel.user_id == self.user_id
                ).count()
                logger.info(f"Project contexts for user {self.user_id}: {user_records}")
            
            # Log access for audit
            self.log_access("list", "project_context", f"count={len(db_models)}, filters={filters}")
            
            return [self._to_entity(model) for model in db_models]

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
        
        # Extract project_name from data or use project_id as fallback
        context_data = db_model.data or {}
        project_name = context_data.get("project_name", f"Project-{db_model.project_id}")
        
        # Extract project_settings from data or use empty dict
        project_settings = context_data.get("project_settings", {})
        
        return ProjectContext(
            id=db_model.id,  # Use id field (should be same as project_id)
            project_name=project_name,
            project_settings=project_settings,
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
        result = project_context.dict() if project_context else {}
        
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