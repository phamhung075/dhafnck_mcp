"""
Simplified end-to-end test for branch context resolution.
Tests the exact scenario that was failing without complex fixtures.
"""

import pytest
import uuid
from datetime import datetime, timezone

from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task,
    GlobalContext, ProjectContext, BranchContext, TaskContext
)
from fastmcp.task_management.interface.controllers.unified_context_controller import UnifiedContextMCPController
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory


class TestBranchContextResolutionSimpleE2E:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                # Clean up in dependency order to avoid foreign key errors
                session.execute(text("DELETE FROM task_contexts WHERE task_id LIKE 'test-%'"))
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("""
                    DELETE FROM branch_contexts 
                    WHERE branch_id IN (
                        SELECT id FROM project_git_branchs 
                        WHERE project_id LIKE 'test-%' OR id LIKE 'test-%'
                    )
                """))
                session.execute(text("DELETE FROM project_git_branchs WHERE project_id LIKE 'test-%' OR id LIKE 'test-%'"))
                session.execute(text("DELETE FROM project_contexts WHERE project_id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                
                # Clean up any test global contexts (but preserve global_singleton)
                session.execute(text("DELETE FROM global_contexts WHERE id LIKE 'test-%'"))
                session.commit()
            except Exception as e:
                print(f"Cleanup error: {e}")
                session.rollback()

    """Simple e2e test for the branch context resolution issue."""
    
    def test_exact_frontend_scenario(self):
        """Test the exact scenario from the frontend error."""
        # Get database session
        db_session = get_session()
        
        try:
            # Setup: Create the exact data structure from production
            # Project: test-project-alpha
            project = Project(
                id=str(uuid.uuid4()),
                name=f"test-project-{uuid.uuid4().hex[:8]}",
                description="Production-like test project",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db_session.add(project)
            
            # Branch with the exact problematic ID
            branch_id = str(uuid.uuid4())
            branch = ProjectGitBranch(
                id=branch_id,
                project_id=project.id,
                name=f"test-feature-{uuid.uuid4().hex[:8]}",
                description="Authentication system implementation",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db_session.add(branch)
            
            # Create contexts
            # Global
            # Check if global_singleton exists first
            existing_global = db_session.query(GlobalContext).filter_by(id="global_singleton").first()
            if existing_global:
                global_ctx = existing_global
            else:
                global_ctx = GlobalContext(
                    id="global_singleton",
                    organization_id="DhafnckMCP",
                    autonomous_rules={"code_review": True},
                    security_policies={"mfa": True},
                    coding_standards={"style": "PEP8"},
                    workflow_templates={},
                    delegation_rules={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db_session.add(global_ctx)
            db_session.flush()  # To get the ID
            
            # Project
            # Check if project context exists first
            existing_project_ctx = db_session.query(ProjectContext).filter_by(project_id=project.id).first()
            if existing_project_ctx:
                project_ctx = existing_project_ctx
            else:
                project_ctx = ProjectContext(
                    project_id=project.id,
                    parent_global_id='global_singleton',
                    team_preferences={},
                    technology_stack={"languages": ["python"], "frameworks": ["fastapi"]},
                    project_workflow={},
                    local_standards={},
                    global_overrides={},
                    delegation_rules={},
                    version=1,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db_session.add(project_ctx)
            
            # Branch - This is what was failing
            branch_ctx = BranchContext(
                branch_id=branch_id,
                parent_project_id=project.id,
                parent_project_context_id=project.id,
                branch_workflow={},
                branch_standards={
                    "branch_name": branch.name,
                    "feature_scope": "Authentication"
                },
                agent_assignments={},
                local_overrides={},
                delegation_rules={},
                updated_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                version=1
            )
            db_session.add(branch_ctx)
            
            db_session.commit()
            
            # Test: Create controller
            factory = UnifiedContextFacadeFactory()
            facade = factory.create_facade()
            controller = UnifiedContextMCPController(factory)
            
            # Test 1: The CORRECT way (getBranchContext)
            # Call the facade directly since controller doesn't have execute method
            correct_result = facade.resolve_context(
                level="branch",
                context_id=branch_id,
                force_refresh=False
            )
            
            # This should succeed
            assert correct_result["success"] is True, f"Failed: {correct_result.get('error')}"
            assert correct_result["context"]["id"] == branch_id
            # Debug print
            print(f"DEBUG: correct_result['context'] keys: {list(correct_result['context'].keys())}")
            print(f"DEBUG: branch_settings: {correct_result['context'].get('branch_settings', {})}")
            # Check that branch settings were retrieved - data is under branch_settings
            assert "branch_settings" in correct_result["context"]
            # Branch name is stored in branch_settings -> branch_standards
            assert "branch_name" in correct_result["context"]["branch_settings"]["branch_standards"]
            assert correct_result["context"]["branch_settings"]["branch_standards"]["branch_name"] == branch.name
            
            # Test 2: The WRONG way that was happening (using task context for branch)
            # Try to get branch as if it were a task
            wrong_result = facade.get_context(
                level="task",
                context_id=branch_id  # Branch ID used as task_id!
            )
            
            # This should fail
            assert wrong_result["success"] is False
            assert "not found" in wrong_result["error"].lower() or "does not exist" in wrong_result["error"].lower()
            
            # Test 3: Verify error message is clear when using wrong level
            wrong_level_result = facade.resolve_context(
                level="task",  # Wrong level!
                context_id=branch_id
            )
            
            assert wrong_level_result["success"] is False
            assert "error" in wrong_level_result
            
            print("✅ All e2e tests passed!")
            print(f"✅ Branch context {branch_id} correctly resolved with level='branch'")
            print(f"✅ Branch context {branch_id} correctly fails with level='task'")
            print(f"✅ Frontend fix verified: use getBranchContext() for branches")
            
        finally:
            db_session.rollback()
            db_session.close()
    
    def test_inheritance_chain(self):
        """Test that inheritance works correctly for branch contexts."""
        db_session = get_session()
        
        try:
            # Create hierarchy
            project = Project(
                id=str(uuid.uuid4()),
                name=f"test-inherit-{uuid.uuid4().hex[:8]}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db_session.add(project)
            
            branch = ProjectGitBranch(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name=f"test-branch-{uuid.uuid4().hex[:8]}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db_session.add(branch)
            
            # Create contexts with data to inherit
            # Check if global_singleton exists first
            existing_global = db_session.query(GlobalContext).filter_by(id="global_singleton").first()
            if existing_global:
                global_ctx = existing_global
            else:
                global_ctx = GlobalContext(
                    id="global_singleton",
                    organization_id="DhafnckMCP",
                    autonomous_rules={"code_review": True},
                    security_policies={"mfa": True},
                    coding_standards={"style": "PEP8"},
                    workflow_templates={},
                    delegation_rules={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db_session.add(global_ctx)
            
            # Check if project context exists first
            existing_project_ctx = db_session.query(ProjectContext).filter_by(project_id=project.id).first()
            if existing_project_ctx:
                project_ctx = existing_project_ctx
            else:
                project_ctx = ProjectContext(
                    project_id=project.id,
                    parent_global_id='global_singleton',
                    team_preferences={},
                    technology_stack={"languages": ["python"], "frameworks": ["fastapi"]},
                    project_workflow={},
                    local_standards={},
                    global_overrides={},
                    delegation_rules={},
                    version=1,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db_session.add(project_ctx)
            
            branch_ctx = BranchContext(
                branch_id=branch.id,
                parent_project_id=project.id,
                parent_project_context_id=project.id,
                branch_workflow={},
                branch_standards={"feature": "auth"},
                agent_assignments={},
                local_overrides={},
                delegation_rules={},
                updated_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                version=1
            )
            db_session.add(branch_ctx)
            
            db_session.commit()
            
            # Test inheritance
            factory = UnifiedContextFacadeFactory()
            facade = factory.create_facade()
            
            result = facade.get_context(
                level="branch",
                context_id=branch.id,
                include_inherited=True
            )
            
            assert result["success"] is True
            # Check inheritance metadata
            assert "_inheritance" in result["context"]
            assert result["context"]["_inheritance"]["chain"] == ["global", "project", "branch"]
            # Check inherited data - they are under their respective settings
            assert "global_settings" in result["context"]  # From global
            assert "coding_standards" in result["context"]["global_settings"]
            assert "coding_standards" in result["context"]["global_settings"]
            # Project settings are under project_settings
            assert "project_settings" in result["context"]
            assert "technology_stack" in result["context"]["project_settings"]
            assert "technology_stack" in result["context"]["project_settings"]
            
            print("✅ Inheritance chain verified!")
            
        finally:
            db_session.rollback()
            db_session.close()