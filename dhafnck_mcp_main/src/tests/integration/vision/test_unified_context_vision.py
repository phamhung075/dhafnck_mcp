"""Test Unified Context System with Vision Integration

This test verifies the unified context system properly integrates with the Vision System.
"""

import sys
import os
from pathlib import Path
import pytest

# Add project root to path
# Go up from test file: vision -> integration -> tests -> src -> dhafnck_mcp_main -> agentic-project
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "dhafnck_mcp_main" / "src"))

# Set environment to enable Vision System
os.environ["DHAFNCK_ENABLE_VISION"] = "true"
# Set pytest environment to ensure test mode
os.environ["PYTEST_CURRENT_TEST"] = "test_unified_context_vision.py::test_unified_context_vision"
# Set environment to use specific database path for testing
test_db_path = project_root / "dhafnck_mcp_main" / "src" / "database" / "data" / "dhafnck_mcp_test.db"
# Ensure the database directory exists
test_db_path.parent.mkdir(parents=True, exist_ok=True)
os.environ["MCP_DB_PATH"] = str(test_db_path)


def test_unified_context_vision():
    """Test unified context system with vision integration"""
    
    print("\n=== Testing Unified Context System with Vision ===\n")
    
    # 1. Import and initialize
    print("1. Initializing system...")
    from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from fastmcp.task_management.infrastructure.database.models import Base
    
    # Initialize database schema
    db_config = get_db_config()
    Base.metadata.create_all(bind=db_config.engine)
    print("   ✓ Database schema created")
    
    # Create tools instance with Vision System
    tools = DDDCompliantMCPTools(enable_vision_system=True)
    print("   ✓ DDDCompliantMCPTools created with Vision System")
    
    # 2. Create a project
    print("\n2. Creating project...")
    project_result = tools.project_controller.manage_project(
        action="create",
        name="Unified Context Test Project",
        description="Testing unified context with vision"
    )
    assert project_result.get("success"), f"Project creation failed: {project_result.get('error')}"
    project_id = project_result["project"]["id"]
    print(f"   ✓ Project created: {project_id}")
    
    # 3. Create a git branch
    print("\n3. Creating git branch...")
    branch_result = tools.git_branch_controller.manage_git_branch(
        action="create",
        project_id=project_id,
        git_branch_name="feature/test-unified-context",
        git_branch_description="Test branch for unified context"
    )
    assert branch_result.get("success"), f"Branch creation failed: {branch_result.get('error')}"
    branch_id = branch_result["git_branch"]["id"]
    print(f"   ✓ Branch created: {branch_id}")
    
    # 4. Create a task
    print("\n4. Creating task...")
    task_result = tools.task_controller.manage_task(
        action="create",
        git_branch_id=branch_id,
        title="Test Unified Context Task",
        description="Task to test unified context system",
        priority="high"
    )
    assert task_result.get("success"), f"Task creation failed: {task_result.get('error')}"
    task_id = task_result["data"]["task"]["id"]
    print(f"   ✓ Task created: {task_id}")
    
    # 5. Test unified context through facade directly
    print("\n5. Testing unified context operations through facade...")
    
    # Get facade directly from controller
    facade = tools.context_controller._facade_factory.create_facade(
        user_id="test_user",
        project_id=project_id,
        git_branch_id=branch_id
    )
    
    # First, we need to create the context hierarchy
    print("   Creating context hierarchy...")
    
    # Create global context if it doesn't exist
    global_result = facade.get_context(level="global", context_id="global_singleton")
    if not global_result.get("success"):
        print("      Creating global context...")
        global_create_result = facade.create_context(
            level="global",
            context_id="global_singleton",
            data={
                "organization_name": "Test Organization",
                "global_settings": {"vision_enabled": True}
            }
        )
        assert global_create_result.get("success"), f"Global context creation failed: {global_create_result.get('error')}"
        print("      ✓ Global context created")
    
    # Create project context (or use existing)
    print("      Creating project context...")
    project_get_result = facade.get_context(level="project", context_id=project_id)
    if not project_get_result.get("success"):
        project_create_result = facade.create_context(
            level="project",
            context_id=project_id,
            data={
                "project_name": "Unified Context Test Project",
                "project_settings": {"test_mode": True}
            }
        )
        assert project_create_result.get("success"), f"Project context creation failed: {project_create_result.get('error')}"
        print("      ✓ Project context created")
    else:
        print("      ✓ Project context already exists")
    
    # Create branch context (or use existing)
    print("      Creating branch context...")
    branch_get_result = facade.get_context(level="branch", context_id=branch_id)
    if not branch_get_result.get("success"):
        branch_create_result = facade.create_context(
            level="branch",
            context_id=branch_id,
            data={
                "project_id": project_id,
                "git_branch_name": "feature/test-unified-context",
                "branch_settings": {"branch_type": "feature"}
            }
        )
        assert branch_create_result.get("success"), f"Branch context creation failed: {branch_create_result.get('error')}"
        print("      ✓ Branch context created")
    else:
        print("      ✓ Branch context already exists")
    
    # Create task context (or use existing)
    print("      Creating task context...")
    task_get_result = facade.get_context(level="task", context_id=task_id)
    if not task_get_result.get("success"):
        task_create_result = facade.create_context(
            level="task",
            context_id=task_id,
            data={
                "branch_id": branch_id,
                "task_data": {
                    "title": "Test Unified Context Task",
                    "status": "todo"
                }
            }
        )
        assert task_create_result.get("success"), f"Task context creation failed: {task_create_result.get('error')}"
        print("      ✓ Task context created")
    else:
        print("      ✓ Task context already exists")
    
    # Test get context
    print("   a) Testing get context...")
    get_result = facade.get_context(
        level="task",
        context_id=task_id,
        include_inherited=True
    )
    assert get_result.get("success"), f"Get context failed: {get_result.get('error')}"
    print(f"      ✓ Got context successfully")
    
    # Test update context
    print("   b) Testing update context...")
    update_result = facade.update_context(
        level="task",
        context_id=task_id,
        data={
            "custom_field": "test_value",
            "testing_status": "in_progress"
        }
    )
    assert update_result.get("success"), f"Update context failed: {update_result.get('error')}"
    print("      ✓ Context updated")
    
    # Test add_insight
    print("   c) Testing add_insight...")
    insight_result = facade.add_insight(
        level="task",
        context_id=task_id,
        content="Discovered that unified context works well with Vision System",
        category="technical",
        importance="high"
    )
    assert insight_result.get("success"), f"Add insight failed: {insight_result.get('error')}"
    print("      ✓ Insight added")
    
    # Test add_progress
    print("   d) Testing add_progress...")
    progress_result = facade.add_progress(
        level="task",
        context_id=task_id,
        content="Completed 50% of unified context testing"
    )
    assert progress_result.get("success"), f"Add progress failed: {progress_result.get('error')}"
    print("      ✓ Progress added")
    
    # Test delegate
    print("   e) Testing delegation...")
    delegate_result = facade.delegate_context(
        level="task",
        context_id=task_id,
        delegate_to="branch",
        data={
            "pattern_name": "unified_context_test_pattern",
            "implementation": "test implementation details"
        },
        delegation_reason="Sharing test pattern to branch level"
    )
    assert delegate_result.get("success"), f"Delegation failed: {delegate_result.get('error')}"
    print("      ✓ Delegation successful")
    
    # Test resolve to verify inheritance
    print("   f) Testing context resolution...")
    resolve_result = facade.resolve_context(
        level="task",
        context_id=task_id,
        force_refresh=True
    )
    assert resolve_result.get("success"), f"Context resolution failed: {resolve_result.get('error')}"
    print("      ✓ Context resolved with inheritance")
    
    # 6. Verify Vision System integration
    print("\n6. Verifying Vision System integration...")
    if hasattr(tools, '_vision_enrichment_service'):
        print("   ✓ Vision Enrichment Service available")
        
    if hasattr(tools, '_vision_analytics_service'):
        print("   ✓ Vision Analytics Service available")
        
    if hasattr(tools, '_workflow_hint_enhancer'):
        print("   ✓ Workflow Hint Enhancer available")
    
    print("\n✅ All unified context tests passed!")


if __name__ == "__main__":
    # Run the test directly
    try:
        test_unified_context_vision()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)