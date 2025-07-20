#!/usr/bin/env python3
"""
Fix unified context integration test failures for PostgreSQL.

The tests are failing due to duplicate key violations when creating test data.
This script ensures unique IDs are used and proper cleanup is performed.
"""

import os
import re
from pathlib import Path


def fix_hardcoded_ids(content: str) -> str:
    """Replace hardcoded IDs with unique UUID-based IDs."""
    
    # First, we need to fix the structure to use consistent variable names
    # Replace task tree IDs with unique values but keep variable references
    replacements = [
        # First pass: Generate unique IDs for entities
        ('id="proj-123"', 'id=str(uuid.uuid4())'),
        ('id="proj-update-123"', 'id=str(uuid.uuid4())'),
        ('id="proj-delegate-123"', 'id=str(uuid.uuid4())'),
        ('id="proj-insights-123"', 'id=str(uuid.uuid4())'),
        ('id="legacy-proj-999"', 'id=str(uuid.uuid4())'),
        
        ('id="branch-456"', 'id=str(uuid.uuid4())'),
        ('id="branch-update-456"', 'id=str(uuid.uuid4())'),
        ('id="branch-delegate-456"', 'id=str(uuid.uuid4())'),
        ('id="branch-insights-456"', 'id=str(uuid.uuid4())'),
        
        ('id="task-789"', 'id=str(uuid.uuid4())'),
        ('id="task-123"', 'id=str(uuid.uuid4())'),
        
        # Second pass: Fix references to use variable names
        ('context_id="proj-123"', 'context_id=project.id'),
        ('context_id="proj-update-123"', 'context_id=project.id'),
        ('context_id="proj-delegate-123"', 'context_id=project.id'),
        ('context_id="proj-insights-123"', 'context_id=project.id'),
        ('context_id="legacy-proj-999"', 'context_id=project.id'),
        
        ('context_id="branch-456"', 'context_id=git_branch.id'),
        ('context_id="branch-update-456"', 'context_id=git_branch.id'),
        ('context_id="branch-delegate-456"', 'context_id=git_branch.id'),
        ('context_id="branch-insights-456"', 'context_id=git_branch.id'),
        
        ('context_id="task-789"', 'context_id=task.id'),
        ('context_id="task-123"', 'context_id=task.id'),
        
        # Fix project_id references in git_branch creations
        ('project_id=str(uuid.uuid4()),', 'project_id=project.id,'),
        
        # Fix git_branch_id references in task creations
        ('git_branch_id=str(uuid.uuid4()),', 'git_branch_id=git_branch.id,'),
        
        # Fix parent references in data
        ('"project_id": "proj-123"', '"project_id": project.id'),
        ('"project_id": "proj-update-123"', '"project_id": project.id'),
        ('"project_id": "proj-delegate-123"', '"project_id": project.id'),
        ('"project_id": "proj-insights-123"', '"project_id": project.id'),
        
        ('"parent_branch_id": "branch-456"', '"parent_branch_id": git_branch.id'),
        ('"parent_branch_id": "branch-update-456"', '"parent_branch_id": git_branch.id'),
        ('"parent_branch_id": "branch-delegate-456"', '"parent_branch_id": git_branch.id'),
        ('"parent_branch_id": "branch-insights-456"', '"parent_branch_id": git_branch.id'),
        
        ('"branch_id": "branch-update-456"', '"branch_id": git_branch.id'),
        
        # Fix specific broken test line 166
        ('session.get(BranchContextModel, "branch-456")', 'session.get(BranchContextModel, git_branch.id)'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    return content


def add_better_cleanup(content: str) -> str:
    """Enhance the cleanup method to handle more edge cases."""
    
    # Find the setup_method and enhance it
    setup_pattern = r'(def setup_method\(self, method\):[\s\S]*?session\.rollback\(\))'
    
    new_setup = '''def setup_method(self, method):
        """Clean up before each test"""
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from sqlalchemy import text
        
        db_config = get_db_config()
        with db_config.get_session() as session:
            # Clean test data but preserve defaults
            try:
                # Clean up in reverse order of foreign key dependencies
                session.execute(text("DELETE FROM task_contexts"))
                session.execute(text("DELETE FROM tasks"))
                session.execute(text("DELETE FROM branch_contexts"))
                session.execute(text("DELETE FROM project_git_branchs WHERE project_id != 'default_project'"))
                session.execute(text("DELETE FROM project_contexts WHERE project_id != 'default_project'"))
                session.execute(text("DELETE FROM projects WHERE id != 'default_project'"))
                # Don't delete global_singleton - it might be needed by the test framework
                session.commit()
            except Exception as e:
                print(f"Cleanup error: {e}")
                session.rollback()'''
    
    content = re.sub(setup_pattern, new_setup, content, flags=re.DOTALL)
    
    return content


def fix_test_file(file_path: Path) -> bool:
    """Fix the test file."""
    print(f"Fixing {file_path}...")
    
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply fixes
        content = fix_hardcoded_ids(content)
        content = add_better_cleanup(content)
        
        # Only write if changed
        if content != original_content:
            file_path.write_text(content)
            print(f"✓ Fixed {file_path}")
            return True
        else:
            print(f"  No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to fix unified context integration test failures."""
    test_file = Path("src/tests/integration/test_unified_context_integration.py")
    
    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        return
    
    if fix_test_file(test_file):
        print("✅ Fixed unified context integration tests for PostgreSQL")
    else:
        print("❌ Failed to fix unified context integration tests")


if __name__ == "__main__":
    main()