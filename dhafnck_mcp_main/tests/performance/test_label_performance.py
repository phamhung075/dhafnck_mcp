#!/usr/bin/env python3
"""
Label Repository Performance Test
Test the performance of SQLite label repository operations
"""
import sys
import asyncio
import tempfile
import os
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.infrastructure.repositories.sqlite.label_repository import SQLiteLabelRepository
from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database


async def measure_time(operation_name, operation_func):
    """Measure execution time of an operation"""
    start_time = time.time()
    result = await operation_func()
    end_time = time.time()
    duration = end_time - start_time
    print(f"   {operation_name}: {duration:.4f}s")
    return result, duration


async def test_label_performance():
    """Test label repository performance"""
    print("⚡ Label Repository Performance Test")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database
        initialize_database(db_path)
        repo = SQLiteLabelRepository(db_path=db_path)
        
        # Test 1: Bulk label creation performance
        print("\n1️⃣  Testing bulk label creation performance...")
        
        async def create_bulk_labels():
            labels = [f"performance-test-{i}" for i in range(1000)]
            return await repo.validate_and_create_labels(labels)
        
        created_labels, duration = await measure_time("Create 1000 labels", create_bulk_labels)
        throughput = len(created_labels) / duration
        print(f"   Throughput: {throughput:.2f} labels/second")
        
        # Test 2: Search performance
        print("\n2️⃣  Testing search performance...")
        
        search_terms = ["performance", "test", "label", "custom", "bug"]
        total_search_time = 0
        
        for term in search_terms:
            async def search_operation():
                return await repo.search_labels(term, limit=50)
            
            results, duration = await measure_time(f"Search for '{term}'", search_operation)
            total_search_time += duration
            print(f"      Found {len(results)} results")
        
        avg_search_time = total_search_time / len(search_terms)
        print(f"   Average search time: {avg_search_time:.4f}s")
        
        # Test 3: Category filtering performance
        print("\n3️⃣  Testing category filtering performance...")
        
        categories = ["custom", "priority", "type", "component", "process", "status"]
        total_category_time = 0
        
        for category in categories:
            async def category_operation():
                return await repo.get_labels_by_category(category)
            
            results, duration = await measure_time(f"Get '{category}' labels", category_operation)
            total_category_time += duration
            print(f"      Found {len(results)} labels")
        
        avg_category_time = total_category_time / len(categories)
        print(f"   Average category query time: {avg_category_time:.4f}s")
        
        # Test 4: Usage count update performance
        print("\n4️⃣  Testing usage count update performance...")
        
        # Get random labels for testing
        all_labels = await repo.get_all_labels()
        test_labels = all_labels[:100]  # Test with 100 labels
        
        async def bulk_usage_update():
            await repo.update_label_usage(test_labels, increment=True)
        
        _, duration = await measure_time("Update usage for 100 labels", bulk_usage_update)
        throughput = len(test_labels) / duration
        print(f"   Throughput: {throughput:.2f} updates/second")
        
        # Test 5: Popular labels performance
        print("\n5️⃣  Testing popular labels query performance...")
        
        async def popular_labels_operation():
            return await repo.get_popular_labels(limit=50)
        
        popular_labels, duration = await measure_time("Get top 50 popular labels", popular_labels_operation)
        print(f"   Retrieved {len(popular_labels)} popular labels")
        
        # Test 6: Normalization performance
        print("\n6️⃣  Testing label normalization performance...")
        
        test_normalizations = [
            "Test   Label   With   Spaces",
            "UPPERCASE LABEL",
            "MiXeD cAsE lAbEl",
            "special!@#$%characters",
            "multiple---hyphens",
            "  leading-and-trailing-spaces  ",
        ] * 100  # Test 600 normalizations
        
        start_time = time.time()
        for label in test_normalizations:
            normalized = await repo.normalize_label(label)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = len(test_normalizations) / duration
        print(f"   Normalize {len(test_normalizations)} labels: {duration:.4f}s")
        print(f"   Throughput: {throughput:.2f} normalizations/second")
        
        # Test 7: Concurrent operations simulation
        print("\n7️⃣  Testing concurrent operations performance...")
        
        async def concurrent_operation(batch_id):
            """Simulate concurrent label operations"""
            # Create some labels
            labels = [f"concurrent-{batch_id}-{i}" for i in range(10)]
            await repo.validate_and_create_labels(labels)
            
            # Search for them
            await repo.search_labels(f"concurrent-{batch_id}", limit=10)
            
            # Update usage
            await repo.update_label_usage(labels[:5], increment=True)
            
            return len(labels)
        
        # Run 10 concurrent operations
        start_time = time.time()
        tasks = [concurrent_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        duration = end_time - start_time
        total_operations = sum(results)
        print(f"   10 concurrent operations: {duration:.4f}s")
        print(f"   Processed {total_operations} labels concurrently")
        
        # Test 8: Database size and index effectiveness
        print("\n8️⃣  Testing database statistics...")
        
        # Get total counts
        all_labels_count = len(await repo.get_all_labels())
        
        async def get_usage_stats():
            popular = await repo.get_popular_labels(limit=1000)
            return len(popular), sum(p['usage_count'] for p in popular)
        
        unique_used_labels, total_usage = await get_usage_stats()
        
        print(f"   Total labels in database: {all_labels_count}")
        print(f"   Labels with usage > 0: {unique_used_labels}")
        print(f"   Total usage count: {total_usage}")
        
        # Performance summary
        print("\n📊 Performance Summary:")
        print("=" * 50)
        print("✅ All performance tests completed successfully!")
        print("\n🏆 Key Metrics:")
        print(f"   • Label creation: {len(created_labels) / duration:.0f} labels/second")
        print(f"   • Search operations: {1/avg_search_time:.0f} searches/second")
        print(f"   • Category queries: {1/avg_category_time:.0f} queries/second")
        print(f"   • Usage updates: {len(test_labels) / duration:.0f} updates/second")
        print(f"   • Label normalization: {throughput:.0f} normalizations/second")
        print(f"   • Database size: {all_labels_count} total labels")
        
        # Performance benchmarks
        benchmarks = {
            "label_creation": len(created_labels) / duration,
            "search_avg": 1/avg_search_time,
            "category_avg": 1/avg_category_time,
            "normalization": throughput
        }
        
        # Basic performance assertions
        assert benchmarks["label_creation"] > 100, "Label creation should be > 100 labels/second"
        assert benchmarks["search_avg"] > 50, "Search should be > 50 searches/second"
        assert benchmarks["category_avg"] > 100, "Category queries should be > 100 queries/second"
        assert benchmarks["normalization"] > 1000, "Normalization should be > 1000 ops/second"
        
        print("\n✅ All performance benchmarks met!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def main():
    await test_label_performance()


if __name__ == "__main__":
    asyncio.run(main())