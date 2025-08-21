"""
Branch Context Repository for unified context system.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from contextlib import contextmanager
import logging

from ...domain.entities.context import BranchContext
from ...infrastructure.database.models import BranchContext as BranchContextModel
from .base_orm_repository import BaseORMRepository

logger = logging.getLogger(__name__)


class BranchContextRepository(BaseORMRepository):
    """Repository for branch context operations."""
    
    def __init__(self, session_factory):
        super().__init__(BranchContextModel)
        self.session_factory = session_factory
    
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
    
    def create(self, entity: BranchContext) -> BranchContext:
        """Create a new branch context."""
        with self.get_db_session() as session:
            # Check if branch context already exists
            existing = session.get(BranchContextModel, entity.id)
            if existing:
                raise ValueError(f"Branch context already exists: {entity.id}")
            
            # Extract known fields and preserve custom fields
            branch_settings = entity.branch_settings or {}
            
            # Get predefined fields
            branch_workflow = branch_settings.get('branch_workflow', {})
            branch_standards = branch_settings.get('branch_standards', {})
            agent_assignments = branch_settings.get('agent_assignments', {})
            
            # Collect any custom fields not in the predefined set
            known_fields = {'branch_workflow', 'branch_standards', 'agent_assignments'}
            custom_fields = {}
            for key, value in branch_settings.items():
                if key not in known_fields:
                    custom_fields[key] = value
            
            # Store custom fields in branch_standards to preserve them
            if custom_fields:
                branch_standards['_custom'] = custom_fields
            
            # Create new branch context with proper field mapping
            # Provide default project_id if not specified
            project_id = entity.project_id or "default-project"
            
            # Combine all data into the data field
            data_field = {
                'branch_workflow': branch_workflow,
                'branch_standards': branch_standards,
                'agent_assignments': agent_assignments,
                'local_overrides': entity.metadata.get('local_overrides', {}),
                'delegation_rules': entity.metadata.get('delegation_rules', {})
            }
            
            db_model = BranchContextModel(
                id=entity.id,  # Use entity.id as the primary key
                branch_id=entity.id,
                parent_project_id=project_id,  # This should reference project_contexts.id
                data=data_field,
                branch_workflow=branch_workflow,
                feature_flags={},  # Using feature_flags instead of branch_standards
                active_patterns={},  # Using active_patterns instead of agent_assignments
                local_overrides=entity.metadata.get('local_overrides', {}),
                delegation_rules=entity.metadata.get('delegation_rules', {})
                # user_id=entity.metadata.get('user_id') or 'system'  # Temporarily disabled for DB compatibility
            )
            
            session.add(db_model)
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def get(self, context_id: str) -> Optional[BranchContext]:
        """Get branch context by ID."""
        with self.get_db_session() as session:
            db_model = session.get(BranchContextModel, context_id)
            return self._to_entity(db_model) if db_model else None
    
    def update(self, context_id: str, entity: BranchContext) -> BranchContext:
        """Update branch context."""
        with self.get_db_session() as session:
            db_model = session.get(BranchContextModel, context_id)
            if not db_model:
                raise ValueError(f"Branch context not found: {context_id}")
            
            # Extract known fields and preserve custom fields
            branch_settings = entity.branch_settings or {}
            
            # Get predefined fields
            branch_workflow = branch_settings.get('branch_workflow', {})
            branch_standards = branch_settings.get('branch_standards', {})
            agent_assignments = branch_settings.get('agent_assignments', {})
            
            # Collect any custom fields not in the predefined set
            known_fields = {'branch_workflow', 'branch_standards', 'agent_assignments'}
            custom_fields = {}
            for key, value in branch_settings.items():
                if key not in known_fields:
                    custom_fields[key] = value
            
            # Store custom fields in branch_standards to preserve them
            if custom_fields:
                branch_standards['_custom'] = custom_fields
            
            # Update fields with proper mapping
            db_model.parent_project_id = entity.project_id
            db_model.branch_workflow = branch_workflow
            db_model.feature_flags = {}  # Using feature_flags instead of branch_standards
            db_model.active_patterns = {}  # Using active_patterns instead of agent_assignments
            
            # Update the data field with all information
            db_model.data = {
                'branch_workflow': branch_workflow,
                'branch_standards': branch_standards,
                'agent_assignments': agent_assignments,
                'local_overrides': entity.metadata.get('local_overrides', {}),
                'delegation_rules': entity.metadata.get('delegation_rules', {})
            }
            db_model.local_overrides = entity.metadata.get('local_overrides', {})
            db_model.delegation_rules = entity.metadata.get('delegation_rules', {})
            # db_model.user_id = entity.metadata.get('user_id') or db_model.user_id or 'system'  # Temporarily disabled for DB compatibility
            db_model.updated_at = datetime.now(timezone.utc)
            
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def delete(self, context_id: str) -> bool:
        """Delete branch context."""
        with self.get_db_session() as session:
            db_model = session.get(BranchContextModel, context_id)
            if not db_model:
                return False
            
            session.delete(db_model)
            return True
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[BranchContext]:
        """List branch contexts."""
        with self.get_db_session() as session:
            stmt = select(BranchContextModel)
            
            # Apply filters if provided
            if filters:
                if "project_id" in filters:
                    stmt = stmt.where(BranchContextModel.project_id == filters["project_id"])
                if "git_branch_name" in filters:
                    stmt = stmt.where(BranchContextModel.git_branch_name == filters["git_branch_name"])
            
            result = session.execute(stmt)
            db_models = result.scalars().all()
            
            return [self._to_entity(model) for model in db_models]
    
    def _to_entity(self, db_model: BranchContextModel) -> BranchContext:
        """Convert database model to domain entity."""
        # Extract data from the data field if available
        data_field = db_model.data or {}
        
        # Reconstruct branch_settings from data field or individual fields
        branch_settings = {
            'branch_workflow': data_field.get('branch_workflow') or db_model.branch_workflow or {},
            'branch_standards': data_field.get('branch_standards') or {},
            'agent_assignments': data_field.get('agent_assignments') or {}
        }
        
        # Extract custom fields from branch_standards if they exist
        branch_standards = branch_settings.get('branch_standards', {})
        if '_custom' in branch_standards:
            # Make a copy to avoid mutating the original
            branch_standards_copy = branch_standards.copy()
            custom_fields = branch_standards_copy.pop('_custom', {})
            # Add custom fields back to branch_settings at root level
            branch_settings.update(custom_fields)
            # Update branch_standards with the cleaned version
            branch_settings['branch_standards'] = branch_standards_copy
        
        return BranchContext(
            id=db_model.id,  # Use the actual id field
            project_id=db_model.parent_project_id,
            git_branch_name=f"branch-{db_model.branch_id}",  # Generate name from ID
            branch_settings=branch_settings,
            metadata={
                'local_overrides': db_model.local_overrides or {},
                'delegation_rules': db_model.delegation_rules or {},
                'created_at': db_model.created_at.isoformat() if db_model.created_at else None,
                'updated_at': db_model.updated_at.isoformat() if db_model.updated_at else None
            }
        )