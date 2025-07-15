-- ===============================================
-- DHAFNCK MCP INITIAL DATA v6.0
-- Default data and system configuration
-- ===============================================

-- ===============================================
-- GLOBAL CONTEXT INITIALIZATION
-- ===============================================

-- Insert default global context (singleton)
INSERT OR REPLACE INTO global_contexts (
    id,
    organization_id,
    autonomous_rules,
    security_policies,
    coding_standards,
    workflow_templates,
    delegation_rules,
    created_at,
    updated_at,
    version,
    last_propagated
) VALUES (
    'global_singleton',
    'dhafnck_mcp_org',
    json('{
        "ai_enabled": true,
        "auto_task_creation": true,
        "context_switching_threshold": 70,
        "completion_protection_threshold": 70,
        "emergency_override_threshold": 200,
        "decision_confidence_minimum": 50,
        "autonomous_operation": true,
        "agent_coordination_enabled": true,
        "workflow_automation": true,
        "smart_delegation": true
    }'),
    json('{
        "mfa_required": false,
        "secure_coding_required": true,
        "audit_trail_enabled": true,
        "compliance_checks": ["basic", "security", "performance"],
        "vulnerability_scanning": true,
        "access_control": "role_based",
        "data_encryption": "at_rest_and_transit",
        "audit_retention_days": 365
    }'),
    json('{
        "style": "python_pep8",
        "review_required": true,
        "test_coverage_minimum": 80,
        "documentation_required": true,
        "code_complexity_max": 10,
        "function_length_max": 50,
        "class_length_max": 500,
        "naming_conventions": {
            "variables": "snake_case",
            "functions": "snake_case",
            "classes": "PascalCase",
            "constants": "UPPER_SNAKE_CASE",
            "files": "snake_case"
        }
    }'),
    json('{
        "estimation_required": true,
        "subtask_creation": "encouraged",
        "completion_summary_required": true,
        "progress_tracking_interval": 1800,
        "checklist_automation": true,
        "template_usage": "recommended",
        "context_inheritance": true,
        "performance_monitoring": true
    }'),
    json('{
        "auto_delegate": {
            "security_issues": true,
            "compliance_violations": true,
            "reusable_patterns": true,
            "critical_insights": true,
            "performance_optimizations": true,
            "architectural_decisions": true
        },
        "thresholds": {
            "task_failure_rate": 0.3,
            "performance_critical": true,
            "security_critical": true,
            "complexity_threshold": 8,
            "duration_threshold_hours": 24
        },
        "escalation": {
            "max_retry_attempts": 3,
            "escalation_timeout": 3600,
            "auto_reassignment": true,
            "notify_stakeholders": true
        }
    }'),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    1,
    CURRENT_TIMESTAMP
);

-- ===============================================
-- DEFAULT PROJECT AND BRANCH
-- ===============================================

