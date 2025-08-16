"""
Temporary fix for UUID/String inconsistency in hierarchical context models.

This module provides a patched version of the context models that handles
the UUID/String mismatch issue by ensuring consistent field definitions.

PROBLEM:
- GlobalContext.id is defined as String but database may expect UUID
- ProjectContext.parent_global_id references "global_singleton" string
- PostgreSQL rejects "global_singleton" as invalid UUID syntax

SOLUTION:
- Use a proper UUID for global_singleton to satisfy PostgreSQL constraints
- Update all references to use this UUID consistently
- Maintain backward compatibility
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Define a consistent global singleton UUID that replaces "global_singleton" string
GLOBAL_SINGLETON_UUID = "00000000-0000-0000-0000-000000000001"

def get_global_singleton_id() -> str:
    """Get the consistent global singleton UUID."""
    return GLOBAL_SINGLETON_UUID


def patch_context_models():
    """
    Patch existing context models to use UUID consistently.
    
    This function modifies the existing model definitions to ensure
    UUID consistency across the hierarchical context system.
    """
    logger.info("Patching context models for UUID consistency...")
    
    from fastmcp.task_management.infrastructure.database.models import (
        GlobalContext, ProjectContext, BranchContext, TaskContext
    )
    
    # Patch GlobalContext to use consistent UUID
    original_global_init = GlobalContext.__init__
    
    def patched_global_init(self, **kwargs):
        # If no id provided or id is "global_singleton", use consistent UUID
        if 'id' not in kwargs or kwargs['id'] == 'global_singleton':
            kwargs['id'] = GLOBAL_SINGLETON_UUID
        original_global_init(self, **kwargs)
    
    GlobalContext.__init__ = patched_global_init
    
    # Patch ProjectContext to use consistent UUID for parent_global_id
    original_project_init = ProjectContext.__init__
    
    def patched_project_init(self, **kwargs):
        # If parent_global_id is "global_singleton", use consistent UUID
        if kwargs.get('parent_global_id') == 'global_singleton':
            kwargs['parent_global_id'] = GLOBAL_SINGLETON_UUID
        original_project_init(self, **kwargs)
    
    ProjectContext.__init__ = patched_project_init
    
    logger.info(f"✅ Context models patched to use UUID: {GLOBAL_SINGLETON_UUID}")
    

def create_global_singleton_if_missing(session):
    """
    Ensure global singleton context exists with consistent UUID.
    
    This function checks if the global singleton exists and creates it
    with the proper UUID if missing.
    """
    from fastmcp.task_management.infrastructure.database.models import GlobalContext
    
    try:
        # Check if global singleton exists (either old string or new UUID)
        existing = session.query(GlobalContext).filter(
            GlobalContext.id.in_(['global_singleton', GLOBAL_SINGLETON_UUID])
        ).first()
        
        if existing:
            # If exists with old string ID, update to UUID
            if existing.id == 'global_singleton':
                logger.info("Migrating global_singleton from string to UUID...")
                existing.id = GLOBAL_SINGLETON_UUID
                session.flush()
                logger.info(f"✅ Migrated global context to UUID: {GLOBAL_SINGLETON_UUID}")
            else:
                logger.info(f"✅ Global singleton already exists with UUID: {existing.id}")
        else:
            # Create new global singleton with UUID
            logger.info("Creating global singleton context with consistent UUID...")
            global_context = GlobalContext(
                id=GLOBAL_SINGLETON_UUID,
                organization_id="DhafnckMCP",
                autonomous_rules={
                    "code_quality": "high",
                    "test_coverage": "required",
                    "documentation": "mandatory"
                },
                security_policies={
                    "authentication": "required",
                    "authorization": "rbac",
                    "data_encryption": "at_rest_and_transit"
                },
                coding_standards={
                    "style": "PEP8",
                    "type_hints": "required",
                    "docstrings": "google_style"
                },
                workflow_templates={
                    "default_workflow": "tdd",
                    "review_process": "mandatory",
                    "deployment": "automated"
                },
                delegation_rules={
                    "auto_delegation": True,
                    "approval_required": False,
                    "confidence_threshold": 0.8
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1
            )
            session.add(global_context)
            session.flush()
            logger.info(f"✅ Created global singleton context with UUID: {GLOBAL_SINGLETON_UUID}")
            
        return GLOBAL_SINGLETON_UUID
        
    except Exception as e:
        logger.error(f"❌ Error managing global singleton: {e}")
        raise


def validate_uuid_consistency(session) -> Dict[str, Any]:
    """
    Validate that all context references use consistent UUIDs.
    
    Returns validation results with any inconsistencies found.
    """
    from fastmcp.task_management.infrastructure.database.models import (
        GlobalContext, ProjectContext, BranchContext, TaskContext
    )
    
    validation_results = {
        "global_context": {"exists": False, "id": None, "consistent": False},
        "project_contexts": {"count": 0, "inconsistent_refs": []},
        "issues_found": [],
        "recommendations": []
    }
    
    try:
        # Check global context
        global_ctx = session.query(GlobalContext).filter_by(id=GLOBAL_SINGLETON_UUID).first()
        if global_ctx:
            validation_results["global_context"]["exists"] = True
            validation_results["global_context"]["id"] = global_ctx.id
            validation_results["global_context"]["consistent"] = True
        else:
            # Check for old string-based global context
            old_global = session.query(GlobalContext).filter_by(id='global_singleton').first()
            if old_global:
                validation_results["global_context"]["exists"] = True
                validation_results["global_context"]["id"] = old_global.id
                validation_results["issues_found"].append(
                    "Global context uses old string ID 'global_singleton' instead of UUID"
                )
                validation_results["recommendations"].append(
                    f"Migrate global context ID from 'global_singleton' to '{GLOBAL_SINGLETON_UUID}'"
                )
        
        # Check project contexts
        project_contexts = session.query(ProjectContext).all()
        validation_results["project_contexts"]["count"] = len(project_contexts)
        
        for project_ctx in project_contexts:
            if project_ctx.parent_global_id == 'global_singleton':
                validation_results["project_contexts"]["inconsistent_refs"].append(
                    f"Project {project_ctx.project_id} references old string ID 'global_singleton'"
                )
            elif project_ctx.parent_global_id != GLOBAL_SINGLETON_UUID:
                validation_results["project_contexts"]["inconsistent_refs"].append(
                    f"Project {project_ctx.project_id} references unknown global ID: {project_ctx.parent_global_id}"
                )
        
        # Add recommendations based on findings
        if validation_results["project_contexts"]["inconsistent_refs"]:
            validation_results["recommendations"].append(
                "Update all project context references to use consistent global UUID"
            )
        
        if not validation_results["issues_found"] and not validation_results["project_contexts"]["inconsistent_refs"]:
            validation_results["recommendations"].append("UUID consistency is maintained across all contexts")
        
    except Exception as e:
        validation_results["issues_found"].append(f"Validation error: {str(e)}")
        logger.error(f"UUID consistency validation failed: {e}")
    
    return validation_results


def migrate_string_ids_to_uuid(session, dry_run: bool = True) -> Dict[str, Any]:
    """
    Migrate old string-based IDs to consistent UUIDs.
    
    Args:
        session: Database session
        dry_run: If True, only shows what would be changed without executing
    
    Returns:
        Migration results with details of changes made or planned
    """
    from fastmcp.task_management.infrastructure.database.models import (
        GlobalContext, ProjectContext, BranchContext, TaskContext
    )
    
    migration_results = {
        "dry_run": dry_run,
        "changes_planned": [],
        "changes_executed": [],
        "errors": [],
        "success": False
    }
    
    try:
        # Step 1: Handle global context migration
        old_global = session.query(GlobalContext).filter_by(id='global_singleton').first()
        if old_global:
            change_desc = f"Migrate global context ID: 'global_singleton' -> '{GLOBAL_SINGLETON_UUID}'"
            migration_results["changes_planned"].append(change_desc)
            
            if not dry_run:
                old_global.id = GLOBAL_SINGLETON_UUID
                session.flush()
                migration_results["changes_executed"].append(change_desc)
                logger.info(f"✅ {change_desc}")
        
        # Step 2: Update project context references
        project_contexts = session.query(ProjectContext).filter_by(parent_global_id='global_singleton').all()
        for project_ctx in project_contexts:
            change_desc = f"Update project {project_ctx.project_id}: parent_global_id -> '{GLOBAL_SINGLETON_UUID}'"
            migration_results["changes_planned"].append(change_desc)
            
            if not dry_run:
                project_ctx.parent_global_id = GLOBAL_SINGLETON_UUID
                migration_results["changes_executed"].append(change_desc)
                logger.info(f"✅ {change_desc}")
        
        # Step 3: Validate consistency after migration
        if not dry_run:
            validation = validate_uuid_consistency(session)
            if validation["issues_found"]:
                migration_results["errors"].extend(validation["issues_found"])
            else:
                migration_results["success"] = True
                logger.info("✅ UUID migration completed successfully")
        else:
            migration_results["success"] = True  # Dry run success
            logger.info("✅ Dry run completed - no changes made")
    
    except Exception as e:
        error_msg = f"Migration failed: {str(e)}"
        migration_results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")
    
    return migration_results


# Convenience function for easy usage
def apply_uuid_fix(session, auto_migrate: bool = False):
    """
    Apply UUID fix to resolve context creation errors.
    
    Args:
        session: Database session
        auto_migrate: If True, automatically migrate old string IDs to UUIDs
    
    This function:
    1. Patches the context models to handle UUID consistently
    2. Ensures global singleton exists with proper UUID
    3. Optionally migrates old string references to UUIDs
    """
    logger.info("Applying UUID fix for hierarchical context system...")
    
    try:
        # Step 1: Patch models
        patch_context_models()
        
        # Step 2: Ensure global singleton exists
        global_id = create_global_singleton_if_missing(session)
        
        # Step 3: Validate consistency
        validation = validate_uuid_consistency(session)
        
        # Step 4: Auto-migrate if requested
        if auto_migrate and (validation["issues_found"] or validation["project_contexts"]["inconsistent_refs"]):
            logger.info("Auto-migrating string IDs to UUIDs...")
            migration_result = migrate_string_ids_to_uuid(session, dry_run=False)
            
            if migration_result["success"]:
                logger.info("✅ UUID migration completed successfully")
            else:
                logger.warning(f"⚠️ UUID migration had issues: {migration_result['errors']}")
        
        session.commit()
        logger.info("✅ UUID fix applied successfully")
        
        return {
            "success": True,
            "global_singleton_uuid": global_id,
            "validation": validation,
            "message": "UUID fix applied - context creation should now work"
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ UUID fix failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "UUID fix failed - manual intervention may be required"
        }


if __name__ == "__main__":
    """Command-line usage for UUID fix."""
    import os
    import sys
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL or SUPABASE_DATABASE_URL required")
        sys.exit(1)
    
    # Create session
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔧 Applying UUID fix for hierarchical context system...")
        result = apply_uuid_fix(session, auto_migrate=True)
        
        if result["success"]:
            print(f"✅ SUCCESS: {result['message']}")
            print(f"Global Singleton UUID: {result['global_singleton_uuid']}")
        else:
            print(f"❌ FAILED: {result['message']}")
            if 'error' in result:
                print(f"Error: {result['error']}")
        
    except Exception as e:
        print(f"❌ UUID fix script failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()