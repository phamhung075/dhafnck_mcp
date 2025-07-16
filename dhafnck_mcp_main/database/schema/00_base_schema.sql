-- ===============================================
-- DHAFNCK MCP BASE DATABASE SCHEMA v6.0
-- Complete modernized schema for the new system
-- 
-- This is the source of truth for all database tables
-- AI has no permission to change schema unless user demands
-- 
-- Execution Order:
-- 1. Projects and Git Branches (project_task_trees)
-- 2. Tasks and Subtasks  
-- 3. Agents and Assignments
-- 4. Hierarchical Context System
-- 5. Labels and Relationships
-- 6. Templates and Checklists
-- 7. Audit and Migration Tables
-- 8. Views and Statistics
-- ===============================================

-- Enable foreign key constraints
-- PRAGMA foreign_keys = ON;  -- Handled by database initializer

-- ===============================================
-- 1. PROJECT MANAGEMENT TABLES
-- ===============================================

-- Projects table - Core organizational structure
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT NOT NULL DEFAULT 'default_id',
    status TEXT DEFAULT 'active',
    metadata TEXT DEFAULT '{}',
    UNIQUE(id, user_id)
);

-- Git branches (task trees) - Project workspaces
CREATE TABLE IF NOT EXISTS project_task_trees (
    id TEXT PRIMARY KEY,  -- UUID
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_agent_id TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'todo',
    metadata TEXT DEFAULT '{}',
    task_count INTEGER DEFAULT 0,
    completed_task_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(id, project_id)
);

-- ===============================================
-- 2. TASK MANAGEMENT TABLES
-- ===============================================

-- Main tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    git_branch_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    details TEXT DEFAULT '',
    estimated_effort TEXT DEFAULT '',
    due_date TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    context_id TEXT,
    FOREIGN KEY (git_branch_id) REFERENCES project_task_trees(id) ON DELETE CASCADE
);

-- Subtasks table
CREATE TABLE IF NOT EXISTS task_subtasks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    assignees TEXT DEFAULT '[]',
    estimated_effort TEXT,
    progress_percentage INTEGER DEFAULT 0,
    progress_notes TEXT DEFAULT '',
    blockers TEXT DEFAULT '',
    completion_summary TEXT DEFAULT '',
    impact_on_parent TEXT DEFAULT '',
    insights_found TEXT DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Task assignees table
CREATE TABLE IF NOT EXISTS task_assignees (
    task_id TEXT NOT NULL,
    assignee TEXT NOT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, assignee),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Task dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    depends_on_task_id TEXT NOT NULL,
    dependency_type TEXT DEFAULT 'blocks',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, depends_on_task_id)
);

-- Project cross tree dependencies (for complex project dependencies)
CREATE TABLE IF NOT EXISTS project_cross_tree_dependencies (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    dependent_task_id TEXT NOT NULL,
    prerequisite_task_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (dependent_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(project_id, dependent_task_id, prerequisite_task_id)
);

-- Project work sessions (agent work tracking)
CREATE TABLE IF NOT EXISTS project_work_sessions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    agent_id TEXT,
    task_id TEXT,
    git_branch_id TEXT,
    status TEXT DEFAULT 'active',
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    max_duration_hours INTEGER DEFAULT 8,
    notes TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (git_branch_id) REFERENCES project_task_trees(id) ON DELETE SET NULL
);

-- Project resource locks (concurrency control)
CREATE TABLE IF NOT EXISTS project_resource_locks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL,
    resource_name TEXT NOT NULL,
    locked_by_agent_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    notes TEXT DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, resource_name)
);

-- ===============================================
-- 3. AGENT MANAGEMENT TABLES
-- ===============================================

