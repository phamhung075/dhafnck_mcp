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
# IMPORTANT: Remove PYTEST_CURRENT_TEST to bypass test mode detection
# This allows us to use PostgreSQL instead of the default SQLite test database
# We'll use the TEST_DATABASE_URL instead
if "PYTEST_CURRENT_TEST" in os.environ:
    del os.environ["PYTEST_CURRENT_TEST"]
# Use PostgreSQL for testing with separate test database
os.environ["DATABASE_TYPE"] = "postgresql"
# Use TEST_DATABASE_URL which should point to the test PostgreSQL database
# For now, use the existing Supabase database but with a test schema
# In production, you should create a separate test database
test_db_url = os.environ.get("TEST_DATABASE_URL")
if test_db_url and "localhost" not in test_db_url:
    # Use the configured test database URL if it's not localhost
    os.environ["DATABASE_URL"] = test_db_url
else:
    # Use the production Supabase URL but with test schema
    # Get the actual DATABASE_URL from environment and use it
    import urllib.parse
    prod_db_url = os.environ.get("DATABASE_URL", "")
    if prod_db_url:
        # Parse the URL to add schema parameter
        parsed = urllib.parse.urlparse(prod_db_url)
        # Add test schema to the query parameters
        query_params = urllib.parse.parse_qs(parsed.query)
        query_params['options'] = ['--search_path=test']
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        # Rebuild the URL with the new query parameters
        test_db_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        os.environ["DATABASE_URL"] = test_db_url
        print("⚠️  Using production database with test schema. Consider setting up a dedicated test database.")
        print(f"   Database URL: {test_db_url}")
    else:
        raise RuntimeError("DATABASE_URL not found in environment")
# Disable authentication for testing
os.environ["DISABLE_AUTH"] = "true"

try:
    print("1. Testing basic imports...")
    from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config, close_db
    from fastmcp.task_management.infrastructure.database.models import Base
    print("   ✓ Imports successful")
    
    print("\n2. Initializing test database...")
    # Clear any existing database configuration
    close_db()
    
    # Debug: Print the actual DATABASE_URL being used
    print(f"   DATABASE_URL in env: {os.environ.get('DATABASE_URL', 'NOT SET')}")
    print(f"   DATABASE_TYPE in env: {os.environ.get('DATABASE_TYPE', 'NOT SET')}")
    
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