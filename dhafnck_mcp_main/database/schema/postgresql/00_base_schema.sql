-- ===============================================
-- DHAFNCK MCP BASE DATABASE SCHEMA v6.0 - PostgreSQL
-- PostgreSQL-compatible schema for production deployment
-- ===============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable foreign key constraints (PostgreSQL default)
-- Foreign keys are enabled by default in PostgreSQL

-- ===============================================
-- 1. PROJECT MANAGEMENT TABLES
-- ===============================================

-- Projects table - Core organizational structure
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id TEXT NOT NULL DEFAULT 'default_id',
    status TEXT DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    UNIQUE(id, user_id)
);

-- Git branches (task trees) - Project workspaces
CREATE TABLE IF NOT EXISTS project_task_trees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_agent_id TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'todo',
    metadata JSONB DEFAULT '{}',
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    git_branch_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    details TEXT DEFAULT '',
    estimated_effort TEXT DEFAULT '',
    due_date TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    context_id UUID,
    FOREIGN KEY (git_branch_id) REFERENCES project_task_trees(id) ON DELETE CASCADE
);

-- ===============================================
-- 3. HIERARCHICAL CONTEXT SYSTEM
-- ===============================================

-- Global context (singleton)
CREATE TABLE IF NOT EXISTS global_contexts (
    id TEXT PRIMARY KEY DEFAULT 'global_singleton',
    organization_id TEXT NOT NULL DEFAULT 'default_org',
    
    -- Core organizational configuration
    autonomous_rules JSONB NOT NULL DEFAULT '{
        "ai_enabled": true,
        "auto_task_creation": true,
        "context_switching_threshold": 70,
        "completion_protection_threshold": 70,
        "emergency_override_threshold": 200,
        "decision_confidence_minimum": 50
    }',
    
    security_policies JSONB NOT NULL DEFAULT '{
        "mfa_required": false,
        "secure_coding_required": true,
        "audit_trail_enabled": true,
        "compliance_checks": ["basic"]
    }',
    
    coding_standards JSONB NOT NULL DEFAULT '{
        "style": "typescript_strict",
        "review_required": true,
        "test_coverage_minimum": 80,
        "documentation_required": true
    }',
    
    workflow_templates JSONB NOT NULL DEFAULT '{
        "estimation_required": true,
        "subtask_creation": "encouraged",
        "completion_summary_required": true,
        "progress_tracking_interval": 1800
    }',
    
    -- Delegation configuration
    delegation_rules JSONB NOT NULL DEFAULT '{
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    last_propagated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project contexts (inherit from global)
CREATE TABLE IF NOT EXISTS project_contexts (
    project_id UUID PRIMARY KEY,
    parent_global_id TEXT DEFAULT 'global_singleton',
    
    -- Project-specific configuration
    team_preferences JSONB NOT NULL DEFAULT '{
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
    
    technology_stack JSONB NOT NULL DEFAULT '{
        "backend": ["python", "fastapi"],
        "frontend": ["typescript", "react"],
        "database": ["sqlite", "postgresql"],
        "infrastructure": ["docker", "github_actions"],
        "monitoring": ["prometheus", "grafana"]
    }',
    
    project_workflow JSONB NOT NULL DEFAULT '{
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
    
    local_standards JSONB NOT NULL DEFAULT '{
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
    global_overrides JSONB NOT NULL DEFAULT '{}',
    
    -- Project-specific delegation rules
    delegation_rules JSONB NOT NULL DEFAULT '{
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    last_inherited TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    inheritance_disabled BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_global_id) REFERENCES global_contexts(id)
);

-- Task contexts (inherit from project)
CREATE TABLE IF NOT EXISTS task_contexts (
    task_id UUID PRIMARY KEY,
    
    -- Hierarchy relationships
    parent_project_id UUID NOT NULL,
    parent_project_context_id UUID NOT NULL,
    
    -- Task-specific data
    task_data JSONB NOT NULL DEFAULT '{
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
    local_overrides JSONB NOT NULL DEFAULT '{}',
    
    -- Implementation and execution details
    implementation_notes JSONB NOT NULL DEFAULT '{
        "approach": "",
        "challenges": [],
        "solutions": [],
        "decisions": [],
        "learnings": []
    }',
    
    -- Delegation configuration and triggers
    delegation_triggers JSONB NOT NULL DEFAULT '{
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
    custom_inheritance_rules JSONB DEFAULT '{}',
    
    -- Performance optimization (cached resolved context)
    resolved_context JSONB DEFAULT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    dependencies_hash TEXT DEFAULT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    last_inherited TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_project_context_id) REFERENCES project_contexts(project_id),
    FOREIGN KEY (parent_project_id) REFERENCES projects(id)
);

-- Context inheritance cache
CREATE TABLE IF NOT EXISTS context_inheritance_cache (
    context_id TEXT NOT NULL,
    context_level TEXT NOT NULL CHECK (context_level IN ('task', 'project', 'global')),
    
    -- Cached resolved context data
    resolved_context JSONB NOT NULL,
    dependencies_hash TEXT NOT NULL,
    resolution_path TEXT NOT NULL,
    
    -- Cache metadata and performance tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_hit TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cache_size_bytes INTEGER DEFAULT 0,
    
    -- Cache invalidation tracking
    invalidated BOOLEAN DEFAULT FALSE,
    invalidation_reason TEXT DEFAULT NULL,
    
    PRIMARY KEY (context_id, context_level)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_project_task_trees_project_id ON project_task_trees(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_git_branch_id ON tasks(git_branch_id);
CREATE INDEX IF NOT EXISTS idx_task_contexts_parent_project_id ON task_contexts(parent_project_id);
CREATE INDEX IF NOT EXISTS idx_context_cache_expires_at ON context_inheritance_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_global_contexts_organization_id ON global_contexts(organization_id);

-- Create triggers for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_task_trees_updated_at BEFORE UPDATE ON project_task_trees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_global_contexts_updated_at BEFORE UPDATE ON global_contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_contexts_updated_at BEFORE UPDATE ON project_contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_contexts_updated_at BEFORE UPDATE ON task_contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();