"""
Fixed version of test_branch_context_resolution_simple_e2e.py
Demonstrates proper PostgreSQL test isolation.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import text

from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectGitBranch, Task,
    GlobalContext, ProjectContext, BranchContext, TaskContext
)
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory


def cleanup_test_data(session):
    """Clean up test data with proper ordering."""
    try:
        # Clean in dependency order
        session.execute(text("DELETE FROM task_contexts WHERE task_id LIKE 'test-%'"))
        session.execute(text("DELETE FROM branch_contexts WHERE branch_id LIKE 'test-%'"))
        session.execute(text("DELETE FROM project_contexts WHERE project_id LIKE 'test-%'"))
        session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
        session.execute(text("DELETE FROM project_git_branchs WHERE id LIKE 'test-%'"))
        session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%'"))
        session.commit()
    except Exception:
        session.rollback()


class TestBranchContextResolutionSimpleE2EFixed:
    """Fixed e2e test with proper PostgreSQL isolation."""
    
    def setup_method(self, method):
        """Clean up before each test"""
        db_config = get_db_config()
        with db_config.get_session() as session:
            cleanup_test_data(session)
    
    def teardown_method(self, method):
        """Clean up after each test"""
        db_config = get_db_config()
        with db_config.get_session() as session:
            cleanup_test_data(session)
    
    def test_exact_frontend_scenario(self):
        """Test the exact scenario from the frontend error - FIXED."""
        db_config = get_db_config()
        
        with db_config.get_session() as db_session:
            try:
                # Setup: Create the exact data structure from production
                # Use unique IDs to avoid conflicts
                project_id = f"test-proj-{uuid.uuid4().hex[:8]}"
                branch_id = f"test-branch-{uuid.uuid4().hex[:8]}"
                
                project = Project(
                    id=project_id,
                    name="test-project-alpha-fixed",
                    description="Production-like test project",
                    user_id="test-user",
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(project)
                
                branch = ProjectGitBranch(
                    id=branch_id,
                    project_id=project_id,
                    name="feature/auth-system-fixed",
                    description="Authentication system implementation",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(branch)
                
                # Create contexts with existence checks
                # Global context
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
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db_session.add(global_ctx)
                
                # Project context
                project_ctx = ProjectContext(
                    project_id=project_id,
                    parent_global_id='global_singleton',
                    team_preferences={},
                    technology_stack={"languages": ["python"], "frameworks": ["fastapi"]},
                    project_workflow={},
                    local_standards={},
                    global_overrides={},
                    delegation_rules={},
                    version=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(project_ctx)
                
                # Branch context
                branch_ctx = BranchContext(
                    branch_id=branch_id,
                    parent_project_id=project_id,
                    parent_project_context_id=project_id,
                    branch_workflow={},
                    branch_standards={
                        "branch_name": branch.name,
                        "feature_scope": "Authentication"
                    },
                    agent_assignments={},
                    local_overrides={},
                    delegation_rules={},
                    version=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(branch_ctx)
                
                db_session.commit()
                
                # Test: Create facade (not controller)
                factory = UnifiedContextFacadeFactory()
                facade = factory.create_facade()
                
                # Test 1: The CORRECT way (getBranchContext using facade)
                correct_result = facade.resolve_context(
                    level="branch",
                    context_id=branch_id,
                    force_refresh=False
                )
                
                # This should succeed
                assert correct_result["success"] is True, f"Failed: {correct_result.get('error')}"
                assert correct_result["context"]["id"] == branch_id
                
                # Check that branch settings were retrieved
                assert "branch_settings" in correct_result["context"]
                assert correct_result["context"]["branch_settings"]["branch_standards"]["branch_name"] == "feature/auth-system-fixed"
                
                # Test 2: The WRONG way that was happening (using task context for branch)
                wrong_result = facade.get_context(
                    level="task",
                    context_id=branch_id  # Branch ID used as task_id!
                )
                
                # This should fail
                assert wrong_result["success"] is False
                assert "not found" in wrong_result["error"].lower() or "does not exist" in wrong_result["error"].lower()
                
                print("✅ All fixed e2e tests passed!")
                print(f"✅ Branch context {branch_id} correctly resolved with level='branch'")
                print(f"✅ Branch context {branch_id} correctly fails with level='task'")
                print(f"✅ Frontend fix verified: use getBranchContext() for branches")
                
            finally:
                db_session.rollback()
    
    def test_inheritance_chain(self):
        """Test that inheritance works correctly for branch contexts - FIXED."""
        db_config = get_db_config()
        
        with db_config.get_session() as db_session:
            try:
                # Create hierarchy with unique IDs
                project_id = f"test-inherit-proj-{uuid.uuid4().hex[:8]}"
                branch_id = f"test-inherit-branch-{uuid.uuid4().hex[:8]}"
                
                project = Project(
                    id=project_id,
                    name="inheritance-test-project-fixed",
                    description="Inheritance test project",
                    user_id="test-user",
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(project)
                
                branch = ProjectGitBranch(
                    id=branch_id,
                    project_id=project_id,
                    name="test-branch-fixed",
                    description="Test branch for inheritance",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(branch)
                
                # Create contexts with data to inherit
                # Global context with existence check
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
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db_session.add(global_ctx)
                
                project_ctx = ProjectContext(
                    project_id=project_id,
                    parent_global_id='global_singleton',
                    team_preferences={},
                    technology_stack={"languages": ["python"], "frameworks": ["fastapi"]},
                    project_workflow={},
                    local_standards={},
                    global_overrides={},
                    delegation_rules={},
                    version=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(project_ctx)
                
                branch_ctx = BranchContext(
                    branch_id=branch_id,
                    parent_project_id=project_id,
                    parent_project_context_id=project_id,
                    branch_workflow={},
                    branch_standards={"feature": "auth"},
                    agent_assignments={},
                    local_overrides={},
                    delegation_rules={},
                    version=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db_session.add(branch_ctx)
                
                db_session.commit()
                
                # Test inheritance using facade
                factory = UnifiedContextFacadeFactory()
                facade = factory.create_facade()
                
                result = facade.get_context(
                    level="branch",
                    context_id=branch_id,
                    include_inherited=True
                )
                
                assert result["success"] is True
                # Check inheritance metadata
                assert "_inheritance" in result["context"]
                assert result["context"]["_inheritance"]["chain"] == ["global", "project", "branch"]
                
                print("✅ Inheritance chain verified in fixed test!")
                
            finally:
                db_session.rollback()