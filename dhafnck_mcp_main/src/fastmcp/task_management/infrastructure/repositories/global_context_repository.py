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
from ...infrastructure.database.models import GlobalContext as GlobalContextModel, GLOBAL_SINGLETON_UUID
from .base_orm_repository import BaseORMRepository

logger = logging.getLogger(__name__)


class GlobalContextRepository(BaseORMRepository):
    """Repository for global context operations."""
    
    def __init__(self, session_factory, user_id: Optional[str] = None):
        super().__init__(GlobalContextModel)
        self.session_factory = session_factory
        self.user_id = user_id
    
    def with_user(self, user_id: str) -> 'GlobalContextRepository':
        """Create a new repository instance scoped to a specific user."""
        return GlobalContextRepository(self.session_factory, user_id)
    
    def _is_valid_uuid(self, value: str) -> bool:
        """Check if a string is a valid UUID."""
        import uuid
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_valid_context_id(self, value: str) -> bool:
        """Check if a string is a valid context ID (UUID or composite ID)."""
        if not value:
            return False
        
        # Accept pure UUIDs
        if self._is_valid_uuid(value):
            return True
        
        # Accept composite context IDs for global contexts (UUID_UUID format)
        if '_' in value:
            parts = value.split('_', 1)  # Split on first underscore only
            if len(parts) == 2:
                # Check if both parts are valid UUIDs
                return self._is_valid_uuid(parts[0]) and self._is_valid_uuid(parts[1])
        
        return False
    
    def _normalize_context_id(self, context_id: str) -> str:
        """
        Normalize context IDs for backward compatibility.
        Converts 'global_singleton' string to the proper UUID for global contexts.
        """
        if context_id == "global_singleton":
            return GLOBAL_SINGLETON_UUID
        return context_id
    
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
        import uuid
        with self.get_db_session() as session:
            # Check if global context already exists for this user
            # Each user gets a unique global context ID
            
            # For user-specific contexts, use the passed context_id if valid context ID
            # Otherwise generate a new UUID  
            if entity.id and self._is_valid_context_id(entity.id):
                context_id = entity.id
            else:
                context_id = str(uuid.uuid4())
            
            # Check if this ID already exists
            existing = session.query(GlobalContextModel).filter(
                GlobalContextModel.id == context_id
            ).first()
            if existing:
                raise ValueError(f"Global context with ID {context_id} already exists. Use update instead.")
            
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
            
            # Store the actual organization_name in workflow_templates metadata
            if entity.organization_name:
                workflow_templates["_metadata"] = {"organization_name": entity.organization_name}
            
            # Create new global context - map domain entity to database model
            # For organization_id, use the default UUID since it's not user-specific
            
            db_model = GlobalContextModel(
                id=context_id,  # Use the validated/generated UUID
                organization_id="00000000-0000-0000-0000-000000000002",  # Default organization UUID
                autonomous_rules=autonomous_rules,
                security_policies=security_policies,
                coding_standards=coding_standards,
                workflow_templates=workflow_templates,
                delegation_rules=delegation_rules,
                user_id=self.user_id,  # CRITICAL FIX: Never fallback to "system" - should always have user_id
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            session.add(db_model)
            session.flush()
            # Keep session.refresh() disabled to avoid UUID handling issues with composite IDs
            # The manual row-to-model conversion in get() method handles this correctly
            # session.refresh(db_model)
            
            return self._to_entity(db_model)
    
    def get(self, context_id: str) -> Optional[GlobalContext]:
        """Get global context by ID."""
        original_id = context_id
        context_id = self._normalize_context_id(context_id)
        
        # For SQLite, we need to handle UUID normalization (remove hyphens)
        # because SQLAlchemy UUID fields store without hyphens in SQLite
        normalized_context_id = self._normalize_uuid_for_sqlite(context_id)
        
        with self.get_db_session() as session:
            # Use raw SQL to avoid SQLAlchemy UUID casting issues
            from sqlalchemy import text
            
            if self.user_id:
                # Query with user filter
                query_sql = """
                    SELECT * FROM global_contexts 
                    WHERE id = :context_id AND user_id = :user_id 
                    LIMIT 1
                """
                result = session.execute(text(query_sql), {
                    "context_id": normalized_context_id,
                    "user_id": self.user_id
                })
            else:
                # Query without user filter
                query_sql = """
                    SELECT * FROM global_contexts 
                    WHERE id = :context_id
                    LIMIT 1
                """
                result = session.execute(text(query_sql), {
                    "context_id": normalized_context_id
                })
            
            row = result.fetchone()
            if not row:
                logger.debug(f"Global context not found for ID: {original_id} (normalized to: {context_id}, sqlite: {normalized_context_id})")
                return None
            
            # Convert row to model instance manually
            # Handle datetime parsing for SQLite string dates
            from datetime import datetime
            import json
            
            def parse_datetime(date_str):
                """Parse datetime string from SQLite."""
                if isinstance(date_str, str):
                    try:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        return datetime.now()
                return date_str
            
            def parse_json(json_str):
                """Parse JSON string from SQLite."""
                if isinstance(json_str, str):
                    try:
                        return json.loads(json_str)
                    except:
                        return {}
                return json_str or {}
            
            db_model = GlobalContextModel()
            db_model.id = row[0]
            db_model.organization_id = row[1]
            db_model.autonomous_rules = parse_json(row[2])
            db_model.security_policies = parse_json(row[3])
            db_model.coding_standards = parse_json(row[4])
            db_model.workflow_templates = parse_json(row[5])
            db_model.delegation_rules = parse_json(row[6])
            db_model.created_at = parse_datetime(row[7])
            db_model.updated_at = parse_datetime(row[8])
            db_model.version = row[9] or 1
            db_model.user_id = row[10]
            
            return self._to_entity(db_model)
    
    def _normalize_uuid_for_sqlite(self, context_id: str) -> str:
        """Normalize UUID format for SQLite storage (remove hyphens)."""
        import re
        return re.sub(r'-', '', context_id)
    
    def update(self, context_id: str, entity: GlobalContext) -> GlobalContext:
        """Update global context."""
        original_id = context_id
        context_id = self._normalize_context_id(context_id)
        
        # For SQLite, we need to handle UUID normalization (remove hyphens)
        # because SQLAlchemy UUID fields store without hyphens in SQLite
        normalized_context_id = self._normalize_uuid_for_sqlite(context_id)
        
        with self.get_db_session() as session:
            # Use raw SQL to avoid SQLAlchemy UUID casting issues
            from sqlalchemy import text
            
            if self.user_id:
                # Query with user filter
                query_sql = """
                    SELECT * FROM global_contexts 
                    WHERE id = :context_id AND user_id = :user_id 
                    LIMIT 1
                """
                result = session.execute(text(query_sql), {
                    "context_id": normalized_context_id,
                    "user_id": self.user_id
                })
            else:
                # Query without user filter
                query_sql = """
                    SELECT * FROM global_contexts 
                    WHERE id = :context_id
                    LIMIT 1
                """
                result = session.execute(text(query_sql), {
                    "context_id": normalized_context_id
                })
            
            row = result.fetchone()
            if not row:
                logger.debug(f"Global context not found for update: {original_id} (normalized to: {context_id}, sqlite: {normalized_context_id})")
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
            
            # Store the organization_name in workflow_templates metadata
            if entity.organization_name:
                workflow_templates["_metadata"] = {"organization_name": entity.organization_name}
            
            # Use raw SQL update to avoid UUID casting issues
            import json
            update_sql = """
                UPDATE global_contexts 
                SET organization_id = :org_id,
                    autonomous_rules = :autonomous_rules,
                    security_policies = :security_policies,
                    coding_standards = :coding_standards,
                    workflow_templates = :workflow_templates,
                    delegation_rules = :delegation_rules,
                    updated_at = :updated_at
                WHERE id = :context_id
            """
            
            # Add user filter if user_id is set
            if self.user_id:
                update_sql += " AND user_id = :user_id"
            
            update_params = {
                "context_id": normalized_context_id,
                "org_id": "00000000-0000-0000-0000-000000000002",  # Default organization UUID
                "autonomous_rules": json.dumps(autonomous_rules),
                "security_policies": json.dumps(security_policies),
                "coding_standards": json.dumps(coding_standards),
                "workflow_templates": json.dumps(workflow_templates),
                "delegation_rules": json.dumps(delegation_rules),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if self.user_id:
                update_params["user_id"] = self.user_id
            
            session.execute(text(update_sql), update_params)
            session.flush()
            
            # Get the updated record using the same approach as get method
            updated_result = session.execute(text(query_sql), {
                "context_id": normalized_context_id,
                "user_id": self.user_id
            } if self.user_id else {"context_id": normalized_context_id})
            
            updated_row = updated_result.fetchone()
            if not updated_row:
                raise ValueError(f"Failed to retrieve updated context: {context_id}")
            
            # Convert row to model instance manually (same as in get method)
            import json
            
            def parse_datetime(date_str):
                """Parse datetime string from SQLite."""
                if isinstance(date_str, str):
                    try:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        return datetime.now()
                return date_str
            
            def parse_json(json_str):
                """Parse JSON string from SQLite."""
                if isinstance(json_str, str):
                    try:
                        return json.loads(json_str)
                    except:
                        return {}
                return json_str or {}
            
            db_model = GlobalContextModel()
            db_model.id = updated_row[0]
            db_model.organization_id = updated_row[1]
            db_model.autonomous_rules = parse_json(updated_row[2])
            db_model.security_policies = parse_json(updated_row[3])
            db_model.coding_standards = parse_json(updated_row[4])
            db_model.workflow_templates = parse_json(updated_row[5])
            db_model.delegation_rules = parse_json(updated_row[6])
            db_model.created_at = parse_datetime(updated_row[7])
            db_model.updated_at = parse_datetime(updated_row[8])
            db_model.version = updated_row[9] or 1
            db_model.user_id = updated_row[10]
            
            return self._to_entity(db_model)
    
    def delete(self, context_id: str) -> bool:
        """Delete global context."""
        context_id = self._normalize_context_id(context_id)
        with self.get_db_session() as session:
            # Use query instead of session.get for UUID fields to avoid casting issues
            db_model = session.query(GlobalContextModel).filter(GlobalContextModel.id == context_id).first()
            if not db_model:
                return False
            
            session.delete(db_model)
            return True
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[GlobalContext]:
        """List global contexts (should only be one per user)."""
        with self.get_db_session() as session:
            stmt = select(GlobalContextModel)
            
            # Add user filter if user_id is set
            if self.user_id:
                stmt = stmt.where(GlobalContextModel.user_id == self.user_id)
            
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
        
        # Get organization_name from workflow_templates metadata if stored there
        org_metadata = db_model.workflow_templates.get("_metadata", {}) if db_model.workflow_templates else {}
        organization_name = org_metadata.get("organization_name", "Default Organization")
        
        return GlobalContext(
            id=db_model.id,
            organization_name=organization_name,  # Get from workflow_templates metadata
            global_settings=global_settings,
            metadata=metadata
        )