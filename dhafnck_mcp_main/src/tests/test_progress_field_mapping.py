#!/usr/bin/env python3
"""
Test for progress field mapping between domain entity and database model
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.database.database_config import get_db_config
from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
from datetime import datetime, timezone
import uuid
from sqlalchemy import text


@pytest.mark.database
def test_progress_field_mapping():
    """Test that overall_progress in entity maps correctly to progress_percentage in database"""
    
    # Use the existing test infrastructure that's already set up by conftest.py
    db_config = get_db_config()
    
    # Find an existing git branch from the test setup using raw SQL to avoid UUID issues
    with db_config.get_session() as session:
        # Use raw SQL to avoid UUID processing issues
        result = session.execute(text(
            "SELECT id FROM project_git_branchs WHERE project_id = 'default_project' LIMIT 1"
        ))
        row = result.fetchone()
        
        if row:
            test_branch_id = row[0]
        else:
            # Create one if needed
            test_branch_id = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO project_git_branchs (id, project_id, name, description, created_at, updated_at, priority, status, metadata, task_count, completed_task_count)
                VALUES (:id, :project_id, :name, :description, :created_at, :updated_at, :priority, :status, :metadata, :task_count, :completed_task_count)
            """), {
                'id': test_branch_id,
                'project_id': 'default_project',
                'name': 'test-progress-branch',
                'description': 'Branch for progress field testing',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'priority': 'medium',
                'status': 'todo',
                'metadata': '{}',
                'task_count': 0,
                'completed_task_count': 0
            })
            session.commit()
    
    # Create repository with the valid git_branch_id
    repo = ORMTaskRepository(git_branch_id=test_branch_id)
    
    # Create a task
    task = repo.create_task(
        title="Test Progress Task",
        description="Testing progress field mapping",
        priority="medium"
    )
    
    assert task is not None
    assert hasattr(task, 'overall_progress'), "Entity should have overall_progress field"
    assert task.overall_progress == 0, "Initial progress should be 0"
    
    # Update progress using overall_progress
    updated_task = repo.update_task(
        str(task.id),
        overall_progress=75
    )
    
    assert updated_task.overall_progress == 75, "Progress should be updated to 75%"
    
    # Retrieve task to verify persistence
    retrieved_task = repo.get_task(str(task.id))
    assert retrieved_task is not None
    assert retrieved_task.overall_progress == 75, "Retrieved task should have correct progress"
    
    # Save task entity with progress
    task.overall_progress = 90
    success = repo.save(task)
    assert success, "Save should succeed"
    
    # Retrieve again to verify save worked
    final_task = repo.get_task(str(task.id))
    assert final_task.overall_progress == 90, "Saved progress should be persisted"
    
    print("✅ Progress field mapping test passed!")


if __name__ == "__main__":
    test_progress_field_mapping()