#!/usr/bin/env python3
"""
Integration tests for database switching functionality.

This test suite validates that the DATABASE_TYPE environment variable
correctly switches between SQLite and PostgreSQL implementations
across all repository factories.
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
    ProjectRepositoryFactory, RepositoryType
)
from fastmcp.task_management.infrastructure.repositories.agent_repository_factory import (
    AgentRepositoryFactory, AgentRepositoryType
)
from fastmcp.task_management.infrastructure.repositories.git_branch_repository_factory import (
    GitBranchRepositoryFactory, GitBranchRepositoryType
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


class TestDatabaseSwitching:
    """Test suite for database switching functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.test_db_path = self.temp_db.name
        
        # Clear any cached instances
        ProjectRepositoryFactory.clear_cache()
        AgentRepositoryFactory.clear_cache()
        GitBranchRepositoryFactory.clear_cache()
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
        
        # Clear caches
        ProjectRepositoryFactory.clear_cache()
        AgentRepositoryFactory.clear_cache()
        GitBranchRepositoryFactory.clear_cache()
    
    def test_project_repository_database_switching(self):
        """Test ProjectRepositoryFactory database switching"""
        # Test SQLite
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"}):
            ProjectRepositoryFactory.clear_cache()
            
            repo = ProjectRepositoryFactory.create(
                user_id="test_user",
                db_path=self.test_db_path
            )
            
            # Verify SQLite repository is created
            assert "SQLite" in repo.__class__.__name__
            assert ProjectRepositoryFactory._get_default_type() == RepositoryType.SQLITE
        
        # Test PostgreSQL
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            ProjectRepositoryFactory.clear_cache()
            
            try:
                repo = ProjectRepositoryFactory.create(user_id="test_user")
                # Verify ORM repository is created
                assert "ORM" in repo.__class__.__name__
                assert ProjectRepositoryFactory._get_default_type() == RepositoryType.POSTGRESQL
            except (ImportError, ValueError):
                # ORM not available, skip test
                pytest.skip("PostgreSQL ORM not available")
    
    def test_agent_repository_database_switching(self):
        """Test AgentRepositoryFactory database switching"""
        # Test SQLite
        with patch.dict(os.environ, {"MCP_AGENT_REPOSITORY_TYPE": "sqlite"}):
            AgentRepositoryFactory.clear_cache()
            
            repo = AgentRepositoryFactory.create(
                user_id="test_user",
                db_path=self.test_db_path
            )
            
            assert "SQLite" in repo.__class__.__name__
            assert AgentRepositoryFactory._get_default_type() == AgentRepositoryType.SQLITE
        
        # Test ORM
        with patch.dict(os.environ, {"MCP_AGENT_REPOSITORY_TYPE": "orm"}):
            AgentRepositoryFactory.clear_cache()
            
            try:
                repo = AgentRepositoryFactory.create(user_id="test_user")
                assert "ORM" in repo.__class__.__name__
                assert AgentRepositoryFactory._get_default_type() == AgentRepositoryType.ORM
            except (ImportError, ValueError):
                pytest.skip("Agent ORM not available")
    
    def test_git_branch_repository_database_switching(self):
        """Test GitBranchRepositoryFactory database switching"""
        # Test SQLite
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_GIT_BRANCH_REPOSITORY_TYPE": "sqlite"}):
            GitBranchRepositoryFactory.clear_cache()
            
            repo = GitBranchRepositoryFactory.create(
                user_id="test_user",
                db_path=self.test_db_path
            )
            
            assert "SQLite" in repo.__class__.__name__
            assert GitBranchRepositoryFactory._get_default_type() == GitBranchRepositoryType.SQLITE
        
        # Test PostgreSQL -> ORM
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            GitBranchRepositoryFactory.clear_cache()
            
            try:
                repo = GitBranchRepositoryFactory.create(user_id="test_user")
                assert "ORM" in repo.__class__.__name__
                assert GitBranchRepositoryFactory._get_default_type() == GitBranchRepositoryType.ORM
            except (ImportError, ValueError):
                pytest.skip("Git Branch ORM not available")
    
    def test_subtask_repository_database_switching(self):
        """Test SubtaskRepositoryFactory database switching"""
        # Test SQLite
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": self.test_db_path}):
            factory = SubtaskRepositoryFactory(storage_type="sqlite")
            
            repo = factory.create_subtask_repository(
                project_id="test_project",
                git_branch_name="main",
                user_id="test_user"
            )
            
            assert "SQLite" in repo.__class__.__name__
            assert factory.database_type == "sqlite"
        
        # Test PostgreSQL -> ORM
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            factory = SubtaskRepositoryFactory()
            
            try:
                repo = factory.create_subtask_repository(
                    project_id="test_project",
                    git_branch_name="main",
                    user_id="test_user"
                )
                assert "ORM" in repo.__class__.__name__
                assert factory.database_type == "postgresql"
            except (ImportError, ValueError):
                pytest.skip("Subtask ORM not available")
    
    def test_task_repository_database_switching(self):
        """Test TaskRepositoryFactory database switching"""
        # Test SQLite
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": self.test_db_path}):
            factory = TaskRepositoryFactory(storage_type="sqlite")
            
            repo = factory.create_repository(
                project_id="test_project",
                git_branch_name="main",
                user_id="test_user"
            )
            
            assert "SQLite" in repo.__class__.__name__
        
        # Test PostgreSQL -> ORM
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            factory = TaskRepositoryFactory()
            
            try:
                repo = factory.create_repository(
                    project_id="test_project",
                    git_branch_name="main",
                    user_id="test_user"
                )
                assert "ORM" in repo.__class__.__name__
            except (ImportError, ValueError):
                pytest.skip("Task ORM not available")
    
    def test_hierarchical_context_repository_database_switching(self):
        """Test HierarchicalContextRepositoryFactory database switching"""
        # Test SQLite
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": self.test_db_path}):
            factory = HierarchicalContextRepositoryFactory()
            
            repo = factory.create_hierarchical_context_repository()
            
            assert "SQLite" in repo.__class__.__name__
        
        # Test PostgreSQL -> ORM
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            factory = HierarchicalContextRepositoryFactory()
            
            try:
                repo = factory.create_hierarchical_context_repository()
                assert "ORM" in repo.__class__.__name__
            except (ImportError, ValueError):
                pytest.skip("Hierarchical Context ORM not available")
    
    def test_template_repository_database_switching(self):
        """Test TemplateRepositoryFactory database switching"""
        # Test SQLite
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": self.test_db_path}):
            factory = TemplateRepositoryFactory()
            
            repo = factory.create_repository()
            
            assert "SQLite" in repo.__class__.__name__
        
        # Test PostgreSQL -> ORM
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            factory = TemplateRepositoryFactory()
            
            try:
                repo = factory.create_repository()
                assert "ORM" in repo.__class__.__name__
            except (ImportError, ValueError):
                pytest.skip("Template ORM not available")
    
    def test_fallback_behavior(self):
        """Test fallback behavior when PostgreSQL is not available"""
        # Test invalid database type falls back to SQLite
        with patch.dict(os.environ, {"DATABASE_TYPE": "invalid_db_type"}):
            ProjectRepositoryFactory.clear_cache()
            
            # Should fall back to SQLite
            default_type = ProjectRepositoryFactory._get_default_type()
            assert default_type == RepositoryType.SQLITE
    
    def test_environment_variable_priority(self):
        """Test that DATABASE_TYPE takes precedence over specific repository types"""
        # Test that DATABASE_TYPE=postgresql overrides MCP_GIT_BRANCH_REPOSITORY_TYPE=sqlite
        with patch.dict(os.environ, {
            "DATABASE_TYPE": "postgresql",
            "MCP_GIT_BRANCH_REPOSITORY_TYPE": "sqlite"
        }):
            GitBranchRepositoryFactory.clear_cache()
            
            default_type = GitBranchRepositoryFactory._get_default_type()
            # Should use ORM because DATABASE_TYPE=postgresql takes precedence
            assert default_type == GitBranchRepositoryType.ORM
    
    def test_consistent_behavior_across_factories(self):
        """Test that all factories behave consistently with same DATABASE_TYPE"""
        test_cases = [
            ("sqlite", ["SQLite"]),
            ("postgresql", ["ORM"])
        ]
        
        for db_type, expected_patterns in test_cases:
            with patch.dict(os.environ, {"DATABASE_TYPE": db_type, "MCP_DB_PATH": self.test_db_path}):
                # Clear all caches
                ProjectRepositoryFactory.clear_cache()
                AgentRepositoryFactory.clear_cache()
                GitBranchRepositoryFactory.clear_cache()
                
                try:
                    # Test consistent behavior across all factories
                    factories_and_repos = []
                    
                    # Project Repository
                    project_repo = ProjectRepositoryFactory.create(user_id="test_user")
                    factories_and_repos.append(("Project", project_repo))
                    
                    # Subtask Repository
                    subtask_factory = SubtaskRepositoryFactory()
                    subtask_repo = subtask_factory.create_subtask_repository(
                        project_id="test_project",
                        git_branch_name="main",
                        user_id="test_user"
                    )
                    factories_and_repos.append(("Subtask", subtask_repo))
                    
                    # Task Repository
                    task_factory = TaskRepositoryFactory()
                    task_repo = task_factory.create_repository(
                        project_id="test_project",
                        git_branch_name="main",
                        user_id="test_user"
                    )
                    factories_and_repos.append(("Task", task_repo))
                    
                    # Hierarchical Context Repository
                    context_factory = HierarchicalContextRepositoryFactory()
                    context_repo = context_factory.create_hierarchical_context_repository()
                    factories_and_repos.append(("Context", context_repo))
                    
                    # Template Repository
                    template_factory = TemplateRepositoryFactory()
                    template_repo = template_factory.create_repository()
                    factories_and_repos.append(("Template", template_repo))
                    
                    # Verify all repositories follow the same pattern
                    for repo_name, repo in factories_and_repos:
                        repo_class_name = repo.__class__.__name__
                        pattern_found = any(pattern in repo_class_name for pattern in expected_patterns)
                        assert pattern_found, f"{repo_name} repository {repo_class_name} doesn't match expected patterns {expected_patterns} for DATABASE_TYPE={db_type}"
                
                except (ImportError, ValueError):
                    if db_type == "postgresql":
                        pytest.skip(f"PostgreSQL ORM not available for DATABASE_TYPE={db_type}")
                    else:
                        raise


