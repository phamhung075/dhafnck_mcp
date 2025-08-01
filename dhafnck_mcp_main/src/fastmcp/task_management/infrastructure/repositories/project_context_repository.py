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
            
            # Extract known fields and preserve custom fields
            project_settings = entity.project_settings or {}
            
            # For test/custom data, store it in one of the existing JSON fields
            # We'll use local_standards to store any custom project settings
            local_standards = project_settings.get('local_standards', {})
            
            # Add any custom fields that aren't in the predefined set
            custom_fields = {}
            known_fields = {'team_preferences', 'technology_stack', 'project_workflow', 'local_standards'}
            for key, value in project_settings.items():
                if key not in known_fields:
                    custom_fields[key] = value
            
            # Merge custom fields into local_standards to preserve them
            if custom_fields:
                local_standards['_custom'] = custom_fields
            
            # Create new project context with proper field mapping
            db_model = ProjectContextModel(
                project_id=entity.id,
                team_preferences=project_settings.get('team_preferences', {}),
                technology_stack=project_settings.get('technology_stack', {}),
                project_workflow=project_settings.get('project_workflow', {}),
                local_standards=local_standards,
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
            
            # Extract known fields and preserve custom fields
            project_settings = entity.project_settings or {}
            
            # For test/custom data, store it in local_standards
            local_standards = project_settings.get('local_standards', {})
            
            # Add any custom fields that aren't in the predefined set
            custom_fields = {}
            known_fields = {'team_preferences', 'technology_stack', 'project_workflow', 'local_standards'}
            for key, value in project_settings.items():
                if key not in known_fields:
                    custom_fields[key] = value
            
            # Merge custom fields into local_standards to preserve them
            if custom_fields:
                local_standards['_custom'] = custom_fields
            
            # Update fields with proper mapping
            db_model.team_preferences = project_settings.get('team_preferences', {})
            db_model.technology_stack = project_settings.get('technology_stack', {})
            db_model.project_workflow = project_settings.get('project_workflow', {})
            db_model.local_standards = local_standards
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
        # Reconstruct project_settings
        project_settings = {
            'team_preferences': db_model.team_preferences or {},
            'technology_stack': db_model.technology_stack or {},
            'project_workflow': db_model.project_workflow or {},
            'local_standards': db_model.local_standards or {}
        }
        
        # Extract custom fields from local_standards if they exist
        local_standards = db_model.local_standards or {}
        if '_custom' in local_standards:
            # Make a copy to avoid mutating the original
            local_standards_copy = local_standards.copy()
            custom_fields = local_standards_copy.pop('_custom', {})
            # Add custom fields back to project_settings at root level
            project_settings.update(custom_fields)
            # Update local_standards with the cleaned version
            project_settings['local_standards'] = local_standards_copy
        
        return ProjectContext(
            id=db_model.project_id,
            project_name=f"Project-{db_model.project_id}",  # Generate name from ID
            project_settings=project_settings,
            metadata={
                'global_overrides': db_model.global_overrides or {},
                'delegation_rules': db_model.delegation_rules or {},
                'created_at': db_model.created_at.isoformat() if db_model.created_at else None,
                'updated_at': db_model.updated_at.isoformat() if db_model.updated_at else None,
                'version': db_model.version
            }
        )