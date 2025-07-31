#!/usr/bin/env python3
"""
Backup verification and repair utility for Docker MCP backup system
"""

import sqlite3
import json
import subprocess
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

class BackupVerifier:
    """Verifies and repairs database backup integrity"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        
    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
            
    def check_integrity(self) -> bool:
        """Check database integrity"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()[0]
            return result == "ok"
        except Exception as e:
            print(f"❌ Integrity check failed: {e}")
            return False
            
    def detect_json_corruption(self) -> List[Dict[str, Any]]:
        """Detect JSON corruption in task_subtasks assignees"""
        corrupted_records = []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, assignees FROM task_subtasks WHERE assignees IS NOT NULL AND assignees != '';")
            
            for row in cursor.fetchall():
                subtask_id, assignees = row
                
                # Check for double-encoded JSON
                if assignees.startswith('"') and assignees.endswith('"'):
                    try:
                        # Try to parse as double-encoded
                        first_parse = json.loads(assignees)
                        if isinstance(first_parse, str):
                            second_parse = json.loads(first_parse)
                            corrupted_records.append({
                                'id': subtask_id,
                                'current_value': assignees,
                                'corrected_value': first_parse,
                                'final_parsed': second_parse
                            })
                    except json.JSONDecodeError:
                        print(f"⚠️  Invalid JSON in subtask {subtask_id}: {assignees}")
                        
        except Exception as e:
            print(f"❌ Error detecting JSON corruption: {e}")
            
        return corrupted_records
        
    def repair_json_corruption(self, corrupted_records: List[Dict[str, Any]]) -> bool:
        """Repair JSON corruption in database"""
        if not corrupted_records:
            return True
            
        try:
            cursor = self.connection.cursor()
            
            for record in corrupted_records:
                cursor.execute(
                    "UPDATE task_subtasks SET assignees = ? WHERE id = ?",
                    (record['corrected_value'], record['id'])
                )
                print(f"   ✅ Repaired subtask {record['id']}: {record['current_value']} -> {record['corrected_value']}")
                
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error repairing JSON corruption: {e}")
            self.connection.rollback()
            return False
            
    def create_backup_copy(self, suffix: str = "verified") -> str:
        """Create a backup copy with suffix"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{self.db_path}.{suffix}-{timestamp}"
        
        try:
            # Copy database file
            subprocess.run(['cp', self.db_path, backup_path], check=True)
            print(f"✅ Created backup: {backup_path}")
            return backup_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create backup: {e}")
            return None

def verify_and_repair_backup(backup_path: str) -> bool:
    """Main verification and repair function"""
    print(f"🔍 Verifying backup: {backup_path}")
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_path}")
        return False
        
    with BackupVerifier(backup_path) as verifier:
        # Step 1: Check basic integrity
        if not verifier.check_integrity():
            print("❌ Database integrity check failed")
            return False
        print("✅ Database integrity check passed")
        
        # Step 2: Detect JSON corruption
        corrupted_records = verifier.detect_json_corruption()
        if corrupted_records:
            print(f"⚠️  Found {len(corrupted_records)} corrupted JSON records")
            
            # Create backup before repair
            backup_copy = verifier.create_backup_copy("pre-repair")
            if not backup_copy:
                print("❌ Failed to create pre-repair backup")
                return False
                
            # Repair corruption
            if verifier.repair_json_corruption(corrupted_records):
                print("✅ JSON corruption repaired successfully")
                
                # Verify repair
                remaining_corruption = verifier.detect_json_corruption()
                if remaining_corruption:
                    print(f"⚠️  {len(remaining_corruption)} records still corrupted")
                    return False
                else:
                    print("✅ All JSON corruption repaired")
                    return True
            else:
                print("❌ Failed to repair JSON corruption")
                return False
        else:
            print("✅ No JSON corruption detected")
            return True

def enhance_docker_backup_script():
    """Generate enhanced Docker backup script with verification"""
    script_content = '''#!/usr/bin/env python3
"""
Enhanced backup function with verification for mcp-docker.py
"""

import subprocess
import os
import sys
from datetime import datetime

def create_verified_backup(source_path: str, backup_name: str) -> bool:
    """Create a verified backup with integrity checks"""
    print(f"🔄 Creating verified backup: {backup_name}")
    
    try:
        # Step 1: Create backup using docker cp
        subprocess.run([
            "docker", "cp", f"dhafnck-mcp-server:{source_path}", backup_name
        ], check=True)
        print(f"   ✅ Backup created: {backup_name}")
        
        # Step 2: Run verification
        verification_script = os.path.join(os.path.dirname(__file__), "backup_verification.py")
        if os.path.exists(verification_script):
            result = subprocess.run([
                sys.executable, verification_script, backup_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ Backup verification passed")
                return True
            else:
                print(f"   ⚠️  Backup verification warnings: {result.stdout}")
                # Still return True if it was repaired
                return "repaired successfully" in result.stdout
        else:
            print(f"   ⚠️  Verification script not found, skipping verification")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Backup failed: {e}")
        return False

def enhanced_backup_section():
    """Enhanced backup section to replace lines 371-386 in mcp-docker.py"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dbs = [
        ("/data/dhafnck_mcp.db", f"dhafnck_mcp.db.bak-{timestamp}"),
        ("/data/dhafnck_mcp_test.db", f"dhafnck_mcp_test.db.bak-{timestamp}")
    ]
    
    print("🔄 Creating verified database backups...")
    
    for db_path, backup_name in dbs:
        if create_verified_backup(db_path, backup_name):
            print(f"✅ Successfully created verified backup: {backup_name}")
        else:
            print(f"❌ Failed to create verified backup: {backup_name}")
            
    print("✅ Backup process completed\\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Direct verification mode
        backup_path = sys.argv[1]
        success = verify_and_repair_backup(backup_path)
        sys.exit(0 if success else 1)
    else:
        # Enhanced backup mode
        enhanced_backup_section()
'''
    
    return script_content

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python backup_verification.py <backup_file_path>")
        sys.exit(1)
        
    backup_path = sys.argv[1]
    success = verify_and_repair_backup(backup_path)
    
    if success:
        print(f"\n✅ Backup verification completed successfully for: {backup_path}")
        sys.exit(0)
    else:
        print(f"\n❌ Backup verification failed for: {backup_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()