-- Project agents
CREATE TABLE IF NOT EXISTS project_agents (
    id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    call_agent TEXT,
    capabilities TEXT DEFAULT '[]',
    specializations TEXT DEFAULT '[]',
    preferred_languages TEXT DEFAULT '[]',
    preferred_frameworks TEXT DEFAULT '[]',
    status TEXT DEFAULT 'available',
    max_concurrent_tasks INTEGER DEFAULT 1,
    current_workload INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    average_task_duration REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 100.0,
    work_hours TEXT DEFAULT '{}',
    timezone TEXT DEFAULT 'UTC',
    priority_preference TEXT DEFAULT 'high',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, project_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Agent assignments to git branches
CREATE TABLE IF NOT EXISTS project_agent_assignments (
    project_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    git_branch_id TEXT NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, agent_id, git_branch_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id, project_id) REFERENCES project_agents(id, project_id) ON DELETE CASCADE,
    FOREIGN KEY (git_branch_id) REFERENCES project_task_trees(id) ON DELETE CASCADE
);

-- Agent coordination tables
CREATE TABLE IF NOT EXISTS coordination_requests (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    requesting_agent_id TEXT NOT NULL,
    target_agent_id TEXT,
    request_type TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    description TEXT NOT NULL,
    context_data TEXT DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    resolution TEXT
);

CREATE TABLE IF NOT EXISTS work_assignments (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    assigned_by TEXT DEFAULT 'system',
    assignment_reason TEXT,
    priority_score INTEGER DEFAULT 50,
    estimated_duration INTEGER,
    status TEXT DEFAULT 'assigned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    outcome TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_handoffs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    from_agent_id TEXT NOT NULL,
    to_agent_id TEXT NOT NULL,
    handoff_reason TEXT NOT NULL,
    context_transfer TEXT DEFAULT '{}',
    completion_percentage INTEGER DEFAULT 0,
    handoff_notes TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at DATETIME,
    completed_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conflict_resolutions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    conflict_type TEXT NOT NULL,
    involved_agents TEXT NOT NULL,
    task_id TEXT,
    conflict_description TEXT NOT NULL,
    resolution_strategy TEXT,
    resolution_outcome TEXT,
    resolved_by TEXT DEFAULT 'system',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_communications (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    from_agent_id TEXT NOT NULL,
    to_agent_id TEXT,
    message_type TEXT DEFAULT 'info',
    subject TEXT,
    content TEXT NOT NULL,
    related_task_id TEXT,
    priority TEXT DEFAULT 'normal',
    read_status BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME,
    FOREIGN KEY (related_task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- ===============================================
-- 4. HIERARCHICAL CONTEXT SYSTEM
-- ===============================================

-- Global context (singleton)
CREATE TABLE IF NOT EXISTS global_contexts (
    id TEXT PRIMARY KEY DEFAULT 'global_singleton',
    organization_id TEXT NOT NULL DEFAULT 'default_org',
    
    -- Core organizational configuration
    autonomous_rules TEXT NOT NULL DEFAULT '{
        "ai_enabled": true,
        "auto_task_creation": true,
        "context_switching_threshold": 70,
        "completion_protection_threshold": 70,
        "emergency_override_threshold": 200,
        "decision_confidence_minimum": 50
    }',
    
    security_policies TEXT NOT NULL DEFAULT '{
        "mfa_required": false,
        "secure_coding_required": true,
        "audit_trail_enabled": true,
        "compliance_checks": ["basic"]
    }',
    
    coding_standards TEXT NOT NULL DEFAULT '{
        "style": "typescript_strict",
        "review_required": true,
        "test_coverage_minimum": 80,
        "documentation_required": true
    }',
    
    workflow_templates TEXT NOT NULL DEFAULT '{
        "estimation_required": true,
        "subtask_creation": "encouraged",
        "completion_summary_required": true,
        "progress_tracking_interval": 1800
    }',
    
    -- Delegation configuration
    delegation_rules TEXT NOT NULL DEFAULT '{
        "auto_delegate": {
            "security_issues": true,
            "compliance_violations": true,
            "reusable_patterns": true,
            "critical_insights": true
        },
        "thresholds": {
            "task_failure_rate": 0.3,
            "performance_critical": true,
            "security_critical": true
        },
        "escalation": {
            "max_retry_attempts": 3,
            "escalation_timeout": 3600
        }
    }',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    last_propagated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project contexts (inherit from global)
