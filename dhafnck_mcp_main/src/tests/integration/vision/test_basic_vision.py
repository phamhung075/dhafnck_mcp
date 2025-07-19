"""Basic Vision System Test

A minimal test to verify Vision System initialization.
"""

import sys
import os
from pathlib import Path

# Add project root to path
# Go up from test file: vision -> integration -> tests -> src -> dhafnck_mcp_main -> agentic-project
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "dhafnck_mcp_main" / "src"))

# Set environment to enable Vision System
os.environ["DHAFNCK_ENABLE_VISION"] = "true"
# Set pytest environment to ensure test mode
os.environ["PYTEST_CURRENT_TEST"] = "test_basic_vision.py::test_basic_vision"
# Set environment to use specific database path for testing
# Use the correct test database path
test_db_path = project_root / "dhafnck_mcp_main" / "src" / "database" / "data" / "dhafnck_mcp_test.db"
# Ensure the database directory exists
test_db_path.parent.mkdir(parents=True, exist_ok=True)
os.environ["MCP_DB_PATH"] = str(test_db_path)

try:
    print("1. Testing basic imports...")
    from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from fastmcp.task_management.infrastructure.database.models import Base
    print("   ✓ Imports successful")
    
    print("\n2. Initializing test database...")
    # Initialize database schema
    db_config = get_db_config()
    Base.metadata.create_all(bind=db_config.engine)
    print("   ✓ Database schema created")
    
    print("\n3. Testing Vision System initialization...")
    tools = DDDCompliantMCPTools(enable_vision_system=True)
    print("   ✓ DDDCompliantMCPTools created")
    
    print("\n4. Checking Vision System components...")
    if hasattr(tools, '_enable_vision_system'):
        print(f"   ✓ Vision System enabled: {tools._enable_vision_system}")
    
    if hasattr(tools, '_vision_enrichment_service'):
        print("   ✓ Vision Enrichment Service initialized")
    
    if hasattr(tools, '_vision_analytics_service'):
        print("   ✓ Vision Analytics Service initialized")
    
    if hasattr(tools, '_enhanced_task_controller'):
        print("   ✓ Enhanced Task Controller initialized")
    
    if hasattr(tools, '_context_enforcing_controller'):
        print("   ✓ Context Enforcing Controller initialized")
    
    if hasattr(tools, '_workflow_hint_enhancer'):
        print("   ✓ Workflow Hint Enhancer initialized")
    
    print("\n5. Testing basic project creation...")
    result = tools.project_controller.manage_project(
        action="create",
        name="Vision Test Project",
        description="Test project"
    )
    
    if result.get("success"):
        print("   ✓ Project created successfully")
        print(f"   Project ID: {result['project']['id']}")
    else:
        print(f"   ✗ Project creation failed: {result.get('error')}")
    
    print("\n✅ Basic Vision System test PASSED")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)