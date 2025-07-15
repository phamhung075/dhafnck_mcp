#!/usr/bin/env python3
"""
Integration tests for ContextIDDetector with real database

Tests the ID detection functionality against an actual database
to ensure it works correctly in production scenarios.
"""

import os
import sys
import pytest
import tempfile
import sqlite3
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.interface.controllers.context_id_detector import ContextIDDetector
from fastmcp.task_management.infrastructure.database.database_source_manager import DatabaseSourceManager


class TestContextIDDetectorIntegration:
    """Integration tests for ContextIDDetector with real database"""
    
    @pytest.fixture
    def test_db(self):
        """Create a temporary test database with sample data"""
        # Create temporary database
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Set the database path for the test
        os.environ['MCP_DB_PATH'] = db_path
        
        # Create tables and insert test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Create project_task_trees table (git branches)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_task_trees (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # Create tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                git_branch_id TEXT NOT NULL,
                status TEXT,
                priority TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (git_branch_id) REFERENCES project_task_trees(id)
            )
        ''')
        
        # Insert test data
        test_project_id = "test-project-123"
        test_branch_id = "test-branch-456"
        test_task_id = "test-task-789"
        
        cursor.execute(
            "INSERT INTO projects (id, name, description) VALUES (?, ?, ?)",
            (test_project_id, "Test Project", "Integration test project")
        )
        
        cursor.execute(
            "INSERT INTO project_task_trees (id, project_id, name, description) VALUES (?, ?, ?, ?)",
            (test_branch_id, test_project_id, "test-branch", "Integration test branch")
        )
        
        cursor.execute(
            "INSERT INTO tasks (id, title, description, git_branch_id, status, priority) VALUES (?, ?, ?, ?, ?, ?)",
            (test_task_id, "Test Task", "Integration test task", test_branch_id, "todo", "medium")
        )
        
        conn.commit()
        conn.close()
        
        yield {
            "db_path": db_path,
            "project_id": test_project_id,
            "branch_id": test_branch_id,
            "task_id": test_task_id
        }
        
        # Cleanup
        os.unlink(db_path)
        if 'MCP_DB_PATH' in os.environ:
            del os.environ['MCP_DB_PATH']
    
    def test_detect_project_id_integration(self, test_db):
        """Test detection of project ID with real database"""
        id_type, associated_project_id = ContextIDDetector.detect_id_type(test_db["project_id"])
        
        assert id_type == "project"
        assert associated_project_id == test_db["project_id"]
    
    def test_detect_git_branch_id_integration(self, test_db):
        """Test detection of git branch ID with real database"""
        id_type, associated_project_id = ContextIDDetector.detect_id_type(test_db["branch_id"])
        
        assert id_type == "git_branch"
        assert associated_project_id == test_db["project_id"]
    
    def test_detect_task_id_integration(self, test_db):
        """Test detection of task ID with real database"""
        id_type, associated_project_id = ContextIDDetector.detect_id_type(test_db["task_id"])
        
        assert id_type == "task"
        assert associated_project_id == test_db["project_id"]
    
    def test_detect_nonexistent_id_integration(self, test_db):
        """Test detection of non-existent ID with real database"""
        id_type, associated_project_id = ContextIDDetector.detect_id_type("nonexistent-id-999")
        
        assert id_type == "unknown"
        assert associated_project_id is None
    
    def test_get_context_levels_integration(self, test_db):
        """Test getting context levels with real database"""
        # Test project level
        project_level = ContextIDDetector.get_context_level_for_id(test_db["project_id"])
        assert project_level == "project"
        
        # Test git branch level (should be task)
        branch_level = ContextIDDetector.get_context_level_for_id(test_db["branch_id"])
        assert branch_level == "task"
        
        # Test task level
        task_level = ContextIDDetector.get_context_level_for_id(test_db["task_id"])
        assert task_level == "task"
        
        # Test unknown ID (defaults to task)
        unknown_level = ContextIDDetector.get_context_level_for_id("unknown-id")
        assert unknown_level == "task"


# Run with: python -m pytest tests/integration/test_context_id_detector_integration.py -v