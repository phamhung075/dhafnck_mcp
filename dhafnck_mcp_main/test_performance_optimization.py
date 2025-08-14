#!/usr/bin/env python3
"""Test script for task loading performance optimization"""

import time
import os
import sys
import logging
from typing import Dict, Any, List

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_performance_improvements():
    """Test the performance improvements for task loading"""
    
    try:
        # Import required modules
        from fastmcp.task_management.infrastructure.database.database_config import get_db_config
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        from fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository import OptimizedTaskRepository
        from fastmcp.task_management.infrastructure.performance.task_performance_optimizer import get_performance_optimizer
        from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
        
        # Get database configuration
        db_config = get_db_config()
        
        # Create task repositories
        standard_repo = ORMTaskRepository()
        optimized_repo = OptimizedTaskRepository()
        
        # Get performance optimizer
        optimizer = get_performance_optimizer()
        
        print("\n" + "="*80)
        print("TASK LOADING PERFORMANCE OPTIMIZATION TEST")
        print("="*80)
        
        # Test configuration
        git_branch_id = "test-fix-branch"  # Use the test fix branch
        test_limit = 50
        
        # Step 1: Create indexes for optimization
        print("\n1. Creating optimized database indexes...")
        with db_config.SessionLocal() as session:
            created_indexes = optimizer.create_optimized_indexes(session)
            print(f"   Created {len(created_indexes)} indexes: {', '.join(created_indexes)}")
        
        # Step 2: Test standard repository performance
        print("\n2. Testing STANDARD repository performance...")
        standard_start = time.time()
        
        # List tasks using standard repository
        standard_tasks = standard_repo.list_tasks(
            status=None,
            priority=None,
            assignee_id=None,
            limit=test_limit
        )
        
        standard_time = time.time() - standard_start
        print(f"   Standard repository: {len(standard_tasks)} tasks loaded in {standard_time:.3f} seconds")
        
        # Step 3: Test optimized repository performance (without cache)
        print("\n3. Testing OPTIMIZED repository performance (no cache)...")
        optimized_start = time.time()
        
        # List tasks using optimized repository
        optimized_tasks = optimized_repo.list_tasks(
            status=None,
            priority=None,
            assignee_id=None,
            limit=test_limit,
            use_cache=False  # Don't use cache for first test
        )
        
        optimized_time = time.time() - optimized_start
        print(f"   Optimized repository: {len(optimized_tasks)} tasks loaded in {optimized_time:.3f} seconds")
        
        # Step 4: Test optimized repository with cache
        print("\n4. Testing OPTIMIZED repository performance (with cache)...")
        cached_start = time.time()
        
        # List tasks again (should use cache)
        cached_tasks = optimized_repo.list_tasks(
            status=None,
            priority=None,
            assignee_id=None,
            limit=test_limit,
            use_cache=True
        )
        
        cached_time = time.time() - cached_start
        print(f"   Cached repository: {len(cached_tasks)} tasks loaded in {cached_time:.3f} seconds")
        
        # Step 5: Test minimal data loading
        print("\n5. Testing MINIMAL data loading performance...")
        minimal_start = time.time()
        
        # List minimal task data
        minimal_tasks = optimized_repo.list_tasks_minimal(
            status=None,
            priority=None,
            assignee_id=None,
            limit=test_limit
        )
        
        minimal_time = time.time() - minimal_start
        print(f"   Minimal data: {len(minimal_tasks)} tasks loaded in {minimal_time:.3f} seconds")
        
        # Step 6: Analyze query performance
        print("\n6. Analyzing query performance...")
        with db_config.SessionLocal() as session:
            analysis = optimizer.analyze_query_performance(session)
            
            if analysis['slow_queries']:
                print("   Slow queries detected:")
                for query in analysis['slow_queries'][:3]:
                    print(f"     - {query['query'][:50]}... (avg: {query['avg_time_ms']:.2f}ms)")
            
            if analysis['recommendations']:
                print("   Performance recommendations:")
                for rec in analysis['recommendations']:
                    print(f"     - {rec}")
        
        # Performance Summary
        print("\n" + "="*80)
        print("PERFORMANCE SUMMARY")
        print("="*80)
        
        # Calculate improvements
        if standard_time > 0:
            optimized_improvement = ((standard_time - optimized_time) / standard_time) * 100
            cached_improvement = ((standard_time - cached_time) / standard_time) * 100
            minimal_improvement = ((standard_time - minimal_time) / standard_time) * 100
        else:
            optimized_improvement = 0
            cached_improvement = 0
            minimal_improvement = 0
        
        print(f"\nPerformance Metrics:")
        print(f"  Standard Query:     {standard_time:.3f}s (baseline)")
        print(f"  Optimized Query:    {optimized_time:.3f}s ({optimized_improvement:+.1f}% improvement)")
        print(f"  Cached Query:       {cached_time:.3f}s ({cached_improvement:+.1f}% improvement)")
        print(f"  Minimal Data Query: {minimal_time:.3f}s ({minimal_improvement:+.1f}% improvement)")
        
        print(f"\nSpeed Improvements:")
        if optimized_time > 0:
            print(f"  Optimized is {standard_time/optimized_time:.1f}x faster than standard")
        if cached_time > 0:
            print(f"  Cached is {standard_time/cached_time:.1f}x faster than standard")
        if minimal_time > 0:
            print(f"  Minimal is {standard_time/minimal_time:.1f}x faster than standard")
        
        # Test pagination metadata
        print("\n7. Testing pagination metadata...")
        pagination = optimizer.get_pagination_metadata(
            total_count=150,
            limit=50,
            offset=50
        )
        print(f"   Pagination: Page {pagination['current_page']} of {pagination['total_pages']}")
        print(f"   Has next: {pagination['has_next']}, Has prev: {pagination['has_prev']}")
        
        print("\n" + "="*80)
        print("✅ Performance optimization test completed successfully!")
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_performance_improvements()
    sys.exit(0 if success else 1)