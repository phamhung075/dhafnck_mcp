#!/usr/bin/env python3
"""
Test Label Migration
Verify that existing labels are properly migrated to the new flexible label system.
"""
import sqlite3
import os
import tempfile
from pathlib import Path

def create_old_schema_db(db_path):
    """Create a database with the old label schema and test data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create old task_labels table (labels stored as text)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_labels (
            task_id TEXT NOT NULL,
            label TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (task_id, label)
        )
    """)
    
    # Create tasks table (simplified)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL
        )
    """)
    
    # Insert test data
    test_tasks = [
        ("task-1", "Task with common labels"),
        ("task-2", "Task with custom labels"),
        ("task-3", "Task with mixed labels"),
    ]
    
    test_labels = [
        # Task 1 - common labels
        ("task-1", "bug"),
        ("task-1", "urgent"),
        ("task-1", "frontend"),
        
        # Task 2 - custom labels
        ("task-2", "custom-label-1"),
        ("task-2", "My Custom Label"),
        ("task-2", "UPPERCASE-LABEL"),
        
        # Task 3 - mixed
        ("task-3", "feature"),
        ("task-3", "platform"),
        ("task-3", "enterprise"),
        ("task-3", "ai-orchestration"),
    ]
    
    cursor.executemany("INSERT INTO tasks (id, title) VALUES (?, ?)", test_tasks)
    cursor.executemany("INSERT INTO task_labels (task_id, label) VALUES (?, ?)", test_labels)
    
    conn.commit()
    conn.close()

def apply_migration(db_path):
    """Apply the migration script - migrate from old text-based labels to new schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("⚠️  Applying migration from old text-based labels to new schema...")
    
    # Get existing labels from old schema
    cursor.execute("SELECT DISTINCT task_id, label FROM task_labels WHERE label IS NOT NULL")
    old_labels = cursor.fetchall()
    
    # Create new schema
    conn.executescript("""
        -- Labels table
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            normalized TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'custom',
            usage_count INTEGER DEFAULT 0,
            is_common BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_labels_normalized ON labels(normalized);
        CREATE INDEX IF NOT EXISTS idx_labels_category ON labels(category);
        
        -- Schema migrations table
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Backup old task_labels table
    cursor.execute("ALTER TABLE task_labels RENAME TO task_labels_old")
    
    # Create new task_labels table with proper foreign key relationship
    cursor.execute("""
        CREATE TABLE task_labels (
            task_id TEXT NOT NULL,
            label_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (task_id, label_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for the new table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_labels_task ON task_labels(task_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_labels_label ON task_labels(label_id)")
    
    # Migrate data: insert labels and recreate relationships
    for task_id, label in old_labels:
        # Normalize label using same logic as SQLiteLabelRepository
        normalized = label.strip().lower()
        normalized = ' '.join(normalized.split())  # Remove multiple spaces
        normalized = normalized.replace(' ', '-')
        
        # Remove invalid characters (keep alphanumeric, hyphens, underscores, slashes)
        import re
        normalized = re.sub(r'[^a-z0-9\-_/]', '', normalized)
        normalized = re.sub(r'-+', '-', normalized)  # Remove multiple consecutive hyphens
        normalized = normalized.strip('-')  # Remove leading/trailing hyphens
        
        # Check if label exists
        cursor.execute("SELECT id FROM labels WHERE normalized = ?", (normalized,))
        result = cursor.fetchone()
        
        if result:
            label_id = result[0]
            # Increment usage count
            cursor.execute("UPDATE labels SET usage_count = usage_count + 1 WHERE id = ?", (label_id,))
        else:
            # Determine category based on common label patterns
            category = 'custom'
            is_common = 0
            
            if normalized in ['bug', 'urgent', 'critical', 'hotfix', 'blocker']:
                category = 'priority'
                is_common = 1
            elif normalized in ['feature', 'enhancement', 'refactor', 'documentation', 'testing', 'research', 'spike']:
                category = 'type'
                is_common = 1
            elif normalized in ['frontend', 'backend', 'api', 'database', 'ui-ux', 'infrastructure', 'devops', 'security']:
                category = 'component'
                is_common = 1
            elif normalized in ['code-review', 'qa', 'deployment', 'monitoring', 'performance', 'optimization']:
                category = 'process'
                is_common = 1
            elif normalized in ['blocked', 'waiting', 'ready', 'in-review', 'needs-clarification']:
                category = 'status'
                is_common = 1
            
            # Insert new label
            cursor.execute("""
                INSERT INTO labels (label, normalized, category, usage_count, is_common)
                VALUES (?, ?, ?, 1, ?)
            """, (label, normalized, category, is_common))
            label_id = cursor.lastrowid
        
        # Create relationship in new table
        cursor.execute("""
            INSERT OR IGNORE INTO task_labels (task_id, label_id)
            VALUES (?, ?)
        """, (task_id, label_id))
    
    # Create triggers for automatic usage count management
    cursor.executescript("""
        CREATE TRIGGER IF NOT EXISTS increment_label_usage
        AFTER INSERT ON task_labels
        FOR EACH ROW
        BEGIN
            UPDATE labels 
            SET usage_count = usage_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.label_id;
        END;
        
        CREATE TRIGGER IF NOT EXISTS decrement_label_usage
        AFTER DELETE ON task_labels
        FOR EACH ROW
        WHEN EXISTS (SELECT 1 FROM labels WHERE id = OLD.label_id)
        BEGIN
            UPDATE labels 
            SET usage_count = CASE 
                WHEN usage_count > 0 THEN usage_count - 1 
                ELSE 0 
            END,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = OLD.label_id;
        END;
    """)
    
    # Drop old table
    cursor.execute("DROP TABLE IF EXISTS task_labels_old")
    
    # Record migration
    cursor.execute("""
        INSERT OR REPLACE INTO schema_migrations (version, description)
        VALUES ('002', 'Migrate labels to new normalized schema')
    """)
    
    conn.commit()
    conn.close()

def verify_migration(db_path):
    """Verify the migration was successful"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 Migration Verification Results:")
    print("=" * 50)
    
    # Check labels table
    cursor.execute("SELECT COUNT(*) FROM labels")
    label_count = cursor.fetchone()[0]
    print(f"✅ Total labels in system: {label_count}")
    
    # Check common vs custom
    cursor.execute("SELECT COUNT(*) FROM labels WHERE is_common = 1")
    common_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM labels WHERE is_common = 0")
    custom_count = cursor.fetchone()[0]
    print(f"   - Common labels: {common_count}")
    print(f"   - Custom labels: {custom_count}")
    
    # Check categories
    print("\n📁 Labels by category:")
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM labels 
        GROUP BY category 
        ORDER BY count DESC
    """)
    for category, count in cursor.fetchall():
        print(f"   - {category}: {count}")
    
    # Check task labels preserved
    print("\n🏷️  Task label assignments:")
    cursor.execute("""
        SELECT t.title, GROUP_CONCAT(l.label, ', ') as labels
        FROM tasks t
        JOIN task_labels tl ON t.id = tl.task_id
        JOIN labels l ON tl.label_id = l.id
        GROUP BY t.id, t.title
    """)
    for title, labels in cursor.fetchall():
        print(f"   - {title}: {labels}")
    
    # Check for duplicates
    cursor.execute("""
        SELECT normalized, COUNT(*) as count 
        FROM labels 
        GROUP BY normalized 
        HAVING count > 1
    """)
    duplicates = cursor.fetchall()
    if duplicates:
        print("\n⚠️  Duplicate labels found:")
        for norm, count in duplicates:
            print(f"   - {norm}: {count} times")
    else:
        print("\n✅ No duplicate labels (normalization working correctly)")
    
    # Show some custom labels
    print("\n🎨 Custom labels migrated:")
    cursor.execute("""
        SELECT label, normalized 
        FROM labels 
        WHERE is_common = 0 
        LIMIT 5
    """)
    for label, normalized in cursor.fetchall():
        print(f"   - '{label}' -> '{normalized}'")
    
    conn.close()

def main():
    print("🔄 Label Migration Test")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Step 1: Create old schema with test data
        print("\n1️⃣  Creating database with old schema...")
        create_old_schema_db(db_path)
        print("   ✅ Old schema created with test data")
        
        # Step 2: Apply migration
        print("\n2️⃣  Applying migration...")
        apply_migration(db_path)
        print("   ✅ Migration completed")
        
        # Step 3: Verify results
        print("\n3️⃣  Verifying migration...")
        verify_migration(db_path)
        
        print("\n✅ Migration test completed successfully!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    main()