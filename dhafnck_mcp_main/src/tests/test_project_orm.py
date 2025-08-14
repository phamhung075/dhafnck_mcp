#!/usr/bin/env python3
"""
Test Script for Project ORM Repository Implementation

This script tests the ORM Project Repository implementation
with the new ORM-only architecture.
"""

import pytest
from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.infrastructure.repositories.orm.project_repository import ORMProjectRepository


class TestProjectORM:
    
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

    """Test suite for Project ORM Repository"""
    
    def test_project_orm_creation(self):
        """Test that ORM repository can be instantiated"""
        repository = ORMProjectRepository()
        assert repository is not None
    
    def test_project_entity_creation(self):
        """Test project entity creation"""
        project = Project.create(
            name="Test Project",
            description="A test project"
        )
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.id is not None