-- Insert default project
INSERT OR REPLACE INTO projects (
    id,
    name,
    description,
    user_id,
    status,
    metadata,
    created_at,
    updated_at
) VALUES (
    'default_project',
    'DhafnckMCP System',
    'Main system project for DhafnckMCP task management and AI agent coordination',
    'system',
    'active',
    json('{
        "project_type": "system",
        "priority": "critical",
        "environment": "production",
        "auto_created": true
    }'),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Insert default git branch (task tree)
INSERT OR REPLACE INTO project_task_trees (
    id,
    project_id,
    name,
    description,
    assigned_agent_id,
    priority,
    status,
    metadata,
    task_count,
    completed_task_count,
    created_at,
    updated_at
) VALUES (
    'main_branch',
    'default_project',
    'main',
    'Main development branch for system tasks',
    '@uber_orchestrator_agent',
    'high',
    'active',
    json('{
        "branch_type": "main",
        "auto_created": true,
        "protected": true
    }'),
    0,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Insert default project context
INSERT OR REPLACE INTO project_contexts (
    project_id,
    parent_global_id,
    team_preferences,
    technology_stack,
    project_workflow,
    local_standards,
    global_overrides,
    delegation_rules,
    created_at,
    updated_at,
    version,
    last_inherited,
    inheritance_disabled
) VALUES (
    'default_project',
    'global_singleton',
    json('{
        "default_priority": "medium",
        "auto_assign_enabled": true,
        "notification_preferences": {
            "email": false,
            "slack": false,
            "system": true
        },
        "working_hours": {
            "timezone": "UTC",
            "start": "00:00",
            "end": "23:59",
            "continuous_operation": true
        },
        "team_size": "ai_agents",
        "collaboration_style": "autonomous"
    }'),
    json('{
        "backend": ["python", "fastapi", "sqlite"],
        "frontend": ["typescript", "react"],
        "database": ["sqlite", "postgresql"],
        "infrastructure": ["docker", "github_actions"],
        "monitoring": ["prometheus", "grafana"],
        "ai_framework": ["transformers", "llama", "openai"],
        "mcp_tools": ["dhafnck_mcp", "task_management"],
        "testing": ["pytest", "unittest", "integration"]
    }'),
    json('{
        "branch_strategy": "git_flow",
        "ci_cd_pipeline": "github_actions",
        "deployment_strategy": "rolling",
        "testing_strategy": "pyramid",
        "code_review": {
            "required": true,
            "min_reviewers": 1,
            "approval_required": true,
            "automated_checks": true
        },
        "automation": {
            "task_creation": true,
            "progress_tracking": true,
            "completion_detection": true,
            "error_handling": true
        }
    }'),
    json('{
        "naming_conventions": {
            "variables": "snake_case",
            "functions": "snake_case",
            "classes": "PascalCase",
            "files": "snake_case",
            "modules": "snake_case"
        },
        "code_organization": {
            "max_file_lines": 1000,
            "max_function_lines": 100,
            "max_class_methods": 30,
            "architecture": "domain_driven_design"
        },
        "ai_specific": {
            "context_awareness": true,
            "autonomous_decision_making": true,
            "learning_enabled": true,
            "adaptation_allowed": true
        }
    }'),
    json('{}'),
    json('{
        "delegate_to_global": {
            "security_patterns": true,
            "reusable_components": true,
            "architectural_decisions": true,
            "compliance_patterns": true,
            "ai_insights": true,
            "performance_optimizations": true
        },
        "bubble_up_thresholds": {
            "task_failure_rate": 0.2,
            "performance_issues": "critical",
            "security_vulnerabilities": "any",
            "compliance_violations": "any",
            "ai_learning_opportunities": "significant"
        },
        "retention_policies": {
            "keep_successful_patterns": true,
            "archive_failed_approaches": true,
            "document_lessons_learned": true,
            "share_ai_insights": true
        }
    }'),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    1,
    CURRENT_TIMESTAMP,
    FALSE
);

-- ===============================================
-- COMMON LABELS
-- ===============================================

-- Insert common labels
INSERT OR REPLACE INTO labels (label, normalized, category, usage_count, is_common) VALUES
('bug', 'bug', 'type', 0, 1),
('feature', 'feature', 'type', 0, 1),
('enhancement', 'enhancement', 'type', 0, 1),
('documentation', 'documentation', 'type', 0, 1),
('refactor', 'refactor', 'type', 0, 1),
('test', 'test', 'type', 0, 1),
('security', 'security', 'priority', 0, 1),
('performance', 'performance', 'priority', 0, 1),
('ui', 'ui', 'component', 0, 1),
('frontend', 'frontend', 'component', 0, 1),
('backend', 'backend', 'component', 0, 1),
('database', 'database', 'component', 0, 1),
('api', 'api', 'component', 0, 1),
('urgent', 'urgent', 'priority', 0, 1),
('low-priority', 'low_priority', 'priority', 0, 1),
('blocked', 'blocked', 'status', 0, 1),
('ready', 'ready', 'status', 0, 1),
('review', 'review', 'status', 0, 1),
('testing', 'testing', 'status', 0, 1),
('ai', 'ai', 'technology', 0, 1),
('automation', 'automation', 'technology', 0, 1),
('mcp', 'mcp', 'technology', 0, 1),
('agent', 'agent', 'technology', 0, 1),
('context', 'context', 'technology', 0, 1),
('workflow', 'workflow', 'process', 0, 1),
('delegation', 'delegation', 'process', 0, 1),
('coordination', 'coordination', 'process', 0, 1),
('monitoring', 'monitoring', 'process', 0, 1),
('optimization', 'optimization', 'process', 0, 1),
('integration', 'integration', 'process', 0, 1),
('deployment', 'deployment', 'process', 0, 1);

-- ===============================================
-- SYSTEM AGENTS
-- ===============================================

-- Insert system agents
INSERT OR REPLACE INTO project_agents (
    id,
    project_id,
    name,
    description,
    call_agent,
    capabilities,
    specializations,
    status,
    max_concurrent_tasks,
    current_workload,
    created_at,
    updated_at
) VALUES 
(
    '@uber_orchestrator_agent',
    'default_project',
    'Uber Orchestrator Agent',
    'Primary coordination agent for complex multi-step workflows and system orchestration',
    '@uber_orchestrator_agent',
    json('["orchestration", "coordination", "planning", "decision_making", "workflow_management"]'),
    json('["complex_workflows", "multi_agent_coordination", "strategic_planning", "resource_allocation"]'),
    'available',
    10,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '@task_planning_agent',
    'default_project',
    'Task Planning Agent',
    'Specialized agent for breaking down complex tasks and creating execution plans',
    '@task_planning_agent',
    json('["task_decomposition", "planning", "estimation", "dependency_analysis"]'),
    json('["project_planning", "task_breakdown", "workflow_design", "resource_planning"]'),
    'available',
    5,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '@coding_agent',
    'default_project',
    'Coding Agent',
    'Development agent for implementing features and writing code',
    '@coding_agent',
    json('["programming", "implementation", "code_writing", "debugging"]'),
    json('["python", "typescript", "api_development", "database_design"]'),
    'available',
    3,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '@test_orchestrator_agent',
    'default_project',
    'Test Orchestrator Agent',
    'Testing coordination agent for quality assurance and test automation',
    '@test_orchestrator_agent',
    json('["testing", "quality_assurance", "test_automation", "validation"]'),
    json('["unit_testing", "integration_testing", "test_planning", "qa_coordination"]'),
    'available',
    5,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    '@system_architect_agent',
    'default_project',
    'System Architect Agent',
    'Architecture and design agent for system design and technical decision making',
    '@system_architect_agent',
    json('["architecture", "system_design", "technical_planning", "pattern_recognition"]'),
    json('["system_architecture", "design_patterns", "scalability", "performance"]'),
    'available',
    3,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ===============================================
-- SYSTEM TEMPLATES
-- ===============================================

-- Insert common task templates
INSERT OR REPLACE INTO templates (
    id,
    name,
    type,
    content,
    description,
    category,
    tags,
    version,
    active,
    created_by
) VALUES 
(
    'feature_implementation_template',
    'Feature Implementation',
    'task',
    json('{
        "title_pattern": "Implement {feature_name}",
        "description_template": "Implement the {feature_name} feature according to specifications.\n\nRequirements:\n- {requirements}\n\nAcceptance Criteria:\n- {acceptance_criteria}\n\nTechnical Notes:\n- {technical_notes}",
        "default_priority": "medium",
        "estimated_effort": "TBD",
        "default_labels": ["feature", "implementation"],
        "checklist_id": "feature_implementation_checklist",
        "subtask_templates": [
            "Design feature architecture",
            "Implement core functionality",
            "Add unit tests",
            "Integration testing",
            "Documentation update"
        ]
    }'),
    'Template for implementing new features',
    'development',
    json('["feature", "implementation", "development"]'),
    1,
    TRUE,
    'system'
),
(
    'bug_fix_template',
    'Bug Fix',
    'task',
    json('{
        "title_pattern": "Fix: {bug_description}",
        "description_template": "Bug Description:\n{bug_description}\n\nSteps to Reproduce:\n1. {step1}\n2. {step2}\n3. {step3}\n\nExpected Behavior:\n{expected_behavior}\n\nActual Behavior:\n{actual_behavior}\n\nRoot Cause Analysis:\n{root_cause}",
        "default_priority": "high",
        "estimated_effort": "TBD",
        "default_labels": ["bug", "fix"],
        "checklist_id": "bug_fix_checklist",
        "subtask_templates": [
            "Reproduce and analyze bug",
            "Identify root cause",
            "Implement fix",
            "Test fix thoroughly",
            "Regression testing"
        ]
    }'),
    'Template for fixing bugs and issues',
    'maintenance',
    json('["bug", "fix", "maintenance"]'),
    1,
    TRUE,
    'system'
),
(
    'research_template',
    'Research Task',
    'task',
    json('{
        "title_pattern": "Research: {research_topic}",
        "description_template": "Research Topic: {research_topic}\n\nObjectives:\n- {objective1}\n- {objective2}\n- {objective3}\n\nScope:\n{scope}\n\nDeliverables:\n- {deliverable1}\n- {deliverable2}\n\nResources:\n{resources}",
        "default_priority": "medium",
        "estimated_effort": "TBD",
        "default_labels": ["research", "analysis"],
        "checklist_id": "research_checklist",
        "subtask_templates": [
            "Define research scope",
            "Gather initial information",
            "Deep dive analysis",
            "Document findings",
            "Present recommendations"
        ]
    }'),
    'Template for research and analysis tasks',
    'research',
    json('["research", "analysis", "investigation"]'),
    1,
    TRUE,
    'system'
);

-- ===============================================
-- SYSTEM CHECKLISTS
-- ===============================================

-- Feature implementation checklist
INSERT OR REPLACE INTO checklists (
    id,
    name,
    description,
    category,
    scope,
    priority,
    auto_apply,
    active
) VALUES (
    'feature_implementation_checklist',
    'Feature Implementation Checklist',
    'Standard checklist for implementing new features',
    'development',
    'task',
    80,
    TRUE,
    TRUE
);

-- Feature implementation checklist items
INSERT OR REPLACE INTO checklist_items (
    checklist_id,
    title,
    description,
    order_index,
    required,
    estimated_duration
) VALUES 
('feature_implementation_checklist', 'Requirements Analysis', 'Analyze and understand the feature requirements thoroughly', 1, TRUE, 3600),
('feature_implementation_checklist', 'Design Architecture', 'Design the feature architecture and integration points', 2, TRUE, 7200),
('feature_implementation_checklist', 'Implement Core Logic', 'Implement the main feature functionality', 3, TRUE, 14400),
('feature_implementation_checklist', 'Add Unit Tests', 'Create comprehensive unit tests', 4, TRUE, 3600),
('feature_implementation_checklist', 'Integration Testing', 'Test feature integration with existing system', 5, TRUE, 3600),
('feature_implementation_checklist', 'Performance Testing', 'Verify feature performance meets requirements', 6, FALSE, 1800),
('feature_implementation_checklist', 'Security Review', 'Review feature for security implications', 7, TRUE, 1800),
('feature_implementation_checklist', 'Documentation', 'Update relevant documentation', 8, TRUE, 3600),
('feature_implementation_checklist', 'Code Review', 'Submit code for peer review', 9, TRUE, 1800),
('feature_implementation_checklist', 'Deployment Preparation', 'Prepare feature for deployment', 10, TRUE, 1800);

-- Bug fix checklist
INSERT OR REPLACE INTO checklists (
    id,
    name,
    description,
    category,
    scope,
    priority,
    auto_apply,
    active
) VALUES (
    'bug_fix_checklist',
    'Bug Fix Checklist',
    'Standard checklist for fixing bugs and issues',
    'maintenance',
    'task',
    90,
    TRUE,
    TRUE
);

-- Bug fix checklist items
INSERT OR REPLACE INTO checklist_items (
    checklist_id,
    title,
    description,
    order_index,
    required,
    estimated_duration
) VALUES 
('bug_fix_checklist', 'Reproduce Bug', 'Reproduce the bug consistently', 1, TRUE, 1800),
('bug_fix_checklist', 'Root Cause Analysis', 'Identify the root cause of the bug', 2, TRUE, 3600),
('bug_fix_checklist', 'Impact Assessment', 'Assess the impact and scope of the bug', 3, TRUE, 1800),
('bug_fix_checklist', 'Fix Implementation', 'Implement the bug fix', 4, TRUE, 7200),
('bug_fix_checklist', 'Fix Verification', 'Verify the fix resolves the issue', 5, TRUE, 1800),
('bug_fix_checklist', 'Regression Testing', 'Test for any regression issues', 6, TRUE, 3600),
('bug_fix_checklist', 'Edge Case Testing', 'Test edge cases related to the fix', 7, FALSE, 1800),
('bug_fix_checklist', 'Documentation Update', 'Update any relevant documentation', 8, FALSE, 1800),
('bug_fix_checklist', 'Stakeholder Notification', 'Notify relevant stakeholders', 9, TRUE, 600);

-- Research checklist
INSERT OR REPLACE INTO checklists (
    id,
    name,
    description,
    category,
    scope,
    priority,
    auto_apply,
    active
) VALUES (
    'research_checklist',
    'Research Task Checklist',
    'Standard checklist for research and analysis tasks',
    'research',
    'task',
    70,
    TRUE,
    TRUE
);

-- Research checklist items
INSERT OR REPLACE INTO checklist_items (
    checklist_id,
    title,
    description,
    order_index,
    required,
    estimated_duration
) VALUES 
('research_checklist', 'Define Scope', 'Clearly define the research scope and objectives', 1, TRUE, 1800),
('research_checklist', 'Literature Review', 'Review existing literature and resources', 2, TRUE, 7200),
('research_checklist', 'Data Collection', 'Collect relevant data and information', 3, TRUE, 10800),
('research_checklist', 'Analysis', 'Analyze collected data and information', 4, TRUE, 14400),
('research_checklist', 'Validation', 'Validate findings and conclusions', 5, TRUE, 3600),
('research_checklist', 'Documentation', 'Document research findings and methodology', 6, TRUE, 7200),
('research_checklist', 'Peer Review', 'Get peer review of research findings', 7, FALSE, 3600),
('research_checklist', 'Recommendations', 'Formulate actionable recommendations', 8, TRUE, 3600),
('research_checklist', 'Presentation', 'Prepare presentation of findings', 9, FALSE, 3600);


