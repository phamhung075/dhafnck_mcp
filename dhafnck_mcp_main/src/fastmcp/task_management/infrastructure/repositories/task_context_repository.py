"""
Task Context Repository for unified context system.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from contextlib import contextmanager
import logging

from ...domain.entities.context import TaskContextUnified as TaskContext
from ...infrastructure.database.models import TaskContext as TaskContextModel
from .base_orm_repository import BaseORMRepository

logger = logging.getLogger(__name__)


class TaskContextRepository(BaseORMRepository):
    """Repository for task context operations."""
    
    def __init__(self, session_factory):
        super().__init__(TaskContextModel)
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
    
    def create(self, entity: TaskContext) -> TaskContext:
        """Create a new task context."""
        with self.get_db_session() as session:
            # Check if task context already exists (using task_id as primary key)
            existing = session.get(TaskContextModel, entity.id)
            if existing:
                raise ValueError(f"Task context already exists: {entity.id}")
            
            # Create new task context with unified schema
            db_model = TaskContextModel(
                task_id=entity.id,
                parent_branch_id=entity.branch_id,
                parent_branch_context_id=entity.branch_id,  # Assuming branch_id serves as both
                task_data=entity.task_data,
                local_overrides=getattr(entity, 'local_overrides', {}),
                implementation_notes=getattr(entity, 'implementation_notes', {}),
                delegation_triggers=getattr(entity, 'delegation_triggers', {}),
                inheritance_disabled=getattr(entity, 'inheritance_disabled', False),
                force_local_only=getattr(entity, 'force_local_only', False),
                version=1
            )
            
            session.add(db_model)
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def get(self, context_id: str) -> Optional[TaskContext]:
        """Get task context by ID."""
        with self.get_db_session() as session:
            db_model = session.get(TaskContextModel, context_id)
            return self._to_entity(db_model) if db_model else None
    
    def update(self, context_id: str, entity: TaskContext) -> TaskContext:
        """Update task context."""
        with self.get_db_session() as session:
            db_model = session.get(TaskContextModel, context_id)
            if not db_model:
                raise ValueError(f"Task context not found: {context_id}")
            
            # Update fields with unified schema
            db_model.parent_branch_id = entity.branch_id
            db_model.task_data = entity.task_data
            db_model.local_overrides = getattr(entity, 'local_overrides', {})
            db_model.implementation_notes = getattr(entity, 'implementation_notes', {})
            db_model.delegation_triggers = getattr(entity, 'delegation_triggers', {})
            db_model.inheritance_disabled = getattr(entity, 'inheritance_disabled', False)
            db_model.force_local_only = getattr(entity, 'force_local_only', False)
            db_model.version += 1
            
            session.flush()
            session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def delete(self, context_id: str) -> bool:
        """Delete task context."""
        with self.get_db_session() as session:
            db_model = session.get(TaskContextModel, context_id)
            if not db_model:
                return False
            
            session.delete(db_model)
            return True
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[TaskContext]:
        """List task contexts."""
        with self.get_db_session() as session:
            stmt = select(TaskContextModel)
            
            # Apply filters if provided
            if filters:
                if "branch_id" in filters:
                    stmt = stmt.where(TaskContextModel.parent_branch_id == filters["branch_id"])
                if "inheritance_disabled" in filters:
                    stmt = stmt.where(TaskContextModel.inheritance_disabled == filters["inheritance_disabled"])
            
            result = session.execute(stmt)
            db_models = result.scalars().all()
            
            return [self._to_entity(model) for model in db_models]
    
    def _to_entity(self, db_model: TaskContextModel) -> TaskContext:
        """Convert database model to domain entity."""
        return TaskContext(
            id=db_model.task_id,
            branch_id=db_model.parent_branch_id,
            task_data=db_model.task_data or {},
            progress=0,  # Progress not in unified schema - could derive from task_data
            insights=[],  # Insights not in unified schema - could derive from task_data
            next_steps=[],  # Next steps not in unified schema - could derive from task_data
            metadata={
                'local_overrides': db_model.local_overrides or {},
                'implementation_notes': db_model.implementation_notes or {},
                'delegation_triggers': db_model.delegation_triggers or {},
                'inheritance_disabled': db_model.inheritance_disabled,
                'force_local_only': db_model.force_local_only,
                'version': db_model.version,
                'created_at': db_model.created_at.isoformat() if db_model.created_at else None,
                'updated_at': db_model.updated_at.isoformat() if db_model.updated_at else None
            }
        )