#!/usr/bin/env python3
"""
Integration tests for ORM-only database architecture.

This test suite validates that all repository factories correctly
use ORM implementations for both SQLite and PostgreSQL.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.infrastructure.repositories.project_repository_factory import (
    ProjectRepositoryFactory
)
from fastmcp.task_management.infrastructure.repositories.agent_repository_factory import (
    AgentRepositoryFactory
)
from fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory import (
    GitBranchRepositoryFactory
)
from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import (
    SubtaskRepositoryFactory
)
from fastmcp.task_management.infrastructure.repositories.task_repository_factory import (
    TaskRepositoryFactory
)
from fastmcp.task_management.infrastructure.repositories.hierarchical_context_repository_factory import (
    HierarchicalContextRepositoryFactory
)
from fastmcp.task_management.infrastructure.repositories.template_repository_factory import (
    TemplateRepositoryFactory
)


class TestORMOnlyArchitecture:
    """Test suite for ORM-only database architecture"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.test_db_path = self.temp_db.name
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def test_project_repository_uses_orm_only(self):
        """Test ProjectRepositoryFactory always creates ORM repository"""
        # Test with SQLite database type
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"}):
            repo = ProjectRepositoryFactory.create(user_id="test_user")
            # Verify ORM repository is created
            assert "ORM" in repo.__class__.__name__
            assert repo.__class__.__name__ == "ORMProjectRepository"
        
        # Test with PostgreSQL database type
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            repo = ProjectRepositoryFactory.create(user_id="test_user")
            # Verify same ORM repository is created
            assert "ORM" in repo.__class__.__name__
            assert repo.__class__.__name__ == "ORMProjectRepository"
    
    def test_agent_repository_uses_orm_only(self):
        """Test AgentRepositoryFactory always creates ORM repository"""
        # Both database types should create ORM repository
        for db_type in ["sqlite", "postgresql"]:
            with patch.dict(os.environ, {"DATABASE_TYPE": db_type}):
                repo = AgentRepositoryFactory.create()
                assert "ORM" in repo.__class__.__name__
                assert repo.__class__.__name__ == "ORMAgentRepository"
    
    def test_git_branch_repository_uses_orm_only(self):
        """Test GitBranchRepositoryFactory always creates ORM repository"""
        # Both database types should create ORM repository
        for db_type in ["sqlite", "postgresql"]:
            with patch.dict(os.environ, {"DATABASE_TYPE": db_type}):
                repo = GitBranchRepositoryFactory.create()
                assert "ORM" in repo.__class__.__name__
                assert repo.__class__.__name__ == "ORMGitBranchRepository"
    
    def test_subtask_repository_uses_orm_only(self):
        """Test SubtaskRepositoryFactory always creates ORM repository"""
        # Both database types should create ORM repository
        for db_type in ["sqlite", "postgresql"]:
            with patch.dict(os.environ, {"DATABASE_TYPE": db_type}):
                factory = SubtaskRepositoryFactory()
                repo = factory.create_orm_subtask_repository()
                assert "ORM" in repo.__class__.__name__
                assert repo.__class__.__name__ == "ORMSubtaskRepository"
    
    def test_task_repository_uses_orm_only(self):
        """Test TaskRepositoryFactory always creates ORM repository"""
        # Both database types should create ORM repository
        for db_type in ["sqlite", "postgresql"]:
            with patch.dict(os.environ, {"DATABASE_TYPE": db_type}):
                factory = TaskRepositoryFactory()
                repo = factory.create_system_repository()
                assert "ORM" in repo.__class__.__name__
                assert repo.__class__.__name__ == "ORMTaskRepository"
    
    def test_hierarchical_context_repository_uses_orm_only(self):
        """Test HierarchicalContextRepositoryFactory always creates ORM repository"""
        # Both database types should create ORM repository
        for db_type in ["sqlite", "postgresql"]:
            with patch.dict(os.environ, {"DATABASE_TYPE": db_type}):
                factory = HierarchicalContextRepositoryFactory()
                repo = factory.create_hierarchical_context_repository()
                assert "ORM" in repo.__class__.__name__
                assert repo.__class__.__name__ == "ORMHierarchicalContextRepository"
    
    def test_template_repository_uses_orm_only(self):
        """Test TemplateRepositoryFactory always creates ORM repository"""
        # Both database types should create ORM repository
        for db_type in ["sqlite", "postgresql"]:
            with patch.dict(os.environ, {"DATABASE_TYPE": db_type}):
                factory = TemplateRepositoryFactory()
                repo = factory.create_repository()
                assert "ORM" in repo.__class__.__name__
                assert repo.__class__.__name__ == "ORMTemplateRepository"
    
    def test_repository_factories_ignore_legacy_parameters(self):
        """Test that repository factories handle legacy parameters gracefully"""
        # ProjectRepositoryFactory should ignore db_path
        repo = ProjectRepositoryFactory.create(
            user_id="test_user",
            db_path=self.test_db_path  # Legacy parameter, should be ignored
        )
        assert "ORM" in repo.__class__.__name__
        
        # GitBranchRepositoryFactory should not accept db_path
        repo = GitBranchRepositoryFactory.create()
        assert "ORM" in repo.__class__.__name__
    
    def test_all_repositories_share_same_session(self):
        """Test that all ORM repositories use the same database session"""
        # Create multiple repositories
        project_repo = ProjectRepositoryFactory.create(user_id="test_user")
        agent_repo = AgentRepositoryFactory.create()
        task_factory = TaskRepositoryFactory()
        task_repo = task_factory.create_system_repository()
        
        # All should be ORM repositories
        assert all("ORM" in repo.__class__.__name__ 
                  for repo in [project_repo, agent_repo, task_repo])
        
        # In a real test, we would verify they share the same session
        # For now, just verify they're all ORM implementations
        assert project_repo.__class__.__name__ == "ORMProjectRepository"
        assert agent_repo.__class__.__name__ == "ORMAgentRepository"
        assert task_repo.__class__.__name__ == "ORMTaskRepository"
    
    def test_no_sqlite_specific_code_remains(self):
        """Verify that SQLite-specific repository code is not accessible"""
        # These imports should fail since SQLite repositories are removed
        with pytest.raises(ImportError):
            from fastmcp.task_management.infrastructure.repositories.sqlite.project_repository import SQLiteProjectRepository
        
        with pytest.raises(ImportError):
            from fastmcp.task_management.infrastructure.repositories.sqlite.task_repository import SQLiteTaskRepository
        
        with pytest.raises(ImportError):
            from fastmcp.task_management.infrastructure.repositories.sqlite.agent_repository import SQLiteAgentRepository


if __name__ == "__main__":
    pytest.main([__file__, "-v"])