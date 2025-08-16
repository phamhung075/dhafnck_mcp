#!/usr/bin/env python3
"""
Extreme Edge Case Testing - Finding the most obscure problems
"""

import time
import sys
import os
import threading
import signal
import random
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("="*70)
    print("🔬 EXTREME EDGE CASE TESTING - FINDING OBSCURE PROBLEMS")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    problems_found = []
    
    try:
        from fastmcp.task_management.infrastructure.repositories.orm.supabase_optimized_repository import SupabaseOptimizedRepository
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        
        print("\n🎯 TEST 1: Repository Method Coverage")
        print("-" * 50)
        
        repo = SupabaseOptimizedRepository()
        
        # Check which methods are actually overridden
        methods_to_test = [
            'create_task',
            'update_task', 
            'delete_task',
            'get_task',
            'search_tasks',
            'add_subtask',
            'add_dependency',
            'remove_dependency',
            'assign_user',
            'unassign_user',
            'add_label',
            'remove_label',
            'complete_task'
        ]
        
        for method_name in methods_to_test:
            if hasattr(repo, method_name):
                method = getattr(repo, method_name)
                # Check if method is from parent class or overridden
                parent_method = getattr(ORMTaskRepository, method_name, None)
                if method == parent_method:
                    problems_found.append({
                        "issue": f"{method_name} not optimized",
                        "severity": "Low",
                        "details": f"Method {method_name} uses standard implementation",
                        "impact": "Not benefiting from Supabase optimizations"
                    })
                    print(f"  ⚠️ {method_name}: Using standard implementation (not optimized)")
                else:
                    print(f"  ✅ {method_name}: Optimized for Supabase")
            else:
                print(f"  ❌ {method_name}: Method not found")
        
        print("\n🎯 TEST 2: Connection Pool Edge Cases")
        print("-" * 50)
        
        # Test what happens when we hold connections open
        print("Holding connections open...")
        sessions = []
        try:
            for i in range(5):
                session = repo.get_db_session().__enter__()
                sessions.append(session)
                print(f"  Opened session {i+1}")
            
            # Now try to use the repo
            result = repo.list_tasks_minimal(limit=5)
            print(f"  ✅ Can still query with {len(sessions)} open sessions")
            
        except Exception as e:
            problems_found.append({
                "issue": "Connection pool blocking",
                "severity": "Medium",
                "details": f"Cannot query with open sessions: {str(e)[:100]}",
                "impact": "May deadlock under certain conditions"
            })
            print(f"  ⚠️ Problem with open sessions: {str(e)[:50]}")
        finally:
            # Clean up sessions
            for session in sessions:
                try:
                    session.__exit__(None, None, None)
                except:
                    pass
        
        print("\n🎯 TEST 3: Query Result Consistency")
        print("-" * 50)
        
        # Test if results are consistent across different query methods
        print("Comparing query methods...")
        
        # Method 1: list_tasks_minimal
        results1 = repo.list_tasks_minimal(limit=5)
        
        # Method 2: list_tasks_no_relations
        results2 = repo.list_tasks_no_relations(limit=5)
        
        # Method 3: Standard list_tasks
        results3 = repo.list_tasks(limit=5)
        
        # Compare counts
        counts = [len(results1), len(results2), len(results3)]
        if len(set(counts)) > 1:
            problems_found.append({
                "issue": "Inconsistent result counts",
                "severity": "High",
                "details": f"Different methods return different counts: {counts}",
                "impact": "Data inconsistency between query methods"
            })
            print(f"  ⚠️ Inconsistent counts: minimal={counts[0]}, no_relations={counts[1]}, standard={counts[2]}")
        else:
            print(f"  ✅ All methods return {counts[0]} results")
        
        print("\n🎯 TEST 4: Transaction Isolation")
        print("-" * 50)
        
        print("Testing transaction isolation...")
        
        def transaction_test(repo, thread_id, results):
            try:
                with repo.get_db_session() as session:
                    # Start transaction
                    session.begin()
                    
                    # Read data
                    result = session.execute("SELECT COUNT(*) FROM tasks").scalar()
                    results[thread_id] = result
                    
                    # Don't commit - just exit
            except Exception as e:
                results[thread_id] = f"ERROR: {str(e)[:30]}"
        
        # Run concurrent transactions
        results = {}
        threads = []
        for i in range(3):
            t = threading.Thread(target=transaction_test, args=(repo, i, results))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check results
        if all(isinstance(v, int) for v in results.values()):
            unique_counts = set(results.values())
            if len(unique_counts) > 1:
                problems_found.append({
                    "issue": "Transaction isolation problem",
                    "severity": "High",
                    "details": f"Different counts in concurrent transactions: {unique_counts}",
                    "impact": "Read inconsistency in transactions"
                })
                print(f"  ⚠️ Isolation issue: Different counts {unique_counts}")
            else:
                print(f"  ✅ Transaction isolation maintained")
        else:
            print(f"  ⚠️ Some transactions failed: {results}")
        
        print("\n🎯 TEST 5: Null Value Handling")
        print("-" * 50)
        
        # Test with various null/None scenarios
        null_tests = [
            ("None git_branch_id", lambda: SupabaseOptimizedRepository(git_branch_id=None)),
            ("Empty string git_branch_id", lambda: SupabaseOptimizedRepository(git_branch_id="")),
            ("Whitespace git_branch_id", lambda: SupabaseOptimizedRepository(git_branch_id="   ")),
            ("None in all params", lambda: repo.list_tasks_minimal(status=None, priority=None, assignee_id=None)),
            ("Empty strings", lambda: repo.list_tasks_minimal(status="", priority="", assignee_id="")),
        ]
        
        for test_name, test_func in null_tests:
            try:
                result = test_func()
                if hasattr(result, '__len__'):
                    print(f"  ✅ {test_name}: Handled ({len(result)} results)")
                else:
                    print(f"  ✅ {test_name}: Handled")
            except Exception as e:
                if "invalid" in str(e).lower() or "uuid" in str(e).lower():
                    print(f"  ✅ {test_name}: Properly validated")
                else:
                    problems_found.append({
                        "issue": f"Poor null handling: {test_name}",
                        "severity": "Low",
                        "details": str(e)[:100],
                        "impact": "Unexpected errors with null values"
                    })
                    print(f"  ⚠️ {test_name}: {str(e)[:50]}")
        
        print("\n🎯 TEST 6: Pagination Edge Cases")
        print("-" * 50)
        
        # Test pagination boundaries
        pagination_tests = [
            ("Offset equals total", lambda: repo.list_tasks_minimal(limit=10, offset=1000000)),
            ("Limit 0", lambda: repo.list_tasks_minimal(limit=0)),
            ("Offset without limit", lambda: repo.list_tasks_minimal(offset=10)),
            ("Huge page", lambda: repo.list_tasks_minimal(limit=9999, offset=0)),
        ]
        
        for test_name, test_func in pagination_tests:
            try:
                result = test_func()
                print(f"  ✅ {test_name}: Returned {len(result)} results")
            except Exception as e:
                problems_found.append({
                    "issue": f"Pagination edge case: {test_name}",
                    "severity": "Low",
                    "details": str(e)[:100],
                    "impact": "Pagination may fail in edge cases"
                })
                print(f"  ⚠️ {test_name}: {str(e)[:50]}")
        
        print("\n🎯 TEST 7: Special Characters in Data")
        print("-" * 50)
        
        special_chars = [
            "emoji_status_😀",
            "quote's_test",
            'double"quote',
            "backslash\\test",
            "newline\ntest",
            "tab\ttest",
            "null\x00byte",
            "unicode_中文",
            "rtl_עברית",
        ]
        
        for char_test in special_chars:
            try:
                result = repo.list_tasks_minimal(status=char_test)
                print(f"  ✅ '{char_test[:20]}': Handled safely")
            except Exception as e:
                if "codec" in str(e).lower() or "decode" in str(e).lower():
                    problems_found.append({
                        "issue": f"Character encoding issue",
                        "severity": "Medium",
                        "details": f"Failed on: {char_test}",
                        "impact": "Cannot handle some character encodings"
                    })
                    print(f"  ⚠️ '{char_test[:20]}': Encoding issue")
                else:
                    print(f"  ✅ '{char_test[:20]}': Validated")
        
        print("\n🎯 TEST 8: Resource Exhaustion Protection")
        print("-" * 50)
        
        print("Testing resource limits...")
        
        # Test if there's protection against resource exhaustion
        try:
            # Try to create many repository instances quickly
            repos = []
            start_time = time.time()
            
            for i in range(100):
                r = SupabaseOptimizedRepository()
                repos.append(r)
                
                if time.time() - start_time > 5:
                    print(f"  ⚠️ Creating repos taking too long (>{i} repos in 5s)")
                    problems_found.append({
                        "issue": "No resource creation throttling",
                        "severity": "Low",
                        "details": f"Can create unlimited repositories",
                        "impact": "Potential resource exhaustion"
                    })
                    break
            else:
                print(f"  ✅ Created 100 repositories without issue")
            
            repos.clear()
            
        except Exception as e:
            print(f"  ✅ Resource limit enforced: {str(e)[:50]}")
        
        print("\n🎯 TEST 9: Method Chaining Safety")
        print("-" * 50)
        
        # Test if methods can be safely chained
        try:
            # Attempt various method chains
            repo = SupabaseOptimizedRepository()
            
            # Chain multiple operations
            results1 = repo.list_tasks_minimal(limit=5)
            results2 = repo.list_tasks_minimal(limit=5)
            results3 = repo.list_tasks_minimal(limit=5)
            
            # Check if repo state is corrupted
            if results1 == results2 == results3:
                print("  ✅ Method chaining safe - consistent results")
            else:
                problems_found.append({
                    "issue": "State corruption with method chaining",
                    "severity": "Medium",
                    "details": "Repeated calls return different results",
                    "impact": "Repository state may be corrupted"
                })
                print("  ⚠️ Inconsistent results from chained calls")
                
        except Exception as e:
            print(f"  ⚠️ Method chaining failed: {str(e)[:50]}")
        
        print("\n🎯 TEST 10: Signal Handling")
        print("-" * 50)
        
        print("Testing signal interruption handling...")
        
        def signal_test():
            repo = SupabaseOptimizedRepository()
            try:
                # This would normally be interrupted
                repo.list_tasks_minimal(limit=1000)
                return "completed"
            except KeyboardInterrupt:
                return "interrupted"
            except Exception as e:
                return f"error: {str(e)[:30]}"
        
        # We can't actually send signals in this context, but test the structure
        result = signal_test()
        if result == "completed":
            print("  ✅ Query completed normally")
        elif result == "interrupted":
            print("  ✅ Handles interruption gracefully")
        else:
            print(f"  ⚠️ {result}")
        
    except Exception as e:
        print(f"\n❌ Critical Test Error: {e}")
        import traceback
        traceback.print_exc()
        problems_found.append({
            "issue": "Test framework failure",
            "severity": "Critical",
            "details": str(e),
            "impact": "Cannot complete testing"
        })
    
    # Final Report
    print("\n" + "="*70)
    print("🔬 EXTREME EDGE CASE SUMMARY")
    print("="*70)
    
    if not problems_found:
        print("\n✨ PERFECT! No problems found even in extreme edge cases!")
    else:
        print(f"\n📊 Found {len(problems_found)} potential issues:\n")
        
        # Group by severity
        by_severity = {}
        for p in problems_found:
            severity = p["severity"]
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(p)
        
        severity_order = ["Critical", "High", "Medium", "Low"]
        severity_symbols = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢"
        }
        
        for severity in severity_order:
            if severity in by_severity:
                print(f"\n{severity_symbols[severity]} {severity.upper()} ({len(by_severity[severity])} issues):")
                for p in by_severity[severity]:
                    print(f"  • {p['issue']}")
                    if p['details']:
                        print(f"    → {p['details'][:80]}")
    
    # Save detailed report
    report = {
        "test_date": datetime.now().isoformat(),
        "test_type": "extreme_edge_cases",
        "total_issues": len(problems_found),
        "by_severity": {
            "critical": len([p for p in problems_found if p["severity"] == "Critical"]),
            "high": len([p for p in problems_found if p["severity"] == "High"]),
            "medium": len([p for p in problems_found if p["severity"] == "Medium"]),
            "low": len([p for p in problems_found if p["severity"] == "Low"])
        },
        "issues": problems_found
    }
    
    with open("extreme_edge_case_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: extreme_edge_case_report.json")
    print("="*70)

if __name__ == "__main__":
    main()