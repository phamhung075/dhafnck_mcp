"""Test core Vision System imports that don't have syntax errors."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment to enable Vision System
os.environ["DHAFNCK_ENABLE_VISION"] = "true"


def test_core_imports():
    """Test that core Vision System modules can be imported."""
    print("\n🧪 Testing Core Vision System Imports\n")
    
    # Domain layer imports
    print("Testing domain layer imports...")
    from fastmcp.task_management.domain.entities.context import TaskContext
    from fastmcp.task_management.domain.entities.task import Task
    from fastmcp.task_management.domain.value_objects.hints import WorkflowHint, HintType, HintPriority
    from fastmcp.task_management.domain.value_objects.progress import ProgressType, ProgressStatus
    from fastmcp.task_management.domain.value_objects.agents import AgentProfile, AgentCapabilities
    from fastmcp.task_management.domain.value_objects.vision_objects import VisionObjective, VisionMetric
    print("✅ Domain layer imports successful")
    
    # Domain events
    print("\nTesting domain events...")
    from fastmcp.task_management.domain.events.hint_events import HintGenerated
    from fastmcp.task_management.domain.events.progress_events import ProgressUpdated
    from fastmcp.task_management.domain.events.agent_events import AgentAssigned
    print("✅ Domain events imports successful")
    
    # Application services
    print("\nTesting application services...")
    from fastmcp.task_management.application.services.hint_generation_service import HintGenerationService
    from fastmcp.task_management.application.services.progress_tracking_service import ProgressTrackingService
    from fastmcp.task_management.application.services.agent_coordination_service import AgentCoordinationService
    from fastmcp.task_management.application.services.vision_analytics_service import VisionAnalyticsService
    print("✅ Application services imports successful")
    
    # Configuration
    print("\nTesting configuration...")
    from fastmcp.vision_orchestration.configuration.config_loader import get_vision_config, is_vision_enabled
    config = get_vision_config()
    assert config is not None
    assert is_vision_enabled() is True
    print("✅ Configuration loaded successfully")


def test_object_creation():
    """Test that Vision System objects can be created."""
    print("\n🧪 Testing Vision System Object Creation\n")
    
    from fastmcp.task_management.domain.entities.context import TaskContext, ContextMetadata, ContextObjective
    from fastmcp.task_management.domain.value_objects.hints import WorkflowHint, HintType, HintPriority
    from fastmcp.task_management.domain.value_objects.vision_objects import VisionObjective, VisionMetric
    from uuid import uuid4
    
    # Create a task context
    metadata = ContextMetadata(task_id=str(uuid4()))
    objective = ContextObjective(title="Test Task", description="Test Description")
    context = TaskContext(metadata=metadata, objective=objective)
    print(f"✅ Created TaskContext: {context.metadata.task_id}")
    
    # Create a workflow hint
    from fastmcp.task_management.domain.value_objects.hints import HintMetadata
    metadata = HintMetadata(
        source="test",
        confidence=0.8,
        reasoning="Test reasoning"
    )
    hint = WorkflowHint.create(
        task_id=uuid4(),
        hint_type=HintType.NEXT_ACTION,
        priority=HintPriority.MEDIUM,
        message="Test hint",
        suggested_action="Test action",
        metadata=metadata
    )
    print(f"✅ Created WorkflowHint: {hint.id}")
    
    # Create vision objective
    vision_obj = VisionObjective(
        title="Test Vision Objective",
        description="Test Vision Description"
    )
    print(f"✅ Created VisionObjective: {vision_obj.id}")


if __name__ == "__main__":
    try:
        test_core_imports()
        test_object_creation()
        
        print("\n\n✅ All core Vision System tests passed!")
        print("\nThe Vision System core components have been successfully integrated!")
        print("All imports and object creation work correctly.")
        
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)