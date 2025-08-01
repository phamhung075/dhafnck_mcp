"""
Global Context Repository for unified context system.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from contextlib import contextmanager
import logging

from ...domain.entities.context import GlobalContext
from ...infrastructure.database.models import GlobalContext as GlobalContextModel
from .base_orm_repository import BaseORMRepository

logger = logging.getLogger(__name__)


class GlobalContextRepository(BaseORMRepository):
    """Repository for global context operations."""
    
    def __init__(self, session_factory):
        super().__init__(GlobalContextModel)
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
    
    def create(self, entity: GlobalContext) -> GlobalContext:
        """Create a new global context."""
        with self.get_db_session() as session:
            # Check if global singleton already exists
            existing = session.get(GlobalContextModel, "global_singleton")
            if existing:
                raise ValueError("Global context already exists. Use update instead.")
            
            # Extract global settings and preserve custom fields
            global_settings = entity.global_settings or {}
            
            # Get the predefined fields
            autonomous_rules = global_settings.get("autonomous_rules", {})
            security_policies = global_settings.get("security_policies", {})
            coding_standards = global_settings.get("coding_standards", {})
            workflow_templates = global_settings.get("workflow_templates", {})
            delegation_rules = global_settings.get("delegation_rules", {})
            
            # Collect any custom fields not in the predefined set
            known_fields = {"autonomous_rules", "security_policies", "coding_standards", 
                          "workflow_templates", "delegation_rules"}
            custom_fields = {}
            for key, value in global_settings.items():
                if key not in known_fields:
                    custom_fields[key] = value
            
            # Store custom fields in one of the existing JSON fields
            # We'll use workflow_templates to store custom data
            if custom_fields:
                workflow_templates["_custom"] = custom_fields
            
            # Create new global context - map domain entity to database model
            db_model = GlobalContextModel(
                id="global_singleton",
                organization_id=entity.organization_name,  # Map organization_name to organization_id
                autonomous_rules=autonomous_rules,
                security_policies=security_policies,
                coding_standards=coding_standards,
                workflow_templates=workflow_templates,
                delegation_rules=delegation_rules,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            session.add(db_model)
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def get(self, context_id: str) -> Optional[GlobalContext]:
        """Get global context by ID."""
        with self.get_db_session() as session:
            db_model = session.get(GlobalContextModel, context_id)
            return self._to_entity(db_model) if db_model else None
    
    def update(self, context_id: str, entity: GlobalContext) -> GlobalContext:
        """Update global context."""
        with self.get_db_session() as session:
            db_model = session.get(GlobalContextModel, context_id)
            if not db_model:
                raise ValueError(f"Global context not found: {context_id}")
            
            # Extract global settings and preserve custom fields
            global_settings = entity.global_settings or {}
            
            # Get the predefined fields
            autonomous_rules = global_settings.get("autonomous_rules", {})
            security_policies = global_settings.get("security_policies", {})
            coding_standards = global_settings.get("coding_standards", {})
            workflow_templates = global_settings.get("workflow_templates", {})
            delegation_rules = global_settings.get("delegation_rules", {})
            
            # Collect any custom fields not in the predefined set
            known_fields = {"autonomous_rules", "security_policies", "coding_standards", 
                          "workflow_templates", "delegation_rules"}
            custom_fields = {}
            for key, value in global_settings.items():
                if key not in known_fields:
                    custom_fields[key] = value
            
            # Store custom fields in workflow_templates
            if custom_fields:
                workflow_templates["_custom"] = custom_fields
            
            # Update fields - map domain entity to database model
            db_model.organization_id = entity.organization_name
            db_model.autonomous_rules = autonomous_rules
            db_model.security_policies = security_policies
            db_model.coding_standards = coding_standards
            db_model.workflow_templates = workflow_templates
            db_model.delegation_rules = delegation_rules
            db_model.updated_at = datetime.now(timezone.utc)
            
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def delete(self, context_id: str) -> bool:
        """Delete global context."""
        with self.get_db_session() as session:
            db_model = session.get(GlobalContextModel, context_id)
            if not db_model:
                return False
            
            session.delete(db_model)
            return True
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[GlobalContext]:
        """List global contexts (should only be one)."""
        with self.get_db_session() as session:
            stmt = select(GlobalContextModel)
            result = session.execute(stmt)
            db_models = result.scalars().all()
            
            return [self._to_entity(model) for model in db_models]
    
    def _to_entity(self, db_model: GlobalContextModel) -> GlobalContext:
        """Convert database model to domain entity."""
        # Map database model fields to domain entity
        global_settings = {
            "autonomous_rules": db_model.autonomous_rules or {},
            "security_policies": db_model.security_policies or {},
            "coding_standards": db_model.coding_standards or {},
            "workflow_templates": db_model.workflow_templates or {},
            "delegation_rules": db_model.delegation_rules or {}
        }
        
        # Extract custom fields from workflow_templates if they exist
        workflow_templates = db_model.workflow_templates or {}
        if "_custom" in workflow_templates:
            # Make a copy to avoid mutating the original
            workflow_templates_copy = workflow_templates.copy()
            custom_fields = workflow_templates_copy.pop("_custom", {})
            # Add custom fields back to global_settings at root level
            global_settings.update(custom_fields)
            # Update workflow_templates with the cleaned version
            global_settings["workflow_templates"] = workflow_templates_copy
        
        metadata = {
            "created_at": db_model.created_at.isoformat() if db_model.created_at else None,
            "updated_at": db_model.updated_at.isoformat() if db_model.updated_at else None,
            "version": db_model.version
        }
        
        return GlobalContext(
            id=db_model.id,
            organization_name=db_model.organization_id,  # Map organization_id to organization_name
            global_settings=global_settings,
            metadata=metadata
        )