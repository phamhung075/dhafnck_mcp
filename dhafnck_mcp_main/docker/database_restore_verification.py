#!/usr/bin/env python3
"""
Database restore verification and fix script for Docker MCP system
"""

import sqlite3
import sys
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

def verify_and_fix_task_counts(db_path: str) -> bool:
    """Verify and fix task counts in project_git_branchs table"""
    print(f"🔍 Verifying task counts in database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get actual task counts per branch
        cursor.execute('SELECT git_branch_id, COUNT(*) as actual_count FROM tasks GROUP BY git_branch_id')
        actual_counts = dict(cursor.fetchall())
        
        # Get actual completed task counts per branch
        cursor.execute('SELECT git_branch_id, COUNT(*) as completed_count FROM tasks WHERE status = "done" GROUP BY git_branch_id')
        completed_counts = dict(cursor.fetchall())
        
        # Get current counts in project_git_branchs
        cursor.execute('SELECT id, name, task_count, completed_task_count FROM project_git_branchs')
        branches = cursor.fetchall()
        
        fixes_needed = []
        
        print(f"   Checking {len(branches)} branches...")
        
        for branch_id, branch_name, current_count, current_completed in branches:
            actual_count = actual_counts.get(branch_id, 0)
            actual_completed = completed_counts.get(branch_id, 0)
            
            if current_count != actual_count or current_completed != actual_completed:
                fixes_needed.append({
                    'branch_id': branch_id,
                    'branch_name': branch_name,
                    'current_count': current_count,
                    'actual_count': actual_count,
                    'current_completed': current_completed,
                    'actual_completed': actual_completed
                })
        
        if fixes_needed:
            print(f"   ⚠️  Found {len(fixes_needed)} branches with incorrect task counts:")
            for fix in fixes_needed:
                print(f"     {fix['branch_name']}: {fix['current_count']} → {fix['actual_count']} tasks, {fix['current_completed']} → {fix['actual_completed']} completed")
            
            # Apply fixes
            print(f"   🔧 Applying fixes...")
            for fix in fixes_needed:
                cursor.execute(
                    'UPDATE project_git_branchs SET task_count = ?, completed_task_count = ? WHERE id = ?',
                    (fix['actual_count'], fix['actual_completed'], fix['branch_id'])
                )
            
            conn.commit()
            print(f"   ✅ Fixed {len(fixes_needed)} branch task counts")
        else:
            print(f"   ✅ All task counts are correct")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error fixing task counts: {e}")
        return False

def verify_database_integrity(db_path: str) -> bool:
    """Verify database integrity"""
    print(f"🔍 Checking database integrity...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute('PRAGMA integrity_check;')
        integrity = cursor.fetchone()[0]
        
        if integrity == 'ok':
            print(f"   ✅ Database integrity check passed")
            return True
        else:
            print(f"   ❌ Database integrity check failed: {integrity}")
            return False
        
    except Exception as e:
        print(f"   ❌ Error checking integrity: {e}")
        return False

def verify_subtask_assignees(db_path: str) -> bool:
    """Verify subtask assignees JSON format"""
    print(f"🔍 Checking subtask assignees format...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for JSON corruption
        cursor.execute('SELECT id, assignees FROM task_subtasks WHERE assignees IS NOT NULL')
        rows = cursor.fetchall()
        
        corrupted_count = 0
        fixes_applied = 0
        
        for subtask_id, assignees in rows:
            if assignees.startswith('"') and assignees.endswith('"'):
                corrupted_count += 1
                try:
                    # Fix double-encoded JSON
                    import json
                    fixed_assignees = json.loads(assignees)
                    cursor.execute('UPDATE task_subtasks SET assignees = ? WHERE id = ?', (fixed_assignees, subtask_id))
                    fixes_applied += 1
                except:
                    print(f"   ⚠️  Could not fix subtask {subtask_id}: {assignees}")
        
        if corrupted_count > 0:
            print(f"   ⚠️  Found {corrupted_count} corrupted subtask assignees")
            print(f"   🔧 Fixed {fixes_applied} subtask assignees")
            conn.commit()
        else:
            print(f"   ✅ All subtask assignees are properly formatted")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking subtask assignees: {e}")
        return False

def verify_table_relationships(db_path: str) -> bool:
    """Verify table relationships and foreign keys"""
    print(f"🔍 Checking table relationships...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check orphaned tasks
        cursor.execute('''
            SELECT COUNT(*) FROM tasks 
            WHERE git_branch_id NOT IN (SELECT id FROM project_git_branchs)
        ''')
        orphaned_tasks = cursor.fetchone()[0]
        
        if orphaned_tasks > 0:
            print(f"   ⚠️  Found {orphaned_tasks} orphaned tasks")
            return False
        
        # Check orphaned subtasks
        cursor.execute('''
            SELECT COUNT(*) FROM task_subtasks 
            WHERE task_id NOT IN (SELECT id FROM tasks)
        ''')
        orphaned_subtasks = cursor.fetchone()[0]
        
        if orphaned_subtasks > 0:
            print(f"   ⚠️  Found {orphaned_subtasks} orphaned subtasks")
            return False
        
        print(f"   ✅ All table relationships are valid")
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking relationships: {e}")
        return False

def generate_database_summary(db_path: str) -> Dict:
    """Generate database summary statistics"""
    print(f"🔍 Generating database summary...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        summary = {}
        
        # Count tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        summary['tables'] = len(tables)
        
        # Count records in main tables
        for table in ['tasks', 'project_git_branchs', 'task_subtasks', 'projects']:
            if table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                summary[table] = cursor.fetchone()[0]
        
        # Task status breakdown
        cursor.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
        summary['task_status'] = dict(cursor.fetchall())
        
        # Branch task distribution
        cursor.execute('''
            SELECT ptt.name, COUNT(t.id) as task_count 
            FROM project_git_branchs ptt 
            LEFT JOIN tasks t ON ptt.id = t.git_branch_id 
            GROUP BY ptt.id, ptt.name
        ''')
        summary['branch_distribution'] = dict(cursor.fetchall())
        
        conn.close()
        return summary
        
    except Exception as e:
        print(f"   ❌ Error generating summary: {e}")
        return {}

def main():
    """Main verification function"""
    if len(sys.argv) < 2:
        print("Usage: python database_restore_verification.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)
    
    print("🔧 Database Restore Verification")
    print("=" * 50)
    
    # Run all verification steps
    results = {
        'integrity': verify_database_integrity(db_path),
        'task_counts': verify_and_fix_task_counts(db_path),
        'subtask_assignees': verify_subtask_assignees(db_path),
        'relationships': verify_table_relationships(db_path)
    }
    
    # Generate summary
    summary = generate_database_summary(db_path)
    
    # Print results
    print("\n" + "=" * 50)
    print("📋 VERIFICATION RESULTS")
    print("=" * 50)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check.replace('_', ' ').title()}: {status}")
    
    if summary:
        print(f"\n📊 DATABASE SUMMARY:")
        print(f"  Tables: {summary.get('tables', 0)}")
        print(f"  Projects: {summary.get('projects', 0)}")
        print(f"  Branches: {summary.get('project_git_branchs', 0)}")
        print(f"  Tasks: {summary.get('tasks', 0)}")
        print(f"  Subtasks: {summary.get('task_subtasks', 0)}")
        
        if 'task_status' in summary:
            print(f"  Task Status Breakdown:")
            for status, count in summary['task_status'].items():
                print(f"    {status}: {count}")
        
        if 'branch_distribution' in summary:
            print(f"  Branch Task Distribution:")
            for branch, count in summary['branch_distribution'].items():
                print(f"    {branch}: {count}")
    
    # Overall result
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n🎉 All verification checks passed!")
        print(f"✅ Database is ready for use")
    else:
        print(f"\n⚠️  Some verification checks failed")
        print(f"❌ Review failed checks and rerun verification")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())