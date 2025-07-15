-- ===============================================
-- DHAFNCK MCP VIEWS AND STATISTICS v6.0
-- Reporting and analytics views
-- ===============================================

-- ===============================================
-- CORE STATISTICS VIEWS
-- ===============================================

-- Task statistics by project and branch
CREATE VIEW IF NOT EXISTS task_statistics AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    ptt.id as git_branch_id,
    ptt.name as git_branch_name,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'todo' THEN 1 END) as todo_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'done' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'blocked' THEN 1 END) as blocked_tasks,
    ROUND(
        (COUNT(CASE WHEN t.status = 'done' THEN 1 END) * 100.0) / 
        NULLIF(COUNT(t.id), 0), 2
    ) as completion_percentage,
    COUNT(CASE WHEN t.priority = 'critical' THEN 1 END) as critical_tasks,
    COUNT(CASE WHEN t.priority = 'high' THEN 1 END) as high_priority_tasks,
    COUNT(CASE WHEN t.priority = 'medium' THEN 1 END) as medium_priority_tasks,
    COUNT(CASE WHEN t.priority = 'low' THEN 1 END) as low_priority_tasks,
    MIN(t.created_at) as oldest_task_date,
    MAX(t.created_at) as newest_task_date,
    COUNT(CASE WHEN t.due_date IS NOT NULL AND t.due_date < datetime('now') AND t.status != 'done' THEN 1 END) as overdue_tasks
FROM projects p
LEFT JOIN project_task_trees ptt ON p.id = ptt.project_id
LEFT JOIN tasks t ON ptt.id = t.git_branch_id
GROUP BY p.id, p.name, ptt.id, ptt.name;

-- Subtask progress summary
CREATE VIEW IF NOT EXISTS subtask_progress AS
SELECT 
    t.id as task_id,
    t.title as task_title,
    t.status as task_status,
    COUNT(ts.id) as total_subtasks,
    COUNT(CASE WHEN ts.status = 'todo' THEN 1 END) as todo_subtasks,
    COUNT(CASE WHEN ts.status = 'in_progress' THEN 1 END) as in_progress_subtasks,
    COUNT(CASE WHEN ts.status = 'done' THEN 1 END) as completed_subtasks,
    ROUND(
        (COUNT(CASE WHEN ts.status = 'done' THEN 1 END) * 100.0) / 
        NULLIF(COUNT(ts.id), 0), 2
    ) as subtask_completion_percentage,
    ROUND(AVG(ts.progress_percentage), 2) as average_progress_percentage,
    GROUP_CONCAT(
        CASE WHEN ts.blockers != '' AND ts.blockers IS NOT NULL 
        THEN ts.title || ': ' || ts.blockers 
        END, '; '
    ) as active_blockers
FROM tasks t
LEFT JOIN task_subtasks ts ON t.id = ts.task_id
GROUP BY t.id, t.title, t.status;

-- Agent workload and performance
CREATE VIEW IF NOT EXISTS agent_workload AS
SELECT 
    pa.project_id,
    pa.id as agent_id,
    pa.name as agent_name,
    pa.status,
    pa.current_workload,
    pa.max_concurrent_tasks,
    pa.completed_tasks,
    pa.success_rate,
    pa.average_task_duration,
    COUNT(wa.id) as active_assignments,
    COUNT(CASE WHEN wa.status = 'assigned' THEN 1 END) as pending_assignments,
    COUNT(CASE WHEN wa.status = 'in_progress' THEN 1 END) as in_progress_assignments,
    COUNT(CASE WHEN wa.status = 'completed' THEN 1 END) as completed_assignments,
    ROUND(
        pa.current_workload * 100.0 / NULLIF(pa.max_concurrent_tasks, 0), 2
    ) as workload_percentage,
    CASE 
        WHEN pa.current_workload >= pa.max_concurrent_tasks THEN 'overloaded'
        WHEN pa.current_workload >= pa.max_concurrent_tasks * 0.8 THEN 'high'
        WHEN pa.current_workload >= pa.max_concurrent_tasks * 0.5 THEN 'medium'
        ELSE 'low'
    END as workload_status
FROM project_agents pa
LEFT JOIN work_assignments wa ON pa.id = wa.agent_id
GROUP BY pa.project_id, pa.id, pa.name, pa.status, pa.current_workload, 
         pa.max_concurrent_tasks, pa.completed_tasks, pa.success_rate, pa.average_task_duration;

