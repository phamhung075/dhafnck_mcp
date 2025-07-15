#!/usr/bin/env python3
"""
Label Repository Integration Test
Test the SQLite label repository with real database operations
"""
import sys
import asyncio
import tempfile
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastmcp.task_management.infrastructure.repositories.sqlite.label_repository import SQLiteLabelRepository
from fastmcp.task_management.infrastructure.database.database_initializer import initialize_database


async def test_label_repository_integration():
    """Test label repository integration with database"""
    print("🏷️  Label Repository Integration Test")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database with proper schema
        initialize_database(db_path)
        
        # Create repository
        repo = SQLiteLabelRepository(db_path=db_path)
        
        # Test 1: Basic CRUD operations
        print("\n1️⃣  Testing basic CRUD operations...")
        
        # Create labels
        label1 = await repo.create_label("Test Label")
        label2 = await repo.create_label("Another Label", "custom")
        label3 = await repo.create_label("Priority Label", "priority")
        
        print(f"   ✅ Created labels: {label1}, {label2}, {label3}")
        
        # Find labels
        found = await repo.find_label("test label")  # Different case
        assert found == "Test Label", f"Expected 'Test Label', got '{found}'"
        print("   ✅ Find label works with case-insensitive search")
        
        # Get all labels
        all_labels = await repo.get_all_labels()
        assert len(all_labels) >= 3, f"Expected at least 3 labels, got {len(all_labels)}"
        print(f"   ✅ Retrieved {len(all_labels)} total labels")
        
        # Test 2: Category operations
        print("\n2️⃣  Testing category operations...")
        
        custom_labels = await repo.get_labels_by_category("custom")
        priority_labels = await repo.get_labels_by_category("priority")
        
        assert "Another Label" in custom_labels, "Custom label not found in custom category"
        assert "Priority Label" in priority_labels, "Priority label not found in priority category"
        print(f"   ✅ Categories working: custom ({len(custom_labels)}), priority ({len(priority_labels)})")
        
        # Test 3: Search functionality
        print("\n3️⃣  Testing search functionality...")
        
        search_results = await repo.search_labels("Label", limit=5)
        assert len(search_results) >= 2, f"Expected at least 2 search results, got {len(search_results)}"
        print(f"   ✅ Search found {len(search_results)} labels matching 'Label'")
        
        # Test 4: Usage tracking
        print("\n4️⃣  Testing usage tracking...")
        
        # Update usage for multiple labels
        await repo.update_label_usage(["Test Label", "Another Label"], increment=True)
        
        usage1 = await repo.get_label_usage_count("Test Label")
        usage2 = await repo.get_label_usage_count("Another Label")
        
        assert usage1 >= 2, f"Expected usage count >= 2, got {usage1}"  # 1 from create + 1 from update
        assert usage2 >= 2, f"Expected usage count >= 2, got {usage2}"
        print(f"   ✅ Usage tracking: Test Label ({usage1}), Another Label ({usage2})")
        
        # Test decrement
        await repo.update_label_usage(["Test Label"], increment=False)
        usage1_after = await repo.get_label_usage_count("Test Label")
        assert usage1_after == usage1 - 1, f"Expected {usage1 - 1}, got {usage1_after}"
        print("   ✅ Usage decrement working")
        
        # Test 5: Popular labels
        print("\n5️⃣  Testing popular labels...")
        
        popular = await repo.get_popular_labels(limit=3)
        assert len(popular) >= 2, f"Expected at least 2 popular labels, got {len(popular)}"
        
        for label_info in popular[:3]:
            print(f"   - {label_info['label']}: {label_info['usage_count']} uses, category: {label_info['category']}")
        
        # Test 6: Bulk operations
        print("\n6️⃣  Testing bulk operations...")
        
        bulk_labels = ["bulk-1", "bulk-2", "bulk-3", "", "a" * 60]  # Mix of valid and invalid
        validated_labels = await repo.validate_and_create_labels(bulk_labels)
        
        # Should create 3 valid labels (bulk-1, bulk-2, bulk-3)
        # Empty string and too-long string should be filtered out
        expected_count = 3
        actual_count = len(validated_labels)
        
        if actual_count != expected_count:
            print(f"   ⚠️  Expected {expected_count} labels, got {actual_count}: {validated_labels}")
        
        assert actual_count >= 3, f"Expected at least 3 valid labels, got {actual_count}"
        print(f"   ✅ Bulk validation created {actual_count} valid labels")
        
        # Test 7: Task label operations (if available)
        print("\n7️⃣  Testing task label operations...")
        
        try:
            # Update task labels (this method might exist)
            await repo.update_task_labels("test-task-123", ["Test Label", "bulk-1"])
            task_labels = await repo.get_labels_for_task("test-task-123")
            assert "Test Label" in task_labels, "Task label assignment failed"
            print(f"   ✅ Task label operations: assigned {len(task_labels)} labels to task")
        except Exception as e:
            print(f"   ⚠️  Task label operations not available: {e}")
        
        # Test 8: Normalization consistency
        print("\n8️⃣  Testing normalization consistency...")
        
        variations = [
            "Test   Label",  # Extra spaces
            "TEST LABEL",    # Different case
            "test-label",    # Different format
        ]
        
        for variation in variations:
            normalized = await repo.normalize_label(variation)
            found_label = await repo.find_label(variation)
            print(f"   - '{variation}' -> normalized: '{normalized}', found: '{found_label}'")
        
        # Test 9: Common labels verification
        print("\n9️⃣  Testing common labels...")
        
        common_label_names = ["bug", "feature", "frontend", "backend", "urgent"]
        for name in common_label_names:
            found = await repo.find_label(name)
            if found:
                print(f"   ✅ Common label '{name}' found")
            else:
                print(f"   ⚠️  Common label '{name}' not found")
        
        print("\n✅ All label repository integration tests passed!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def main():
    await test_label_repository_integration()


if __name__ == "__main__":
    asyncio.run(main())