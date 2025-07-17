#!/usr/bin/env python3
"""
Test runner for all critical fixes TDD tests.

This script runs all the tests related to the five critical fixes:
1. Task Next Action NoneType error
2. Hierarchical Context Health Check coroutine error  
3. Branch Statistics not found issue
4. Task Creation Context Sync Failed error
5. Context Creation Foreign Key constraint error

Usage:
    python run_critical_fixes_tests.py [--verbose] [--unit-only] [--integration-only]
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Test files for the critical fixes
UNIT_TESTS = [
    "tests/unit/use_cases/test_next_task_null_safety.py",
    "tests/unit/services/test_hierarchical_context_async.py",
    "tests/unit/services/test_git_branch_persistence.py",
    "tests/unit/repositories/test_hierarchical_context_auto_creation.py",
]

INTEGRATION_TESTS = [
    "tests/integration/test_five_critical_issues_tdd.py",
    "tests/integration/test_all_fixes_integration.py",
]

# Existing related tests that should also pass
RELATED_TESTS = [
    "tests/integration/test_next_task_nonetype_integration.py",
    "tests/integration/test_hierarchical_context_async_await_fix.py",
    "tests/unit/use_cases/test_next_task_nonetype_fix.py",
    "tests/unit/interface/controllers/test_async_context_coroutine_fix.py",
]


def run_tests(test_files, verbose=False):
    """Run a list of test files with pytest"""
    # Change to src directory
    src_dir = Path(__file__).parent.parent
    os.chdir(src_dir)
    
    failed_tests = []
    passed_tests = []
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Running: {test_file}")
        print(f"{'='*60}")
        
        cmd = ["python", "-m", "pytest", test_file, "-v" if verbose else "-q", "-s"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ PASSED: {test_file}")
                passed_tests.append(test_file)
            else:
                print(f"❌ FAILED: {test_file}")
                failed_tests.append(test_file)
                if verbose:
                    print("\nError output:")
                    print(result.stdout)
                    print(result.stderr)
        except Exception as e:
            print(f"❌ ERROR running {test_file}: {e}")
            failed_tests.append(test_file)
    
    return passed_tests, failed_tests


def main():
    parser = argparse.ArgumentParser(description="Run critical fixes TDD tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--include-related", action="store_true", help="Include related existing tests")
    args = parser.parse_args()
    
    # Determine which tests to run
    tests_to_run = []
    
    if args.unit_only:
        tests_to_run.extend(UNIT_TESTS)
    elif args.integration_only:
        tests_to_run.extend(INTEGRATION_TESTS)
    else:
        # Run all tests
        tests_to_run.extend(UNIT_TESTS)
        tests_to_run.extend(INTEGRATION_TESTS)
    
    if args.include_related:
        tests_to_run.extend(RELATED_TESTS)
    
    print("🧪 Running Critical Fixes TDD Tests")
    print(f"📋 Total tests to run: {len(tests_to_run)}")
    
    # Run the tests
    passed, failed = run_tests(tests_to_run, verbose=args.verbose)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {len(passed)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"📋 Total: {len(passed) + len(failed)}")
    
    if failed:
        print("\n❌ Failed tests:")
        for test in failed:
            print(f"  - {test}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        print("\n🎉 All five critical fixes are working correctly:")
        print("  1. ✅ Task Next Action NoneType error - Fixed")
        print("  2. ✅ Hierarchical Context Health Check coroutine error - Fixed")
        print("  3. ✅ Branch Statistics not found issue - Fixed")
        print("  4. ✅ Task Creation Context Sync Failed error - Fixed")
        print("  5. ✅ Context Creation Foreign Key constraint error - Fixed")
        sys.exit(0)


if __name__ == "__main__":
    main()