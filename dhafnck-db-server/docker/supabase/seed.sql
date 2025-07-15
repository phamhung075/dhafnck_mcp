-- Seed data for dhafnck-db-server
-- This file is run after migrations to populate initial data

-- Set application user for audit tracking
SET app.current_user = 'system';

-- Create some sample templates for testing
INSERT INTO templates (id, name, category, type, description, content, variables, required_variables, compatible_agents) VALUES 
(
    uuid_generate_v4(),
    'Task Summary Template',
    'reporting',
    'document',
    'Template for generating task summary reports',
    '# Task Summary Report

## Task: {{task_title}}

**Status:** {{task_status}}
**Priority:** {{task_priority}}
**Assigned to:** {{assignees}}

### Description
{{task_description}}

### Progress
- Total Subtasks: {{total_subtasks}}
- Completed: {{completed_subtasks}}
- Progress: {{completion_percentage}}%

### Details
{{task_details}}

Generated at: {{timestamp}}',
    '{"task_title": "string", "task_status": "string", "task_priority": "string", "assignees": "array", "task_description": "string", "total_subtasks": "number", "completed_subtasks": "number", "completion_percentage": "number", "task_details": "string", "timestamp": "datetime"}',
    '["task_title", "task_status"]',
    '["task-planning-agent", "scribe-agent"]'
),
(
    uuid_generate_v4(),
    'API Endpoint Documentation',
    'documentation',
    'document',
    'Template for documenting API endpoints',
    '# {{endpoint_name}} API Documentation

## Endpoint
`{{http_method}} {{endpoint_path}}`

## Description
{{endpoint_description}}

## Parameters
{{#each parameters}}
- **{{name}}** ({{type}}, {{required}}): {{description}}
{{/each}}

## Request Body
```json
{{request_body_example}}
```

## Response
```json
{{response_example}}
```

## Error Codes
{{#each error_codes}}
- **{{code}}**: {{description}}
{{/each}}

## Examples
{{examples}}',
    '{"endpoint_name": "string", "http_method": "string", "endpoint_path": "string", "endpoint_description": "string", "parameters": "array", "request_body_example": "string", "response_example": "string", "error_codes": "array", "examples": "string"}',
    '["endpoint_name", "http_method", "endpoint_path"]',
    '["documentation-agent", "coding-agent"]'
);

-- Create sample checklists
INSERT INTO task_checklists (id, task_id, checklist_type, source, priority, status, auto_generated) VALUES
(
    uuid_generate_v4(),
    uuid_generate_v4(), -- This would be a real task ID in production
    'quality_assurance',
    'automated_generation',
    'high',
    'not_started',
    true
),
(
    uuid_generate_v4(),
    uuid_generate_v4(), -- This would be a real task ID in production
    'code_review',
    'template_based',
    'medium',
    'not_started',
    true
);

-- Create sample checklist items for the QA checklist
INSERT INTO checklist_items (
    checklist_id,
    title,
    description,
    category,
    priority,
    validation_type,
    validation_criteria,
    estimated_effort
) VALUES
(
    (SELECT id FROM task_checklists WHERE checklist_type = 'quality_assurance' LIMIT 1),
    'Code formatting check',
    'Verify that all code follows the project formatting standards',
    'code_quality',
    'medium',
    'automated',
    '{"tool": "black", "config": "pyproject.toml", "pass_criteria": "no_formatting_changes"}',
    '15 minutes'
),
(
    (SELECT id FROM task_checklists WHERE checklist_type = 'quality_assurance' LIMIT 1),
    'Unit test coverage',
    'Ensure minimum test coverage is met',
    'testing',
    'high',
    'automated',
    '{"tool": "pytest-cov", "min_coverage": 80, "exclude": ["tests/", "migrations/"]}',
    '30 minutes'
),
(
    (SELECT id FROM task_checklists WHERE checklist_type = 'quality_assurance' LIMIT 1),
    'Documentation review',
    'Review and update relevant documentation',
    'documentation',
    'medium',
    'manual',
    '{"checklist": ["README updated", "API docs current", "inline comments added"]}',
    '45 minutes'
);

-- Create sample checklist items for code review
INSERT INTO checklist_items (
    checklist_id,
    title,
    description,
    category,
    priority,
    validation_type,
    validation_criteria,
    estimated_effort
) VALUES
(
    (SELECT id FROM task_checklists WHERE checklist_type = 'code_review' LIMIT 1),
    'Security review',
    'Check for common security vulnerabilities',
    'security',
    'high',
    'automated',
    '{"tools": ["bandit", "safety"], "fail_on": ["high", "critical"]}',
    '20 minutes'
),
(
    (SELECT id FROM task_checklists WHERE checklist_type = 'code_review' LIMIT 1),
    'Code complexity check',
    'Verify code complexity is within acceptable limits',
    'maintainability',
    'medium',
    'automated',
    '{"tool": "radon", "max_complexity": 10, "exclude": ["tests/"]}',
    '15 minutes'
),
(
    (SELECT id FROM task_checklists WHERE checklist_type = 'code_review' LIMIT 1),
    'Architecture compliance',
    'Ensure code follows architectural patterns',
    'architecture',
    'high',
    'manual',
    '{"checklist": ["DDD principles followed", "proper separation of concerns", "dependency injection used"]}',
    '60 minutes'
);

-- Create template-checklist mappings
INSERT INTO template_checklist_mappings (
    template_id,
    checklist_type,
    generates_checklists,
    required_validations,
    minimum_completion_percentage
) VALUES
(
    (SELECT id FROM templates WHERE name = 'API Endpoint Documentation' LIMIT 1),
    'documentation',
    '["documentation_review", "api_testing"]',
    '["manual_review", "automated_testing"]',
    90.00
);

-- Create some sample quality gates
INSERT INTO quality_gates (
    task_id,
    checklist_id,
    gate_type,
    gate_config,
    is_blocking,
    minimum_completion_percentage,
    required_categories
) VALUES
(
    uuid_generate_v4(), -- This would be a real task ID in production
    (SELECT id FROM task_checklists WHERE checklist_type = 'quality_assurance' LIMIT 1),
    'quality_gate',
    '{"name": "pre_deployment", "description": "Quality gate before deployment"}',
    true,
    95.00,
    '["testing", "security", "documentation"]'
);

-- Update checklist completion stats (this will be triggered automatically in production)
SELECT update_checklist_completion_stats() FROM checklist_items LIMIT 1;

-- Create some file monitoring patterns
INSERT INTO glob_pattern_monitoring (task_id, pattern, template_ids) VALUES
(
    uuid_generate_v4(), -- This would be a real task ID in production
    'src/**/*.py',
    (SELECT json_agg(id) FROM templates WHERE category = 'documentation')
),
(
    uuid_generate_v4(), -- This would be a real task ID in production
    'tests/**/*.py',
    (SELECT json_agg(id) FROM templates WHERE name LIKE '%test%')
);

-- Reset the application user setting
RESET app.current_user;