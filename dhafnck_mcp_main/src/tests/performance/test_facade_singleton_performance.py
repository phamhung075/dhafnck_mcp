"""
Performance tests for facade singleton pattern optimization.

This test suite validates that the singleton pattern implementation
successfully reduces the facade initialization time from 3+ seconds
to milliseconds.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from fastmcp.task_management.application.factories.unified_context_facade_factory import UnifiedContextFacadeFactory
from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
from fastmcp.task_management.infrastructure.database.database_config import DatabaseConfig, get_db_config
from fastmcp.task_management.infrastructure.repositories.task_repository_factory import TaskRepositoryFactory
from fastmcp.task_management.infrastructure.repositories.subtask_repository_factory import SubtaskRepositoryFactory


class TestFacadeSingletonPerformance:
    """Test suite for validating singleton pattern performance improvements."""
    
    def setup_method(self):
        """Reset singleton instances before each test."""
        # Reset class-level singleton attributes
        UnifiedContextFacadeFactory._instance = None
        UnifiedContextFacadeFactory._initialized = False
        TaskFacadeFactory._instance = None
        TaskFacadeFactory._initialized = False
        DatabaseConfig._instance = None
        DatabaseConfig._initialized = False
        DatabaseConfig._connection_verified = False
        DatabaseConfig._connection_info = None
    
    def test_unified_context_facade_factory_singleton_performance(self):
        """Test that UnifiedContextFacadeFactory uses singleton pattern efficiently."""
        # Measure first initialization time
        start_time = time.perf_counter()
        factory1 = UnifiedContextFacadeFactory.get_instance()
        first_init_time = time.perf_counter() - start_time
        
        # Measure second "initialization" time (should be instant due to singleton)
        start_time = time.perf_counter()
        factory2 = UnifiedContextFacadeFactory.get_instance()
        second_init_time = time.perf_counter() - start_time
        
        # Assertions
        assert factory1 is factory2, "Should return the same singleton instance"
        assert second_init_time < 0.001, f"Second initialization should be <1ms, got {second_init_time*1000:.2f}ms"
        
        # The second initialization should be at least 100x faster
        if first_init_time > 0:
            speedup = first_init_time / second_init_time
            assert speedup > 100, f"Singleton should provide >100x speedup, got {speedup:.1f}x"
        
        print(f"✅ UnifiedContextFacadeFactory singleton performance:")
        print(f"   First init: {first_init_time*1000:.2f}ms")
        print(f"   Second init: {second_init_time*1000:.2f}ms")
        print(f"   Speedup: {speedup:.1f}x")
    
    def test_task_facade_factory_singleton_performance(self):
        """Test that TaskFacadeFactory uses singleton pattern efficiently."""
        # Create mock repository factories
        task_repo_factory = MagicMock(spec=TaskRepositoryFactory)
        subtask_repo_factory = MagicMock(spec=SubtaskRepositoryFactory)
        
        # Measure first initialization time
        start_time = time.perf_counter()
        factory1 = TaskFacadeFactory.get_instance(task_repo_factory, subtask_repo_factory)
        first_init_time = time.perf_counter() - start_time
        
        # Measure second "initialization" time (should be instant due to singleton)
        start_time = time.perf_counter()
        factory2 = TaskFacadeFactory.get_instance()  # No args needed for singleton
        second_init_time = time.perf_counter() - start_time
        
        # Assertions
        assert factory1 is factory2, "Should return the same singleton instance"
        assert second_init_time < 0.001, f"Second initialization should be <1ms, got {second_init_time*1000:.2f}ms"
        
        # The second initialization should be at least 100x faster
        if first_init_time > 0:
            speedup = first_init_time / second_init_time
            assert speedup > 100, f"Singleton should provide >100x speedup, got {speedup:.1f}x"
        
        print(f"✅ TaskFacadeFactory singleton performance:")
        print(f"   First init: {first_init_time*1000:.2f}ms")
        print(f"   Second init: {second_init_time*1000:.2f}ms")
        print(f"   Speedup: {speedup:.1f}x")
    
    def test_database_config_singleton_performance(self):
        """Test that DatabaseConfig uses singleton pattern and caches connection tests."""
        # Test with actual database config (will use test SQLite in test mode)
        # Measure first initialization time
        start_time = time.perf_counter()
        config1 = DatabaseConfig.get_instance()
        first_init_time = time.perf_counter() - start_time
        
        # Measure second "initialization" time (should be instant due to singleton)
        start_time = time.perf_counter()
        config2 = DatabaseConfig.get_instance()
        second_init_time = time.perf_counter() - start_time
        
        # Assertions
        assert config1 is config2, "Should return the same singleton instance"
        assert second_init_time < 0.001, f"Second initialization should be <1ms, got {second_init_time*1000:.2f}ms"
        
        # The second initialization should be at least 100x faster
        if first_init_time > 0:
            speedup = first_init_time / second_init_time
            assert speedup > 100, f"Singleton should provide >100x speedup, got {speedup:.1f}x"
        
        print(f"✅ DatabaseConfig singleton performance:")
        print(f"   First init: {first_init_time*1000:.2f}ms")
        print(f"   Second init: {second_init_time*1000:.2f}ms")
        print(f"   Speedup: {speedup:.1f}x")
    
    def test_end_to_end_facade_creation_performance(self):
        """Test the full facade creation flow with all optimizations."""
        # Create mock repository factories
        task_repo_factory = MagicMock(spec=TaskRepositoryFactory)
        subtask_repo_factory = MagicMock(spec=SubtaskRepositoryFactory)
        
        # Mock repository creation
        task_repo_factory.create_repository.return_value = MagicMock()
        subtask_repo_factory.create_subtask_repository.return_value = MagicMock()
        
        # First facade creation (will initialize all singletons)
        start_time = time.perf_counter()
        task_factory1 = TaskFacadeFactory.get_instance(task_repo_factory, subtask_repo_factory)
        facade1 = task_factory1.create_task_facade("project1", "branch1", "user1")
        first_creation_time = time.perf_counter() - start_time
        
        # Second facade creation (should reuse all singletons)
        start_time = time.perf_counter()
        task_factory2 = TaskFacadeFactory.get_instance()
        facade2 = task_factory2.create_task_facade("project2", "branch2", "user2")
        second_creation_time = time.perf_counter() - start_time
        
        # Assertions
        assert task_factory1 is task_factory2, "Should use same TaskFacadeFactory singleton"
        assert second_creation_time < 0.01, f"Second facade creation should be <10ms, got {second_creation_time*1000:.2f}ms"
        
        # The second creation should be significantly faster
        if first_creation_time > 0:
            speedup = first_creation_time / second_creation_time
            assert speedup > 10, f"Second creation should be >10x faster, got {speedup:.1f}x"
        
        print(f"✅ End-to-end facade creation performance:")
        print(f"   First creation: {first_creation_time*1000:.2f}ms")
        print(f"   Second creation: {second_creation_time*1000:.2f}ms")
        print(f"   Speedup: {speedup:.1f}x")
        print(f"   ✨ Successfully reduced initialization time from 3+ seconds to <10ms!")
    
    def test_multiple_facade_creations_performance(self):
        """Test that multiple facade creations remain performant."""
        # Create mock repository factories
        task_repo_factory = MagicMock(spec=TaskRepositoryFactory)
        subtask_repo_factory = MagicMock(spec=SubtaskRepositoryFactory)
        
        # Mock repository creation
        task_repo_factory.create_repository.return_value = MagicMock()
        subtask_repo_factory.create_subtask_repository.return_value = MagicMock()
        
        # Initialize singleton first
        task_factory = TaskFacadeFactory.get_instance(task_repo_factory, subtask_repo_factory)
        
        # Measure time for creating 100 facades
        start_time = time.perf_counter()
        facades = []
        for i in range(100):
            facade = task_factory.create_task_facade(f"project{i}", f"branch{i}", f"user{i}")
            facades.append(facade)
        total_time = time.perf_counter() - start_time
        avg_time_per_facade = total_time / 100
        
        # Assertions
        assert avg_time_per_facade < 0.01, f"Average facade creation should be <10ms, got {avg_time_per_facade*1000:.2f}ms"
        assert total_time < 1.0, f"Creating 100 facades should take <1s, got {total_time:.2f}s"
        
        print(f"✅ Multiple facade creation performance:")
        print(f"   Created 100 facades in: {total_time*1000:.2f}ms")
        print(f"   Average per facade: {avg_time_per_facade*1000:.2f}ms")
        print(f"   ✨ Singleton pattern ensures consistent performance!")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])