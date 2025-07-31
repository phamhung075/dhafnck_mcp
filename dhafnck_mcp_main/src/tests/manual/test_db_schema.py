#!/usr/bin/env python3
"""
Check test database schema.
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

def check_schema():
    # Connect to test database
    db_path = Path(__file__).parent.parent.parent.parent / "database" / "data" / "dhafnck_mcp_test.db"
    
    print(f"Checking database schema at: {db_path}")
    
    if not db_path.exists():
        print("❌ Test database does not exist")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n📋 Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check specific context tables
    context_tables = ['task_contexts', 'branch_contexts', 'project_contexts', 'global_contexts']
    
    for table_name in context_tables:
        print(f"\n🔍 Checking {table_name}:")
        try:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            if columns:
                print(f"  ✅ Table exists with {len(columns)} columns:")
                for col in columns:
                    print(f"    - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
            else:
                print(f"  ❌ Table {table_name} does not exist")
        except sqlite3.Error as e:
            print(f"  ❌ Error checking {table_name}: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_schema()