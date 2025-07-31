#!/usr/bin/env python3
"""
Debug script to analyze the Docker backup system and database corruption issue
"""

import sqlite3
import json
import subprocess
import os
import sys
from datetime import datetime

def analyze_database(db_path, db_name):
    """Analyze database structure and data"""
    print(f"\n🔍 Analyzing {db_name} database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check database info
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()[0]
        print(f"   Integrity check: {integrity}")
        
        # Get file size
        file_size = os.path.getsize(db_path)
        print(f"   File size: {file_size} bytes")
        
        # Get modification time
        mod_time = datetime.fromtimestamp(os.path.getmtime(db_path))
        print(f"   Modified: {mod_time}")
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"   Tables: {[table[0] for table in tables]}")
        
        # Check task_subtasks table specifically
        if ('task_subtasks',) in tables:
            cursor.execute("SELECT COUNT(*) FROM task_subtasks;")
            subtask_count = cursor.fetchone()[0]
            print(f"   Subtasks count: {subtask_count}")
            
            # Check for assignees data corruption
            cursor.execute("SELECT id, assignees FROM task_subtasks LIMIT 5;")
            sample_subtasks = cursor.fetchall()
            print(f"   Sample subtasks assignees:")
            for subtask_id, assignees in sample_subtasks:
                print(f"     {subtask_id}: {assignees!r}")
                
                # Test JSON parsing
                try:
                    if assignees:
                        parsed = json.loads(assignees)
                        print(f"       -> Parsed: {parsed}")
                    else:
                        print(f"       -> Empty assignees")
                except json.JSONDecodeError as e:
                    print(f"       -> JSON ERROR: {e}")
        
        conn.close()
        return {
            'integrity': integrity,
            'file_size': file_size,
            'mod_time': mod_time,
            'tables': [table[0] for table in tables],
            'subtask_count': subtask_count if ('task_subtasks',) in tables else 0
        }
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        return None

def test_docker_backup_process():
    """Test the Docker backup process"""
    print("\n🐳 Testing Docker backup process...")
    
    # Check if Docker is running
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, check=True)
        print("   ✅ Docker is running")
    except subprocess.CalledProcessError:
        print("   ❌ Docker is not running")
        return False
    
    # Check if container is running
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=dhafnck-mcp-server', '--format', '{{.Names}}'],
            capture_output=True, text=True, check=True
        )
        if 'dhafnck-mcp-server' in result.stdout:
            print("   ✅ dhafnck-mcp-server container is running")
        else:
            print("   ❌ dhafnck-mcp-server container is not running")
            return False
    except subprocess.CalledProcessError:
        print("   ❌ Failed to check container status")
        return False
    
    # Test backup process
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    test_backup_name = f"dhafnck_mcp.db.test-{timestamp}"
    
    try:
        print(f"   🔄 Testing backup: {test_backup_name}")
        subprocess.run([
            'docker', 'cp', 'dhafnck-mcp-server:/data/dhafnck_mcp.db', test_backup_name
        ], check=True)
        print(f"   ✅ Test backup created successfully")
        
        # Analyze test backup
        test_backup_info = analyze_database(test_backup_name, "Test Backup")
        
        # Clean up test backup
        os.remove(test_backup_name)
        print(f"   🧹 Test backup cleaned up")
        
        return test_backup_info
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Backup test failed: {e}")
        return False

def compare_databases(db1_path, db1_name, db2_path, db2_name):
    """Compare two databases"""
    print(f"\n⚖️  Comparing {db1_name} vs {db2_name}")
    
    db1_info = analyze_database(db1_path, db1_name)
    db2_info = analyze_database(db2_path, db2_name)
    
    if not db1_info or not db2_info:
        print("❌ Cannot compare databases - one or both failed to analyze")
        return False
    
    # Compare key metrics
    print(f"\n📊 Comparison Results:")
    print(f"   File sizes: {db1_info['file_size']} vs {db2_info['file_size']}")
    print(f"   Subtask counts: {db1_info['subtask_count']} vs {db2_info['subtask_count']}")
    print(f"   Integrity: {db1_info['integrity']} vs {db2_info['integrity']}")
    
    # Check for significant differences
    size_diff = abs(db1_info['file_size'] - db2_info['file_size'])
    count_diff = abs(db1_info['subtask_count'] - db2_info['subtask_count'])
    
    if size_diff > 100000:  # 100KB difference
        print(f"   ⚠️  Large file size difference: {size_diff} bytes")
    
    if count_diff > 0:
        print(f"   ⚠️  Subtask count difference: {count_diff}")
    
    if db1_info['integrity'] != 'ok' or db2_info['integrity'] != 'ok':
        print(f"   ❌ Integrity issues detected")
        return False
    
    print(f"   ✅ Databases appear consistent")
    return True

def main():
    """Main debug function"""
    print("🔧 Docker Backup System Debug Analysis")
    print("=" * 50)
    
    # Paths
    backup_path = "/home/daihungpham/agentic-project/dhafnck_mcp.db.bak-20250715-230833"
    current_path = "/home/daihungpham/agentic-project/dhafnck_mcp_main/database/data/dhafnck_mcp.db"
    
    # 1. Analyze the problematic backup file
    print("\n1️⃣ Analyzing problematic backup file...")
    backup_info = analyze_database(backup_path, "Problematic Backup")
    
    # 2. Analyze current database
    print("\n2️⃣ Analyzing current database...")
    current_info = analyze_database(current_path, "Current Database")
    
    # 3. Compare databases
    print("\n3️⃣ Comparing databases...")
    comparison_result = compare_databases(backup_path, "Backup", current_path, "Current")
    
    # 4. Test Docker backup process
    print("\n4️⃣ Testing Docker backup process...")
    test_result = test_docker_backup_process()
    
    # 5. Summary and recommendations
    print("\n" + "=" * 50)
    print("📋 SUMMARY AND RECOMMENDATIONS")
    print("=" * 50)
    
    if backup_info and backup_info['integrity'] == 'ok':
        print("✅ Backup file integrity is OK")
    else:
        print("❌ Backup file has integrity issues")
    
    if current_info and current_info['integrity'] == 'ok':
        print("✅ Current database integrity is OK")
    else:
        print("❌ Current database has integrity issues")
    
    if comparison_result:
        print("✅ Databases are consistent")
    else:
        print("❌ Databases have significant differences")
    
    if test_result:
        print("✅ Docker backup process works correctly")
    else:
        print("❌ Docker backup process has issues")
    
    # Specific recommendations
    print("\n🎯 RECOMMENDATIONS:")
    
    if backup_info and backup_info['integrity'] == 'ok':
        print("• The backup file appears to be valid, not corrupted")
        print("• The 'database disk image is malformed' error was likely transient")
        print("• Consider the backup system to be working correctly")
    
    if not test_result:
        print("• Start the Docker container before running backup operations")
        print("• Check Docker permissions and container health")
    
    print("• Run database VACUUM periodically to optimize storage")
    print("• Monitor backup file sizes for consistency")
    print("• Consider implementing backup verification in the Docker script")

if __name__ == "__main__":
    main()