CREATE TABLE IF NOT EXISTS project_contexts (
    project_id TEXT PRIMARY KEY,
    parent_global_id TEXT DEFAULT 'global_singleton',
    
    -- Project-specific configuration
    team_preferences TEXT NOT NULL DEFAULT '{
        "default_priority": "medium",
        "auto_assign_enabled": false,
        "notification_preferences": {
            "email": true,
            "slack": false
        },
        "working_hours": {
            "timezone": "UTC",
            "start": "09:00",
            "end": "17:00"
        }
    }',
    
    technology_stack TEXT NOT NULL DEFAULT '{
        "backend": ["python", "fastapi"],
        "frontend": ["typescript", "react"],
        "database": ["sqlite", "postgresql"],
        "infrastructure": ["docker", "github_actions"],
        "monitoring": ["prometheus", "grafana"]
    }',
    
    project_workflow TEXT NOT NULL DEFAULT '{
        "branch_strategy": "git_flow",
        "ci_cd_pipeline": "github_actions",
        "deployment_strategy": "blue_green",
        "testing_strategy": "pyramid",
        "code_review": {
            "required": true,
            "min_reviewers": 1,
            "approval_required": true
        }
    }',
    
    local_standards TEXT NOT NULL DEFAULT '{
        "naming_conventions": {
            "variables": "snake_case",
            "functions": "snake_case",
            "classes": "PascalCase",
            "files": "snake_case"
        },
        "code_organization": {
            "max_file_lines": 500,
            "max_function_lines": 50,
            "max_class_methods": 20
        }
    }',
    
    -- Override capabilities for global settings
    global_overrides TEXT NOT NULL DEFAULT '{}',
    
    -- Project-specific delegation rules
    delegation_rules TEXT NOT NULL DEFAULT '{
        "delegate_to_global": {
            "security_patterns": true,
            "reusable_components": true,
            "architectural_decisions": true,
            "compliance_patterns": true
        },
        "bubble_up_thresholds": {
            "task_failure_rate": 0.3,
            "performance_issues": "critical",
            "security_vulnerabilities": "any",
            "compliance_violations": "any"
        },
        "retention_policies": {
            "keep_successful_patterns": true,
            "archive_failed_approaches": true,
            "document_lessons_learned": true
        }
    }',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    last_inherited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    inheritance_disabled BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_global_id) REFERENCES global_contexts(id)
);

-- Task contexts (inherit from project)
CREATE TABLE IF NOT EXISTS task_contexts (
    task_id TEXT PRIMARY KEY,
    
    -- Hierarchy relationships
    parent_project_id TEXT NOT NULL,
    parent_project_context_id TEXT NOT NULL,
    
    -- Task-specific data
    task_data TEXT NOT NULL DEFAULT '{
        "metadata": {},
        "objective": {},
        "requirements": {},
        "technical": {},
        "dependencies": {},
        "progress": {},
        "subtasks": {},
        "notes": {}
    }',
    
    -- Local overrides for inherited settings
    local_overrides TEXT NOT NULL DEFAULT '{}',
    
    -- Implementation and execution details
    implementation_notes TEXT NOT NULL DEFAULT '{
        "approach": "",
        "challenges": [],
        "solutions": [],
        "decisions": [],
        "learnings": []
    }',
    
    -- Delegation configuration and triggers
    delegation_triggers TEXT NOT NULL DEFAULT '{
        "patterns": {
            "security_discovery": "global",
            "team_improvement": "project",
            "reusable_utility": "project",
            "architectural_insight": "global",
            "performance_optimization": "project"
        },
        "auto_delegate": {
            "critical_errors": true,
            "security_vulnerabilities": true,
            "performance_bottlenecks": true,
            "reusable_patterns": true
        },
        "thresholds": {
            "completion_time_exceeded": 2.0,
            "error_rate_threshold": 0.1,
            "performance_degradation": 0.2
        }
    }',
    
    -- Inheritance control
    inheritance_disabled BOOLEAN DEFAULT FALSE,
    force_local_only BOOLEAN DEFAULT FALSE,
    custom_inheritance_rules TEXT DEFAULT '{}',
    
    -- Performance optimization (cached resolved context)
    resolved_context TEXT DEFAULT NULL,
    resolved_at TIMESTAMP DEFAULT NULL,
    dependencies_hash TEXT DEFAULT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    last_inherited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_project_context_id) REFERENCES project_contexts(project_id),
    FOREIGN KEY (parent_project_id) REFERENCES projects(id)
);

