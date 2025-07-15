-- Migration: Add Vision System context fields
-- Date: 2025-01-09
-- Description: Adds mandatory fields for Vision System context enforcement

BEGIN TRANSACTION;

-- Check if migration has already been applied
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Only apply migration if not already applied
INSERT OR IGNORE INTO migration_history (migration_name) 
VALUES ('001_add_vision_context_fields');

-- Add vision system fields to contexts table if they don't exist
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we need to handle this carefully

-- Note: In SQLite, we can't easily check if columns exist before adding them
-- In production, you might want to use a more sophisticated migration tool
-- For now, we'll document the changes needed:

-- The following columns need to be added to any existing context storage:
-- 1. completion_summary TEXT - Required when task is completed
-- 2. testing_notes TEXT - Optional but recommended
-- 3. next_recommendations TEXT - Optional but recommended  
-- 4. vision_alignment_score REAL - Vision hierarchy alignment score

-- Since contexts are stored as JSON in the current implementation,
-- these fields will be added to the progress section of the context JSON structure
-- No actual table alterations are needed for the JSON-based storage

-- Add overall_progress column to tasks table if using direct SQL storage
-- ALTER TABLE tasks ADD COLUMN overall_progress REAL DEFAULT 0;

-- Add is_strategic_priority column to tasks table if using direct SQL storage
-- ALTER TABLE tasks ADD COLUMN is_strategic_priority BOOLEAN DEFAULT FALSE;

-- Create indexes for better query performance
-- CREATE INDEX IF NOT EXISTS idx_tasks_overall_progress ON tasks(overall_progress);
-- CREATE INDEX IF NOT EXISTS idx_tasks_strategic_priority ON tasks(is_strategic_priority);

-- Log successful migration
INSERT INTO migration_history (migration_name, applied_at) 
VALUES ('001_add_vision_context_fields_completed', CURRENT_TIMESTAMP)
ON CONFLICT(migration_name) DO NOTHING;

COMMIT;

-- Rollback script (save separately)
-- BEGIN TRANSACTION;
-- No rollback needed for JSON-based context storage
-- DELETE FROM migration_history WHERE migration_name IN ('001_add_vision_context_fields', '001_add_vision_context_fields_completed');
-- COMMIT;