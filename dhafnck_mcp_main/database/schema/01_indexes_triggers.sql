-- ===============================================
-- DHAFNCK MCP INDEXES AND TRIGGERS v6.0
-- Performance optimization and data integrity
-- ===============================================

-- ===============================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ===============================================

-- Projects and task trees
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_project_task_trees_project ON project_task_trees(project_id);
CREATE INDEX IF NOT EXISTS idx_project_task_trees_name ON project_task_trees(name, project_id);
CREATE INDEX IF NOT EXISTS idx_project_task_trees_status ON project_task_trees(status);
CREATE INDEX IF NOT EXISTS idx_project_task_trees_assigned_agent ON project_task_trees(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_project_task_trees_priority ON project_task_trees(priority);
CREATE INDEX IF NOT EXISTS idx_project_task_trees_created_at ON project_task_trees(created_at);

-- Tasks
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_git_branch_id ON tasks(git_branch_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_context_id ON tasks(context_id);

-- Subtasks
CREATE INDEX IF NOT EXISTS idx_task_subtasks_task_id ON task_subtasks(task_id);
CREATE INDEX IF NOT EXISTS idx_task_subtasks_status ON task_subtasks(status);
CREATE INDEX IF NOT EXISTS idx_task_subtasks_priority ON task_subtasks(priority);
CREATE INDEX IF NOT EXISTS idx_task_subtasks_progress ON task_subtasks(progress_percentage);

-- Task dependencies
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_type ON task_dependencies(dependency_type);

-- Project cross tree dependencies
CREATE INDEX IF NOT EXISTS idx_project_cross_tree_deps_project ON project_cross_tree_dependencies(project_id);
CREATE INDEX IF NOT EXISTS idx_project_cross_tree_deps_dependent ON project_cross_tree_dependencies(dependent_task_id);
CREATE INDEX IF NOT EXISTS idx_project_cross_tree_deps_prerequisite ON project_cross_tree_dependencies(prerequisite_task_id);

-- Project work sessions
CREATE INDEX IF NOT EXISTS idx_project_work_sessions_project ON project_work_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_project_work_sessions_agent ON project_work_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_project_work_sessions_task ON project_work_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_project_work_sessions_status ON project_work_sessions(status);
CREATE INDEX IF NOT EXISTS idx_project_work_sessions_started ON project_work_sessions(started_at);

-- Project resource locks
CREATE INDEX IF NOT EXISTS idx_project_resource_locks_project ON project_resource_locks(project_id);
CREATE INDEX IF NOT EXISTS idx_project_resource_locks_resource ON project_resource_locks(resource_name);
CREATE INDEX IF NOT EXISTS idx_project_resource_locks_agent ON project_resource_locks(locked_by_agent_id);
CREATE INDEX IF NOT EXISTS idx_project_resource_locks_expires ON project_resource_locks(expires_at);

-- Agents
CREATE INDEX IF NOT EXISTS idx_project_agents_project ON project_agents(project_id);
CREATE INDEX IF NOT EXISTS idx_project_agents_status ON project_agents(status);
CREATE INDEX IF NOT EXISTS idx_project_agents_workload ON project_agents(current_workload);
CREATE INDEX IF NOT EXISTS idx_project_agent_assignments_agent ON project_agent_assignments(agent_id);
CREATE INDEX IF NOT EXISTS idx_project_agent_assignments_branch ON project_agent_assignments(git_branch_id);

-- Agent coordination
CREATE INDEX IF NOT EXISTS idx_coordination_requests_agent ON coordination_requests(requesting_agent_id);
CREATE INDEX IF NOT EXISTS idx_coordination_requests_target ON coordination_requests(target_agent_id);
CREATE INDEX IF NOT EXISTS idx_coordination_requests_type ON coordination_requests(coordination_type);
CREATE INDEX IF NOT EXISTS idx_work_assignments_task ON work_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_work_assignments_agent ON work_assignments(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_work_assignments_completed ON work_assignments(is_completed);
CREATE INDEX IF NOT EXISTS idx_work_handoffs_task ON work_handoffs(task_id);
CREATE INDEX IF NOT EXISTS idx_work_handoffs_from_agent ON work_handoffs(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_work_handoffs_to_agent ON work_handoffs(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_work_handoffs_status ON work_handoffs(status);
CREATE INDEX IF NOT EXISTS idx_conflict_resolutions_task ON conflict_resolutions(task_id);
CREATE INDEX IF NOT EXISTS idx_conflict_resolutions_resolved ON conflict_resolutions(is_resolved);
CREATE INDEX IF NOT EXISTS idx_agent_communications_from ON agent_communications(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_communications_task ON agent_communications(task_id);

-- Hierarchical contexts
CREATE INDEX IF NOT EXISTS idx_global_contexts_org ON global_contexts(organization_id);
CREATE INDEX IF NOT EXISTS idx_global_contexts_updated ON global_contexts(updated_at);
CREATE INDEX IF NOT EXISTS idx_project_contexts_global ON project_contexts(parent_global_id);
CREATE INDEX IF NOT EXISTS idx_project_contexts_updated ON project_contexts(updated_at);
CREATE INDEX IF NOT EXISTS idx_project_contexts_inherited ON project_contexts(last_inherited);
CREATE INDEX IF NOT EXISTS idx_project_contexts_inheritance_disabled ON project_contexts(inheritance_disabled);
CREATE INDEX IF NOT EXISTS idx_task_contexts_project ON task_contexts(parent_project_context_id);
CREATE INDEX IF NOT EXISTS idx_task_contexts_project_id ON task_contexts(parent_project_id);
CREATE INDEX IF NOT EXISTS idx_task_contexts_resolved_at ON task_contexts(resolved_at);
CREATE INDEX IF NOT EXISTS idx_task_contexts_updated ON task_contexts(updated_at);
CREATE INDEX IF NOT EXISTS idx_task_contexts_inheritance ON task_contexts(inheritance_disabled, force_local_only);
CREATE INDEX IF NOT EXISTS idx_task_contexts_dependencies_hash ON task_contexts(dependencies_hash);

-- Context insights
CREATE INDEX IF NOT EXISTS idx_context_insights_context ON context_insights(context_id, context_type);
CREATE INDEX IF NOT EXISTS idx_context_insights_category ON context_insights(category);
CREATE INDEX IF NOT EXISTS idx_context_insights_importance ON context_insights(importance);
CREATE INDEX IF NOT EXISTS idx_context_insights_actionable ON context_insights(actionable);
CREATE INDEX IF NOT EXISTS idx_context_insights_created_at ON context_insights(created_at);
CREATE INDEX IF NOT EXISTS idx_context_insights_expires_at ON context_insights(expires_at);

-- Context delegations
CREATE INDEX IF NOT EXISTS idx_delegations_source ON context_delegations(source_level, source_id);
CREATE INDEX IF NOT EXISTS idx_delegations_target ON context_delegations(target_level, target_id);
CREATE INDEX IF NOT EXISTS idx_delegations_processed ON context_delegations(processed, auto_delegated);
CREATE INDEX IF NOT EXISTS idx_delegations_created_at ON context_delegations(created_at);
CREATE INDEX IF NOT EXISTS idx_delegations_trigger_type ON context_delegations(trigger_type);
CREATE INDEX IF NOT EXISTS idx_delegations_status ON context_delegations(implementation_status);

-- Context cache
CREATE INDEX IF NOT EXISTS idx_cache_expires ON context_inheritance_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_dependencies ON context_inheritance_cache(dependencies_hash);
CREATE INDEX IF NOT EXISTS idx_cache_hit_count ON context_inheritance_cache(hit_count DESC);
CREATE INDEX IF NOT EXISTS idx_cache_invalidated ON context_inheritance_cache(invalidated);

-- Context propagations
CREATE INDEX IF NOT EXISTS idx_propagations_source ON context_propagations(source_level, source_id);
CREATE INDEX IF NOT EXISTS idx_propagations_status ON context_propagations(propagation_status);
CREATE INDEX IF NOT EXISTS idx_propagations_created_at ON context_propagations(created_at);

-- Labels
CREATE INDEX IF NOT EXISTS idx_labels_normalized ON labels(normalized);
CREATE INDEX IF NOT EXISTS idx_labels_category ON labels(category);
CREATE INDEX IF NOT EXISTS idx_labels_usage_count ON labels(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_task_labels_task ON task_labels(task_id);
CREATE INDEX IF NOT EXISTS idx_task_labels_label ON task_labels(label_id);

-- Templates
CREATE INDEX IF NOT EXISTS idx_templates_type ON templates(type);
CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_active ON templates(active);
CREATE INDEX IF NOT EXISTS idx_templates_usage_count ON templates(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_template_usage_template ON template_usage(template_id);
CREATE INDEX IF NOT EXISTS idx_template_usage_context ON template_usage(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_template_cache_expires ON template_cache(expires_at);

-- Checklists
CREATE INDEX IF NOT EXISTS idx_checklists_category ON checklists(category);
CREATE INDEX IF NOT EXISTS idx_checklists_scope ON checklists(scope);
CREATE INDEX IF NOT EXISTS idx_checklists_auto_apply ON checklists(auto_apply);
CREATE INDEX IF NOT EXISTS idx_checklist_items_checklist ON checklist_items(checklist_id);
CREATE INDEX IF NOT EXISTS idx_checklist_items_order ON checklist_items(order_index);
CREATE INDEX IF NOT EXISTS idx_checklist_progress_context ON checklist_progress(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_checklist_progress_completion ON checklist_progress(completion_percentage);
CREATE INDEX IF NOT EXISTS idx_checklist_item_completion_progress ON checklist_item_completion(progress_id);
CREATE INDEX IF NOT EXISTS idx_checklist_item_completion_item ON checklist_item_completion(item_id);

-- Audit and migration
CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit_log(changed_by);

-- ===============================================
-- TRIGGERS FOR DATA INTEGRITY AND AUTOMATION
-- ===============================================

-- Update timestamps
CREATE TRIGGER IF NOT EXISTS update_project_timestamp 
    AFTER UPDATE ON projects
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_task_tree_timestamp 
    AFTER UPDATE ON project_task_trees
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE project_task_trees SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_task_timestamp 
    AFTER UPDATE ON tasks
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_subtask_timestamp 
    AFTER UPDATE ON task_subtasks
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE task_subtasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_agent_timestamp 
    AFTER UPDATE ON project_agents
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE project_agents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id AND project_id = NEW.project_id;
END;

-- Update task when subtasks change
CREATE TRIGGER IF NOT EXISTS update_task_on_subtask_change 
    AFTER UPDATE ON task_subtasks
    FOR EACH ROW 
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.task_id;
END;

-- Update task count on project_task_trees
CREATE TRIGGER IF NOT EXISTS update_task_count_on_insert
    AFTER INSERT ON tasks
    FOR EACH ROW
BEGIN
    UPDATE project_task_trees 
    SET task_count = task_count + 1 
    WHERE id = NEW.git_branch_id;
END;

CREATE TRIGGER IF NOT EXISTS update_task_count_on_delete
    AFTER DELETE ON tasks
    FOR EACH ROW
BEGIN
    UPDATE project_task_trees 
    SET task_count = task_count - 1 
    WHERE id = OLD.git_branch_id;
END;

CREATE TRIGGER IF NOT EXISTS update_completed_count_on_status_change
    AFTER UPDATE OF status ON tasks
    FOR EACH ROW
    WHEN OLD.status != NEW.status
BEGIN
    UPDATE project_task_trees 
    SET completed_task_count = completed_task_count + 
        CASE WHEN NEW.status = 'done' THEN 1 ELSE 0 END -
        CASE WHEN OLD.status = 'done' THEN 1 ELSE 0 END
    WHERE id = NEW.git_branch_id;
END;

-- Context system triggers
CREATE TRIGGER IF NOT EXISTS update_global_context_timestamp 
    AFTER UPDATE ON global_contexts
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE global_contexts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_project_context_timestamp 
    AFTER UPDATE ON project_contexts
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE project_contexts SET updated_at = CURRENT_TIMESTAMP WHERE project_id = NEW.project_id;
END;

CREATE TRIGGER IF NOT EXISTS update_task_context_timestamp 
    AFTER UPDATE ON task_contexts
    FOR EACH ROW 
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE task_contexts SET updated_at = CURRENT_TIMESTAMP WHERE task_id = NEW.task_id;
END;

-- Auto-invalidate cache on context changes
CREATE TRIGGER IF NOT EXISTS invalidate_cache_on_global_change
    AFTER UPDATE ON global_contexts
    FOR EACH ROW
BEGIN
    UPDATE context_inheritance_cache SET invalidated = 1, invalidation_reason = 'global_context_updated' 
    WHERE context_level IN ('project', 'task');
END;

CREATE TRIGGER IF NOT EXISTS invalidate_cache_on_project_change
    AFTER UPDATE ON project_contexts
    FOR EACH ROW
BEGIN
    UPDATE context_inheritance_cache SET invalidated = 1, invalidation_reason = 'project_context_updated'
    WHERE (context_level = 'task' AND context_id IN (
        SELECT task_id FROM task_contexts WHERE parent_project_context_id = NEW.project_id
    )) OR (context_level = 'project' AND context_id = NEW.project_id);
END;

CREATE TRIGGER IF NOT EXISTS invalidate_cache_on_task_change
    AFTER UPDATE ON task_contexts
    FOR EACH ROW
BEGIN
    UPDATE context_inheritance_cache SET invalidated = 1, invalidation_reason = 'task_context_updated'
    WHERE context_level = 'task' AND context_id = NEW.task_id;
END;

-- Label usage count updates
CREATE TRIGGER IF NOT EXISTS increment_label_usage
    AFTER INSERT ON task_labels
    FOR EACH ROW
BEGIN
    UPDATE labels SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.label_id;
END;

CREATE TRIGGER IF NOT EXISTS decrement_label_usage
    AFTER DELETE ON task_labels
    FOR EACH ROW
BEGIN
    UPDATE labels SET usage_count = usage_count - 1, updated_at = CURRENT_TIMESTAMP 
    WHERE id = OLD.label_id;
END;

-- Template usage tracking
CREATE TRIGGER IF NOT EXISTS update_template_usage_on_use
    AFTER INSERT ON template_usage
    FOR EACH ROW
BEGIN
    UPDATE templates 
    SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP 
    WHERE id = NEW.template_id;
END;

-- Checklist progress automation
CREATE TRIGGER IF NOT EXISTS update_checklist_progress_on_item_completion
    AFTER UPDATE ON checklist_item_completion
    FOR EACH ROW
    WHEN NEW.completed != OLD.completed
BEGIN
    UPDATE checklist_progress 
    SET completion_percentage = (
        SELECT ROUND(
            (COUNT(CASE WHEN completed = 1 THEN 1 END) * 100.0) / COUNT(*), 2
        )
        FROM checklist_item_completion 
        WHERE progress_id = NEW.progress_id
    ),
    completed_at = CASE 
        WHEN (
            SELECT COUNT(CASE WHEN completed = 0 THEN 1 END) 
            FROM checklist_item_completion 
            WHERE progress_id = NEW.progress_id
        ) = 0 THEN CURRENT_TIMESTAMP 
        ELSE NULL 
    END
    WHERE id = NEW.progress_id;
END;

-- Audit logging triggers
CREATE TRIGGER IF NOT EXISTS audit_tasks_insert
    AFTER INSERT ON tasks
    FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, operation, record_id, new_values, changed_by)
    VALUES ('tasks', 'INSERT', NEW.id, json_object(
        'title', NEW.title,
        'description', NEW.description,
        'git_branch_id', NEW.git_branch_id,
        'status', NEW.status,
        'priority', NEW.priority
    ), 'system');
END;

CREATE TRIGGER IF NOT EXISTS audit_tasks_update
    AFTER UPDATE ON tasks
    FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, operation, record_id, old_values, new_values, changed_by)
    VALUES ('tasks', 'UPDATE', NEW.id, json_object(
        'title', OLD.title,
        'description', OLD.description,
        'status', OLD.status,
        'priority', OLD.priority
    ), json_object(
        'title', NEW.title,
        'description', NEW.description,
        'status', NEW.status,
        'priority', NEW.priority
    ), 'system');
END;

CREATE TRIGGER IF NOT EXISTS audit_tasks_delete
    AFTER DELETE ON tasks
    FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, operation, record_id, old_values, changed_by)
    VALUES ('tasks', 'DELETE', OLD.id, json_object(
        'title', OLD.title,
        'description', OLD.description,
        'status', OLD.status,
        'priority', OLD.priority
    ), 'system');
END;