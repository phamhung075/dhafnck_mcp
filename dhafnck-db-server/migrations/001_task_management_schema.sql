-- Task Management System Database Schema (PostgreSQL)
-- Converted from SQLite for dhafnck_mcp project
-- Date: 2025-07-03

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types for better type safety
CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done', 'blocked', 'cancelled');
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');

-- ===============================================
-- TASK MANAGEMENT SCHEMA
-- ===============================================

-- Main tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    project_id VARCHAR(100),
    status task_status NOT NULL DEFAULT 'todo',
    priority task_priority NOT NULL DEFAULT 'medium',
    details TEXT DEFAULT '',
    estimated_effort VARCHAR(50) DEFAULT '',
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    context_id VARCHAR(100),
    -- User/project/tree hierarchy support
    user_id VARCHAR(100) NOT NULL DEFAULT 'default_id',
    git_branch_name VARCHAR(100) NOT NULL DEFAULT 'main'
);

-- Indexes for performance
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_hierarchy ON tasks(user_id, project_id, git_branch_name);
CREATE INDEX idx_tasks_title_search ON tasks USING gin(to_tsvector('english', title));
CREATE INDEX idx_tasks_description_search ON tasks USING gin(to_tsvector('english', description));

-- Task assignees (many-to-many relationship)
CREATE TABLE task_assignees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    assignee VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(task_id, assignee)
);

CREATE INDEX idx_task_assignees_task_id ON task_assignees(task_id);
CREATE INDEX idx_task_assignees_assignee ON task_assignees(assignee);

-- Task labels (many-to-many relationship)
CREATE TABLE task_labels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    label VARCHAR(100) NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(task_id, label)
);

CREATE INDEX idx_task_labels_task_id ON task_labels(task_id);
CREATE INDEX idx_task_labels_label ON task_labels(label);

-- Task dependencies (many-to-many relationship)
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(task_id, depends_on_task_id),
    -- Prevent self-dependencies
    CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id)
);

CREATE INDEX idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);

-- Task subtasks
CREATE TABLE task_subtasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    completed BOOLEAN DEFAULT FALSE,
    assignee VARCHAR(100),
    estimated_effort VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_task_subtasks_task_id ON task_subtasks(task_id);
CREATE INDEX idx_task_subtasks_completed ON task_subtasks(completed);

-- Task tree structure for project hierarchies
CREATE TABLE task_trees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    project_id VARCHAR(100) NOT NULL,
    tree_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, project_id, tree_name)
);

CREATE INDEX idx_task_trees_user_project ON task_trees(user_id, project_id);

-- Task statistics materialized view for performance
CREATE MATERIALIZED VIEW task_statistics AS
SELECT 
    user_id,
    project_id,
    git_branch_name,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'todo' THEN 1 END) as todo_tasks,
    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN status = 'done' THEN 1 END) as done_tasks,
    COUNT(CASE WHEN status = 'blocked' THEN 1 END) as blocked_tasks,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_tasks,
    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_priority_tasks,
    COUNT(CASE WHEN priority = 'medium' THEN 1 END) as medium_priority_tasks,
    COUNT(CASE WHEN priority = 'low' THEN 1 END) as low_priority_tasks,
    COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent_priority_tasks
FROM tasks
GROUP BY user_id, project_id, git_branch_name;

-- Index for materialized view
CREATE INDEX idx_task_statistics_hierarchy ON task_statistics(user_id, project_id, git_branch_name);

-- Task completion progress view with subtask progress
CREATE VIEW task_completion_progress AS
SELECT 
    t.id as task_id,
    t.title,
    t.status,
    COUNT(st.id) as total_subtasks,
    COUNT(CASE WHEN st.completed = true THEN 1 END) as completed_subtasks,
    CASE 
        WHEN COUNT(st.id) = 0 THEN 0
        ELSE ROUND((COUNT(CASE WHEN st.completed = true THEN 1 END) * 100.0) / COUNT(st.id), 1)
    END as completion_percentage
FROM tasks t
LEFT JOIN task_subtasks st ON t.id = st.task_id
GROUP BY t.id, t.title, t.status;

-- ===============================================
-- MIGRATION SUPPORT TABLES
-- ===============================================

-- Track migration status
CREATE TABLE migration_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_type VARCHAR(50) NOT NULL,
    source_file VARCHAR(255),
    target_table VARCHAR(100),
    records_migrated INTEGER DEFAULT 0,
    migration_started_at TIMESTAMPTZ DEFAULT NOW(),
    migration_completed_at TIMESTAMPTZ,
    migration_status VARCHAR(20) DEFAULT 'started',
    migration_errors TEXT,
    notes TEXT
);

-- Task ID mapping for migration tracking
CREATE TABLE task_id_mapping (
    old_id VARCHAR(100),
    new_id UUID,
    migration_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (old_id, new_id)
);

-- ===============================================
-- FUNCTIONS AND TRIGGERS
-- ===============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update task updated_at timestamp
CREATE TRIGGER update_task_timestamp
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update subtask updated_at timestamp
CREATE TRIGGER update_subtask_timestamp
    BEFORE UPDATE ON task_subtasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to refresh task statistics materialized view
CREATE OR REPLACE FUNCTION refresh_task_statistics()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY task_statistics;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to refresh statistics after task changes
CREATE TRIGGER refresh_task_statistics_trigger
    AFTER INSERT OR UPDATE OR DELETE ON tasks
    FOR EACH STATEMENT
    EXECUTE FUNCTION refresh_task_statistics();

-- Function to prevent circular dependencies
CREATE OR REPLACE FUNCTION check_circular_dependency()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if adding this dependency would create a circular reference
    IF EXISTS (
        WITH RECURSIVE dependency_chain AS (
            SELECT depends_on_task_id as task_id
            FROM task_dependencies
            WHERE task_id = NEW.depends_on_task_id
            
            UNION ALL
            
            SELECT td.depends_on_task_id
            FROM task_dependencies td
            JOIN dependency_chain dc ON td.task_id = dc.task_id
        )
        SELECT 1 FROM dependency_chain WHERE task_id = NEW.task_id
    ) THEN
        RAISE EXCEPTION 'Circular dependency detected between tasks % and %', NEW.task_id, NEW.depends_on_task_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to check for circular dependencies
CREATE TRIGGER check_circular_dependency_trigger
    BEFORE INSERT ON task_dependencies
    FOR EACH ROW
    EXECUTE FUNCTION check_circular_dependency();

-- ===============================================
-- INITIAL DATA SETUP
-- ===============================================

-- Create default task tree
INSERT INTO task_trees (id, user_id, project_id, tree_name, description) 
VALUES (uuid_generate_v4(), 'default_id', 'dhafnck_mcp', 'main', 'Default main task tree')
ON CONFLICT (user_id, project_id, tree_name) DO NOTHING;

-- Refresh the materialized view
REFRESH MATERIALIZED VIEW task_statistics;