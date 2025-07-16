"""
Test suite for ORM Hierarchical Context Repository

This test suite verifies the ORM implementation of the hierarchical context repository,
ensuring it maintains compatibility with the existing SQLite implementation while
providing the same functionality through SQLAlchemy ORM.
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from typing import Dict, Any

from fastmcp.task_management.infrastructure.repositories.orm.hierarchical_context_repository import ORMHierarchicalContextRepository
from fastmcp.task_management.infrastructure.database.database_config import get_db_config, Base
from fastmcp.task_management.infrastructure.database.models import (
    GlobalContext, ProjectContext, TaskContext, ContextDelegation, ContextInheritanceCache
)


class TestORMHierarchicalContextRepository:
    """Test suite for ORM Hierarchical Context Repository"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with in-memory SQLite database"""
        # Set environment variables for testing
        os.environ["DATABASE_TYPE"] = "sqlite"
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        
        # Create test database
        self.db_config = get_db_config()
        Base.metadata.create_all(bind=self.db_config.engine)
        
        # Create repository instance
        self.repository = ORMHierarchicalContextRepository()
        
        yield
        
        # Cleanup
        Base.metadata.drop_all(bind=self.db_config.engine)
        self.db_config.close()

    def test_create_global_context(self):
        """Test creating a global context"""
        global_id = "test_global"
        data = {
            "organization_id": "test_org",
            "autonomous_rules": {"ai_enabled": True},
            "security_policies": {"encryption": "required"},
            "coding_standards": {"style": "PEP8"},
            "workflow_templates": {"default": "agile"},
            "delegation_rules": {"auto_approve": False}
        }
        
        result = self.repository.create_global_context(global_id, data)
        
        assert result is not None
        assert result["id"] == global_id
        assert result["organization_id"] == "test_org"
        assert result["autonomous_rules"]["ai_enabled"] is True
        assert result["security_policies"]["encryption"] == "required"

    def test_get_global_context(self):
        """Test retrieving a global context"""
        global_id = "test_global"
        data = {
            "organization_id": "test_org",
            "autonomous_rules": {"ai_enabled": True}
        }
        
        # Create context first
        self.repository.create_global_context(global_id, data)
        
        # Retrieve context
        result = self.repository.get_global_context(global_id)
        
        assert result is not None
        assert result["id"] == global_id
        assert result["organization_id"] == "test_org"
        assert result["autonomous_rules"]["ai_enabled"] is True

    def test_get_nonexistent_global_context(self):
        """Test retrieving a non-existent global context"""
        result = self.repository.get_global_context("nonexistent")
        assert result is None

    def test_update_global_context(self):
        """Test updating a global context"""
        global_id = "test_global"
        data = {
            "organization_id": "test_org",
            "autonomous_rules": {"ai_enabled": True}
        }
        
        # Create context first
        self.repository.create_global_context(global_id, data)
        
        # Update context
        updates = {
            "autonomous_rules": {"ai_enabled": False, "auto_task_creation": True},
            "security_policies": {"encryption": "required"}
        }
        
        result = self.repository.update_global_context(global_id, updates)
        assert result is True
        
        # Verify updates
        updated_context = self.repository.get_global_context(global_id)
        assert updated_context["autonomous_rules"]["ai_enabled"] is False
        assert updated_context["autonomous_rules"]["auto_task_creation"] is True
        assert updated_context["security_policies"]["encryption"] == "required"

    def test_delete_global_context(self):
        """Test deleting a global context"""
        global_id = "test_global"
        data = {"organization_id": "test_org"}
        
        # Create context first
        self.repository.create_global_context(global_id, data)
        
        # Delete context
        result = self.repository.delete_global_context(global_id)
        assert result is True
        
        # Verify deletion
        deleted_context = self.repository.get_global_context(global_id)
        assert deleted_context is None

    def test_list_global_contexts(self):
        """Test listing all global contexts"""
        # Create multiple contexts
        for i in range(3):
            self.repository.create_global_context(f"global_{i}", {"organization_id": f"org_{i}"})
        
        contexts = self.repository.list_global_contexts()
        
        assert len(contexts) == 3
        assert all(ctx["id"].startswith("global_") for ctx in contexts)

    def test_create_project_context(self):
        """Test creating a project context"""
        project_id = "test_project"
        data = {
            "parent_global_id": "global_singleton",
            "team_preferences": {"notification_enabled": True},
            "technology_stack": {"language": "python"},
            "project_workflow": {"methodology": "agile"},
            "local_standards": {"code_review": "required"},
            "global_overrides": {"priority": "high"},
            "delegation_rules": {"auto_delegate": True}
        }
        
        result = self.repository.create_project_context(project_id, data)
        
        assert result is not None
        assert result["project_id"] == project_id
        assert result["parent_global_id"] == "global_singleton"
        assert result["team_preferences"]["notification_enabled"] is True

    def test_get_project_context(self):
        """Test retrieving a project context"""
        project_id = "test_project"
        data = {
            "team_preferences": {"notification_enabled": True}
        }
        
        # Create context first
        self.repository.create_project_context(project_id, data)
        
        # Retrieve context
        result = self.repository.get_project_context(project_id)
        
        assert result is not None
        assert result["project_id"] == project_id
        assert result["team_preferences"]["notification_enabled"] is True

    def test_update_project_context(self):
        """Test updating a project context"""
        project_id = "test_project"
        data = {"team_preferences": {"notification_enabled": True}}
        
        # Create context first
        self.repository.create_project_context(project_id, data)
        
        # Update context
        updates = {
            "team_preferences": {"notification_enabled": False, "slack_integration": True},
            "technology_stack": {"language": "python", "framework": "fastapi"}
        }
        
        result = self.repository.update_project_context(project_id, updates)
        assert result is True
        
        # Verify updates
        updated_context = self.repository.get_project_context(project_id)
        assert updated_context["team_preferences"]["notification_enabled"] is False
        assert updated_context["team_preferences"]["slack_integration"] is True
        assert updated_context["technology_stack"]["language"] == "python"

    def test_create_task_context(self):
        """Test creating a task context"""
        task_id = "test_task"
        data = {
            "parent_project_id": "test_project",
            "parent_project_context_id": "test_project",
            "task_data": {"priority": "high"},
            "local_overrides": {"timeout": 3600},
            "implementation_notes": {"approach": "iterative"},
            "delegation_triggers": {"completion_threshold": 90}
        }
        
        result = self.repository.create_task_context(task_id, data)
        
        assert result is not None
        assert result["task_id"] == task_id
        assert result["parent_project_id"] == "test_project"
        assert result["task_data"]["priority"] == "high"

    def test_get_task_context(self):
        """Test retrieving a task context"""
        task_id = "test_task"
        data = {
            "parent_project_id": "test_project",
            "task_data": {"priority": "high"}
        }
        
        # Create context first
        self.repository.create_task_context(task_id, data)
        
        # Retrieve context
        result = self.repository.get_task_context(task_id)
        
        assert result is not None
        assert result["task_id"] == task_id
        assert result["task_data"]["priority"] == "high"

    def test_update_task_context(self):
        """Test updating a task context"""
        task_id = "test_task"
        data = {
            "parent_project_id": "test_project",
            "task_data": {"priority": "high"}
        }
        
        # Create context first
        self.repository.create_task_context(task_id, data)
        
        # Update context
        updates = {
            "task_data": {"priority": "medium", "estimated_hours": 8},
            "local_overrides": {"timeout": 7200}
        }
        
        result = self.repository.update_task_context(task_id, updates)
        assert result is True
        
        # Verify updates
        updated_context = self.repository.get_task_context(task_id)
        assert updated_context["task_data"]["priority"] == "medium"
        assert updated_context["task_data"]["estimated_hours"] == 8
        assert updated_context["local_overrides"]["timeout"] == 7200

    @pytest.mark.asyncio
    async def test_store_delegation(self):
        """Test storing a delegation"""
        delegation_data = {
            "source_level": "task",
            "source_id": "task_1",
            "target_level": "project",
            "target_id": "project_1",
            "delegated_data": {"pattern": "singleton"},
            "reason": "Reusable pattern identified",
            "trigger_type": "manual"
        }
        
        delegation_id = await self.repository.store_delegation(delegation_data)
        
        assert delegation_id is not None
        assert isinstance(delegation_id, str)
        
        # Verify delegation was stored
        stored_delegation = await self.repository.get_delegation(delegation_id)
        assert stored_delegation is not None
        assert stored_delegation["source_level"] == "task"
        assert stored_delegation["target_level"] == "project"
        assert stored_delegation["delegated_data"]["pattern"] == "singleton"

    @pytest.mark.asyncio
    async def test_get_delegations_with_filters(self):
        """Test retrieving delegations with filters"""
        # Create multiple delegations
        delegation_data_1 = {
            "source_level": "task",
            "source_id": "task_1",
            "target_level": "project",
            "target_id": "project_1",
            "delegated_data": {"pattern": "singleton"},
            "reason": "Test delegation 1",
            "trigger_type": "manual"
        }
        
        delegation_data_2 = {
            "source_level": "project",
            "source_id": "project_1",
            "target_level": "global",
            "target_id": "global_singleton",
            "delegated_data": {"pattern": "factory"},
            "reason": "Test delegation 2",
            "trigger_type": "auto_pattern"
        }
        
        await self.repository.store_delegation(delegation_data_1)
        await self.repository.store_delegation(delegation_data_2)
        
        # Test filter by source level
        task_delegations = await self.repository.get_delegations({"source_level": "task"})
        assert len(task_delegations) == 1
        assert task_delegations[0]["source_level"] == "task"
        
        # Test filter by trigger type
        manual_delegations = await self.repository.get_delegations({"trigger_type": "manual"})
        assert len(manual_delegations) == 1
        assert manual_delegations[0]["trigger_type"] == "manual"

    @pytest.mark.asyncio
    async def test_update_delegation(self):
        """Test updating a delegation"""
        delegation_data = {
            "source_level": "task",
            "source_id": "task_1",
            "target_level": "project",
            "target_id": "project_1",
            "delegated_data": {"pattern": "singleton"},
            "reason": "Test delegation",
            "trigger_type": "manual"
        }
        
        delegation_id = await self.repository.store_delegation(delegation_data)
        
        # Update delegation
        updates = {
            "processed": True,
            "approved": True,
            "processed_by": "system"
        }
        
        result = await self.repository.update_delegation(delegation_id, updates)
        assert result is True
        
        # Verify updates
        updated_delegation = await self.repository.get_delegation(delegation_id)
        assert updated_delegation["processed"] is True
        assert updated_delegation["approved"] is True
        assert updated_delegation["processed_by"] == "system"

    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """Test cache entry operations"""
        cache_data = {
            "context_id": "test_context",
            "context_level": "task",
            "resolved_context": {"key": "value"},
            "dependencies_hash": "abc123",
            "resolution_path": "global->project->task",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": datetime.now(timezone.utc).isoformat(),
            "hit_count": 1,
            "last_hit": datetime.now(timezone.utc).isoformat(),
            "cache_size_bytes": 1024,
            "invalidated": False
        }
        
        # Store cache entry
        result = await self.repository.store_cache_entry(cache_data)
        assert result is True
        
        # Retrieve cache entry
        retrieved_cache = await self.repository.get_cache_entry("task", "test_context")
        assert retrieved_cache is not None
        assert retrieved_cache["context_id"] == "test_context"
        assert retrieved_cache["resolved_context"]["key"] == "value"
        
        # Invalidate cache entry
        result = await self.repository.invalidate_cache_entry("task", "test_context", "Test invalidation")
        assert result is True
        
        # Verify invalidation
        invalidated_cache = await self.repository.get_cache_entry("task", "test_context")
        assert invalidated_cache["invalidated"] is True
        assert invalidated_cache["invalidation_reason"] == "Test invalidation"

    @pytest.mark.asyncio
    async def test_cache_statistics(self):
        """Test cache statistics"""
        # Create some cache entries
        for i in range(3):
            cache_data = {
                "context_id": f"context_{i}",
                "context_level": "task",
                "resolved_context": {"key": f"value_{i}"},
                "dependencies_hash": f"hash_{i}",
                "resolution_path": "global->project->task",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": datetime.now(timezone.utc).isoformat(),
                "hit_count": i + 1,
                "last_hit": datetime.now(timezone.utc).isoformat(),
                "cache_size_bytes": 1024 * (i + 1),
                "invalidated": i == 2  # Invalidate last entry
            }
            await self.repository.store_cache_entry(cache_data)
        
        # Get statistics
        stats = await self.repository.get_cache_statistics()
        
        assert stats["total_entries"] == 3
        assert stats["total_size_bytes"] == 1024 + 2048 + 3072  # Sum of cache sizes
        assert stats["total_hits"] == 1 + 2 + 3  # Sum of hit counts
        assert stats["invalidated_count"] == 1

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality"""
        # Create some test data
        self.repository.create_global_context("test_global", {"organization_id": "test_org"})
        self.repository.create_project_context("test_project", {"team_preferences": {}})
        
        # Run health check
        health_status = await self.repository.health_check()
        
        assert health_status["status"] == "healthy"
        assert health_status["database"]["connected"] is True
        assert health_status["database"]["type"] == "orm"
        assert health_status["database"]["row_counts"]["global_contexts"] == 1
        assert health_status["database"]["row_counts"]["project_contexts"] == 1

    def test_resolve_context_inheritance(self):
        """Test context resolution with inheritance"""
        # Create global context
        self.repository.create_global_context("global_singleton", {
            "autonomous_rules": {"ai_enabled": True, "auto_task_creation": True},
            "security_policies": {"encryption": "required"}
        })
        
        # Create project context
        self.repository.create_project_context("test_project", {
            "parent_global_id": "global_singleton",
            "team_preferences": {"notification_enabled": True},
            "technology_stack": {"language": "python"},
            "inheritance_disabled": False
        })
        
        # Create task context
        self.repository.create_task_context("test_task", {
            "parent_project_id": "test_project",
            "parent_project_context_id": "test_project",
            "task_data": {"priority": "high"},
            "local_overrides": {"timeout": 3600},
            "inheritance_disabled": False
        })
        
        # Test task context resolution with inheritance
        resolved_task = self.repository.resolve_context("task", "test_task", include_inheritance=True)
        
        # Should include all levels
        assert "autonomous_rules" in resolved_task  # From global
        assert "team_preferences" in resolved_task  # From project
        assert "task_data" in resolved_task  # From task
        assert resolved_task["task_data"]["priority"] == "high"
        
        # Test project context resolution with inheritance
        resolved_project = self.repository.resolve_context("project", "test_project", include_inheritance=True)
        
        # Should include global and project
        assert "autonomous_rules" in resolved_project  # From global
        assert "team_preferences" in resolved_project  # From project
        assert resolved_project["team_preferences"]["notification_enabled"] is True

    def test_context_delegation(self):
        """Test context delegation between levels"""
        # Create source task context
        self.repository.create_task_context("source_task", {
            "parent_project_id": "test_project",
            "parent_project_context_id": "test_project",
            "task_data": {"reusable_pattern": "singleton_implementation"}
        })
        
        # Create target project context
        self.repository.create_project_context("target_project", {
            "team_preferences": {"notification_enabled": True}
        })
        
        # Delegate pattern from task to project
        delegate_data = {"pattern": "singleton_implementation", "usage": "common"}
        result = self.repository.delegate_context(
            "task", "source_task",
            "project", "target_project",
            delegate_data, "Reusable pattern identified"
        )
        
        assert result is True
        
        # Verify delegation was applied
        updated_project = self.repository.get_project_context("target_project")
        assert "pattern" in updated_project["local_standards"]
        assert updated_project["local_standards"]["pattern"] == "singleton_implementation"

    def test_search_contexts(self):
        """Test searching contexts across all levels"""
        # Create contexts with searchable content
        self.repository.create_global_context("search_global", {
            "autonomous_rules": {"search_term": "findable_value"}
        })
        
        self.repository.create_project_context("search_project", {
            "team_preferences": {"search_term": "findable_value"}
        })
        
        self.repository.create_task_context("search_task", {
            "parent_project_id": "test_project",
            "task_data": {"search_term": "findable_value"}
        })
        
        # Search across all levels
        results = self.repository.search_contexts("findable_value")
        
        assert len(results) == 3
        levels = [result["_level"] for result in results]
        assert "global" in levels
        assert "project" in levels
        assert "task" in levels

    def test_get_context_hierarchy(self):
        """Test getting complete context hierarchy"""
        # Create hierarchy
        self.repository.create_global_context("global_singleton", {
            "autonomous_rules": {"ai_enabled": True}
        })
        
        self.repository.create_project_context("hierarchy_project", {
            "parent_global_id": "global_singleton",
            "team_preferences": {"notification_enabled": True}
        })
        
        self.repository.create_task_context("hierarchy_task", {
            "parent_project_id": "hierarchy_project",
            "parent_project_context_id": "hierarchy_project",
            "task_data": {"priority": "high"}
        })
        
        # Get hierarchy for task
        hierarchy = self.repository.get_context_hierarchy("task", "hierarchy_task")
        
        assert hierarchy["global"] is not None
        assert hierarchy["project"] is not None
        assert hierarchy["task"] is not None
        assert hierarchy["global"]["autonomous_rules"]["ai_enabled"] is True
        assert hierarchy["project"]["team_preferences"]["notification_enabled"] is True
        assert hierarchy["task"]["task_data"]["priority"] == "high"

    def test_merge_contexts(self):
        """Test merging multiple contexts"""
        global_context = {
            "_level": "global",
            "autonomous_rules": {"ai_enabled": True},
            "security_policies": {"encryption": "required"}
        }
        
        project_context = {
            "_level": "project",
            "autonomous_rules": {"auto_task_creation": True},  # Should merge with global
            "team_preferences": {"notification_enabled": True}
        }
        
        task_context = {
            "_level": "task",
            "autonomous_rules": {"context_switching": True},  # Should merge with previous
            "task_data": {"priority": "high"}
        }
        
        merged = self.repository.merge_contexts([global_context, project_context, task_context])
        
        # Should have merged autonomous_rules
        assert merged["autonomous_rules"]["ai_enabled"] is True
        assert merged["autonomous_rules"]["auto_task_creation"] is True
        assert merged["autonomous_rules"]["context_switching"] is True
        
        # Should have all other fields
        assert merged["security_policies"]["encryption"] == "required"
        assert merged["team_preferences"]["notification_enabled"] is True
        assert merged["task_data"]["priority"] == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])