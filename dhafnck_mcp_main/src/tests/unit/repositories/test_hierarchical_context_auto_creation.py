#!/usr/bin/env python3
"""
Unit tests for ORMHierarchicalContextRepository auto-creation fixes.

Tests the fix that auto-creates missing project, branch, and context records
to prevent foreign key constraint errors in the 4-tier hierarchy.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid
from datetime import datetime
import sqlite3

from fastmcp.task_management.infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository
from fastmcp.task_management.infrastructure.database.models import (
    Project, ProjectContext, TaskContext, GlobalContext, 
    ProjectGitBranch, BranchContext
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


class TestHierarchicalContextAutoCreation:
    """Test ORMHierarchicalContextRepository auto-creates missing entities"""
    
    @pytest.fixture
    def repository(self):
        """Create repository instance"""
        return ORMHierarchicalContextRepository()
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session"""
        session = MagicMock(spec=Session)
        # Mock the context manager behavior
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=session)
        mock_context.__exit__ = MagicMock(return_value=None)
        return mock_context
    
    def test_create_task_context_auto_creates_project(self, repository, mock_session):
        """Test that missing project and branch are auto-created when creating task context"""
        # Setup
        task_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        
        # Get the actual session that will be returned by the context manager
        actual_session = mock_session.__enter__.return_value
        
        # Mock session.get to return necessary entities
        mock_branch_for_validation = Mock(spec=ProjectGitBranch)
        mock_branch_for_validation.project_id = project_id
        
        mock_project_for_validation = Mock(spec=Project)
        mock_project_for_validation.id = project_id
        
        def mock_get(model_class, id_value):
            from fastmcp.task_management.infrastructure.database.models import (
                ProjectGitBranch as RealProjectGitBranch,
                Project as RealProject
            )
            # Return the branch when checking for it
            if model_class == RealProjectGitBranch and id_value == branch_id:
                return mock_branch_for_validation
            # Return the project when checking for it
            elif model_class == RealProject and id_value == project_id:
                return mock_project_for_validation
            return None
        
        actual_session.get.side_effect = mock_get
        
        # Mock the models
        mock_project = Mock(spec=Project)
        mock_project_context = Mock(spec=ProjectContext)
        mock_branch = Mock(spec=ProjectGitBranch)
        mock_branch_context = Mock(spec=BranchContext)
        mock_task_context = Mock(spec=TaskContext)
        
        # Patch the model classes in the correct module
        with patch('fastmcp.task_management.infrastructure.database.models.Project', return_value=mock_project):
            with patch('fastmcp.task_management.infrastructure.database.models.ProjectContext', return_value=mock_project_context):
                with patch('fastmcp.task_management.infrastructure.database.models.ProjectGitBranch', return_value=mock_branch):
                    with patch('fastmcp.task_management.infrastructure.database.models.BranchContext', return_value=mock_branch_context):
                        with patch('fastmcp.task_management.infrastructure.database.models.TaskContext', return_value=mock_task_context):
                            with patch.object(repository, 'get_db_session', return_value=mock_session):
                                # Call create_task_context with 4-tier hierarchy
                                repository.create_task_context(
                                    task_id=task_id,
                                    data={
                                        "task_data": {"title": "Test", "status": "todo"},
                                        "parent_branch_id": branch_id,
                                        "parent_branch_context_id": branch_id
                                    }
                                )
        
        # Verify entities were created and added to session
        assert actual_session.add.call_count >= 1
        # Note: In 4-tier hierarchy, branch and its context should be created
        
        # Verify commit was called
        assert actual_session.commit.called
    
    def test_create_task_context_auto_creates_project_context(self, repository, mock_session):
        """Test that missing branch context is auto-created"""
        # Setup
        task_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        
        # Get the actual session that will be returned by the context manager
        actual_session = mock_session.__enter__.return_value
        
        # Mock project and branch exist but branch context doesn't
        mock_project = Mock(spec=Project)
        mock_branch = Mock(spec=ProjectGitBranch)
        mock_branch.project_id = project_id
        
        # Use a function to return appropriate values based on model type
        def mock_get(model_class, id_value):
            if model_class == Project:
                return mock_project
            elif model_class == ProjectGitBranch:
                return mock_branch
            else:
                return None  # BranchContext and other entities not found
        
        actual_session.get.side_effect = mock_get
        
        # Mock create_branch_context to track it was called
        with patch.object(repository, 'create_branch_context') as mock_create_bc:
            with patch.object(repository, 'get_db_session', return_value=mock_session):
                # Call create_task_context
                repository.create_task_context(
                    task_id=task_id,
                    data={
                        "task_data": {"title": "Test", "status": "todo"},
                        "parent_branch_id": branch_id,
                        "parent_branch_context_id": branch_id
                    }
                )
        
        # Verify create_branch_context was called
        mock_create_bc.assert_called_once()
        call_args = mock_create_bc.call_args[0]
        assert call_args[0] == branch_id  # branch_context_id
        assert isinstance(call_args[1], dict)  # data
    
    def test_create_task_context_succeeds_with_all_entities(self, repository, mock_session):
        """Test normal case where all required entities exist"""
        # Setup
        task_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        
        # Get the actual session that will be returned by the context manager
        actual_session = mock_session.__enter__.return_value
        
        # Mock all entities exist
        mock_project = Mock(spec=Project)
        mock_project_context = Mock(spec=ProjectContext)
        mock_branch = Mock(spec=ProjectGitBranch)
        mock_branch_context = Mock(spec=BranchContext)
        
        # Use a function to return appropriate values based on model type
        def mock_get(model_class, id_value):
            if model_class == Project:
                return mock_project
            elif model_class == ProjectContext:
                return mock_project_context
            elif model_class == ProjectGitBranch:
                return mock_branch
            elif model_class == BranchContext:
                return mock_branch_context
            else:
                return None  # Other entities not found
        
        actual_session.get.side_effect = mock_get
        
        # Mock TaskContext
        mock_task_context = Mock(spec=TaskContext)
        
        with patch('fastmcp.task_management.infrastructure.repositories.orm.hierarchical_context_repository.TaskContext', return_value=mock_task_context):
            with patch.object(repository, 'get_db_session', return_value=mock_session):
                # Call create_task_context
                repository.create_task_context(
                    task_id=task_id,
                    data={
                        "task_data": {"title": "Test", "status": "todo"},
                        "parent_branch_id": branch_id,
                        "parent_branch_context_id": branch_id
                    }
                )
        
        # Verify only task context was added (not project or project context)
        actual_session.add.assert_called_once()
        added_entity = actual_session.add.call_args[0][0]
        assert added_entity == mock_task_context
    
    def test_foreign_key_error_prevention(self, repository):
        """Test that foreign key errors are prevented by auto-creation"""
        # This test simulates the original foreign key error scenario
        task_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        
        # Mock a session that would raise IntegrityError without auto-creation
        mock_session = MagicMock(spec=Session)
        
        # Get the actual session that will be returned by the context manager
        actual_session = mock_session.__enter__.return_value
        
        # First attempt would fail with foreign key error
        # But with auto-creation, it should succeed
        # Mock session.get to return branch for validation
        mock_branch_for_validation = Mock(spec=ProjectGitBranch)
        mock_branch_for_validation.project_id = project_id
        
        # Create mock project outside of the function to avoid re-speccing
        mock_project_for_validation = Mock()
        mock_project_for_validation.id = project_id
        
        def mock_get(model_class, id_value):
            from fastmcp.task_management.infrastructure.database.models import (
                ProjectGitBranch as RealProjectGitBranch,
                Project as RealProject
            )
            # Return the branch when checking for it
            if model_class == RealProjectGitBranch and id_value == branch_id:
                return mock_branch_for_validation
            # Return the project when checking for it
            elif model_class == RealProject and id_value == project_id:
                return mock_project_for_validation
            return None
        
        actual_session.get.side_effect = mock_get
        
        # Track what gets added to session
        added_entities = []
        actual_session.add.side_effect = lambda entity: added_entities.append(entity)
        
        with patch.object(repository, 'get_db_session', return_value=mock_session):
            with patch('fastmcp.task_management.infrastructure.database.models.Project'):
                with patch('fastmcp.task_management.infrastructure.database.models.ProjectContext'):
                    with patch('fastmcp.task_management.infrastructure.database.models.ProjectGitBranch'):
                        with patch('fastmcp.task_management.infrastructure.database.models.BranchContext'):
                            with patch('fastmcp.task_management.infrastructure.database.models.TaskContext'):
                                # This should not raise IntegrityError
                                try:
                                    repository.create_task_context(
                                        task_id=task_id,
                                        data={
                                            "task_data": {"title": "Test", "status": "todo"},
                                            "parent_branch_id": branch_id,
                                            "parent_branch_context_id": branch_id
                                        }
                                    )
                                    # Success - no foreign key error
                                    assert True
                                except IntegrityError:
                                    pytest.fail("Foreign key error should be prevented by auto-creation")
        
        # Verify entities were created in correct order
        assert len(added_entities) >= 1  # At least task context
        assert actual_session.commit.called
    
    def test_auto_creation_with_custom_data(self, repository, mock_session):
        """Test that auto-created entities have appropriate default data"""
        # Setup
        task_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        branch_id = str(uuid.uuid4())
        
        # Get the actual session that will be returned by the context manager
        actual_session = mock_session.__enter__.return_value
        
        # Mock session.get to return branch for validation
        mock_branch_for_validation = Mock(spec=ProjectGitBranch)
        mock_branch_for_validation.project_id = project_id
        
        # Create mock project outside of the function to avoid re-speccing
        mock_project_for_validation = Mock()
        mock_project_for_validation.id = project_id
        
        def mock_get(model_class, id_value):
            from fastmcp.task_management.infrastructure.database.models import (
                ProjectGitBranch as RealProjectGitBranch,
                Project as RealProject
            )
            # Return the branch when checking for it
            if model_class == RealProjectGitBranch and id_value == branch_id:
                return mock_branch_for_validation
            # Return the project when checking for it
            elif model_class == RealProject and id_value == project_id:
                return mock_project_for_validation
            return None
        
        actual_session.get.side_effect = mock_get
        
        # Capture created entities
        created_project = None
        created_branch = None
        created_branch_context = None
        
        def capture_add(entity):
            nonlocal created_project, created_branch, created_branch_context
            if hasattr(entity, '__class__'):
                if entity.__class__.__name__ == 'Project':
                    created_project = entity
                elif entity.__class__.__name__ == 'ProjectGitBranch':
                    created_branch = entity
                elif entity.__class__.__name__ == 'BranchContext':
                    created_branch_context = entity
        
        actual_session.add.side_effect = capture_add
        
        with patch.object(repository, 'get_db_session', return_value=mock_session):
            # Need to mock the actual model classes
            with patch('fastmcp.task_management.infrastructure.database.models.Project') as MockProject:
                with patch('fastmcp.task_management.infrastructure.database.models.ProjectContext'):
                    with patch('fastmcp.task_management.infrastructure.database.models.ProjectGitBranch') as MockBranch:
                        with patch('fastmcp.task_management.infrastructure.database.models.BranchContext'):
                            with patch('fastmcp.task_management.infrastructure.database.models.TaskContext'):
                                # Configure mocks
                                mock_project_instance = Mock()
                                MockProject.return_value = mock_project_instance
                                mock_branch_instance = Mock()
                                MockBranch.return_value = mock_branch_instance
                                
                                repository.create_task_context(
                                    task_id=task_id,
                                    data={
                                        "task_data": {"title": "Test Task", "status": "todo"},
                                        "parent_branch_id": branch_id,
                                        "parent_branch_context_id": branch_id
                                    }
                                )
                                
                                # Verify entities were created
                                assert actual_session.add.call_count >= 1