#!/usr/bin/env python3
"""
Debug script to test context creation step by step
"""

import sys
import os
sys.path.append('/home/daihungpham/agentic-project/dhafnck_mcp_main/src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastmcp.task_management.infrastructure.database.database_config import Base
from fastmcp.task_management.infrastructure.database.models import Project, ProjectGitBranch
from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory

def main():
    # Set up test database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    # Create project and git branch
    session = SessionLocal()
    
    project = Project(
        id="proj-123",
        name="Test Project",
        description="Test project for context hierarchy",
        user_id="test_user"
    )
    session.add(project)
    
    git_branch = ProjectGitBranch(
        id="branch-456",
        project_id="proj-123",
        name="feature/test",
        description="Test branch for context hierarchy"
    )
    session.add(git_branch)
    session.commit()
    
    # Verify records were created
    projects = session.query(Project).all()
    branches = session.query(ProjectGitBranch).all()
    
    print(f"Projects created: {len(projects)}")
    for p in projects:
        print(f"  - Project ID: {p.id}, Name: {p.name}")
    
    print(f"Git branches created: {len(branches)}")
    for b in branches:
        print(f"  - Branch ID: {b.id}, Project ID: {b.project_id}, Name: {b.name}")
    
    session.close()
    
    # Create facade
    facade_factory = UnifiedContextFacadeFactory(session_factory=SessionLocal)
    facade = facade_factory.create_facade()
    
    # Try to create project context
    print("\nCreating project context...")
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
    
    # Try to create branch context
    print("\nCreating branch context...")
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

if __name__ == "__main__":
    main()