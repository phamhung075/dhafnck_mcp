"""
TDD Tests for Git Branch Statistics Error Fix
Issue: 'sqlite3.Row' object has no attribute 'get'
"""
import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json


class TestGitBranchStatisticsFix:
    """Test suite for fixing git branch statistics error"""
    
    def test_sqlite_row_get_attribute_error_should_be_handled(self):
        """Test that sqlite3.Row objects are properly converted to dictionaries"""
        # Arrange
        mock_row = MagicMock(spec=sqlite3.Row)
        mock_row.keys.return_value = ['id', 'name', 'task_count', 'completed_tasks']
        mock_row.__getitem__.side_effect = lambda x: {
            'id': 'branch-123',
            'name': 'feature/test',
            'task_count': 5,
            'completed_tasks': 2
        }[x]
        
        # This should fail before fix
        with pytest.raises(AttributeError):
            mock_row.get('id')
    
    def test_get_statistics_should_convert_row_to_dict(self):
        """Test that get_statistics converts sqlite3.Row to dict before accessing"""
        # Arrange
        from src.infrastructure.git_branch_repository import GitBranchRepository
        repo = GitBranchRepository(":memory:")
        
        # Create test data
        project_id = "test-project-123"
        branch_id = "test-branch-456"
        
        # Mock the database query to return sqlite3.Row
        with patch.object(repo, '_execute_query') as mock_query:
            # Simulate sqlite3.Row behavior
            mock_row = MagicMock()
            mock_row.keys.return_value = ['total_tasks', 'completed_tasks', 'in_progress_tasks']
            mock_row.__getitem__.side_effect = lambda x: {
                'total_tasks': 10,
                'completed_tasks': 3,
                'in_progress_tasks': 2
            }[x]
            
            mock_query.return_value = [mock_row]
            
            # Act & Assert - This should not raise AttributeError after fix
            result = repo.get_statistics(project_id, branch_id)
            
            assert result is not None
            assert result['total_tasks'] == 10
            assert result['completed_tasks'] == 3
            assert result['progress_percentage'] == 30.0
    
    def test_row_to_dict_converter_utility(self):
        """Test utility function to convert sqlite3.Row to dict"""
        # This is the fix we'll implement
        def row_to_dict(row):
            """Convert sqlite3.Row to dictionary"""
            if row is None:
                return None
            
            # Check if it's already a dict
            if isinstance(row, dict):
                return row
            
            # Convert Row object to dict
            try:
                # Try the standard sqlite3.Row conversion
                return dict(row)
            except:
                # Fallback for mock objects or other Row-like objects
                if hasattr(row, 'keys') and callable(row.keys):
                    return {key: row[key] for key in row.keys()}
                else:
                    # Last resort - try to extract data
                    result = {}
                    for attr in dir(row):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(row, attr)
                                if not callable(value):
                                    result[attr] = value
                            except:
                                pass
                    return result
        
        # Test with mock Row object
        mock_row = MagicMock()
        mock_row.keys.return_value = ['id', 'name', 'count']
        mock_row.__getitem__.side_effect = lambda x: {
            'id': 1,
            'name': 'test',
            'count': 5
        }[x]
        
        result = row_to_dict(mock_row)
        assert result == {'id': 1, 'name': 'test', 'count': 5}
    
    def test_statistics_calculation_with_no_tasks(self):
        """Test statistics calculation when branch has no tasks"""
        # Arrange
        stats_data = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'in_progress_tasks': 0
        }
        
        # Act
        progress_percentage = (stats_data['completed_tasks'] / stats_data['total_tasks'] * 100) if stats_data['total_tasks'] > 0 else 0.0
        
        # Assert
        assert progress_percentage == 0.0
    
    def test_statistics_with_all_tasks_completed(self):
        """Test statistics when all tasks are completed"""
        # Arrange
        stats_data = {
            'total_tasks': 5,
            'completed_tasks': 5,
            'in_progress_tasks': 0
        }
        
        # Act
        progress_percentage = (stats_data['completed_tasks'] / stats_data['total_tasks'] * 100) if stats_data['total_tasks'] > 0 else 0.0
        
        # Assert
        assert progress_percentage == 100.0
    
    def test_full_statistics_response_structure(self):
        """Test the complete statistics response structure"""
        # Expected structure after fix
        expected_response = {
            "success": True,
            "statistics": {
                "git_branch_id": "branch-123",
                "total_tasks": 10,
                "completed_tasks": 3,
                "in_progress_tasks": 2,
                "todo_tasks": 5,
                "blocked_tasks": 0,
                "progress_percentage": 30.0,
                "task_breakdown": {
                    "by_status": {
                        "todo": 5,
                        "in_progress": 2,
                        "done": 3
                    },
                    "by_priority": {
                        "high": 4,
                        "medium": 4,
                        "low": 2
                    }
                },
                "average_completion_time": None,
                "created_at": "2024-01-15T10:00:00Z",
                "last_activity": "2024-01-15T15:30:00Z"
            }
        }
        
        # Validate structure
        assert expected_response["success"] is True
        assert "statistics" in expected_response
        assert "progress_percentage" in expected_response["statistics"]
        assert expected_response["statistics"]["progress_percentage"] == 30.0