-- Context system health
CREATE VIEW IF NOT EXISTS context_health AS
SELECT 
    'global' as level,
    COUNT(*) as total_contexts,
    COUNT(CASE WHEN updated_at > datetime('now', '-1 day') THEN 1 END) as recently_updated,
    COUNT(CASE WHEN delegation_rules IS NOT NULL THEN 1 END) as with_delegation_rules,
    AVG(version) as average_version
FROM global_contexts
UNION ALL
SELECT 
    'project' as level,
    COUNT(*) as total_contexts,
    COUNT(CASE WHEN updated_at > datetime('now', '-1 day') THEN 1 END) as recently_updated,
    COUNT(CASE WHEN inheritance_disabled = 0 THEN 1 END) as with_inheritance,
    AVG(version) as average_version
FROM project_contexts
UNION ALL
SELECT 
    'task' as level,
    COUNT(*) as total_contexts,
    COUNT(CASE WHEN updated_at > datetime('now', '-1 day') THEN 1 END) as recently_updated,
    COUNT(CASE WHEN resolved_context IS NOT NULL THEN 1 END) as with_resolved_cache,
    AVG(version) as average_version
FROM task_contexts;

-- Label usage analytics
CREATE VIEW IF NOT EXISTS label_analytics AS
SELECT 
    l.id,
    l.label,
    l.category,
    l.usage_count,
    l.is_common,
    COUNT(tl.task_id) as active_task_count,
    l.usage_count - COUNT(tl.task_id) as historical_usage,
    ROUND(
        (COUNT(tl.task_id) * 100.0) / NULLIF(l.usage_count, 0), 2
    ) as current_usage_percentage,
    MIN(tl.added_at) as first_used,
    MAX(tl.added_at) as last_used,
    julianday('now') - julianday(MAX(tl.added_at)) as days_since_last_use
FROM labels l
LEFT JOIN task_labels tl ON l.id = tl.label_id
GROUP BY l.id, l.label, l.category, l.usage_count, l.is_common
ORDER BY l.usage_count DESC;

-- Template effectiveness
CREATE VIEW IF NOT EXISTS template_effectiveness AS
SELECT 
    t.id,
    t.name,
    t.type,
    t.category,
    t.usage_count,
    t.success_rate,
    t.active,
    COUNT(tu.id) as total_usages,
    COUNT(CASE WHEN tu.outcome = 'success' THEN 1 END) as successful_usages,
    COUNT(CASE WHEN tu.outcome = 'failure' THEN 1 END) as failed_usages,
    COUNT(CASE WHEN tu.outcome = 'pending' THEN 1 END) as pending_usages,
    ROUND(
        (COUNT(CASE WHEN tu.outcome = 'success' THEN 1 END) * 100.0) / 
        NULLIF(COUNT(CASE WHEN tu.outcome IN ('success', 'failure') THEN 1 END), 0), 2
    ) as actual_success_rate,
    AVG(tu.duration_seconds) as average_duration,
    AVG(tu.feedback_score) as average_feedback_score,
    julianday('now') - julianday(t.last_used) as days_since_last_use
FROM templates t
LEFT JOIN template_usage tu ON t.id = tu.template_id
WHERE t.active = 1
GROUP BY t.id, t.name, t.type, t.category, t.usage_count, t.success_rate, t.active
ORDER BY t.usage_count DESC;

-- Checklist completion analytics
CREATE VIEW IF NOT EXISTS checklist_analytics AS
SELECT 
    c.id,
    c.name,
    c.category,
    c.scope,
    c.auto_apply,
    COUNT(cp.id) as total_instances,
    COUNT(CASE WHEN cp.completed_at IS NOT NULL THEN 1 END) as completed_instances,
    ROUND(
        (COUNT(CASE WHEN cp.completed_at IS NOT NULL THEN 1 END) * 100.0) / 
        NULLIF(COUNT(cp.id), 0), 2
    ) as completion_rate,
    AVG(cp.completion_percentage) as average_completion_percentage,
    AVG(
        CASE WHEN cp.completed_at IS NOT NULL 
        THEN julianday(cp.completed_at) - julianday(cp.started_at) 
        END
    ) as average_completion_days,
    COUNT(ci.id) as total_items,
    AVG(
        CASE WHEN ci.estimated_duration IS NOT NULL 
        THEN ci.estimated_duration 
        END
    ) as average_estimated_duration
FROM checklists c
LEFT JOIN checklist_progress cp ON c.id = cp.checklist_id
LEFT JOIN checklist_items ci ON c.id = ci.checklist_id
WHERE c.active = 1
GROUP BY c.id, c.name, c.category, c.scope, c.auto_apply
ORDER BY completion_rate DESC;

