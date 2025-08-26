#!/usr/bin/env python3
"""
Debug script for vision enrichment service tests.
"""
import json
import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from dhafnck_mcp_main.src.fastmcp.vision_orchestration.vision_enrichment_service import VisionEnrichmentService

class MockTask:
    def __init__(self, title="Test", description="Test desc", status="todo", priority=3, labels=None, dependencies=None):
        self.id = uuid4()
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.labels = labels or []
        self.dependencies = dependencies or []
    
    def priority_score(self):
        return self.priority / 5.0
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "labels": self.labels
        }

def main():
    print("🔍 Debugging Vision Enrichment Service")
    
    # Create sample config (matching test configuration)
    config = {
        "objectives": [
            {
                "id": str(uuid4()),
                "title": "Improve User Experience", 
                "description": "Enhance overall user experience",
                "level": "organization",
                "priority": 5,
                "status": "active",
                "owner": "Product Team",
                "tags": ["user", "experience", "improvement"],
                "metrics": [
                    {
                        "name": "User Satisfaction Score",
                        "current_value": 7.5,
                        "target_value": 9.0,
                        "unit": "score",
                        "type": "custom",
                        "baseline_value": 6.0
                    }
                ],
                "children": [
                    {
                        "id": str(uuid4()),
                        "title": "Reduce Page Load Time",
                        "description": "Improve website performance",
                        "level": "project",
                        "priority": 4,
                        "status": "active",
                        "owner": "Engineering",
                        "tags": ["performance", "web"],
                        "metrics": [
                            {
                                "name": "Average Load Time",
                                "current_value": 3.2,
                                "target_value": 2.0,
                                "unit": "seconds",
                                "type": "time"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(config, f)
        config_path = Path(f.name)
    
    try:
        # Test with patches
        with patch('fastmcp.vision_orchestration.vision_enrichment_service.get_vision_config') as mock_config:
            with patch('fastmcp.vision_orchestration.vision_enrichment_service.is_phase_enabled', return_value=True):
                mock_config.return_value = {"vision_system": {"vision_enrichment": {}}}
                
                print(f"📁 Config path: {config_path}")
                print(f"📄 Config exists: {config_path.exists()}")
                
                service = VisionEnrichmentService(config_path=config_path)
                
                print(f"🧠 Vision cache size: {len(service._vision_cache)}")
                print(f"🏗️ Hierarchy cache size: {len(service._hierarchy_cache)}")
                
                for obj_id, obj in service._vision_cache.items():
                    print(f"  - {obj_id}: {obj.title} (level: {obj.level}, status: {obj.status})")
                
                # Test alignment (matching failing test)
                task = MockTask(
                    title="Improve Page Performance",
                    description="Reduce load time for better user experience", 
                    status="in_progress",
                    priority=4,
                    labels=["performance", "user", "web"]
                )
                
                print(f"🎯 Task: {task.title}")
                print(f"📝 Description: {task.description}")
                print(f"🏷️ Labels: {task.labels}")
                
                alignments = service._calculate_alignments(task)
                print(f"⚡ Alignments found: {len(alignments)}")
                
                for alignment in alignments:
                    print(f"  - Score: {alignment.alignment_score:.3f}, Type: {alignment.contribution_type}")
                    print(f"    Rationale: {alignment.rationale}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        config_path.unlink()

if __name__ == "__main__":
    main()