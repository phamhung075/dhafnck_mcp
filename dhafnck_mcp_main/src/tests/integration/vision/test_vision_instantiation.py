"""Test Vision System instantiation without database dependencies."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment to enable Vision System
os.environ["DHAFNCK_ENABLE_VISION"] = "true"
# Disable database to avoid conflicts
os.environ["DHAFNCK_USE_MOCK_REPOSITORIES"] = "true"


def test_vision_system_instantiation():
    """Test that Vision System can be instantiated without errors."""
    print("\n🧪 Testing Vision System Instantiation\n")
    
    # Import after environment setup
    from fastmcp.task_management.interface.ddd_compliant_mcp_tools import DDDCompliantMCPTools
    
    # Test instantiation with Vision System enabled
    print("Creating DDDCompliantMCPTools with Vision System enabled...")
    tools = DDDCompliantMCPTools(enable_vision_system=True)
    
    # Verify Vision System controllers exist
    assert tools.enhanced_task_controller is not None
    print("✅ Enhanced task controller initialized")
    
    assert tools.context_enforcing_controller is not None
    print("✅ Context enforcing controller initialized")
    
    assert tools.subtask_progress_controller is not None
    print("✅ Subtask progress controller initialized")
    
    assert tools.workflow_hint_enhancer is not None
    print("✅ Workflow hint enhancer initialized")
    
    # Verify Vision services exist
    assert tools.vision_enrichment_service is not None
    print("✅ Vision enrichment service initialized")
    
    assert tools.vision_analytics_service is not None
    print("✅ Vision analytics service initialized")
    
    print("\n✅ All Vision System components initialized successfully!")


if __name__ == "__main__":
    try:
        test_vision_system_instantiation()
        print("\n✅ Vision System instantiation test passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)