-- ===============================================
-- SYSTEM HEALTH AND MONITORING VIEWS
-- ===============================================

-- Database health overview
CREATE VIEW IF NOT EXISTS database_health AS
SELECT 
    'tasks' as table_name,
    COUNT(*) as record_count,
    COUNT(CASE WHEN created_at > datetime('now', '-1 day') THEN 1 END) as recent_additions,
    COUNT(CASE WHEN updated_at > datetime('now', '-1 day') THEN 1 END) as recent_updates,
    MAX(updated_at) as last_activity
FROM tasks
UNION ALL
SELECT 
    'subtasks' as table_name,
    COUNT(*) as record_count,
    COUNT(CASE WHEN created_at > datetime('now', '-1 day') THEN 1 END) as recent_additions,
    COUNT(CASE WHEN updated_at > datetime('now', '-1 day') THEN 1 END) as recent_updates,
    MAX(updated_at) as last_activity
FROM task_subtasks
UNION ALL
SELECT 
    'agents' as table_name,
    COUNT(*) as record_count,
    COUNT(CASE WHEN created_at > datetime('now', '-1 day') THEN 1 END) as recent_additions,
    COUNT(CASE WHEN updated_at > datetime('now', '-1 day') THEN 1 END) as recent_updates,
    MAX(updated_at) as last_activity
FROM project_agents
UNION ALL
SELECT 
    'contexts' as table_name,
    (SELECT COUNT(*) FROM global_contexts) + 
    (SELECT COUNT(*) FROM project_contexts) + 
    (SELECT COUNT(*) FROM task_contexts) as record_count,
    (SELECT COUNT(*) FROM global_contexts WHERE updated_at > datetime('now', '-1 day')) +
    (SELECT COUNT(*) FROM project_contexts WHERE updated_at > datetime('now', '-1 day')) +
    (SELECT COUNT(*) FROM task_contexts WHERE updated_at > datetime('now', '-1 day')) as recent_additions,
    (SELECT COUNT(*) FROM global_contexts WHERE updated_at > datetime('now', '-1 day')) +
    (SELECT COUNT(*) FROM project_contexts WHERE updated_at > datetime('now', '-1 day')) +
    (SELECT COUNT(*) FROM task_contexts WHERE updated_at > datetime('now', '-1 day')) as recent_updates,
    (SELECT MAX(updated_at) FROM (
        SELECT updated_at FROM global_contexts 
        UNION ALL SELECT updated_at FROM project_contexts 
        UNION ALL SELECT updated_at FROM task_contexts
    )) as last_activity;

-- Cache performance metrics
CREATE VIEW IF NOT EXISTS cache_performance AS
SELECT 
    context_level,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN invalidated = 0 THEN 1 END) as valid_entries,
    COUNT(CASE WHEN invalidated = 1 THEN 1 END) as invalidated_entries,
    ROUND(
        (COUNT(CASE WHEN invalidated = 0 THEN 1 END) * 100.0) / 
        NULLIF(COUNT(*), 0), 2
    ) as cache_hit_rate,
    AVG(hit_count) as average_hit_count,
    SUM(cache_size_bytes) as total_cache_size,
    COUNT(CASE WHEN expires_at < datetime('now') THEN 1 END) as expired_entries,
    MIN(created_at) as oldest_entry,
    MAX(last_hit) as most_recent_hit
FROM context_inheritance_cache
GROUP BY context_level;

-- Recent activity dashboard
CREATE VIEW IF NOT EXISTS recent_activity AS
SELECT 
    'task_created' as activity_type,
    t.id as entity_id,
    t.title as entity_name,
    t.created_at as activity_time,
    p.name as project_name,
    ptt.name as branch_name
FROM tasks t
JOIN project_task_trees ptt ON t.git_branch_id = ptt.id
JOIN projects p ON ptt.project_id = p.id
WHERE t.created_at > datetime('now', '-7 days')
UNION ALL
SELECT 
    'task_completed' as activity_type,
    t.id as entity_id,
    t.title as entity_name,
    t.updated_at as activity_time,
    p.name as project_name,
    ptt.name as branch_name
FROM tasks t
JOIN project_task_trees ptt ON t.git_branch_id = ptt.id
JOIN projects p ON ptt.project_id = p.id
WHERE t.status = 'done' AND t.updated_at > datetime('now', '-7 days')
UNION ALL
SELECT 
    'subtask_completed' as activity_type,
    ts.id as entity_id,
    ts.title as entity_name,
    ts.completed_at as activity_time,
    p.name as project_name,
    ptt.name as branch_name