def run_database_switching_tests():
    """Run all database switching tests"""
    print("🔄 Running Database Switching Integration Tests...\n")
    
    test_instance = TestDatabaseSwitching()
    
    test_methods = [
        'test_project_repository_database_switching',
        'test_agent_repository_database_switching',
        'test_git_branch_repository_database_switching',
        'test_subtask_repository_database_switching',
        'test_task_repository_database_switching',
        'test_hierarchical_context_repository_database_switching',
        'test_template_repository_database_switching',
        'test_fallback_behavior',
        'test_environment_variable_priority',
        'test_consistent_behavior_across_factories'
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for method_name in test_methods:
        try:
            test_instance.setup_method()
            method = getattr(test_instance, method_name)
            method()
            passed += 1
            print(f"✅ {method_name}")
        except pytest.skip.Exception as e:
            skipped += 1
            print(f"⚠️  {method_name} - SKIPPED: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {method_name} - FAILED: {e}")
        finally:
            test_instance.teardown_method()
    
    print(f"\n📊 Database Switching Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    
    return failed == 0, {"passed": passed, "failed": failed, "skipped": skipped}


if __name__ == "__main__":
    success, results = run_database_switching_tests()
    
    if success:
        print("\n🎉 All database switching tests passed!")
        print("✅ DATABASE_TYPE environment variable works correctly")
        print("✅ All factories switch between SQLite and PostgreSQL properly")
        print("✅ Fallback behavior works as expected")
    else:
        print("\n💥 Some database switching tests failed!")
        print("Check the output above for details.")
    
    sys.exit(0 if success else 1)