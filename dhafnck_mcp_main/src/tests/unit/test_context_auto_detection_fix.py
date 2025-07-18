"""Unit Tests for Enhanced Context Auto-Detection Logic

Test scenarios for the improved auto-detection functionality that addresses
Issue #3: Context Management Auto-Detection improvements.

Test Categories:
1. Valid task ID with successful auto-detection
2. Invalid task ID format handling
3. Non-existent task ID handling  
4. Task exists but no git_branch_id
5. Database connection failure simulation
6. Task system unavailable simulation
7. Enhanced error response validation
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from fastmcp.task_management.interface.controllers.context_auto_detection_fix import (
    ContextAutoDetectionEnhanced,
    AutoDetectionErrorType
)


class TestContextAutoDetectionEnhanced:
    """Test suite for enhanced context auto-detection functionality"""
    
    def test_valid_task_id_successful_detection(self):
        """Test successful auto-detection with valid task ID and branch"""
        # Arrange
        task_id = str(uuid.uuid4())
        expected_branch_id = str(uuid.uuid4())
        
        mock_task = Mock()
        mock_task.git_branch_id = expected_branch_id
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_session') as mock_get_session:
            mock_session = Mock()
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            # Act
            branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(task_id)
            
            # Assert
            assert branch_id == expected_branch_id
            assert error is None
            mock_session.query.assert_called_once()
    
    def test_empty_task_id_handling(self):
        """Test handling of empty or None task_id"""
        # Act
        branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task("")
        
        # Assert
        assert branch_id is None
        assert error is not None
        assert error["error_type"] == AutoDetectionErrorType.INVALID_TASK_ID_FORMAT.value
        assert "Empty task_id provided" in error["message"]
    
    def test_invalid_task_id_format_handling(self):
        """Test handling of invalid UUID format"""
        # Arrange
        invalid_task_id = "invalid-uuid-format"
        
        # Act
        branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(invalid_task_id)
        
        # Assert
        assert branch_id is None
        assert error is not None
        assert error["error_type"] == AutoDetectionErrorType.INVALID_TASK_ID_FORMAT.value
        assert "Invalid task_id format" in error["message"]
        assert "suggestion" in error
    
    def test_task_not_found_handling(self):
        """Test handling when task ID doesn't exist in database"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_session') as mock_get_session:
            mock_session = Mock()
            mock_session.query.return_value.filter_by.return_value.first.return_value = None
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            # Act
            branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(task_id)
            
            # Assert
            assert branch_id is None
            assert error is not None
            assert error["error_type"] == AutoDetectionErrorType.TASK_NOT_FOUND.value
            assert "not found in database" in error["message"]
            assert "fallback_options" in error
            assert len(error["fallback_options"]) > 0
    
    def test_task_no_branch_id_handling(self):
        """Test handling when task exists but has no git_branch_id"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        mock_task = Mock()
        mock_task.git_branch_id = None
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_session') as mock_get_session:
            mock_session = Mock()
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            # Act
            branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(task_id)
            
            # Assert
            assert branch_id is None
            assert error is not None
            assert error["error_type"] == AutoDetectionErrorType.TASK_NO_BRANCH.value
            assert "no associated git_branch_id" in error["message"]
            assert "fallback_options" in error
    
    def test_import_error_handling(self):
        """Test handling when task management system components are unavailable"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_session', side_effect=ImportError("Module not found")):
            # Act
            branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(task_id)
            
            # Assert
            assert branch_id is None
            assert error is not None
            assert error["error_type"] == AutoDetectionErrorType.TASK_SYSTEM_UNAVAILABLE.value
            assert "Task management system components are not available" in error["message"]
            assert "fallback_options" in error
    
    def test_database_connection_error_handling(self):
        """Test handling of database connection errors"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("SQLite connection failed")
            
            # Act
            branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(task_id)
            
            # Assert
            assert branch_id is None
            assert error is not None
            assert error["error_type"] == AutoDetectionErrorType.DATABASE_CONNECTION_FAILED.value
            assert "Failed to connect to database" in error["message"]
            assert "Database error" in error["diagnostic"]
    
    def test_unknown_error_handling(self):
        """Test handling of unexpected errors"""
        # Arrange
        task_id = str(uuid.uuid4())
        
        with patch('fastmcp.task_management.infrastructure.database.database_config.get_session') as mock_get_session:
            mock_get_session.side_effect = ValueError("Unexpected error")
            
            # Act
            branch_id, error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(task_id)
            
            # Assert
            assert branch_id is None
            assert error is not None
            assert error["error_type"] == AutoDetectionErrorType.UNKNOWN_ERROR.value
            assert "Unexpected error" in error["message"]
    
    def test_uuid_format_validation(self):
        """Test UUID format validation logic"""
        # Test valid UUIDs
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            str(uuid.uuid4()),
            "00000000-0000-0000-0000-000000000000"
        ]
        
        for valid_uuid in valid_uuids:
            assert ContextAutoDetectionEnhanced._is_valid_uuid_format(valid_uuid) is True
        
        # Test invalid formats
        invalid_formats = [
            "invalid-uuid",
            "123-456-789",
            "123e4567-e89b-12d3-a456",  # Too short
            "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
            "",
            None
        ]
        
        for invalid_format in invalid_formats:
            if invalid_format is not None:
                assert ContextAutoDetectionEnhanced._is_valid_uuid_format(invalid_format) is False


class TestEnhancedErrorResponse:
    """Test suite for enhanced error response generation"""
    
    def test_task_system_unavailable_error_response(self):
        """Test error response for task system unavailable"""
        # Arrange
        action = "create"
        error_details = {
            "error_type": AutoDetectionErrorType.TASK_SYSTEM_UNAVAILABLE.value,
            "message": "Task management system components are not available",
            "diagnostic": "Import error: Module not found",
            "fallback_options": ["Provide git_branch_id directly"]
        }
        
        # Act
        response = ContextAutoDetectionEnhanced.create_enhanced_error_response(action, error_details)
        
        # Assert
        assert response["success"] is False
        assert response["error_code"] == "AUTO_DETECTION_FAILED"
        assert "immediate_solutions" in response
        assert "manage_hierarchical_context" in response["hint"]
        assert len(response["immediate_solutions"]) >= 2
    
    def test_task_not_found_error_response(self):
        """Test error response for task not found"""
        # Arrange
        action = "update"
        error_details = {
            "error_type": AutoDetectionErrorType.TASK_NOT_FOUND.value,
            "message": "Task not found",
            "fallback_options": ["Create task first"]
        }
        
        # Act
        response = ContextAutoDetectionEnhanced.create_enhanced_error_response(action, error_details)
        
        # Assert
        assert response["success"] is False
        assert "Create the task first" in response["hint"]
        assert "immediate_solutions" in response
        assert "manage_task action='create'" in str(response["immediate_solutions"])
    
    def test_task_no_branch_error_response(self):
        """Test error response for task with no branch"""
        # Arrange
        action = "get"
        error_details = {
            "error_type": AutoDetectionErrorType.TASK_NO_BRANCH.value,
            "message": "Task has no branch",
            "fallback_options": ["Update task with branch"]
        }
        
        # Act
        response = ContextAutoDetectionEnhanced.create_enhanced_error_response(action, error_details)
        
        # Assert
        assert response["success"] is False
        assert "not linked to a git branch" in response["hint"]
        assert "manage_task action='update'" in str(response["immediate_solutions"])
    
    def test_fallback_options_inclusion(self):
        """Test that fallback options are properly included in response"""
        # Arrange
        action = "create"
        fallback_options = [
            "Option 1: Direct parameter",
            "Option 2: Alternative tool", 
            "Option 3: System check"
        ]
        error_details = {
            "error_type": AutoDetectionErrorType.UNKNOWN_ERROR.value,
            "message": "Unknown error",
            "fallback_options": fallback_options
        }
        
        # Act
        response = ContextAutoDetectionEnhanced.create_enhanced_error_response(action, error_details)
        
        # Assert
        assert "fallback_options" in response
        assert response["fallback_options"] == fallback_options
        assert len(response["fallback_options"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])