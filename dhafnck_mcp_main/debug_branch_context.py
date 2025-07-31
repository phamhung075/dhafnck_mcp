#!/usr/bin/env python3
"""
Debug script to test branch context creation and verify foreign keys
"""

import sys
import os
sys.path.append('/home/daihungpham/agentic-project/dhafnck_mcp_main/src')

from fastmcp.task_management.infrastructure.database.database_config import get_session
from fastmcp.task_management.infrastructure.database.models import Project, ProjectGitBranch, BranchContext, ProjectContext
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory

def main():
    print("=== Debug Branch Context Creation ===")
    
    # Create project and git branch using the test database
    with get_session() as session:
        # Clear any existing data
        session.query(BranchContext).delete()
        session.query(ProjectContext).delete()
        session.query(ProjectGitBranch).filter_by(id="branch-456").delete()
        session.query(Project).filter_by(id="proj-123").delete()
        session.commit()
        
        # Create project
        project = Project(
            id="proj-123",
            name="Test Project",
            description="Test project for context hierarchy",
            user_id="test_user"
        )
        session.add(project)
        
        # Create git branch
        git_branch = ProjectGitBranch(
            id="branch-456",
            project_id="proj-123",
            name="feature/test",
            description="Test branch for context hierarchy"
        )
        session.add(git_branch)
        session.commit()
        
        print(f"✓ Created project: {project.id}")
        print(f"✓ Created git branch: {git_branch.id}")
    
    # Create facade
    facade_factory = UnifiedContextFacadeFactory()
    facade = facade_factory.create_facade()
    
    # Create project context
    print("\n=== Creating Project Context ===")
    project_result = facade.create_context(
        level="project", 
        context_id="proj-123",
        data={
            "project_name": "Test Project",
            "project_settings": {
                "team_preferences": {"language": "Python"},
                "technology_stack": {"framework": "FastAPI"}
            }
        }
    )
    print(f"Project context result: {project_result}")
    
    # Create branch context
    print("\n=== Creating Branch Context ===")
    branch_result = facade.create_context(
        level="branch",
        context_id="branch-456",
        data={
            "project_id": "proj-123",
            "git_branch_name": "feature/test",
            "branch_settings": {
                "branch_workflow": {"type": "feature"},
                "branch_standards": {"review": "required"}
            }
        }
    )
    print(f"Branch context result: {branch_result}")
    
    # Verify branch context was created
    print("\n=== Verifying Branch Context ===")
    with get_session() as session:
        branch_context = session.query(BranchContext).filter_by(branch_id="branch-456").first()
        if branch_context:
            print(f"✓ Branch context found: {branch_context.branch_id}")
            print(f"  parent_project_id: {branch_context.parent_project_id}")
            print(f"  parent_project_context_id: {branch_context.parent_project_context_id}")
        else:
            print("✗ Branch context not found!")
    
    # Try to create task context
    print("\n=== Creating Task Context ===")
    task_result = facade.create_context(
        level="task",
        context_id="task-789",
        data={
            "branch_id": "branch-456",
            "task_data": {
                "title": "Implement authentication",
                "status": "in_progress"
            }
        }
    )
    print(f"Task context result: {task_result}")

if __name__ == "__main__":
    main()