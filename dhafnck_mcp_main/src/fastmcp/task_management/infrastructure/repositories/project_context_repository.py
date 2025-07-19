"""
Project Context Repository for unified context system.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from contextlib import contextmanager
import logging

from ...domain.entities.context import ProjectContext
from ...infrastructure.database.models import ProjectContext as ProjectContextModel
from .base_orm_repository import BaseORMRepository

logger = logging.getLogger(__name__)


class ProjectContextRepository(BaseORMRepository):
    """Repository for project context operations."""
    
    def __init__(self, session_factory):
        super().__init__(ProjectContextModel)
        self.session_factory = session_factory
        self.model_class = ProjectContextModel
    
    @contextmanager
    def get_db_session(self):
        """Override to use custom session factory for testing."""
        if self._session:
            # Use existing session from transaction
            yield self._session
        else:
            # Use custom session factory
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
        """Create a new project context."""
        with self.get_db_session() as session:
            # Check if project context already exists
            existing = session.get(ProjectContextModel, entity.id)
            if existing:
                raise ValueError(f"Project context already exists: {entity.id}")
            
            # Create new project context with proper field mapping
            db_model = ProjectContextModel(
                project_id=entity.id,
                team_preferences=entity.project_settings.get('team_preferences', {}),
                technology_stack=entity.project_settings.get('technology_stack', {}),
                project_workflow=entity.project_settings.get('project_workflow', {}),
                local_standards=entity.project_settings.get('local_standards', {}),
                global_overrides=entity.metadata.get('global_overrides', {}),
                delegation_rules=entity.metadata.get('delegation_rules', {})
            )
            
            session.add(db_model)
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def get(self, context_id: str) -> Optional[ProjectContext]:
        """Get project context by ID."""
        with self.get_db_session() as session:
            db_model = session.get(ProjectContextModel, context_id)
            return self._to_entity(db_model) if db_model else None
    
    def update(self, context_id: str, entity: ProjectContext) -> ProjectContext:
        """Update project context."""
        with self.get_db_session() as session:
            db_model = session.get(ProjectContextModel, context_id)
            if not db_model:
                raise ValueError(f"Project context not found: {context_id}")
            
            # Update fields with proper mapping
            db_model.team_preferences = entity.project_settings.get('team_preferences', {})
            db_model.technology_stack = entity.project_settings.get('technology_stack', {})
            db_model.project_workflow = entity.project_settings.get('project_workflow', {})
            db_model.local_standards = entity.project_settings.get('local_standards', {})
            db_model.global_overrides = entity.metadata.get('global_overrides', {})
            db_model.delegation_rules = entity.metadata.get('delegation_rules', {})
            db_model.updated_at = datetime.now(timezone.utc)
            
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def delete(self, context_id: str) -> bool:
        """Delete project context."""
        with self.get_db_session() as session:
            db_model = session.get(ProjectContextModel, context_id)
            if not db_model:
                return False
            
            session.delete(db_model)
            session.flush()
            return True
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[ProjectContext]:
        """List project contexts."""
        with self.get_db_session() as session:
            stmt = select(ProjectContextModel)
            
            # Apply filters if provided
            if filters:
                if "project_id" in filters:
                    stmt = stmt.where(ProjectContextModel.project_id == filters["project_id"])
            
            result = session.execute(stmt)
            db_models = result.scalars().all()
            
            return [self._to_entity(model) for model in db_models]
    
    def _to_entity(self, db_model: ProjectContextModel) -> ProjectContext:
        """Convert database model to domain entity."""
        return ProjectContext(
            id=db_model.project_id,
            project_name=f"Project-{db_model.project_id}",  # Generate name from ID
            project_settings={
                'team_preferences': db_model.team_preferences or {},
                'technology_stack': db_model.technology_stack or {},
                'project_workflow': db_model.project_workflow or {},
                'local_standards': db_model.local_standards or {}
            },
            metadata={
                'global_overrides': db_model.global_overrides or {},
                'delegation_rules': db_model.delegation_rules or {},
                'created_at': db_model.created_at.isoformat() if db_model.created_at else None,
                'updated_at': db_model.updated_at.isoformat() if db_model.updated_at else None,
                'version': db_model.version
            }
        )