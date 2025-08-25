#!/usr/bin/env python3
"""
Simple SQLite inspection of test database.
"""

import sqlite3
import os

# Test database path
db_path = "/home/daihungpham/__projects__/agentic-project/dhafnck_mcp_main/database/data/dhafnck_mcp_test.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check total project contexts
    cursor.execute("SELECT COUNT(*) FROM project_contexts")
    total = cursor.fetchone()[0]
    print(f"Total project contexts: {total}")
    
    # Check contexts by user_id
    cursor.execute("""
        SELECT user_id, COUNT(*) 
        FROM project_contexts 
        GROUP BY user_id
        ORDER BY COUNT(*) DESC
    """)
    user_counts = cursor.fetchall()
    print("Project contexts by user_id:")
    for user_id, count in user_counts:
        print(f"  {user_id or 'NULL'}: {count}")
    
    # Show recent contexts
    cursor.execute("""
        SELECT id, project_id, user_id, created_at 
        FROM project_contexts 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    recent = cursor.fetchall()
    print("\nRecent project contexts:")
    for row in recent:
        print(f"  ID: {row[0]}, project_id: {row[1]}, user_id: {row[2]}, created_at: {row[3]}")
    
    # Check for specific user
    test_user = "6cfd3f73-9504-42cd-af8a-6fd5b7b7b7bd"
    cursor.execute("SELECT COUNT(*) FROM project_contexts WHERE user_id = ?", (test_user,))
    user_count = cursor.fetchone()[0]
    print(f"\nContexts for test user {test_user}: {user_count}")
    
    # Show a sample of user IDs from recent tests
    cursor.execute("""
        SELECT user_id, COUNT(*) 
        FROM project_contexts 
        WHERE created_at > datetime('now', '-1 hour')
        GROUP BY user_id
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    recent_users = cursor.fetchall()
    print("\nRecent users (last hour):")
    for user_id, count in recent_users:
        print(f"  {user_id}: {count} contexts")
    
    conn.close()
else:
    print(f"Database not found at: {db_path}")