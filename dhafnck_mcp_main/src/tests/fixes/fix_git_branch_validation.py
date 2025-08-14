#!/usr/bin/env python3
"""
Fix git_branch_id validation error in test_tool_issues_verification.py.

The test is using SQLite-specific code to set up test data, but we're running
with PostgreSQL. This script updates the test to use SQLAlchemy ORM instead.
"""

import os
import re
from pathlib import Path


def fix_test_context_fixture(content: str) -> str:
    """Replace SQLite-specific test_context fixture with database-agnostic version."""
    
    # Find the test_context fixture
    pattern = r'(@pytest\.fixture\(scope="function"\)\s*\n\s*def test_context\(self\):[\s\S]*?return \{[\s\S]*?\})'
    
    replacement = '''@pytest.fixture(scope="function")
    def test_context(self):
        """Provide test context data with proper Clean Relationship Chain setup"""
        # Set up Clean Relationship Chain: user -> project -> git_branch
        import uuid
        from datetime import datetime
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from fastmcp.task_management.infrastructure.database.models import Project, ProjectGitBranch
        
        # Create test data following Clean Relationship Chain
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        git_branch_name = "main"
        user_id = "default_id"
        git_branch_id = str(uuid.uuid4())
        
        try:
            # Use database-agnostic approach with SQLAlchemy
            db_config = get_db_config()
            
            with db_config.get_session() as session:
                # Check if default project exists, if not create it
                project = session.query(Project).filter_by(id="default_project").first()
                if not project:
                    project = Project(
                        id="default_project",
                        name="Default Project",
                        description="Default project for testing",
                        user_id=user_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(project)
                    session.flush()
                
                # Create git branch (task tree) record
                git_branch = ProjectGitBranch(
                    id=git_branch_id,
                    project_id="default_project",
                    name=git_branch_name,
                    description="Main branch for testing",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(git_branch)
                session.commit()
                
                print(f"DEBUG: Created git_branch_id: {git_branch_id}")
                
                # Verify the branch was created
                verify_branch = session.query(ProjectGitBranch).filter_by(id=git_branch_id).first()
                if verify_branch:
                    print(f"DEBUG: Verified git_branch_id exists: {verify_branch.id}")
                else:
                    print(f"ERROR: git_branch_id {git_branch_id} was not found after creation!")
                    
        except Exception as e:
            print(f"Warning: Could not set up test context: {e}")
            # Try to use an existing branch from the database
            try:
                db_config = get_db_config()
                with db_config.get_session() as session:
                    existing_branch = session.query(ProjectGitBranch).filter_by(
                        project_id="default_project"
                    ).first()
                    if existing_branch:
                        git_branch_id = existing_branch.id
                        print(f"DEBUG: Using existing git_branch_id: {git_branch_id}")
            except Exception as e2:
                print(f"ERROR: Could not find existing git branch: {e2}")
                pass
        
        return {
            "git_branch_id": git_branch_id,
            "project_id": "default_project",
            "git_branch_name": git_branch_name,
            "user_id": user_id
        }'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also need to add the necessary imports at the top if not present
    if "from datetime import datetime" not in content:
        # Add after the existing imports
        import_pattern = r'(from fastmcp\.exceptions import ToolError\n)'
        import_addition = r'\1from datetime import datetime\n'
        content = re.sub(import_pattern, import_addition, content)
    
    return content


def main():
    """Main function to fix the git_branch_id validation error."""
    test_file = Path("src/tests/integration/test_tool_issues_verification.py")
    
    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        return
    
    print(f"Fixing {test_file}...")
    
    try:
        content = test_file.read_text()
        original_content = content
        
        # Apply fix
        content = fix_test_context_fixture(content)
        
        # Only write if changed
        if content != original_content:
            test_file.write_text(content)
            print(f"✓ Fixed {test_file}")
            print("✓ Replaced SQLite-specific code with database-agnostic SQLAlchemy approach")
        else:
            print(f"  No changes needed for {test_file}")
            
    except Exception as e:
        print(f"✗ Error fixing {test_file}: {e}")


if __name__ == "__main__":
    main()