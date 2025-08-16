#!/usr/bin/env python3
"""
Final Performance Test for Supabase Optimizations
"""

import time
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_direct_performance():
    """Test performance by directly using the repositories"""
    
    print("=" * 60)
    print("Testing Supabase Optimization Performance")
    print("=" * 60)
    
    # Set environment to use Supabase
    os.environ["DATABASE_TYPE"] = "supabase"
    
    try:
        from fastmcp.task_management.infrastructure.repositories.orm.supabase_optimized_repository import SupabaseOptimizedRepository
        
        print("\n✅ SupabaseOptimizedRepository imported successfully")
        
        # Create repository instance
        repo = SupabaseOptimizedRepository()
        
        # Test list_tasks_minimal
        print("\nTesting list_tasks_minimal performance...")
        times = []
        
        for i in range(5):
            start = time.time()
            
            try:
                tasks = repo.list_tasks_minimal(limit=10)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                print(f"  Test {i+1}: {elapsed:>8.2f}ms - Retrieved {len(tasks)} tasks")
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                print(f"  Test {i+1}: {elapsed:>8.2f}ms - Error: {str(e)[:50]}")
        
        if times:
            avg = sum(times) / len(times)
            print(f"\n  Average: {avg:>8.2f}ms")
            
            if avg < 1000:
                print("  ✅ EXCELLENT - Query optimization working!")
            elif avg < 3000:
                print("  ✅ GOOD - Significant improvement")
            else:
                print("  ⚠️  Still needs optimization")
    
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nTrying alternative import...")
        
        try:
            from fastmcp.task_management.infrastructure.repositories.orm.optimized_task_repository import OptimizedTaskRepository
            print("✅ Using OptimizedTaskRepository instead")
            
            repo = OptimizedTaskRepository()
            
            # Test performance
            start = time.time()
            tasks = repo.list_tasks_minimal(limit=10)
            elapsed = (time.time() - start) * 1000
            
            print(f"\n  Response time: {elapsed:.2f}ms")
            print(f"  Retrieved {len(tasks)} tasks")
            
        except Exception as e2:
            print(f"❌ Alternative also failed: {e2}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_direct_performance()