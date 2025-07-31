#!/usr/bin/env python3
"""
Debug script to investigate database lock issues
"""

import sqlite3
import sys
import os
import time
import psutil
from datetime import datetime

def check_database_locks(db_path: str):
    """Check for database locks and analyze locking processes"""
    print(f"🔍 Checking database locks: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    # Check file permissions
    stat = os.stat(db_path)
    print(f"   File permissions: {oct(stat.st_mode)[-3:]}")
    print(f"   Owner: UID {stat.st_uid}, GID {stat.st_gid}")
    print(f"   Size: {stat.st_size} bytes")
    print(f"   Modified: {datetime.fromtimestamp(stat.st_mtime)}")
    
    # Check if file is currently open by any process
    print(f"\n🔍 Checking processes using database file...")
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if process has the database file open
                files = proc.open_files()
                for f in files:
                    if db_path in f.path:
                        print(f"   Process {proc.info['pid']} ({proc.info['name']}): {f.path} (mode: {f.mode})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"   Error checking processes: {e}")
    
    # Try to connect to database
    print(f"\n🔍 Testing database connection...")
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        print("   ✅ Connection successful")
        
        # Check for active transactions
        cursor = conn.cursor()
        cursor.execute("PRAGMA database_list;")
        databases = cursor.fetchall()
        print(f"   Database list: {databases}")
        
        # Check WAL mode
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        print(f"   Journal mode: {journal_mode}")
        
        # Check locking mode
        cursor.execute("PRAGMA locking_mode;")
        locking_mode = cursor.fetchone()[0]
        print(f"   Locking mode: {locking_mode}")
        
        # Check if database is busy
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()[0]
        print(f"   Integrity check: {integrity}")
        
        conn.close()
        return True
        
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"   ❌ Database is locked: {e}")
            return False
        else:
            print(f"   ❌ Database error: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_concurrent_access(db_path: str):
    """Test concurrent database access"""
    print(f"\n🔍 Testing concurrent database access...")
    
    connections = []
    try:
        # Try to open multiple connections
        for i in range(3):
            conn = sqlite3.connect(db_path, timeout=2.0)
            connections.append(conn)
            print(f"   ✅ Connection {i+1} opened")
        
        # Test concurrent reads
        for i, conn in enumerate(connections):
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks;")
            count = cursor.fetchone()[0]
            print(f"   ✅ Connection {i+1} read {count} tasks")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Concurrent access error: {e}")
        return False
    finally:
        for conn in connections:
            try:
                conn.close()
            except:
                pass

def check_disk_space(db_path: str):
    """Check available disk space"""
    print(f"\n🔍 Checking disk space for database location...")
    
    try:
        statvfs = os.statvfs(os.path.dirname(db_path))
        
        # Calculate disk usage
        total = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_bavail
        used = total - free
        
        print(f"   Total space: {total / (1024**3):.2f} GB")
        print(f"   Used space: {used / (1024**3):.2f} GB")
        print(f"   Free space: {free / (1024**3):.2f} GB")
        print(f"   Usage: {(used / total) * 100:.1f}%")
        
        if free < 100 * 1024 * 1024:  # Less than 100MB
            print(f"   ⚠️  Low disk space warning")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking disk space: {e}")
        return False

def simulate_database_operation(db_path: str):
    """Simulate the database operation that causes lock"""
    print(f"\n🔍 Simulating database operations...")
    
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        # Get a test subtask
        cursor.execute("SELECT id FROM task_subtasks LIMIT 1;")
        row = cursor.fetchone()
        if not row:
            print("   ❌ No subtasks found to test")
            return False
        
        subtask_id = row[0]
        print(f"   Testing with subtask ID: {subtask_id}")
        
        # Test update operation (similar to what frontend does)
        cursor.execute("""
            UPDATE task_subtasks 
            SET assignees = ? 
            WHERE id = ?
        """, ('["@test_agent"]', subtask_id))
        
        conn.commit()
        print(f"   ✅ Update operation successful")
        
        # Rollback the test change
        cursor.execute("""
            UPDATE task_subtasks 
            SET assignees = ? 
            WHERE id = ?
        """, ('[]', subtask_id))
        
        conn.commit()
        print(f"   ✅ Rollback successful")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database operation error: {e}")
        return False

def main():
    """Main debug function"""
    print("🔧 Database Lock Debug Analysis")
    print("=" * 50)
    
    # Test both host and container database paths
    db_paths = [
        "/home/daihungpham/agentic-project/dhafnck_mcp_main/database/data/dhafnck_mcp.db",
        "/data/dhafnck_mcp.db"  # Container path
    ]
    
    results = {}
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n📍 Testing database: {db_path}")
            
            results[db_path] = {
                'lock_check': check_database_locks(db_path),
                'concurrent_access': test_concurrent_access(db_path),
                'disk_space': check_disk_space(db_path),
                'operation_test': simulate_database_operation(db_path)
            }
        else:
            print(f"\n📍 Database not found: {db_path}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    for db_path, result in results.items():
        print(f"\n🗄️  {db_path}:")
        print(f"   Lock check: {'✅ PASS' if result['lock_check'] else '❌ FAIL'}")
        print(f"   Concurrent access: {'✅ PASS' if result['concurrent_access'] else '❌ FAIL'}")
        print(f"   Disk space: {'✅ PASS' if result['disk_space'] else '❌ FAIL'}")
        print(f"   Operation test: {'✅ PASS' if result['operation_test'] else '❌ FAIL'}")
    
    # Recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    
    all_tests_passed = all(
        all(result.values()) for result in results.values()
    )
    
    if all_tests_passed:
        print("• All database tests passed - lock issue may be intermittent")
        print("• Monitor for concurrent access patterns")
        print("• Check application-level transaction handling")
    else:
        print("• Database lock detected - investigate failed tests")
        print("• Consider switching to WAL mode for better concurrency")
        print("• Check for long-running transactions")
        print("• Verify proper connection handling in application")

if __name__ == "__main__":
    main()