"""Test Vision Enrichment Service with Null Repository Fix"""

import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastmcp.vision_orchestration.vision_enrichment_service import VisionEnrichmentService


class TestVisionEnrichmentServiceNullRepositoryFix:
    """Test that VisionEnrichmentService handles null repositories gracefully."""
    
    def test_initialization_with_null_repositories(self, caplog):
        """Test that service initializes properly with null repositories."""
        with caplog.at_level(logging.INFO):
            service = VisionEnrichmentService(
                task_repository=None,
                vision_repository=None
            )
        
        # Verify service was created
        assert service is not None
        assert service.task_repository is None
        assert service.vision_repository is None
        
        # Check that appropriate log messages were recorded
        assert "operating in degraded mode" in caplog.text
        assert "some features unavailable" in caplog.text
    
    def test_vision_enrichment_disabled_no_error(self):
        """Test that when vision enrichment is disabled, no error occurs."""
        with patch('fastmcp.vision_orchestration.vision_enrichment_service.is_phase_enabled') as mock_enabled:
            mock_enabled.return_value = False
            
            # This should not raise an error even with null repository
            service = VisionEnrichmentService(
                task_repository=None,
                vision_repository=None
            )
            
            assert service is not None
            assert service._vision_cache == {}
            assert service._hierarchy_cache == {}
    
    @patch('fastmcp.vision_orchestration.vision_enrichment_service.is_phase_enabled')
    def test_load_hierarchy_with_null_repository_graceful_degradation(self, mock_enabled, caplog):
        """Test that _load_vision_hierarchy handles null repository gracefully."""
        mock_enabled.return_value = True
        
        with caplog.at_level(logging.INFO):
            service = VisionEnrichmentService(
                task_repository=None,
                vision_repository=None  # This is the key: null repository
            )
        
        # Verify no exception was raised
        assert service is not None
        
        # Verify appropriate warning was logged
        assert "Vision repository not available - skipping database load" in caplog.text
        
        # Verify service still has empty caches (graceful degradation)
        assert isinstance(service._vision_cache, dict)
        assert isinstance(service._hierarchy_cache, dict)
    
    def test_calculate_task_alignment_with_null_task_repository(self, caplog):
        """Test that calculate_task_alignment handles null task repository."""
        service = VisionEnrichmentService(
            task_repository=None,
            vision_repository=None
        )
        
        task_id = uuid4()
        
        with caplog.at_level(logging.WARNING):
            result = service.calculate_task_alignment(task_id)
        
        # Should return None gracefully
        assert result is None
        
        # Should log appropriate warning
        assert "Task repository not available" in caplog.text
    
    def test_enrich_task_with_disabled_enrichment(self):
        """Test that enrich_task works when enrichment is disabled."""
        # Create a mock task
        task = MagicMock()
        task.to_dict.return_value = {"id": "test-123", "title": "Test Task"}
        
        with patch('fastmcp.vision_orchestration.vision_enrichment_service.is_phase_enabled') as mock_enabled:
            mock_enabled.return_value = False
            
            service = VisionEnrichmentService(
                task_repository=None,
                vision_repository=None
            )
            
            result = service.enrich_task(task)
            
            # Should return task data without vision context
            assert result == {"id": "test-123", "title": "Test Task"}
            assert "vision_context" not in result
    
    def test_update_objective_metrics_with_null_repository(self, caplog):
        """Test that update_objective_metrics handles null repository gracefully."""
        service = VisionEnrichmentService(
            task_repository=None,
            vision_repository=None
        )
        
        # Add a mock objective to cache
        objective_id = uuid4()
        mock_objective = MagicMock()
        mock_objective.id = objective_id
        mock_objective.metrics = []
        service._vision_cache[objective_id] = mock_objective
        
        with caplog.at_level(logging.WARNING):
            result = service.update_objective_metrics(objective_id, {"test_metric": 1.0})
        
        # Should still return updated objective
        assert result is not None
        
        # Should log warning about repository unavailability
        assert "Vision repository not available - metrics updated only in cache" in caplog.text
    
    def test_is_enrichment_enabled_works_regardless_of_repository(self):
        """Test that enrichment status check works regardless of repository availability."""
        with patch('fastmcp.vision_orchestration.vision_enrichment_service.is_phase_enabled') as mock_enabled:
            mock_enabled.return_value = True
            
            service = VisionEnrichmentService(
                task_repository=None,
                vision_repository=None
            )
            
            assert service.is_enrichment_enabled() is True
            
            # Change the mock return value
            mock_enabled.return_value = False
            assert service.is_enrichment_enabled() is False
    
    @patch('fastmcp.vision_orchestration.vision_enrichment_service.is_phase_enabled')
    @patch('pathlib.Path.exists')
    def test_load_hierarchy_from_config_with_null_repository(self, mock_exists, mock_enabled):
        """Test that hierarchy can be loaded from config even with null repository."""
        mock_enabled.return_value = True
        mock_exists.return_value = True
        
        mock_config = {
            "objectives": [
                {
                    "id": str(uuid4()),
                    "title": "Test Objective",
                    "description": "Test Description",
                    "level": "project",
                    "metrics": []
                }
            ]
        }
        
        with patch('builtins.open', mock_open_json(mock_config)):
            service = VisionEnrichmentService(
                task_repository=None,
                vision_repository=None
            )
            
            # Should have loaded from config
            assert len(service._vision_cache) == 1
            assert "Test Objective" in [obj.title for obj in service._vision_cache.values()]


def mock_open_json(json_data):
    """Helper to mock open() for JSON data."""
    import json
    from unittest.mock import mock_open
    
    return mock_open(read_data=json.dumps(json_data))


if __name__ == "__main__":
    pytest.main([__file__])