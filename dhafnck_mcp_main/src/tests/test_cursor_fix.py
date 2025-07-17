#!/usr/bin/env python3
"""Test script to verify the SQLAlchemy cursor fix"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastmcp.task_management.infrastructure.repositories.sqlite.base_repository_compat import SQLiteBaseRepositoryCompat

def test_cursor_methods():
    """Test that cursor methods work correctly"""
    print("Testing SQLAlchemy cursor fix...")
    
    # Create a test repository
    repo = SQLiteBaseRepositoryCompat(db_path=":memory:")
    
    # Test basic connection and cursor
    with repo._get_connection() as conn:
        print("✓ Connection created successfully")
        
        # Test cursor() method
        cursor = conn.cursor()
        print("✓ cursor() method works")
        
        # Create a test table
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        print("✓ CREATE TABLE executed")
        
        # Test INSERT with lastrowid
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test1",))
        last_id = cursor.lastrowid
        print(f"✓ INSERT executed, lastrowid: {last_id}")
        
        # Test SELECT with fetchone
        cursor.execute("SELECT * FROM test_table WHERE id = ?", (last_id,))
        row = cursor.fetchone()
        print(f"✓ SELECT with fetchone: {row}")
        
        # Test SELECT with fetchall
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test2",))
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test3",))
        
        cursor.execute("SELECT * FROM test_table")
        rows = cursor.fetchall()
        print(f"✓ SELECT with fetchall: {len(rows)} rows")
        
        # Test rowcount
        cursor.execute("DELETE FROM test_table WHERE name = ?", ("test1",))
        print(f"✓ DELETE executed, rowcount: {cursor.rowcount}")
        
        conn.commit()
        print("✓ Transaction committed")
    
    print("\n✅ All cursor compatibility tests passed!")

if __name__ == "__main__":
    try:
        test_cursor_methods()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()