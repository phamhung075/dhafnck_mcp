-- Performance Indexes for Task Listing Optimization
-- These indexes dramatically improve query performance for task listing with subtasks

-- Index for filtering tasks by git_branch_id and status (most common query)
CREATE INDEX IF NOT EXISTS idx_tasks_branch_status 
ON tasks(git_branch_id, status);

-- Index for filtering tasks by git_branch_id and priority
CREATE INDEX IF NOT EXISTS idx_tasks_branch_priority 
ON tasks(git_branch_id, priority);

-- Index for ordering tasks by created_at
CREATE INDEX IF NOT EXISTS idx_tasks_created_at 
ON tasks(created_at DESC);

-- Composite index for the most common query pattern
CREATE INDEX IF NOT EXISTS idx_tasks_branch_status_created 
ON tasks(git_branch_id, status, created_at DESC);

-- Index for subtask counts (foreign key relationship)
CREATE INDEX IF NOT EXISTS idx_subtasks_task_id_status 
ON task_subtasks(task_id, status);

-- Index for assignee counts
CREATE INDEX IF NOT EXISTS idx_task_assignees_task_id 
ON task_assignees(task_id);

-- Index for dependency counts
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id 
ON task_dependencies(task_id);

-- Index for label relationships
CREATE INDEX IF NOT EXISTS idx_task_labels_task_id 
ON task_labels(task_id);

-- Performance statistics (run ANALYZE to update query planner)
ANALYZE tasks;
ANALYZE task_subtasks;
ANALYZE task_assignees;
ANALYZE task_dependencies;
ANALYZE task_labels;