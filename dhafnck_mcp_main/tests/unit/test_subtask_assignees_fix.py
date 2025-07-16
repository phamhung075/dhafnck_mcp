#!/usr/bin/env python3

"""
Test for Subtask Assignees Fix

This test verifies that the fix for the "'str' object has no attribute 'copy'" error
when assigning agents to subtasks is working correctly.

Issue: When updating subtask assignees, the task entity received assignees as a JSON string
instead of a list, causing the error when trying to copy the subtask dictionary.

Fix: Updated the _load_task_relations method in SQLiteTaskRepository to properly parse
JSON assignees strings into lists.
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects import TaskId, TaskStatus, Priority
from fastmcp.task_management.infrastructure.repositories.sqlite.task_repository import SQLiteTaskRepository


class TestSubtaskAssigneesFix:
    """Test class for subtask assignees fix"""

    def test_parse_json_assignees_valid_json(self):
        """Test _parse_json_assignees with valid JSON"""
        repo = SQLiteTaskRepository()
        
        # Test empty list
        result = repo._parse_json_assignees('[]')
        assert result == []
        
        # Test list with agents
        result = repo._parse_json_assignees('["@coding_agent", "@test_agent"]')
        assert result == ["@coding_agent", "@test_agent"]
        
        # Test empty string
        result = repo._parse_json_assignees('')
        assert result == []
        
        # Test None
        result = repo._parse_json_assignees(None)
        assert result == []
    
    def test_parse_json_assignees_invalid_json(self):
        """Test _parse_json_assignees with invalid JSON"""
        repo = SQLiteTaskRepository()
        
        # Test invalid JSON (should return empty list and log warning)
        result = repo._parse_json_assignees('[invalid json')
        assert result == []
        
        # Test non-list JSON
        result = repo._parse_json_assignees('"not a list"')
        assert result == []
        
        # Test object instead of list
        result = repo._parse_json_assignees('{"key": "value"}')
        assert result == []

    @patch('fastmcp.task_management.infrastructure.repositories.sqlite.task_repository.SQLiteTaskRepository._get_connection')
    def test_load_task_relations_assignees_parsing(self, mock_get_connection):
        """Test that _load_task_relations properly parses JSON assignees"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock database rows for subtasks
        mock_subtask_row = {
            'id': 'subtask-123',
            'title': 'Test Subtask',
            'description': 'Test description',
            'status': 'todo',
            'priority': 'medium',
            'assignees': '["@coding_agent", "@test_agent"]',  # JSON string
            'estimated_effort': '2 hours'
        }
        
        # Mock the execute method to return different data for different queries
        def mock_execute(query, params=()):
            mock_result = MagicMock()
            if 'task_assignees' in query:
                mock_result.fetchall.return_value = []  # Empty assignees
            elif 'task_labels' in query:
                mock_result.fetchall.return_value = []  # Empty labels
            elif 'task_dependencies' in query:
                mock_result.fetchall.return_value = []  # Empty dependencies
            elif 'task_subtasks' in query:
                mock_result.fetchall.return_value = [mock_subtask_row]  # Our test subtask
            else:
                mock_result.fetchall.return_value = []
            return mock_result
        
        mock_conn.execute.side_effect = mock_execute
        
        # Test the method
        repo = SQLiteTaskRepository()
        relations = repo._load_task_relations('task-123')
        
        # Verify assignees are parsed correctly
        assert len(relations['subtasks']) == 1
        subtask = relations['subtasks'][0]
        assert subtask['assignees'] == ["@coding_agent", "@test_agent"]
        assert isinstance(subtask['assignees'], list)
        assert not isinstance(subtask['assignees'], str)

    def test_task_update_subtask_with_list_assignees(self):
        """Test that Task.update_subtask works with properly parsed assignees"""
        from datetime import datetime, timezone
        
        # Create a task with a subtask that has list assignees (not string)
        task = Task(
            id=TaskId('12345678-1234-1234-1234-123456789012'),
            title='Test Task',
            description='Test description',
            git_branch_id='87654321-4321-4321-4321-210987654321',
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            subtasks=[
                {
                    'id': 'subtask-123',
                    'title': 'Test Subtask',
                    'description': 'Test description',
                    'status': 'todo',
                    'priority': 'medium',
                    'assignees': [],  # This should be a list, not a string
                    'estimated_effort': '2 hours',
                    'completed': False
                }
            ]
        )
        
        # Test updating the subtask assignees
        updates = {'assignees': ['@coding_agent', '@test_agent']}
        success = task.update_subtask('subtask-123', updates)
        
        # Verify the update worked
        assert success == True
        
        # Verify the assignees are updated correctly
        updated_subtask = task.get_subtask('subtask-123')
        assert updated_subtask is not None
        assert updated_subtask['assignees'] == ['@coding_agent', '@test_agent']
        assert isinstance(updated_subtask['assignees'], list)

    def test_task_update_subtask_handles_string_assignees_gracefully(self):
        """Test that Task.update_subtask handles string assignees gracefully after the fix"""
        from datetime import datetime, timezone
        
        # Create a task with a subtask that has string assignees (this was the bug)
        task = Task(
            id=TaskId('12345678-1234-1234-1234-123456789012'),
            title='Test Task',
            description='Test description',
            git_branch_id='87654321-4321-4321-4321-210987654321',
            status=TaskStatus.todo(),
            priority=Priority.medium(),
            subtasks=[
                {
                    'id': 'subtask-123',
                    'title': 'Test Subtask',
                    'description': 'Test description',
                    'status': 'todo',
                    'priority': 'medium',
                    'assignees': '[]',  # This is a string, not a list (the bug)
                    'estimated_effort': '2 hours',
                    'completed': False
                }
            ]
        )
        
        # Test updating the subtask assignees should work now (after the fix)
        updates = {'assignees': ['@coding_agent', '@test_agent']}
        
        # This should work because the task entity now handles string assignees
        # The backend repository fix ensures assignees come as lists, not strings
        try:
            success = task.update_subtask('subtask-123', updates)
            # If we get here without an error, the fix worked
            assert success == True
        except AttributeError as e:
            if "'str' object has no attribute 'copy'" in str(e):
                pytest.fail("The fix didn't work - still getting string assignees error")
            else:
                raise  # Re-raise if it's a different error

    def test_database_json_consistency(self):
        """Test that the database save/load cycle maintains JSON consistency"""
        repo = SQLiteTaskRepository()
        
        # Test data with different assignee scenarios
        test_cases = [
            [],  # Empty list
            ['@coding_agent'],  # Single agent
            ['@coding_agent', '@test_agent'],  # Multiple agents
            ['@coding_agent', '@test_agent', '@ui_designer_agent'],  # Many agents
        ]
        
        for assignees in test_cases:
            # Test JSON dumps (save)
            json_str = json.dumps(assignees)
            
            # Test JSON loads (load)
            parsed_assignees = repo._parse_json_assignees(json_str)
            
            # Verify consistency
            assert parsed_assignees == assignees
            assert isinstance(parsed_assignees, list)
            assert all(isinstance(agent, str) for agent in parsed_assignees)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])