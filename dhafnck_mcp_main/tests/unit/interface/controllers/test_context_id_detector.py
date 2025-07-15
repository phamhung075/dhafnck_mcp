#!/usr/bin/env python3
"""
Unit tests for ContextIDDetector

Tests the ID detection functionality that determines whether a given ID
is a project ID, git branch ID, or task ID.
"""

import pytest
from unittest.mock import Mock, patch
import sqlite3

from fastmcp.task_management.interface.controllers.context_id_detector import ContextIDDetector


class TestContextIDDetector:
    """Test cases for ContextIDDetector"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.execute.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            yield mock_conn, mock_cursor
    
    def test_detect_project_id(self, mock_db_connection):
        """Test detection of project ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock to return result for project query
        project_id = "ae88dd28-1905-444d-81d0-e338297239a4"
        mock_cursor.fetchone.side_effect = [
            (project_id,),  # First query (projects table) returns result
            None,           # Second query (project_task_trees) returns None
            None            # Third query (tasks) returns None
        ]
        
        # Test
        id_type, associated_project_id = ContextIDDetector.detect_id_type(project_id)
        
        # Assert
        assert id_type == "project"
        assert associated_project_id == project_id
        
        # Verify the correct query was executed
        mock_conn.execute.assert_any_call(
            'SELECT id FROM projects WHERE id = ?',
            (project_id,)
        )
    
    def test_detect_git_branch_id(self, mock_db_connection):
        """Test detection of git branch ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock
        git_branch_id = "529a5847-ceb7-4b06-9fc4-472865ec40d1"
        project_id = "ae88dd28-1905-444d-81d0-e338297239a4"
        
        mock_cursor.fetchone.side_effect = [
            None,                  # First query (projects) returns None
            (project_id,),        # Second query (project_task_trees) returns project_id
            None                  # Third query (tasks) returns None
        ]
        
        # Test
        id_type, associated_project_id = ContextIDDetector.detect_id_type(git_branch_id)
        
        # Assert
        assert id_type == "git_branch"
        assert associated_project_id == project_id
        
        # Verify the correct query was executed
        mock_conn.execute.assert_any_call(
            'SELECT project_id FROM project_task_trees WHERE id = ?',
            (git_branch_id,)
        )
    
    def test_detect_task_id(self, mock_db_connection):
        """Test detection of task ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock
        task_id = "d00a377e-535d-4518-9d2f-c952c9af8b2c"
        project_id = "ae88dd28-1905-444d-81d0-e338297239a4"
        
        mock_cursor.fetchone.side_effect = [
            None,                    # First query (projects) returns None
            None,                    # Second query (project_task_trees) returns None
            (task_id, project_id)    # Third query (tasks) returns task_id and project_id
        ]
        
        # Test
        id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
        
        # Assert
        assert id_type == "task"
        assert associated_project_id == project_id
    
    def test_detect_unknown_id(self, mock_db_connection):
        """Test detection of unknown ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock - all queries return None
        unknown_id = "00000000-0000-0000-0000-000000000000"
        mock_cursor.fetchone.return_value = None
        
        # Test
        id_type, associated_project_id = ContextIDDetector.detect_id_type(unknown_id)
        
        # Assert
        assert id_type == "unknown"
        assert associated_project_id is None
    
    def test_get_context_level_for_project_id(self, mock_db_connection):
        """Test getting context level for project ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock
        project_id = "ae88dd28-1905-444d-81d0-e338297239a4"
        mock_cursor.fetchone.side_effect = [(project_id,), None, None]
        
        # Test
        context_level = ContextIDDetector.get_context_level_for_id(project_id)
        
        # Assert
        assert context_level == "project"
    
    def test_get_context_level_for_git_branch_id(self, mock_db_connection):
        """Test getting context level for git branch ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock
        git_branch_id = "529a5847-ceb7-4b06-9fc4-472865ec40d1"
        project_id = "ae88dd28-1905-444d-81d0-e338297239a4"
        mock_cursor.fetchone.side_effect = [None, (project_id,), None]
        
        # Test
        context_level = ContextIDDetector.get_context_level_for_id(git_branch_id)
        
        # Assert
        assert context_level == "task"  # Git branches use task-level contexts
    
    def test_get_context_level_for_task_id(self, mock_db_connection):
        """Test getting context level for task ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock
        task_id = "d00a377e-535d-4518-9d2f-c952c9af8b2c"
        project_id = "ae88dd28-1905-444d-81d0-e338297239a4"
        mock_cursor.fetchone.side_effect = [None, None, (task_id, project_id)]
        
        # Test
        context_level = ContextIDDetector.get_context_level_for_id(task_id)
        
        # Assert
        assert context_level == "task"
    
    def test_get_context_level_for_unknown_id(self, mock_db_connection):
        """Test getting context level for unknown ID"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock
        unknown_id = "00000000-0000-0000-0000-000000000000"
        mock_cursor.fetchone.return_value = None
        
        # Test
        context_level = ContextIDDetector.get_context_level_for_id(unknown_id)
        
        # Assert
        assert context_level == "task"  # Defaults to task level
    
    def test_database_error_handling(self):
        """Test handling of database errors"""
        # Mock database connection to raise an exception
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Database connection failed")
            
            # Test
            id_type, associated_project_id = ContextIDDetector.detect_id_type("any-id")
            
            # Assert
            assert id_type == "unknown"
            assert associated_project_id is None
    
    @patch('fastmcp.task_management.infrastructure.database.database_source_manager.get_database_path')
    def test_uses_correct_database_path(self, mock_get_db_path, mock_db_connection):
        """Test that the detector uses the correct database path"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup mock
        expected_db_path = "/data/dhafnck_mcp.db"
        mock_get_db_path.return_value = expected_db_path
        mock_cursor.fetchone.return_value = None
        
        # Test
        ContextIDDetector.detect_id_type("test-id")
        
        # Assert
        mock_get_db_path.assert_called_once()


# Run with: python -m pytest tests/unit/interface/controllers/test_context_id_detector.py -v