FROM task_subtasks ts
JOIN tasks t ON ts.task_id = t.id
JOIN project_task_trees ptt ON t.git_branch_id = ptt.id
JOIN projects p ON ptt.project_id = p.id
WHERE ts.status = 'done' AND ts.completed_at > datetime('now', '-7 days')
UNION ALL
SELECT 
    'agent_assigned' as activity_type,
    wa.id as entity_id,
    'Assignment to ' || wa.agent_id as entity_name,
    wa.created_at as activity_time,
    p.name as project_name,
    ptt.name as branch_name
FROM work_assignments wa
JOIN tasks t ON wa.task_id = t.id
JOIN project_task_trees ptt ON t.git_branch_id = ptt.id
JOIN projects p ON ptt.project_id = p.id
WHERE wa.created_at > datetime('now', '-7 days')
ORDER BY activity_time DESC;

-- Performance bottlenecks
CREATE VIEW IF NOT EXISTS performance_bottlenecks AS
SELECT 
    'overdue_tasks' as bottleneck_type,
    COUNT(*) as count,
    'Tasks past due date' as description,
    'high' as severity
FROM tasks 
WHERE due_date IS NOT NULL 
    AND due_date < datetime('now') 
    AND status != 'done'
UNION ALL
SELECT 
    'blocked_tasks' as bottleneck_type,
    COUNT(*) as count,
    'Tasks in blocked status' as description,
    'medium' as severity
FROM tasks 
WHERE status = 'blocked'
UNION ALL
SELECT 
    'overloaded_agents' as bottleneck_type,
    COUNT(*) as count,
    'Agents at max capacity' as description,
    'high' as severity
FROM project_agents 
WHERE current_workload >= max_concurrent_tasks
UNION ALL
SELECT 
    'stale_contexts' as bottleneck_type,
    COUNT(*) as count,
    'Contexts not updated in 7 days' as description,
    'low' as severity
FROM task_contexts 
WHERE updated_at < datetime('now', '-7 days')
UNION ALL
SELECT 
    'invalidated_cache' as bottleneck_type,
    COUNT(*) as count,
    'Invalidated cache entries' as description,
    'medium' as severity
FROM context_inheritance_cache 
WHERE invalidated = 1;

-- ===============================================
-- OPERATIONAL DASHBOARDS
-- ===============================================

-- Executive summary
CREATE VIEW IF NOT EXISTS executive_summary AS
SELECT 
    (SELECT COUNT(*) FROM projects WHERE status = 'active') as active_projects,
    (SELECT COUNT(*) FROM project_task_trees) as total_branches,
    (SELECT COUNT(*) FROM tasks) as total_tasks,
    (SELECT COUNT(*) FROM tasks WHERE status = 'done') as completed_tasks,
    (SELECT COUNT(*) FROM tasks WHERE status = 'in_progress') as active_tasks,
    (SELECT COUNT(*) FROM tasks WHERE status = 'blocked') as blocked_tasks,
    (SELECT COUNT(*) FROM project_agents WHERE status = 'available') as available_agents,
    (SELECT COUNT(*) FROM project_agents WHERE current_workload >= max_concurrent_tasks) as overloaded_agents,
    ROUND(
        (SELECT COUNT(*) FROM tasks WHERE status = 'done') * 100.0 / 
        NULLIF((SELECT COUNT(*) FROM tasks), 0), 2
    ) as overall_completion_rate,
    (SELECT COUNT(*) FROM tasks WHERE due_date < datetime('now') AND status != 'done') as overdue_tasks,
    (SELECT COUNT(*) FROM coordination_requests WHERE status = 'pending') as pending_coordination_requests,
    (SELECT COUNT(*) FROM context_delegations WHERE processed = 0) as pending_delegations;

-- Agent coordination status
CREATE VIEW IF NOT EXISTS coordination_status AS
SELECT 
    cr.request_type,
    cr.priority,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN cr.status = 'pending' THEN 1 END) as pending_requests,
    COUNT(CASE WHEN cr.status = 'resolved' THEN 1 END) as resolved_requests,
    AVG(
        CASE WHEN cr.resolved_at IS NOT NULL 
        THEN julianday(cr.resolved_at) - julianday(cr.created_at) 
        END
    ) as average_resolution_days,
    MAX(cr.created_at) as last_request_time
FROM coordination_requests cr
GROUP BY cr.request_type, cr.priority
ORDER BY pending_requests DESC, total_requests DESC;