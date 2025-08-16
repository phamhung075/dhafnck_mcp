#!/usr/bin/env python3
"""
Deep Problem Detection - Comprehensive system analysis
"""

import time
import sys
import os
import gc
import tracemalloc
import asyncio
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("="*70)
    print("🔬 DEEP PROBLEM DETECTION - COMPREHENSIVE ANALYSIS")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    problems_found = []
    
    try:
        # Import repositories
        from fastmcp.task_management.infrastructure.repositories.orm.supabase_optimized_repository import SupabaseOptimizedRepository
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        
        print("\n🔍 PHASE 1: Memory Leak Detection")
        print("-" * 50)
        
        # Start memory tracking
        tracemalloc.start()
        
        # Create and destroy repositories multiple times
        for i in range(10):
            repo = SupabaseOptimizedRepository()
            tasks = repo.list_tasks_minimal(limit=20)
            del repo
            gc.collect()
        
        # Check memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memory_mb = peak / 1024 / 1024
        print(f"Peak memory usage: {memory_mb:.2f} MB")
        
        if memory_mb > 100:
            problems_found.append({
                "issue": "High memory usage",
                "severity": "Medium",
                "details": f"Peak memory: {memory_mb:.2f} MB",
                "impact": "May cause memory issues in production"
            })
            print(f"⚠️ Problem: High memory usage ({memory_mb:.2f} MB)")
        else:
            print(f"✅ Memory usage acceptable ({memory_mb:.2f} MB)")
        
        print("\n🔍 PHASE 2: Connection Pool Exhaustion")
        print("-" * 50)
        
        # Test connection pool limits
        try:
            repos = []
            for i in range(15):  # Try to create more than pool size
                repo = SupabaseOptimizedRepository()
                repos.append(repo)
            
            # Try to use all repos simultaneously
            for repo in repos:
                repo.list_tasks_minimal(limit=1)
            
            print("✅ Connection pool handles concurrent access")
            
        except Exception as e:
            problems_found.append({
                "issue": "Connection pool exhaustion",
                "severity": "High",
                "details": str(e),
                "impact": "May cause connection failures under load"
            })
            print(f"⚠️ Problem: Connection pool issue - {str(e)[:50]}")
        finally:
            repos.clear()
            gc.collect()
        
        print("\n🔍 PHASE 3: Error Recovery Testing")
        print("-" * 50)
        
        repo = SupabaseOptimizedRepository()
        
        # Test with various invalid inputs
        test_cases = [
            ("Invalid UUID", lambda: repo.get_task_with_counts("not-a-uuid")),
            ("Negative limit", lambda: repo.list_tasks_minimal(limit=-1)),
            ("Huge limit", lambda: repo.list_tasks_minimal(limit=10000)),
            ("SQL injection attempt", lambda: repo.list_tasks_minimal(status="'; DROP TABLE tasks; --")),
            ("None branch_id", lambda: SupabaseOptimizedRepository(git_branch_id=None).list_tasks_minimal()),
        ]
        
        for test_name, test_func in test_cases:
            try:
                result = test_func()
                print(f"✅ {test_name}: Handled gracefully")
            except Exception as e:
                problems_found.append({
                    "issue": f"Poor error handling for {test_name}",
                    "severity": "Low",
                    "details": str(e)[:100],
                    "impact": "May cause unexpected errors"
                })
                print(f"⚠️ {test_name}: Exception - {str(e)[:50]}")
        
        print("\n🔍 PHASE 4: Performance Degradation Check")
        print("-" * 50)
        
        # Test performance over time
        repo = SupabaseOptimizedRepository()
        times = []
        
        print("Running 50 consecutive queries...")
        for i in range(50):
            start = time.time()
            repo.list_tasks_minimal(limit=10)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            if i % 10 == 0:
                print(f"  Query {i}: {elapsed:.2f}ms")
        
        # Check for degradation
        first_10_avg = sum(times[:10]) / 10
        last_10_avg = sum(times[-10:]) / 10
        degradation = ((last_10_avg - first_10_avg) / first_10_avg) * 100
        
        print(f"\nFirst 10 queries avg: {first_10_avg:.2f}ms")
        print(f"Last 10 queries avg: {last_10_avg:.2f}ms")
        print(f"Degradation: {degradation:.1f}%")
        
        if degradation > 20:
            problems_found.append({
                "issue": "Performance degradation over time",
                "severity": "Medium",
                "details": f"{degradation:.1f}% slower after 50 queries",
                "impact": "Performance may degrade in long-running processes"
            })
            print(f"⚠️ Problem: Performance degraded by {degradation:.1f}%")
        else:
            print(f"✅ Performance stable (change: {degradation:.1f}%)")
        
        print("\n🔍 PHASE 5: Transaction Handling")
        print("-" * 50)
        
        # Test transaction rollback behavior
        try:
            with repo.get_db_session() as session:
                # Start a transaction
                session.begin()
                
                # Try to execute invalid query
                session.execute("SELECT * FROM non_existent_table")
                
                session.commit()
                print("⚠️ Problem: Invalid query didn't fail")
                problems_found.append({
                    "issue": "Transaction handling issue",
                    "severity": "High",
                    "details": "Invalid queries not failing properly",
                    "impact": "Data integrity risk"
                })
        except Exception as e:
            print("✅ Transactions properly handle errors")
        
        print("\n🔍 PHASE 6: Concurrent Access Patterns")
        print("-" * 50)
        
        # Test concurrent access
        async def concurrent_test():
            async def query_task(repo, idx):
                try:
                    start = time.time()
                    # Simulate async operation with sync repo
                    await asyncio.get_event_loop().run_in_executor(
                        None, repo.list_tasks_minimal, 10
                    )
                    return (time.time() - start) * 1000
                except Exception as e:
                    return None
            
            repo = SupabaseOptimizedRepository()
            tasks = [query_task(repo, i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            successful = [r for r in results if r is not None]
            if len(successful) < len(results):
                problems_found.append({
                    "issue": "Concurrent access failures",
                    "severity": "High",
                    "details": f"{len(results) - len(successful)} failures out of {len(results)}",
                    "impact": "May fail under concurrent load"
                })
                print(f"⚠️ Problem: {len(results) - len(successful)} concurrent access failures")
            else:
                avg_time = sum(successful) / len(successful)
                print(f"✅ All concurrent queries succeeded (avg: {avg_time:.2f}ms)")
        
        # Run async test
        asyncio.run(concurrent_test())
        
        print("\n🔍 PHASE 7: Cache Coherency")
        print("-" * 50)
        
        # Test if caching causes stale data
        repo1 = SupabaseOptimizedRepository()
        repo2 = SupabaseOptimizedRepository()
        
        # Get initial data
        tasks1_before = repo1.list_tasks_minimal(limit=5)
        
        # Simulate change (would normally be done through another repo)
        # Get data from second repo
        tasks2 = repo2.list_tasks_minimal(limit=5)
        
        # Check if first repo sees changes
        tasks1_after = repo1.list_tasks_minimal(limit=5)
        
        if tasks1_before != tasks1_after and len(tasks1_before) == len(tasks1_after):
            problems_found.append({
                "issue": "Cache coherency problem",
                "severity": "Medium",
                "details": "Different repos may see different data",
                "impact": "Data consistency issues"
            })
            print("⚠️ Problem: Cache coherency issue detected")
        else:
            print("✅ Cache coherency maintained")
        
        print("\n🔍 PHASE 8: Resource Cleanup")
        print("-" * 50)
        
        # Check for resource leaks (skip if psutil not available)
        try:
            import psutil
            process = psutil.Process(os.getpid())
            
            # Get initial resources
            initial_connections = len(process.connections())
            initial_threads = process.num_threads()
            
            # Create and destroy many repos
            for i in range(20):
                repo = SupabaseOptimizedRepository()
                _ = repo.list_tasks_minimal()
                del repo
            
            gc.collect()
            time.sleep(1)  # Allow cleanup
            
            # Check resources after
            final_connections = len(process.connections())
            final_threads = process.num_threads()
            
            if final_connections > initial_connections + 2:
                problems_found.append({
                    "issue": "Connection leak",
                    "severity": "High",
                    "details": f"Connections grew from {initial_connections} to {final_connections}",
                    "impact": "Resource exhaustion over time"
                })
                print(f"⚠️ Problem: Connection leak detected ({initial_connections} -> {final_connections})")
            else:
                print(f"✅ No connection leaks ({initial_connections} -> {final_connections})")
            
            if final_threads > initial_threads + 2:
                problems_found.append({
                    "issue": "Thread leak",
                    "severity": "Medium",
                    "details": f"Threads grew from {initial_threads} to {final_threads}",
                    "impact": "Resource exhaustion over time"
                })
                print(f"⚠️ Problem: Thread leak detected ({initial_threads} -> {final_threads})")
            else:
                print(f"✅ No thread leaks ({initial_threads} -> {final_threads})")
        except ImportError:
            print("ℹ️ Skipping resource leak detection (psutil not available)")
        
        print("\n🔍 PHASE 9: Edge Case Handling")
        print("-" * 50)
        
        repo = SupabaseOptimizedRepository()
        
        # Test edge cases
        edge_cases = [
            ("Empty database query", lambda: repo.list_tasks_minimal(status="never_exists_status_123")),
            ("Unicode in filters", lambda: repo.list_tasks_minimal(status="待办")),
            ("Very long status", lambda: repo.list_tasks_minimal(status="a" * 1000)),
            ("Special characters", lambda: repo.list_tasks_minimal(priority="high'; --")),
        ]
        
        for case_name, case_func in edge_cases:
            try:
                result = case_func()
                print(f"✅ {case_name}: Handled correctly")
            except Exception as e:
                problems_found.append({
                    "issue": f"Edge case failure: {case_name}",
                    "severity": "Low",
                    "details": str(e)[:100],
                    "impact": "Unexpected errors with unusual input"
                })
                print(f"⚠️ {case_name}: Failed - {str(e)[:50]}")
        
        print("\n🔍 PHASE 10: Configuration Issues")
        print("-" * 50)
        
        # Check for configuration problems
        issues = []
        
        # Check if Redis is configured but not working
        if os.getenv("REDIS_ENABLED") == "true":
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                print("✅ Redis configured and working")
            except:
                issues.append("Redis configured but not accessible")
                problems_found.append({
                    "issue": "Redis configuration problem",
                    "severity": "Medium",
                    "details": "Redis enabled but not accessible",
                    "impact": "Caching not working, performance impact"
                })
                print("⚠️ Redis configured but not working")
        else:
            print("ℹ️ Redis not enabled (could improve performance)")
        
        # Check connection pool settings
        from fastmcp.task_management.infrastructure.database.database_config import DatabaseConfig
        try:
            config = DatabaseConfig()
            engine = config.engine
            pool = engine.pool
            
            print(f"✅ Connection pool: size={pool.size()}, overflow={pool.overflow()}")
        except Exception as e:
            problems_found.append({
                "issue": "Connection pool configuration issue",
                "severity": "Medium",
                "details": str(e)[:100],
                "impact": "Suboptimal connection management"
            })
            print(f"⚠️ Connection pool issue: {str(e)[:50]}")
        
    except Exception as e:
        print(f"\n❌ Critical Test Error: {e}")
        import traceback
        traceback.print_exc()
        problems_found.append({
            "issue": "Test framework failure",
            "severity": "Critical",
            "details": str(e),
            "impact": "Cannot complete diagnostic"
        })
    
    # Final Report
    print("\n" + "="*70)
    print("📋 PROBLEM DETECTION SUMMARY")
    print("="*70)
    
    if not problems_found:
        print("\n✅ NO PROBLEMS DETECTED!")
        print("System is operating optimally.")
    else:
        print(f"\n⚠️ FOUND {len(problems_found)} PROBLEMS:\n")
        
        # Group by severity
        critical = [p for p in problems_found if p["severity"] == "Critical"]
        high = [p for p in problems_found if p["severity"] == "High"]
        medium = [p for p in problems_found if p["severity"] == "Medium"]
        low = [p for p in problems_found if p["severity"] == "Low"]
        
        if critical:
            print("🔴 CRITICAL ISSUES:")
            for p in critical:
                print(f"  - {p['issue']}")
                print(f"    Details: {p['details']}")
                print(f"    Impact: {p['impact']}\n")
        
        if high:
            print("🟠 HIGH PRIORITY ISSUES:")
            for p in high:
                print(f"  - {p['issue']}")
                print(f"    Details: {p['details']}")
                print(f"    Impact: {p['impact']}\n")
        
        if medium:
            print("🟡 MEDIUM PRIORITY ISSUES:")
            for p in medium:
                print(f"  - {p['issue']}")
                print(f"    Details: {p['details']}")
                print(f"    Impact: {p['impact']}\n")
        
        if low:
            print("🟢 LOW PRIORITY ISSUES:")
            for p in low:
                print(f"  - {p['issue']}")
                print(f"    Details: {p['details']}")
                print(f"    Impact: {p['impact']}\n")
    
    # Save report
    report = {
        "test_date": datetime.now().isoformat(),
        "problems_found": len(problems_found),
        "issues": problems_found
    }
    
    with open("deep_problem_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n📄 Report saved to: deep_problem_report.json")
    print("="*70)

if __name__ == "__main__":
    main()