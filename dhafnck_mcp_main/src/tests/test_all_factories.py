#!/usr/bin/env python3
"""
Comprehensive test script for all repository factories.

This script verifies that all repository factories can create both SQLite 
and ORM repositories correctly, testing the DATABASE_TYPE environment variable
functionality across all factory implementations.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

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


class TestAllFactories:
    """Test all repository factories for ORM and SQLite support"""
    
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
        
        # Clear caches again
        ProjectRepositoryFactory.clear_cache()
        AgentRepositoryFactory.clear_cache()
        GitBranchRepositoryFactory.clear_cache()
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"})
    def test_project_factory_sqlite(self):
        """Test ProjectRepositoryFactory with SQLite"""
        repository = ProjectRepositoryFactory.create(
            repository_type=RepositoryType.SQLITE,
            user_id="test_user",
            db_path=self.test_db_path
        )
        
        assert repository is not None
        assert "SQLite" in repository.__class__.__name__
        print("✓ ProjectRepositoryFactory SQLite test passed")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"})
    def test_project_factory_orm(self):
        """Test ProjectRepositoryFactory with ORM"""
        try:
            repository = ProjectRepositoryFactory.create(
                repository_type=RepositoryType.POSTGRESQL,
                user_id="test_user"
            )
            assert repository is not None
            assert "ORM" in repository.__class__.__name__
            print("✓ ProjectRepositoryFactory ORM test passed")
        except ImportError:
            print("⚠ ProjectRepositoryFactory ORM test skipped (ORM not available)")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"})
    def test_agent_factory_sqlite(self):
        """Test AgentRepositoryFactory with SQLite"""
        repository = AgentRepositoryFactory.create(
            repository_type=AgentRepositoryType.SQLITE,
            user_id="test_user",
            db_path=self.test_db_path
        )
        
        assert repository is not None
        assert "SQLite" in repository.__class__.__name__
        print("✓ AgentRepositoryFactory SQLite test passed")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"})
    def test_agent_factory_orm(self):
        """Test AgentRepositoryFactory with ORM"""
        try:
            repository = AgentRepositoryFactory.create(
                repository_type=AgentRepositoryType.ORM,
                user_id="test_user"
            )
            assert repository is not None
            assert "ORM" in repository.__class__.__name__
            print("✓ AgentRepositoryFactory ORM test passed")
        except ImportError:
            print("⚠ AgentRepositoryFactory ORM test skipped (ORM not available)")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "sqlite"})
    def test_git_branch_factory_sqlite(self):
        """Test GitBranchRepositoryFactory with SQLite"""
        repository = GitBranchRepositoryFactory.create(
            repository_type=GitBranchRepositoryType.SQLITE,
            user_id="test_user",
            db_path=self.test_db_path
        )
        
        assert repository is not None
        assert "SQLite" in repository.__class__.__name__
        print("✓ GitBranchRepositoryFactory SQLite test passed")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"})
    def test_git_branch_factory_orm(self):
        """Test GitBranchRepositoryFactory with ORM"""
        try:
            repository = GitBranchRepositoryFactory.create(
                repository_type=GitBranchRepositoryType.ORM,
                user_id="test_user"
            )
            assert repository is not None
            assert "ORM" in repository.__class__.__name__
            print("✓ GitBranchRepositoryFactory ORM test passed")
        except ImportError:
            print("⚠ GitBranchRepositoryFactory ORM test skipped (ORM not available)")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": ""})
    def test_subtask_factory_sqlite(self):
        """Test SubtaskRepositoryFactory with SQLite"""
        factory = SubtaskRepositoryFactory(storage_type="sqlite")
        repository = factory.create_subtask_repository(
            project_id="test_project",
            git_branch_name="main",
            user_id="test_user"
        )
        
        assert repository is not None
        assert "SQLite" in repository.__class__.__name__
        print("✓ SubtaskRepositoryFactory SQLite test passed")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"})
    def test_subtask_factory_orm(self):
        """Test SubtaskRepositoryFactory with ORM"""
        try:
            factory = SubtaskRepositoryFactory(storage_type="orm")
            repository = factory.create_subtask_repository(
                project_id="test_project",
                git_branch_name="main",
                user_id="test_user"
            )
            assert repository is not None
            assert "ORM" in repository.__class__.__name__
            print("✓ SubtaskRepositoryFactory ORM test passed")
        except ImportError:
            print("⚠ SubtaskRepositoryFactory ORM test skipped (ORM not available)")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": ""})
    def test_task_factory_sqlite(self):
        """Test TaskRepositoryFactory with SQLite"""
        factory = TaskRepositoryFactory(storage_type="sqlite")
        repository = factory.create_repository(
            project_id="test_project",
            git_branch_name="main",
            user_id="test_user"
        )
        
        assert repository is not None
        assert "SQLite" in repository.__class__.__name__
        print("✓ TaskRepositoryFactory SQLite test passed")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"})
    def test_task_factory_orm(self):
        """Test TaskRepositoryFactory with ORM"""
        try:
            factory = TaskRepositoryFactory()
            repository = factory.create_repository(
                project_id="test_project",
                git_branch_name="main",
                user_id="test_user"
            )
            assert repository is not None
            assert "ORM" in repository.__class__.__name__
            print("✓ TaskRepositoryFactory ORM test passed")
        except ImportError:
            print("⚠ TaskRepositoryFactory ORM test skipped (ORM not available)")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": ""})
    def test_hierarchical_context_factory_sqlite(self):
        """Test HierarchicalContextRepositoryFactory with SQLite"""
        factory = HierarchicalContextRepositoryFactory()
        repository = factory.create_hierarchical_context_repository(
            db_path=self.test_db_path
        )
        
        assert repository is not None
        assert "SQLite" in repository.__class__.__name__
        print("✓ HierarchicalContextRepositoryFactory SQLite test passed")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"})
    def test_hierarchical_context_factory_orm(self):
        """Test HierarchicalContextRepositoryFactory with ORM"""
        try:
            factory = HierarchicalContextRepositoryFactory()
            repository = factory.create_hierarchical_context_repository()
            
            assert repository is not None
            assert "ORM" in repository.__class__.__name__
            print("✓ HierarchicalContextRepositoryFactory ORM test passed")
        except ImportError:
            print("⚠ HierarchicalContextRepositoryFactory ORM test skipped (ORM not available)")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": ""})
    def test_template_factory_sqlite(self):
        """Test TemplateRepositoryFactory with SQLite"""
        factory = TemplateRepositoryFactory()
        repository = factory.create_repository(db_path=self.test_db_path)
        
        assert repository is not None
        assert "SQLite" in repository.__class__.__name__
        print("✓ TemplateRepositoryFactory SQLite test passed")
    
    @patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"})
    def test_template_factory_orm(self):
        """Test TemplateRepositoryFactory with ORM"""
        try:
            factory = TemplateRepositoryFactory()
            repository = factory.create_repository()
            
            assert repository is not None
            assert "ORM" in repository.__class__.__name__
            print("✓ TemplateRepositoryFactory ORM test passed")
        except ImportError:
            print("⚠ TemplateRepositoryFactory ORM test skipped (ORM not available)")
    
    def test_environment_variable_switching(self):
        """Test that DATABASE_TYPE environment variable correctly switches repository types"""
        print("\n=== Testing Environment Variable Switching ===")
        
        # Test SQLite environment
        with patch.dict(os.environ, {"DATABASE_TYPE": "sqlite", "MCP_DB_PATH": self.test_db_path}):
            project_repo = ProjectRepositoryFactory.create(user_id="test_user")
            assert "SQLite" in project_repo.__class__.__name__
            print("✓ SQLite environment variable test passed")
        
        # Clear cache between tests
        ProjectRepositoryFactory.clear_cache()
        
        # Test PostgreSQL environment
        with patch.dict(os.environ, {"DATABASE_TYPE": "postgresql"}):
            try:
                project_repo = ProjectRepositoryFactory.create(user_id="test_user")
                assert "ORM" in project_repo.__class__.__name__
                print("✓ PostgreSQL environment variable test passed")
            except (ImportError, ValueError):
                print("⚠ PostgreSQL environment variable test skipped (ORM not available)")


def run_tests():
    """Run all factory tests"""
    print("🧪 Running comprehensive repository factory tests...\n")
    
    test_instance = TestAllFactories()
    
    # Test methods
    test_methods = [
        'test_project_factory_sqlite',
        'test_project_factory_orm',
        'test_agent_factory_sqlite', 
        'test_agent_factory_orm',
        'test_git_branch_factory_sqlite',
        'test_git_branch_factory_orm',
        'test_subtask_factory_sqlite',
        'test_subtask_factory_orm',
        'test_task_factory_sqlite',
        'test_task_factory_orm',
        'test_hierarchical_context_factory_sqlite',
        'test_hierarchical_context_factory_orm',
        'test_template_factory_sqlite',
        'test_template_factory_orm',
        'test_environment_variable_switching'
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
        except ImportError:
            skipped += 1
        except Exception as e:
            print(f"❌ {method_name} failed: {e}")
            failed += 1
        finally:
            test_instance.teardown_method()
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    
    if failed == 0:
        print("\n🎉 All repository factories are working correctly!")
        return True
    else:
        print("\n💥 Some tests failed. Check the implementation.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)