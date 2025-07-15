"""Simple Vision System Test

Tests Vision System components without database dependencies.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Disable database usage
os.environ["DHAFNCK_REPOSITORY_TYPE"] = "mock"
os.environ["DHAFNCK_ENABLE_VISION"] = "true"

print("Vision System Simple Test")
print("=" * 50)

# Test 1: Import Vision Components
print("\n1. Testing Vision component imports...")
try:
    from fastmcp.task_management.domain.value_objects.vision_objects import (
        VisionObjective, VisionAlignment, VisionMetric, VisionInsight,
        VisionHierarchyLevel, ContributionType
    )
    print("   ✓ Domain value objects imported")
    
    from fastmcp.task_management.infrastructure.repositories.sqlite.vision_repository import SQLiteVisionRepository
    print("   ✓ SQLite repository imported")
    
    from fastmcp.vision_orchestration.vision_enrichment_service import VisionEnrichmentService
    print("   ✓ Vision enrichment service imported")
    
    from fastmcp.task_management.application.services.vision_analytics_service import VisionAnalyticsService
    print("   ✓ Vision analytics service imported")
    
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Create Vision Objects
print("\n2. Testing Vision object creation...")
try:
    # Create a vision objective
    objective = VisionObjective(
        title="Improve Code Quality",
        description="Enhance codebase maintainability",
        level=VisionHierarchyLevel.PROJECT,
        priority=4,
        status="active"
    )
    print(f"   ✓ Created objective: {objective.title}")
    
    # Create a vision metric
    metric = VisionMetric(
        name="code_coverage",
        current_value=0.75,
        target_value=0.95,
        unit="percentage"
    )
    print(f"   ✓ Created metric: {metric.name} = {metric.current_value}")
    
except Exception as e:
    print(f"   ✗ Object creation failed: {e}")
    sys.exit(1)

# Test 3: SQLite Repository Operations
print("\n3. Testing SQLite repository...")
try:
    repo = SQLiteVisionRepository()
    
    # List default objectives
    objectives = repo.list_objectives()
    print(f"   ✓ Found {len(objectives)} default objectives")
    
    # Create new objective
    new_obj = VisionObjective(
        title="Test Objective",
        description="Testing repository",
        level=VisionHierarchyLevel.TEAM
    )
    created = repo.create_objective(new_obj)
    print(f"   ✓ Created objective: {created.id}")
    
    # Retrieve objective
    retrieved = repo.get_objective(created.id)
    print(f"   ✓ Retrieved objective: {retrieved.title}")
    
except Exception as e:
    print(f"   ✗ Repository test failed: {e}")
    sys.exit(1)

# Test 4: Vision Services
print("\n4. Testing Vision services...")
try:
    # Create services with mock repository
    enrichment_service = VisionEnrichmentService(
        task_repository=None,
        vision_repository=repo
    )
    print("   ✓ Vision enrichment service created")
    
    analytics_service = VisionAnalyticsService(
        task_repository=None,
        vision_repository=repo,
        enrichment_service=enrichment_service
    )
    print("   ✓ Vision analytics service created")
    
    # Test enrichment enabled check
    if enrichment_service.is_enrichment_enabled():
        print("   ✓ Vision enrichment is enabled")
    else:
        print("   ⚠ Vision enrichment is disabled")
    
except Exception as e:
    print(f"   ✗ Service test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Configuration Loading
print("\n5. Testing configuration...")
try:
    from fastmcp.vision_orchestration.configuration.config_loader import (
        get_vision_config, is_vision_enabled, is_phase_enabled
    )
    
    config = get_vision_config()
    print(f"   ✓ Configuration loaded")
    
    if is_vision_enabled():
        print("   ✓ Vision System enabled")
    
    phases = ["context_enforcement", "progress_tracking", "workflow_hints", 
              "agent_coordination", "vision_enrichment"]
    
    enabled_phases = [p for p in phases if is_phase_enabled(p)]
    print(f"   ✓ Enabled phases: {', '.join(enabled_phases)}")
    
except Exception as e:
    print(f"   ✗ Configuration test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ Vision System Simple Test PASSED")
print("=" * 50)