-- Context insights
CREATE TABLE IF NOT EXISTS context_insights (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    context_id TEXT NOT NULL,
    context_type TEXT NOT NULL CHECK (context_type IN ('global', 'project', 'task')),
    
    -- Insight content
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    importance TEXT DEFAULT 'medium' CHECK (importance IN ('low', 'medium', 'high', 'critical')),
    confidence_score REAL DEFAULT 0.5,
    
    -- Source information
    source_agent TEXT DEFAULT 'system',
    source_type TEXT DEFAULT 'analysis',
    related_task_id TEXT,
    
    -- Workflow integration
    actionable BOOLEAN DEFAULT FALSE,
    action_taken BOOLEAN DEFAULT FALSE,
    action_result TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    
    FOREIGN KEY (related_task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Context delegations
CREATE TABLE IF NOT EXISTS context_delegations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    
    -- Source and target identification
    source_level TEXT NOT NULL CHECK (source_level IN ('task', 'project', 'global')),
    source_id TEXT NOT NULL,
    target_level TEXT NOT NULL CHECK (target_level IN ('task', 'project', 'global')),
    target_id TEXT NOT NULL,
    
    -- Delegation content and metadata
    delegated_data TEXT NOT NULL,
    delegation_reason TEXT NOT NULL,
    trigger_type TEXT DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'auto_threshold', 'auto_pattern', 'ai_initiated')),
    confidence_score REAL DEFAULT NULL,
    
    -- Processing status and workflow
    auto_delegated BOOLEAN DEFAULT FALSE,
    processed BOOLEAN DEFAULT FALSE,
    approved BOOLEAN DEFAULT NULL,
    rejected_reason TEXT DEFAULT NULL,
    
    -- Impact tracking
    impact_assessment TEXT DEFAULT '{}',
    implementation_status TEXT DEFAULT 'pending' CHECK (implementation_status IN ('pending', 'implemented', 'rejected', 'expired')),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP DEFAULT NULL,
    implemented_at TIMESTAMP DEFAULT NULL,
    created_by TEXT DEFAULT 'system',
    processed_by TEXT DEFAULT NULL
);

-- Context inheritance cache
CREATE TABLE IF NOT EXISTS context_inheritance_cache (
    context_id TEXT NOT NULL,
    context_level TEXT NOT NULL CHECK (context_level IN ('task', 'project', 'global')),
    
    -- Cached resolved context data
    resolved_context TEXT NOT NULL,
    dependencies_hash TEXT NOT NULL,
    resolution_path TEXT NOT NULL,
    
    -- Cache metadata and performance tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_hit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cache_size_bytes INTEGER DEFAULT 0,
    
    -- Cache invalidation tracking
    invalidated BOOLEAN DEFAULT FALSE,
    invalidation_reason TEXT DEFAULT NULL,
    
    PRIMARY KEY (context_id, context_level)
);

