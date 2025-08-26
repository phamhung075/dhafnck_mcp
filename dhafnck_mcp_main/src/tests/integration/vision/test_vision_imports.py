"""Test that all Vision System imports work correctly after Phase 6 integration."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment to enable Vision System
os.environ["DHAFNCK_ENABLE_VISION"] = "true"

import pytest


def test_vision_imports():
    """Test that all Vision System modules can be imported."""
    print("\n\n=== Testing Vision System Imports ===\n")
    
    # Phase 1: Context Enforcement
    print("Phase 1: Context Enforcement...")
    from fastmcp.task_management.domain.entities.context import TaskContext
    from fastmcp.task_management.application.services.context_validation_service import ContextValidationService
    # Context enforcing functionality is now integrated into TaskMCPController
    from fastmcp.task_management.interface.controllers.task_mcp_controller import TaskMCPController
    print("✅ Context enforcement imports successful")
    
    # Phase 2: Progress Tracking
    print("\nPhase 2: Progress Tracking...")
    from fastmcp.task_management.domain.value_objects.progress import ProgressType, ProgressStatus
    from fastmcp.task_management.application.services.progress_tracking_service import ProgressTrackingService
    from fastmcp.task_management.domain.events.progress_events import ProgressUpdated
    print("✅ Progress tracking imports successful")
    
    # Phase 3: Workflow Hints
    print("\nPhase 3: Workflow Hints...")
    from fastmcp.task_management.domain.value_objects.hints import WorkflowHint, HintType
    from fastmcp.task_management.application.services.hint_generation_service import HintGenerationService
    from fastmcp.task_management.interface.controllers.workflow_hint_enhancer import WorkflowHintEnhancer
    from fastmcp.task_management.domain.events.hint_events import HintGenerated
    print("✅ Workflow hints imports successful")
    
    # Phase 4: Agent Coordination
    print("\nPhase 4: Agent Coordination...")
    from fastmcp.task_management.domain.value_objects.agents import AgentProfile
    from fastmcp.task_management.domain.value_objects.coordination import CoordinationStrategy
    from fastmcp.task_management.application.services.agent_coordination_service import AgentCoordinationService
    from fastmcp.task_management.domain.events.agent_events import AgentAssigned
    print("✅ Agent coordination imports successful")
    
    # Phase 5: Vision Enrichment
    print("\nPhase 5: Vision Enrichment...")
    from fastmcp.task_management.domain.value_objects.vision_objects import VisionObjective, VisionMetric
    from fastmcp.task_management.application.services.vision_analytics_service import VisionAnalyticsService
    # Vision functionality is integrated into TaskMCPController, not a separate EnhancedTaskMCPController
    print("✅ Vision enrichment imports successful")
    
    # Phase 6: Integration
    print("\nPhase 6: Integration...")
    from fastmcp.vision_orchestration.configuration.config_loader import get_vision_config, is_vision_enabled
    print("✅ Vision configuration imports successful")
    
    # Test configuration loading
    config = get_vision_config()
    assert config is not None
    assert is_vision_enabled() is True
    print("✅ Vision configuration loaded successfully")
    
    print("\n✅ All Vision System imports successful!")
    assert True  # Test completed successfully


def test_vision_objects():
    """Test that Vision System objects can be created."""
    print("\n\n=== Testing Vision System Object Creation ===\n")
    
    from fastmcp.task_management.domain.entities.context import TaskContext, ContextMetadata, ContextObjective
    from fastmcp.task_management.domain.value_objects.hints import WorkflowHint, HintType, HintPriority
    from fastmcp.task_management.domain.value_objects.progress import ProgressType, ProgressStatus
    from uuid import uuid4
    
    # Create a task context
    metadata = ContextMetadata(task_id=str(uuid4()))
    objective = ContextObjective(title="Test Task", description="Test Description")
    context = TaskContext(metadata=metadata, objective=objective)
    print(f"✅ Created TaskContext: {context.metadata.task_id}")
    
    # Create a workflow hint with metadata
    from fastmcp.task_management.domain.value_objects.hints import HintMetadata
    
    hint_metadata = HintMetadata(
        source="test_system",
        confidence=0.8,
        reasoning="Test reasoning"
    )
    
    hint = WorkflowHint.create(
        task_id=uuid4(),
        hint_type=HintType.NEXT_ACTION,
        priority=HintPriority.medium(),
        message="Test hint",
        suggested_action="Test action",
        metadata=hint_metadata
    )
    print(f"✅ Created WorkflowHint: {hint.id}")
    
    print("\n✅ All Vision System objects created successfully!")
    assert True  # Test completed successfully


def test_vision_domain_events():
    """Test that Vision System domain events work correctly."""
    print("\n\n=== Testing Vision System Domain Events ===\n")
    
    from fastmcp.task_management.domain.events.hint_events import HintGenerated
    from fastmcp.task_management.domain.events.progress_events import ProgressUpdated
    from fastmcp.task_management.domain.events.agent_events import AgentAssigned
    from fastmcp.task_management.domain.value_objects.hints import HintType, HintPriority
    from fastmcp.task_management.domain.value_objects.progress import ProgressType
    from uuid import uuid4
    
    # Create hint event
    hint_event = HintGenerated(
        hint_id=uuid4(),
        task_id=uuid4(),
        hint_type=HintType.NEXT_ACTION,
        priority=HintPriority.high(),
        message="Test hint",
        suggested_action="Test action",
        source_rule="test_rule",
        confidence=0.9
    )
    print(f"✅ Created HintGenerated event: {hint_event.event_type}")
    
    # Create progress event
    progress_event = ProgressUpdated(
        task_id=str(uuid4()),
        progress_type=ProgressType.IMPLEMENTATION,
        old_percentage=0.0,
        new_percentage=50.0,
        agent_id="test_agent"
    )
    print(f"✅ Created ProgressUpdated event")
    
    # Create agent event
    agent_event = AgentAssigned(
        agent_id="agent_1",
        task_id=str(uuid4()),
        role="developer",
        assigned_by="orchestrator"
    )
    print(f"✅ Created AgentAssigned event")
    
    print("\n✅ All Vision System domain events created successfully!")
    assert True  # Test completed successfully


if __name__ == "__main__":
    print("\n🧪 Running Vision System Import Tests\n")
    
    try:
        # Run all tests
        test_vision_imports()
        test_vision_objects()
        test_vision_domain_events()
        
        print("\n\n✅ All Vision System tests passed!")
        print("\nThe Vision System has been successfully integrated with Phase 6!")
        print("All imports, objects, and events are working correctly.")
        
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)