#!/usr/bin/env python3
"""
Simple test for progress field mapping between domain entity and database model
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_progress_field_mapping_simple():
    """Test that overall_progress in entity maps correctly to progress_percentage in database"""
    
    # Import here to ensure database is initialized
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    from fastmcp.task_management.infrastructure.database.models import Task
    from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
    from sqlalchemy import text
    import uuid
    
    db_config = get_db_config()
    
    # Get the existing git branch from conftest setup
    with db_config.get_session() as session:
        result = session.execute(text(
            "SELECT id FROM project_git_branchs LIMIT 1"
        ))
        row = result.fetchone()
        if row:
            test_branch_id = row[0]
        else:
            pytest.skip("No git branch available for testing")
    
    # Create repository with the valid git_branch_id
    repo = ORMTaskRepository(git_branch_id=test_branch_id)
    
    # Test 1: Check that _model_to_entity maps progress_percentage to overall_progress
    task_id = str(uuid.uuid4())
    with db_config.get_session() as session:
        # Create a task directly in the database with progress_percentage
        session.execute(text("""
            INSERT INTO tasks (id, title, description, git_branch_id, status, priority, 
                              details, estimated_effort, progress_percentage, created_at, updated_at)
            VALUES (:id, :title, :description, :git_branch_id, :status, :priority,
                    :details, :estimated_effort, :progress_percentage, datetime('now'), datetime('now'))
        """), {
            'id': task_id,
            'title': 'Test Progress Mapping',
            'description': 'Testing progress field mapping',
            'git_branch_id': test_branch_id,
            'status': 'in_progress',
            'priority': 'medium',
            'details': '',
            'estimated_effort': '',
            'progress_percentage': 75
        })
        session.commit()
    
    # Check task was created
    with db_config.get_session() as session:
        result = session.execute(text(
            "SELECT id, git_branch_id, progress_percentage FROM tasks WHERE id = :id"
        ), {'id': task_id})
        row = result.fetchone()
        print(f"Task in DB: id={row[0] if row else None}, branch={row[1] if row else None}, progress={row[2] if row else None}")
        print(f"Repository branch: {test_branch_id}")
    
    # Retrieve using repository to test mapping
    entity = repo.get_task(task_id)
    assert entity is not None, "Task should be retrieved"
    assert hasattr(entity, 'overall_progress'), "Entity should have overall_progress field"
    assert entity.overall_progress == 75.0, f"Expected overall_progress to be 75.0, got {entity.overall_progress}"
    
    # Test 2: Check that update with overall_progress maps to progress_percentage
    updated_entity = repo.update_task(task_id, overall_progress=90.0)
    assert updated_entity.overall_progress == 90.0, "Progress should be updated to 90%"
    
    # Verify in database
    with db_config.get_session() as session:
        result = session.execute(text(
            "SELECT progress_percentage FROM tasks WHERE id = :id"
        ), {'id': task_id})
        row = result.fetchone()
        assert row[0] == 90, f"Database should have progress_percentage of 90, got {row[0]}"
    
    print("✅ Progress field mapping test passed!")


if __name__ == "__main__":
    test_progress_field_mapping_simple()