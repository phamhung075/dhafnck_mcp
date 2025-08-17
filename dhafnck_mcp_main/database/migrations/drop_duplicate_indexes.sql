-- Migration: Drop duplicate indexes for performance optimization
-- Date: 2025-08-17
-- Issue: Duplicate indexes cause unnecessary storage overhead and slow down write operations

-- ============================================
-- Table: task_labels
-- ============================================
-- Duplicate: idx_task_label_task and idx_task_labels_task_id both index (task_id)
-- Keep: idx_task_label_task (shorter name, same functionality)
DROP INDEX IF EXISTS idx_task_labels_task_id;

-- Note: idx_task_labels_lookup covers (task_id, label_id) which is more comprehensive
-- than single column indexes, but we keep idx_task_label_task for single column lookups

-- ============================================
-- Table: task_subtasks  
-- ============================================
-- Duplicate: idx_subtasks_parent_status and idx_subtasks_task_id_status both index (task_id, status)
-- Keep: idx_subtasks_parent_status (more descriptive name)
DROP INDEX IF EXISTS idx_subtasks_task_id_status;

-- Note: idx_subtask_task covers single column (task_id) lookups
-- idx_subtasks_parent_status covers (task_id, status) compound lookups
-- idx_subtasks_progress covers (task_id, progress_percentage) compound lookups

-- ============================================
-- Table: task_assignees
-- ============================================
-- idx_task_assignees_task_id is redundant because idx_assignees_task_lookup 
-- covers (task_id, assignee_id) and can be used for task_id lookups
-- However, keeping single column index for better performance on simple lookups

-- ============================================
-- Table: tasks
-- ============================================
-- Multiple overlapping indexes on git_branch_id with different column combinations:
-- - idx_tasks_git_branch: (git_branch_id) - basic single column
-- - idx_tasks_branch_status: (git_branch_id, status) - compound
-- - idx_tasks_branch_status_created: (git_branch_id, status, created_at) - compound with sort
-- - idx_tasks_efficient_list: (git_branch_id, status, priority, created_at) - most comprehensive
-- - idx_tasks_branch_priority: (git_branch_id, priority, status, created_at) - different order

-- Keep the most comprehensive ones and drop basic single column since compound indexes can serve single column queries
DROP INDEX IF EXISTS idx_tasks_git_branch; -- Covered by all compound indexes

-- idx_tasks_branch_status is covered by idx_tasks_branch_status_created
DROP INDEX IF EXISTS idx_tasks_branch_status;

-- Keep both idx_tasks_efficient_list and idx_tasks_branch_priority as they have different column orders
-- which can be optimal for different query patterns

-- ============================================
-- Summary of dropped indexes:
-- ============================================
-- 1. idx_task_labels_task_id (duplicate of idx_task_label_task)
-- 2. idx_subtasks_task_id_status (duplicate of idx_subtasks_parent_status)  
-- 3. idx_tasks_git_branch (covered by compound indexes)
-- 4. idx_tasks_branch_status (covered by idx_tasks_branch_status_created)

-- This will reduce index maintenance overhead and improve write performance
-- while maintaining all necessary query performance optimizations