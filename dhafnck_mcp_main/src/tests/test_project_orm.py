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