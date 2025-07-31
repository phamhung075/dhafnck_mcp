#!/usr/bin/env python3
"""
Simple test to verify label functionality
"""
import sqlite3
import tempfile
import os

def test_label_functionality():
    """Test basic label functionality"""
    print("🏷️  Label Functionality Test")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Create minimal schema for testing
        conn.executescript("""
            -- Create tasks table
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL
            );
            
            -- Create labels table
            CREATE TABLE labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                normalized TEXT NOT NULL UNIQUE,
                category TEXT DEFAULT 'custom',
                usage_count INTEGER DEFAULT 0,
                is_common BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create task_labels junction table
            CREATE TABLE task_labels (
                task_id TEXT NOT NULL,
                label_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (task_id, label_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
            );
            
            -- Create indexes
            CREATE INDEX idx_labels_normalized ON labels(normalized);
            CREATE INDEX idx_task_labels_task ON task_labels(task_id);
            CREATE INDEX idx_task_labels_label ON task_labels(label_id);
            
            -- Create triggers
            CREATE TRIGGER increment_label_usage
            AFTER INSERT ON task_labels
            BEGIN
                UPDATE labels 
                SET usage_count = usage_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.label_id;
            END;
            
            CREATE TRIGGER decrement_label_usage
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
        
        print("✅ Schema created successfully")
        
        # Test 1: Create labels
        print("\n1️⃣  Testing label creation...")
        cursor = conn.cursor()
        
        test_labels = [
            ("Platform", "platform", "custom"),
            ("Enterprise", "enterprise", "custom"),
            ("AI Orchestration", "ai-orchestration", "custom"),
            ("bug", "bug", "type"),
            ("feature", "feature", "type")
        ]
        
        for label, normalized, category in test_labels:
            cursor.execute("""
                INSERT OR IGNORE INTO labels (label, normalized, category, is_common)
                VALUES (?, ?, ?, ?)
            """, (label, normalized, category, 1 if category != "custom" else 0))
        
        conn.commit()
        print("   ✅ Labels created")
        
        # Test 2: Create task and assign labels
        print("\n2️⃣  Testing task label assignment...")
        
        # Create a task
        cursor.execute("INSERT INTO tasks (id, title) VALUES (?, ?) ON CONFLICT (name) DO UPDATE SET updated_at = labels.updated_at", 
                      ("task-1", "Test Task"))
        
        # Assign labels to task
        cursor.execute("SELECT id FROM labels WHERE normalized IN (?, ?, ?)",
                      ("platform", "enterprise", "bug"))
        label_ids = [row[0] for row in cursor.fetchall()]
        
        for label_id in label_ids:
            cursor.execute("INSERT INTO task_labels (task_id, label_id) VALUES (?, ?) ON CONFLICT (id) DO NOTHING",
                          ("task-1", label_id))
        
        conn.commit()
        print("   ✅ Labels assigned to task")
        
        # Test 3: Verify usage counts
        print("\n3️⃣  Testing usage count triggers...")
        
        cursor.execute("""
            SELECT label, usage_count 
            FROM labels 
            WHERE normalized IN ('platform', 'enterprise', 'bug')
            ORDER BY label
        """)
        
        for label, count in cursor.fetchall():
            print(f"   - {label}: {count} uses")
            assert count == 1, f"Expected usage count 1, got {count}"
        
        print("   ✅ Usage counts updated correctly")
        
        # Test 4: Test duplicate prevention
        print("\n4️⃣  Testing duplicate prevention...")
        
        # Try to insert duplicate with different case
        cursor.execute("""
            INSERT OR IGNORE INTO labels (label, normalized, category)
            VALUES (?, ?, ?)
        """, ("PLATFORM", "platform", "custom"))
        
        cursor.execute("SELECT COUNT(*) FROM labels WHERE normalized = ?", ("platform",))
        count = cursor.fetchone()[0]
        assert count == 1, f"Expected 1 label, found {count}"
        
        print("   ✅ Duplicate prevention working")
        
        # Test 5: Query task labels
        print("\n5️⃣  Testing label queries...")
        
        cursor.execute("""
            SELECT l.label, l.category
            FROM labels l
            JOIN task_labels tl ON l.id = tl.label_id
            WHERE tl.task_id = ?
            ORDER BY l.label
        """, ("task-1",))
        
        task_labels = cursor.fetchall()
        print(f"   Task has {len(task_labels)} labels:")
        for label, category in task_labels:
            print(f"   - {label} ({category})")
        
        # Test 6: Remove label and check usage count
        print("\n6️⃣  Testing label removal...")
        
        cursor.execute("""
            DELETE FROM task_labels 
            WHERE task_id = ? AND label_id = (
                SELECT id FROM labels WHERE normalized = ?
            )
        """, ("task-1", "bug"))
        
        cursor.execute("SELECT usage_count FROM labels WHERE normalized = ?", ("bug",))
        count = cursor.fetchone()[0]
        assert count == 0, f"Expected usage count 0 after removal, got {count}"
        
        print("   ✅ Label removal and usage count update working")
        
        conn.close()
        print("\n✅ All label functionality tests passed!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    test_label_functionality()