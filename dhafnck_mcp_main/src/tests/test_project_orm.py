#!/usr/bin/env python3
"""
Test Script for Project ORM Repository Implementation

This script tests the ORM Project Repository implementation
with PostgreSQL database backend.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastmcp.task_management.domain.entities.project import Project
from fastmcp.task_management.infrastructure.repositories.project_repository_factory import (
    ProjectRepositoryFactory, RepositoryType
)
from fastmcp.task_management.infrastructure.repositories.orm.project_repository import ORMProjectRepository
from fastmcp.task_management.infrastructure.database.database_config import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectORMTest:
    """Test suite for Project ORM Repository"""
    
    def __init__(self):
        self.repository: Optional[ORMProjectRepository] = None
        self.test_projects: List[Project] = []
    
    async def setup(self):
        """Set up test environment"""
        logger.info("Setting up test environment...")
        
        # Set environment for PostgreSQL
        os.environ['DATABASE_TYPE'] = 'postgresql'
        
        # Initialize database
        try:
            await init_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        
        # Create ORM repository
        try:
            factory = ProjectRepositoryFactory()
            factory._register_orm_repository()
            self.repository = factory.create(repository_type=RepositoryType.POSTGRESQL)
            logger.info("ORM Project Repository created successfully")
        except Exception as e:
            logger.error(f"Failed to create ORM repository: {e}")
            raise
    
    async def test_create_project(self):
        """Test project creation"""
        logger.info("Testing project creation...")
        
        try:
            # Create test project using domain entity
            project = Project.create(
                name="Test Project ORM",
                description="A test project for ORM implementation"
            )
            
            # Save using repository
            await self.repository.save(project)
            self.test_projects.append(project)
            
            logger.info(f"✓ Project created with ID: {project.id}")
            return project
            
        except Exception as e:
            logger.error(f"✗ Project creation failed: {e}")
            raise
    
    async def test_find_project(self, project_id: str):
        """Test project retrieval"""
        logger.info(f"Testing project retrieval for ID: {project_id}")
        
        try:
            found_project = await self.repository.find_by_id(project_id)
            
            if found_project:
                logger.info(f"✓ Project found: {found_project.name}")
                logger.info(f"  Description: {found_project.description}")
                logger.info(f"  Created: {found_project.created_at}")
                return found_project
            else:
                logger.error("✗ Project not found")
                return None
                
        except Exception as e:
            logger.error(f"✗ Project retrieval failed: {e}")
            raise
    
    async def test_update_project(self, project_id: str):
        """Test project update"""
        logger.info(f"Testing project update for ID: {project_id}")
        
        try:
            # Get existing project
            project = await self.repository.find_by_id(project_id)
            if not project:
                raise ValueError("Project not found for update")
            
            # Update project
            project.description = "Updated description via ORM"
            project.updated_at = datetime.now()
            
            # Save changes
            await self.repository.update(project)
            
            # Verify update
            updated_project = await self.repository.find_by_id(project_id)
            if updated_project and "Updated description" in updated_project.description:
                logger.info("✓ Project updated successfully")
                return updated_project
            else:
                logger.error("✗ Project update verification failed")
                return None
                
        except Exception as e:
            logger.error(f"✗ Project update failed: {e}")
            raise
    
    async def test_list_projects(self):
        """Test listing all projects"""
        logger.info("Testing project listing...")
        
        try:
            projects = await self.repository.find_all()
            logger.info(f"✓ Found {len(projects)} projects")
            
            for i, project in enumerate(projects, 1):
                logger.info(f"  {i}. {project.name} ({project.id})")
            
            return projects
            
        except Exception as e:
            logger.error(f"✗ Project listing failed: {e}")
            raise
    
    async def test_find_by_name(self, name: str):
        """Test finding project by name"""
        logger.info(f"Testing find project by name: {name}")
        
        try:
            project = await self.repository.find_by_name(name)
            
            if project:
                logger.info(f"✓ Project found by name: {project.id}")
                return project
            else:
                logger.info("✗ Project not found by name")
                return None
                
        except Exception as e:
            logger.error(f"✗ Find by name failed: {e}")
            raise
    
    async def test_search_projects(self):
        """Test project search functionality"""
        logger.info("Testing project search...")
        
        try:
            # Search for test projects
            search_results = self.repository.search_projects("Test", limit=10)
            logger.info(f"✓ Search returned {len(search_results)} results")
            
            for project in search_results:
                logger.info(f"  - {project.name}: {project.description}")
            
            return search_results
            
        except Exception as e:
            logger.error(f"✗ Project search failed: {e}")
            raise
    
    async def test_project_statistics(self, project_id: str):
        """Test project statistics"""
        logger.info(f"Testing project statistics for ID: {project_id}")
        
        try:
            stats = self.repository.get_project_statistics(project_id)
            logger.info("✓ Project statistics retrieved:")
            logger.info(f"  Project Name: {stats['project_name']}")
            logger.info(f"  Status: {stats['status']}")
            logger.info(f"  Total Branches: {stats['total_branches']}")
            logger.info(f"  Assigned Branches: {stats['assigned_branches']}")
            logger.info(f"  Total Tasks: {stats['total_tasks']}")
            logger.info(f"  Completed Tasks: {stats['completed_tasks']}")
            logger.info(f"  Completion: {stats['completion_percentage']:.1f}%")
            
            return stats
            
        except Exception as e:
            logger.error(f"✗ Project statistics failed: {e}")
            raise
    
    async def test_project_health_summary(self):
        """Test project health summary"""
        logger.info("Testing project health summary...")
        
        try:
            health = await self.repository.get_project_health_summary()
            logger.info("✓ Project health summary:")
            logger.info(f"  Total Projects: {health['total_projects']}")
            logger.info(f"  Projects by Status: {health['projects_by_status']}")
            logger.info(f"  Projects with Branches: {health['projects_with_branches']}")
            logger.info(f"  Total Branches: {health['total_branches']}")
            logger.info(f"  Assigned Branches: {health['assigned_branches']}")
            logger.info(f"  Average Branches per Project: {health['average_branches_per_project']:.2f}")
            
            return health
            
        except Exception as e:
            logger.error(f"✗ Project health summary failed: {e}")
            raise
    
    async def test_count_projects(self):
        """Test project count"""
        logger.info("Testing project count...")
        
        try:
            count = await self.repository.count()
            logger.info(f"✓ Total project count: {count}")
            return count
            
        except Exception as e:
            logger.error(f"✗ Project count failed: {e}")
            raise
    
    async def test_project_exists(self, project_id: str):
        """Test project existence check"""
        logger.info(f"Testing project existence for ID: {project_id}")
        
        try:
            exists = await self.repository.exists(project_id)
            logger.info(f"✓ Project exists: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"✗ Project existence check failed: {e}")
            raise
    
    async def cleanup(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        
        try:
            for project in self.test_projects:
                await self.repository.delete(project.id)
                logger.info(f"✓ Deleted test project: {project.id}")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("=" * 60)
        logger.info("STARTING PROJECT ORM REPOSITORY TESTS")
        logger.info("=" * 60)
        
        try:
            # Setup
            await self.setup()
            
            # Test project creation
            test_project = await self.test_create_project()
            
            # Test project retrieval
            found_project = await self.test_find_project(test_project.id)
            
            # Test project update
            await self.test_update_project(test_project.id)
            
            # Test project listing
            await self.test_list_projects()
            
            # Test find by name
            await self.test_find_by_name("Test Project ORM")
            
            # Test search
            await self.test_search_projects()
            
            # Test project statistics
            await self.test_project_statistics(test_project.id)
            
            # Test health summary
            await self.test_project_health_summary()
            
            # Test count
            await self.test_count_projects()
            
            # Test existence
            await self.test_project_exists(test_project.id)
            
            logger.info("=" * 60)
            logger.info("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"TEST FAILED: {e}")
            logger.error("=" * 60)
            raise
            
        finally:
            # Cleanup
            await self.cleanup()


async def main():
    """Main test function"""
    test_suite = ProjectORMTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())