#!/usr/bin/env python3
"""
Data Mismatch Investigation - Deep dive into repository inconsistencies
"""

import time
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    print("="*70)
    print("🔍 DATA MISMATCH INVESTIGATION")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        # Import repositories
        from fastmcp.task_management.infrastructure.repositories.orm.supabase_optimized_repository import SupabaseOptimizedRepository
        from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
        
        print("\n📊 PHASE 1: Repository Initialization")
        print("-" * 50)
        
        # Initialize both repositories with same branch ID (use valid UUID)
        import uuid
        branch_id = str(uuid.uuid4())  # Generate valid UUID
        optimized_repo = SupabaseOptimizedRepository(git_branch_id=branch_id)
        standard_repo = ORMTaskRepository(git_branch_id=branch_id)
        print(f"✅ Both repositories initialized with branch_id: {branch_id}")
        
        print("\n📊 PHASE 2: List Tasks Comparison")
        print("-" * 50)
        
        # Get tasks from optimized repo (minimal)
        print("\nFetching from SupabaseOptimizedRepository...")
        optimized_tasks = optimized_repo.list_tasks_minimal(limit=10)
        print(f"  Found {len(optimized_tasks)} tasks")
        if optimized_tasks:
            print(f"  First task ID: {optimized_tasks[0]['id']}")
            print(f"  First task title: {optimized_tasks[0]['title']}")
        
        # Get tasks from standard repo
        print("\nFetching from ORMTaskRepository...")
        standard_tasks = standard_repo.list_tasks(limit=10)
        print(f"  Found {len(standard_tasks)} tasks")
        if standard_tasks:
            print(f"  First task ID: {standard_tasks[0].id}")
            print(f"  First task title: {standard_tasks[0].title}")
        
        print("\n📊 PHASE 3: Data Consistency Check")
        print("-" * 50)
        
        # Check if counts match
        if len(optimized_tasks) != len(standard_tasks):
            print(f"❌ Task count mismatch: {len(optimized_tasks)} vs {len(standard_tasks)}")
        else:
            print(f"✅ Task count matches: {len(optimized_tasks)}")
        
        # Check if IDs match
        if optimized_tasks and standard_tasks:
            optimized_ids = [t['id'] for t in optimized_tasks]
            standard_ids = [t.id for t in standard_tasks]
            
            print("\n🔍 ID Comparison:")
            print(f"  Optimized IDs (first 3): {optimized_ids[:3]}")
            print(f"  Standard IDs (first 3): {standard_ids[:3]}")
            
            # Check for exact match
            if optimized_ids == standard_ids:
                print("✅ Task IDs match exactly")
            else:
                print("❌ Task IDs don't match!")
                
                # Find differences
                only_in_optimized = set(optimized_ids) - set(standard_ids)
                only_in_standard = set(standard_ids) - set(optimized_ids)
                
                if only_in_optimized:
                    print(f"  Tasks only in optimized: {list(only_in_optimized)[:3]}")
                if only_in_standard:
                    print(f"  Tasks only in standard: {list(only_in_standard)[:3]}")
        
        print("\n📊 PHASE 4: Query Analysis")
        print("-" * 50)
        
        # Check if branch filtering is applied differently
        print("\nTesting without branch filter...")
        optimized_no_branch = SupabaseOptimizedRepository()
        standard_no_branch = ORMTaskRepository()
        
        opt_all = optimized_no_branch.list_tasks_minimal(limit=5)
        std_all = standard_no_branch.list_tasks(limit=5)
        
        print(f"  Optimized (no filter): {len(opt_all)} tasks")
        print(f"  Standard (no filter): {len(std_all)} tasks")
        
        # Check ordering
        print("\n🔍 Ordering Check:")
        if opt_all and std_all:
            print(f"  Optimized first: {opt_all[0]['title'] if opt_all else 'None'}")
            print(f"  Standard first: {std_all[0].title if std_all else 'None'}")
        
        print("\n📊 PHASE 5: SQL Query Inspection")
        print("-" * 50)
        
        # Enable SQL logging temporarily
        import logging
        sql_logger = logging.getLogger('sqlalchemy.engine')
        sql_logger.setLevel(logging.INFO)
        
        print("\nExecuting with SQL logging...")
        
        # Capture queries
        print("\n[Optimized Repository Query]")
        opt_test = optimized_repo.list_tasks_minimal(limit=1)
        
        print("\n[Standard Repository Query]")
        std_test = standard_repo.list_tasks(limit=1)
        
        print("\n📊 PHASE 6: Root Cause Analysis")
        print("-" * 50)
        
        # Check if it's a timing issue (data being created between calls)
        print("\nChecking for timing issues...")
        opt1 = optimized_repo.list_tasks_minimal(limit=5)
        time.sleep(0.1)
        opt2 = optimized_repo.list_tasks_minimal(limit=5)
        
        if [t['id'] for t in opt1] == [t['id'] for t in opt2]:
            print("✅ Optimized repo returns consistent data")
        else:
            print("❌ Optimized repo returns different data on consecutive calls!")
        
        std1 = standard_repo.list_tasks(limit=5)
        time.sleep(0.1)
        std2 = standard_repo.list_tasks(limit=5)
        
        if [t.id for t in std1] == [t.id for t in std2]:
            print("✅ Standard repo returns consistent data")
        else:
            print("❌ Standard repo returns different data on consecutive calls!")
        
        print("\n📊 PHASE 7: Filter Testing")
        print("-" * 50)
        
        # Test with specific filters
        print("\nTesting with status filter (status='todo')...")
        opt_todo = optimized_repo.list_tasks_minimal(status='todo', limit=5)
        std_todo = standard_repo.list_tasks(status='todo', limit=5)
        
        print(f"  Optimized 'todo' tasks: {len(opt_todo)}")
        print(f"  Standard 'todo' tasks: {len(std_todo)}")
        
        if opt_todo and std_todo:
            opt_todo_ids = [t['id'] for t in opt_todo]
            std_todo_ids = [t.id for t in std_todo]
            if opt_todo_ids == std_todo_ids:
                print("✅ Filtered results match")
            else:
                print("❌ Filtered results don't match")
        
        print("\n📊 PHASE 8: Database Connection Check")
        print("-" * 50)
        
        # Check if both repos use same database
        from fastmcp.task_management.infrastructure.database.connection import DatabaseConnection
        
        conn = DatabaseConnection()
        print(f"Database URL (masked): {conn.database_url[:30]}...")
        print(f"Database type: {conn.database_type}")
        
        # Check session factory
        with optimized_repo.get_db_session() as opt_session:
            with standard_repo.get_db_session() as std_session:
                # Check if pointing to same database
                opt_bind = str(opt_session.bind.url) if opt_session.bind else "None"
                std_bind = str(std_session.bind.url) if std_session.bind else "None"
                
                if opt_bind == std_bind:
                    print("✅ Both repositories use same database connection")
                else:
                    print(f"❌ Different connections!")
                    print(f"  Optimized: {opt_bind[:30]}...")
                    print(f"  Standard: {std_bind[:30]}...")
        
        print("\n" + "="*70)
        print("📋 INVESTIGATION SUMMARY")
        print("="*70)
        
        # Determine the issue
        if len(optimized_tasks) != len(standard_tasks):
            print("\n🔴 PRIMARY ISSUE: Different task counts returned")
            print("   This suggests filtering or query logic differences")
        elif optimized_tasks and standard_tasks and [t['id'] for t in optimized_tasks] != [t.id for t in standard_tasks]:
            print("\n🔴 PRIMARY ISSUE: Different task IDs returned")
            print("   This suggests ordering or pagination differences")
        else:
            print("\n🟢 NO MISMATCH DETECTED in this test run")
            print("   The issue may be intermittent or environment-specific")
        
        print("\n💡 LIKELY CAUSES:")
        print("1. Different ORDER BY clauses (created_at vs updated_at)")
        print("2. Branch ID filtering applied differently")
        print("3. Relationship joins affecting result set")
        print("4. Cache or session state differences")
        print("5. Timezone handling in timestamps")
        
        print("\n🔧 RECOMMENDED FIXES:")
        print("1. Ensure both repos use same ORDER BY (created_at DESC)")
        print("2. Verify branch_id filtering is consistent")
        print("3. Check that optimized repo doesn't skip important filters")
        print("4. Ensure both use same session/transaction isolation")
        
    except Exception as e:
        print(f"\n❌ Investigation Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()