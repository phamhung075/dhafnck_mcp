#!/usr/bin/env python3
"""
Comprehensive database restoration script with verification and repair
"""

import os
import sys
import subprocess
import sqlite3
import json
import shutil
from datetime import datetime
from typing import Optional

def backup_current_database(container_db_path: str = "/data/dhafnck_mcp.db") -> Optional[str]:
    """Create backup of current database before restoration"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"dhafnck_mcp.db.pre-restore-{timestamp}"
    
    try:
        print(f"🔄 Creating backup of current database...")
        subprocess.run([
            "docker", "cp", f"dhafnck-mcp-server:{container_db_path}", backup_name
        ], check=True)
        print(f"✅ Current database backed up to: {backup_name}")
        return backup_name
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to backup current database: {e}")
        return None

def verify_backup_file(backup_path: str) -> bool:
    """Verify backup file integrity and repair if needed"""
    print(f"🔍 Verifying backup file: {backup_path}")
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        return False
    
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()[0]
        
        if integrity != "ok":
            print(f"❌ Backup file integrity check failed: {integrity}")
            conn.close()
            return False
        
        print(f"✅ Backup file integrity check passed")
        
        # Check for JSON corruption in subtasks
        cursor.execute("SELECT id, assignees FROM task_subtasks WHERE assignees IS NOT NULL")
        rows = cursor.fetchall()
        
        corrupted_count = 0
        for subtask_id, assignees in rows:
            if assignees.startswith('"') and assignees.endswith('"'):
                corrupted_count += 1
        
        if corrupted_count > 0:
            print(f"⚠️  Found {corrupted_count} corrupted JSON records - will repair during restore")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verifying backup file: {e}")
        return False

def repair_json_corruption(db_path: str) -> bool:
    """Repair JSON corruption in database"""
    print(f"🔧 Repairing JSON corruption in database...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find and fix corrupted JSON
        cursor.execute("SELECT id, assignees FROM task_subtasks WHERE assignees IS NOT NULL")
        rows = cursor.fetchall()
        
        repairs = 0
        for subtask_id, assignees in rows:
            if assignees.startswith('"') and assignees.endswith('"'):
                try:
                    # Fix double-encoded JSON
                    fixed_assignees = json.loads(assignees)
                    cursor.execute("UPDATE task_subtasks SET assignees = ? WHERE id = ?", (fixed_assignees, subtask_id))
                    repairs += 1
                except:
                    print(f"   ⚠️  Could not repair subtask {subtask_id}")
        
        if repairs > 0:
            conn.commit()
            print(f"   ✅ Repaired {repairs} corrupted JSON records")
        else:
            print(f"   ✅ No JSON corruption found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error repairing JSON corruption: {e}")
        return False

def fix_task_counts(db_path: str) -> bool:
    """Fix task counts in project_git_branches table"""
    print(f"🔧 Fixing task counts in project branches...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get actual task counts per branch
        cursor.execute('SELECT git_branch_id, COUNT(*) FROM tasks GROUP BY git_branch_id')
        actual_counts = dict(cursor.fetchall())
        
        # Get actual completed task counts per branch
        cursor.execute('SELECT git_branch_id, COUNT(*) FROM tasks WHERE status = "done" GROUP BY git_branch_id')
        completed_counts = dict(cursor.fetchall())
        
        # Update task counts
        cursor.execute('SELECT id, name FROM project_git_branches')
        branches = cursor.fetchall()
        
        fixes = 0
        for branch_id, branch_name in branches:
            actual_count = actual_counts.get(branch_id, 0)
            completed_count = completed_counts.get(branch_id, 0)
            
            cursor.execute(
                'UPDATE project_git_branches SET task_count = ?, completed_task_count = ? WHERE id = ?',
                (actual_count, completed_count, branch_id)
            )
            
            if actual_count > 0:
                print(f"   ✅ {branch_name}: {actual_count} tasks ({completed_count} completed)")
                fixes += 1
        
        conn.commit()
        print(f"   ✅ Fixed task counts for {fixes} branches")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing task counts: {e}")
        return False

def restore_database(backup_path: str, container_db_path: str = "/data/dhafnck_mcp.db") -> bool:
    """Restore database from backup to container"""
    print(f"🔄 Restoring database to container...")
    
    try:
        # Copy backup to container
        subprocess.run([
            "docker", "cp", backup_path, f"dhafnck-mcp-server:{container_db_path}"
        ], check=True)
        
        # Fix database permissions
        subprocess.run([
            "docker", "exec", "--user", "root", "dhafnck-mcp-server",
            "chown", "dhafnck:dhafnck", container_db_path
        ], check=True)
        
        subprocess.run([
            "docker", "exec", "--user", "root", "dhafnck-mcp-server",
            "chmod", "664", container_db_path
        ], check=True)
        
        print(f"✅ Database restored successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to restore database: {e}")
        return False

def verify_restored_database(container_db_path: str = "/data/dhafnck_mcp.db") -> bool:
    """Verify the restored database in container"""
    print(f"🔍 Verifying restored database...")
    
    try:
        # Run verification script in container
        result = subprocess.run([
            "docker", "exec", "dhafnck-mcp-server", "python", "-c", f'''
import sqlite3
import json

db_path = "{container_db_path}"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check integrity
cursor.execute("PRAGMA integrity_check;")
integrity = cursor.fetchone()[0]
print("Integrity: " + integrity)

# Check task counts
cursor.execute("SELECT name, task_count FROM project_git_branches WHERE task_count > 0")
branches = cursor.fetchall()
print("Branches with tasks: " + str(len(branches)))
for name, count in branches:
    print("  " + name + ": " + str(count) + " tasks")

# Check subtask JSON
cursor.execute("SELECT COUNT(*) FROM task_subtasks WHERE assignees LIKE '\\"%\\"'")
corrupted = cursor.fetchone()[0]
print("Corrupted subtasks: " + str(corrupted))

conn.close()
'''
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database verification completed")
            print(f"   Output: {result.stdout}")
            return "Integrity: ok" in result.stdout and "Corrupted subtasks: 0" in result.stdout
        else:
            print(f"❌ Database verification failed: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"❌ Error verifying restored database: {e}")
        return False

def restart_frontend():
    """Restart frontend to refresh UI with restored data"""
    print(f"🔄 Restarting frontend to refresh UI...")
    
    try:
        # Stop frontend
        subprocess.run([
            "docker-compose", "-f", "dhafnck_mcp_main/docker/docker-compose.yml",
            "stop", "dhafnck-frontend"
        ], capture_output=True, text=True)
        
        # Start frontend
        subprocess.run([
            "docker-compose", "-f", "dhafnck_mcp_main/docker/docker-compose.yml",
            "start", "dhafnck-frontend"
        ], capture_output=True, text=True)
        
        print(f"✅ Frontend restarted successfully")
        print(f"🌐 Frontend available at: http://localhost:3800")
        return True
        
    except Exception as e:
        print(f"❌ Failed to restart frontend: {e}")
        return False

def main():
    """Main restoration function"""
    if len(sys.argv) < 2:
        print("Usage: python restore_database.py <backup_file_path>")
        sys.exit(1)
    
    backup_path = sys.argv[1]
    
    print("🔧 Database Restoration with Verification")
    print("=" * 60)
    
    # Step 1: Backup current database
    current_backup = backup_current_database()
    if not current_backup:
        print("❌ Failed to backup current database")
        sys.exit(1)
    
    # Step 2: Verify backup file
    if not verify_backup_file(backup_path):
        print("❌ Backup file verification failed")
        sys.exit(1)
    
    # Step 3: Create working copy and repair it
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    working_copy = f"dhafnck_mcp.db.restored-{timestamp}"
    
    try:
        shutil.copy2(backup_path, working_copy)
        print(f"✅ Created working copy: {working_copy}")
        
        # Repair JSON corruption
        if not repair_json_corruption(working_copy):
            print("❌ Failed to repair JSON corruption")
            sys.exit(1)
        
        # Fix task counts
        if not fix_task_counts(working_copy):
            print("❌ Failed to fix task counts")
            sys.exit(1)
        
        # Step 4: Restore to container
        if not restore_database(working_copy):
            print("❌ Database restoration failed")
            sys.exit(1)
        
        # Step 5: Verify restored database
        if not verify_restored_database():
            print("❌ Restored database verification failed")
            sys.exit(1)
        
        # Step 6: Restart frontend
        if not restart_frontend():
            print("⚠️  Frontend restart failed - you may need to restart manually")
        
        print(f"\n🎉 Database restoration completed successfully!")
        print(f"✅ Original database backed up to: {current_backup}")
        print(f"✅ Restored database verified and ready for use")
        print(f"🌐 Frontend available at: http://localhost:3800")
        
        # Clean up working copy
        os.remove(working_copy)
        
    except Exception as e:
        print(f"❌ Restoration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()