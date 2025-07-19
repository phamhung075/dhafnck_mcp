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
            
            # Create new global context - map domain entity to database model
            db_model = GlobalContextModel(
                id="global_singleton",
                organization_id=entity.organization_name,  # Map organization_name to organization_id
                autonomous_rules=entity.global_settings.get("autonomous_rules", {}),
                security_policies=entity.global_settings.get("security_policies", {}),
                coding_standards=entity.global_settings.get("coding_standards", {}),
                workflow_templates=entity.global_settings.get("workflow_templates", {}),
                delegation_rules=entity.global_settings.get("delegation_rules", {}),
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
            
            # Update fields - map domain entity to database model
            db_model.organization_id = entity.organization_name
            db_model.autonomous_rules = entity.global_settings.get("autonomous_rules", {})
            db_model.security_policies = entity.global_settings.get("security_policies", {})
            db_model.coding_standards = entity.global_settings.get("coding_standards", {})
            db_model.workflow_templates = entity.global_settings.get("workflow_templates", {})
            db_model.delegation_rules = entity.global_settings.get("delegation_rules", {})
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