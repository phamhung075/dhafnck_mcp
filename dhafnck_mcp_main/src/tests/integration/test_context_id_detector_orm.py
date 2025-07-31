#!/usr/bin/env python3
"""
Integration tests for ContextIDDetector with ORM database

Tests the ID detection functionality against the ORM database
to ensure it works correctly in production scenarios.
"""

import os
import sys
import pytest
from pathlib import Path
from datetime import datetime, timezone

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.interface.controllers.context_id_detector_orm import ContextIDDetector
from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import Project, ProjectGitBranch, Task


class TestContextIDDetectorORM:
    
    def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                session.execute(text("DELETE FROM tasks WHERE id LIKE 'test-%'"))
                session.execute(text("DELETE FROM projects WHERE id LIKE 'test-%' AND id != 'default_project'"))
                session.commit()
            except:
                session.rollback()

    """Integration tests for ContextIDDetector with ORM database"""
    
    @pytest.fixture
    def setup_test_data(self):
        """Create test data in the ORM database"""
        # Test IDs
        test_project_id = "test-project-123"
        test_branch_id = "test-branch-456"
        test_task_id = "test-task-789"
        
        # Create test data in database
        with get_session() as session:
            # Create project
            project = Project(
                id=test_project_id,
                name="Test Project",
                description="Integration test project",
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(project)
            
            # Create git branch (project task tree)
            branch = ProjectGitBranch(
                id=test_branch_id,
                project_id=test_project_id,
                name="test-branch",
                description="Integration test branch",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(branch)
            
            # Create task
            task = Task(
                id=test_task_id,
                title="Test Task",
                description="Integration test task",
                git_branch_id=test_branch_id,
                status="todo",
                priority="medium",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(task)
            
            session.commit()
        
        yield {
            "project_id": test_project_id,
            "branch_id": test_branch_id,
            "task_id": test_task_id
        }
        
        # Cleanup after test
        with get_session() as session:
            session.query(Task).filter_by(id=test_task_id).delete()
            session.query(ProjectGitBranch).filter_by(id=test_branch_id).delete()
            session.query(Project).filter_by(id=test_project_id).delete()
            session.commit()
    
    def test_detect_project_id_integration(self, setup_test_data):
        """Test detecting a project ID"""
        project_id = setup_test_data["project_id"]
        
        id_type, associated_project_id = ContextIDDetector.detect_id_type(project_id)
        
        assert id_type == "project"
        assert associated_project_id == project_id
    
    def test_detect_git_branch_id_integration(self, setup_test_data):
        """Test detecting a git branch ID"""
        branch_id = setup_test_data["branch_id"]
        project_id = setup_test_data["project_id"]
        
        id_type, associated_project_id = ContextIDDetector.detect_id_type(branch_id)
        
        assert id_type == "git_branch"
        assert associated_project_id == project_id
    
    def test_detect_task_id_integration(self, setup_test_data):
        """Test detecting a task ID"""
        task_id = setup_test_data["task_id"]
        project_id = setup_test_data["project_id"]
        
        id_type, associated_project_id = ContextIDDetector.detect_id_type(task_id)
        
        assert id_type == "task"
        assert associated_project_id == project_id
    
    def test_detect_unknown_id_integration(self):
        """Test detecting an unknown ID"""
        unknown_id = "unknown-id-000"
        
        id_type, associated_project_id = ContextIDDetector.detect_id_type(unknown_id)
        
        assert id_type == "unknown"
        assert associated_project_id is None
    
    def test_get_context_levels_integration(self, setup_test_data):
        """Test getting appropriate context levels for different ID types"""
        # Project ID should use project level
        project_id = setup_test_data["project_id"]
        level = ContextIDDetector.get_context_level_for_id(project_id)
        assert level == "project"
        
        # Git branch ID should use task level
        branch_id = setup_test_data["branch_id"]
        level = ContextIDDetector.get_context_level_for_id(branch_id)
        assert level == "task"
        
        # Task ID should use task level
        task_id = setup_test_data["task_id"]
        level = ContextIDDetector.get_context_level_for_id(task_id)
        assert level == "task"
        
        # Unknown ID should default to task level
        unknown_id = "unknown-id-000"
        level = ContextIDDetector.get_context_level_for_id(unknown_id)
        assert level == "task"
    
    def test_edge_cases(self, setup_test_data):
        """Test edge cases for ID detection"""
        # Test with None
        id_type, associated_project_id = ContextIDDetector.detect_id_type(None)
        assert id_type == "unknown"
        assert associated_project_id is None
        
        # Test with empty string
        id_type, associated_project_id = ContextIDDetector.detect_id_type("")
        assert id_type == "unknown"
        assert associated_project_id is None
        
        # Test with malformed ID
        id_type, associated_project_id = ContextIDDetector.detect_id_type("not-a-uuid")
        assert id_type == "unknown"
        assert associated_project_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])