-- Context change propagation log
CREATE TABLE IF NOT EXISTS context_propagations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    
    -- Source of change
    source_level TEXT NOT NULL CHECK (source_level IN ('task', 'project', 'global')),
    source_id TEXT NOT NULL,
    change_type TEXT NOT NULL CHECK (change_type IN ('create', 'update', 'delete', 'delegation')),
    
    -- Affected contexts
    affected_contexts TEXT NOT NULL,
    
    -- Change details
    changes_summary TEXT NOT NULL,
    propagation_rules_applied TEXT DEFAULT '{}',
    
    -- Status tracking
    propagation_status TEXT DEFAULT 'pending' CHECK (propagation_status IN ('pending', 'in_progress', 'completed', 'failed')),
    completion_percentage REAL DEFAULT 0.0,
    error_details TEXT DEFAULT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP DEFAULT NULL,
    completed_at TIMESTAMP DEFAULT NULL,
    duration_ms INTEGER DEFAULT NULL
);

-- ===============================================
-- 5. LABEL SYSTEM
-- ===============================================

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

-- Task labels junction table
CREATE TABLE IF NOT EXISTS task_labels (
    task_id TEXT NOT NULL,
    label_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, label_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);

-- ===============================================
-- 6. TEMPLATE SYSTEM
-- ===============================================

-- Templates table
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'general',
    tags TEXT DEFAULT '[]',
    version INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    estimated_duration INTEGER DEFAULT NULL,
    complexity_score INTEGER DEFAULT 1,
    created_by TEXT DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT NULL
);

-- Template usage tracking
CREATE TABLE IF NOT EXISTS template_usage (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    template_id TEXT NOT NULL,
    used_by TEXT DEFAULT 'system',
    context_type TEXT DEFAULT 'task',
    context_id TEXT,
    outcome TEXT DEFAULT 'pending',
    duration_seconds INTEGER,
    feedback_score REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
);

-- Template cache
CREATE TABLE IF NOT EXISTS template_cache (
    cache_key TEXT PRIMARY KEY,
    template_data TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================================
-- 7. CHECKLIST SYSTEM
-- ===============================================

-- Dynamic checklists
CREATE TABLE IF NOT EXISTS checklists (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'general',
    scope TEXT DEFAULT 'task',
    priority INTEGER DEFAULT 50,
    auto_apply BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Checklist items
CREATE TABLE IF NOT EXISTS checklist_items (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    checklist_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    order_index INTEGER NOT NULL,
    required BOOLEAN DEFAULT TRUE,
    validation_rule TEXT DEFAULT '',
    dependencies TEXT DEFAULT '[]',
    estimated_duration INTEGER DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
);

-- Checklist progress tracking
CREATE TABLE IF NOT EXISTS checklist_progress (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    checklist_id TEXT NOT NULL,
    context_type TEXT NOT NULL,
    context_id TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NULL,
    completion_percentage REAL DEFAULT 0.0,
    current_item_id TEXT DEFAULT NULL,
    notes TEXT DEFAULT '',
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE,
    FOREIGN KEY (current_item_id) REFERENCES checklist_items(id),
    UNIQUE(checklist_id, context_type, context_id)
);

-- Checklist item completion
CREATE TABLE IF NOT EXISTS checklist_item_completion (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    progress_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completion_notes TEXT DEFAULT '',
    completed_at TIMESTAMP DEFAULT NULL,
    validated BOOLEAN DEFAULT FALSE,
    validation_result TEXT DEFAULT '',
    FOREIGN KEY (progress_id) REFERENCES checklist_progress(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES checklist_items(id) ON DELETE CASCADE,
    UNIQUE(progress_id, item_id)
);

-- ===============================================
-- 8. AUDIT TABLES
-- ===============================================

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_id TEXT NOT NULL,
    old_values TEXT DEFAULT NULL,
    new_values TEXT DEFAULT NULL,
    changed_by TEXT DEFAULT 'system',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT DEFAULT NULL,
    ip_address TEXT DEFAULT NULL,
    user_agent TEXT DEFAULT NULL
);