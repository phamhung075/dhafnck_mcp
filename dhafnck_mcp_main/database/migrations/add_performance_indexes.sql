-- Performance Indexes for Task Listing Optimization
-- These indexes dramatically improve query performance for task listing with subtasks
-- Updated 2025-08-17: Removed duplicate indexes

-- NOTE: idx_tasks_branch_status removed - covered by idx_tasks_branch_status_created
-- The composite index can serve queries filtering by (git_branch_id, status)

-- Index for filtering tasks by git_branch_id and priority
CREATE INDEX IF NOT EXISTS idx_tasks_branch_priority 
ON tasks(git_branch_id, priority, status, created_at DESC);

-- Index for ordering tasks by created_at (kept for queries that only sort by date)
CREATE INDEX IF NOT EXISTS idx_tasks_created_at 
ON tasks(created_at DESC);

-- Composite index for the most common query pattern
CREATE INDEX IF NOT EXISTS idx_tasks_branch_status_created 
ON tasks(git_branch_id, status, created_at DESC);

-- Index for subtask parent and status (renamed from idx_subtasks_task_id_status)
-- This supports both counting subtasks and filtering by status
CREATE INDEX IF NOT EXISTS idx_subtasks_parent_status 
ON task_subtasks(task_id, status);

-- Index for assignee lookups (single column is sufficient)
-- The models already define idx_assignee_task, no need for duplicate
-- CREATE INDEX IF NOT EXISTS idx_task_assignees_task_id ON task_assignees(task_id);
-- Skipped - already exists as idx_assignee_task

-- Index for dependency counts
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id 
ON task_dependencies(task_id);

-- NOTE: idx_task_labels_task_id removed - duplicate of idx_task_label_task
-- The model already defines idx_task_label_task which serves the same purpose

-- Performance statistics (run ANALYZE to update query planner)
ANALYZE tasks;
ANALYZE task_subtasks;
ANALYZE task_assignees;
ANALYZE task_dependencies;
ANALYZE task_labels;