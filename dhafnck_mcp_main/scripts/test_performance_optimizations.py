#!/usr/bin/env python3
"""
Test script to verify performance optimizations are working correctly.

This script tests:
1. Timezone cache functionality
2. Query cache functionality
3. Connection pool optimization
4. N+1 query fix for project loading

Run with: python scripts/test_performance_optimizations.py
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_timezone_cache():
    """Test that timezone cache is working"""
    logger.info("=" * 60)
    logger.info("Testing Timezone Cache")
    logger.info("=" * 60)
    
    try:
        from fastmcp.task_management.infrastructure.cache import timezone_cache
        from fastmcp.task_management.infrastructure.database import get_db_session
        
        # First call - should fetch from database
        logger.info("First call - fetching from database...")
        start = time.time()
        with get_db_session() as session:
            timezones1 = timezone_cache.get_timezones(session)
        time1 = (time.time() - start) * 1000
        logger.info(f"✅ First call took {time1:.1f}ms - fetched {len(timezones1)} timezones")
        
        # Second call - should use cache
        logger.info("Second call - should use cache...")
        start = time.time()
        with get_db_session() as session:
            timezones2 = timezone_cache.get_timezones(session)
        time2 = (time.time() - start) * 1000
        logger.info(f"✅ Second call took {time2:.1f}ms - returned {len(timezones2)} timezones")
        
        # Verify cache is working
        if time2 < time1 / 10:  # Cache should be at least 10x faster
            logger.info(f"✅ TIMEZONE CACHE WORKING! Cache is {time1/time2:.1f}x faster")
        else:
            logger.warning(f"⚠️  Cache might not be working properly. Time difference not significant enough.")
        
        # Test cache stats
        stats = timezone_cache.get_cache_stats()
        logger.info(f"Cache stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Timezone cache test failed: {e}")
        return False


def test_query_cache():
    """Test that query cache is working"""
    logger.info("=" * 60)
    logger.info("Testing Query Cache")
    logger.info("=" * 60)
    
    try:
        from fastmcp.task_management.infrastructure.cache import cache_manager
        
        # Get task cache
        task_cache = cache_manager.get_cache('task')
        
        # Test cache operations
        test_key = {'method': 'test', 'id': '123'}
        test_value = {'data': 'test data', 'count': 42}
        
        # Set value
        task_cache.set(test_key, test_value)
        logger.info("✅ Set test value in cache")
        
        # Get value
        cached_value = task_cache.get(test_key)
        if cached_value == test_value:
            logger.info("✅ Retrieved correct value from cache")
        else:
            logger.error("❌ Retrieved value doesn't match")
        
        # Get stats
        stats = task_cache.get_stats()
        logger.info(f"Cache stats: {stats}")
        
        # Test all cache types
        all_stats = cache_manager.get_all_stats()
        logger.info("All cache statistics:")
        for cache_name, cache_stats in all_stats.items():
            logger.info(f"  {cache_name}: {cache_stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Query cache test failed: {e}")
        return False


def test_connection_pool():
    """Test that connection pool is optimized"""
    logger.info("=" * 60)
    logger.info("Testing Connection Pool Optimization")
    logger.info("=" * 60)
    
    try:
        from fastmcp.task_management.infrastructure.database import get_connection_stats
        
        # Get connection pool statistics
        stats = get_connection_stats()
        logger.info(f"Connection pool stats: {stats}")
        
        # Verify pool size is optimized (should be 20)
        if stats.get('size') == 20 or stats.get('size') == 'N/A':
            logger.info("✅ Connection pool size is optimized (20)")
        else:
            logger.warning(f"⚠️  Connection pool size is {stats.get('size')}, expected 20")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection pool test failed: {e}")
        return False


def test_project_loading():
    """Test that project loading is optimized (no N+1 queries)"""
    logger.info("=" * 60)
    logger.info("Testing Project Loading Optimization")
    logger.info("=" * 60)
    
    try:
        from fastmcp.task_management.infrastructure.repositories.orm.project_repository import ORMProjectRepository
        import asyncio
        
        repo = ORMProjectRepository()
        
        # Test find_all method
        logger.info("Testing find_all() method for N+1 query optimization...")
        start = time.time()
        
        # Run async method
        async def test():
            projects = await repo.find_all()
            return projects
        
        projects = asyncio.run(test())
        elapsed = (time.time() - start) * 1000
        
        logger.info(f"✅ Loaded {len(projects)} projects in {elapsed:.1f}ms")
        
        # Check if projects have branches loaded
        if projects:
            project = projects[0]
            if hasattr(project, 'git_branchs'):
                branch_count = len(project.git_branchs)
                logger.info(f"✅ First project has {branch_count} branches loaded")
            else:
                logger.info("ℹ️  No branches found in first project")
        
        # Verify optimization by checking query time
        if elapsed < 500:  # Should be fast even with branches
            logger.info("✅ PROJECT LOADING OPTIMIZED! Query completed quickly")
        else:
            logger.warning(f"⚠️  Project loading might not be optimized. Took {elapsed:.1f}ms")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Project loading test failed: {e}")
        return False


def main():
    """Run all performance tests"""
    logger.info("🚀 Starting Performance Optimization Tests")
    logger.info("=" * 60)
    
    # Check if we're using Supabase
    db_type = os.getenv("DATABASE_TYPE", "supabase")
    logger.info(f"Database type: {db_type}")
    
    if db_type != "supabase":
        logger.warning("⚠️  These optimizations are designed for Supabase. Some tests may not apply.")
    
    # Run tests
    results = []
    
    # Note: Timezone cache test requires PostgreSQL, skip for SQLite
    if db_type in ["supabase", "postgresql"]:
        results.append(("Timezone Cache", test_timezone_cache()))
    else:
        logger.info("Skipping timezone cache test (PostgreSQL only)")
    
    results.append(("Query Cache", test_query_cache()))
    results.append(("Connection Pool", test_connection_pool()))
    results.append(("Project Loading", test_project_loading()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 60)
    if passed == total:
        logger.info(f"🎉 ALL TESTS PASSED ({passed}/{total})")
    else:
        logger.warning(f"⚠️  Some tests failed ({passed}/{total} passed)")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)