-- Template and Checklist System Database Schema (PostgreSQL)
-- Converted from SQLite for dhafnck_mcp project
-- Date: 2025-07-03

-- Create ENUM types for templates and checklists
CREATE TYPE template_type AS ENUM ('document', 'config', 'code', 'email', 'report');
CREATE TYPE checklist_type AS ENUM ('quality_assurance', 'deployment', 'testing', 'code_review', 'documentation');
CREATE TYPE checklist_status AS ENUM ('not_started', 'in_progress', 'completed', 'failed', 'blocked');
CREATE TYPE checklist_item_status AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'skipped', 'blocked');
CREATE TYPE validation_type AS ENUM ('manual', 'automated', 'file_exists', 'content_check', 'test_result');

-- ===============================================
-- TEMPLATES SCHEMA
-- ===============================================

CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    type template_type NOT NULL DEFAULT 'document',
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    description TEXT,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    validation_rules JSONB DEFAULT '[]',
    output_format VARCHAR(50) DEFAULT 'markdown',
    usage_scenarios JSONB DEFAULT '[]',
    required_variables JSONB DEFAULT '[]',
    optional_variables JSONB DEFAULT '[]',
    compatible_agents JSONB DEFAULT '["*"]',
    default_globs TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_type ON templates(type);
CREATE INDEX idx_templates_created_by ON templates(created_by);
CREATE INDEX idx_templates_name_search ON templates USING gin(to_tsvector('english', name));
CREATE INDEX idx_templates_description_search ON templates USING gin(to_tsvector('english', description));
CREATE INDEX idx_templates_variables ON templates USING gin(variables);
CREATE INDEX idx_templates_active ON templates(is_active) WHERE is_active = true;

-- Template usage tracking
CREATE TABLE template_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    task_id UUID,
    project_id VARCHAR(100),
    git_branch_name VARCHAR(100) DEFAULT 'main',
    agent_name VARCHAR(100),
    variables_used JSONB DEFAULT '{}',
    output_path TEXT,
    rendered_content TEXT,
    generation_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT false,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_template_usage_template_id ON template_usage(template_id);
CREATE INDEX idx_template_usage_task_id ON template_usage(task_id);
CREATE INDEX idx_template_usage_project ON template_usage(project_id, git_branch_name);
CREATE INDEX idx_template_usage_generated_at ON template_usage(generated_at);

-- ===============================================
-- CHECKLISTS SCHEMA  
-- ===============================================

CREATE TABLE task_checklists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) NOT NULL,
    checklist_type checklist_type NOT NULL,
    source VARCHAR(255) NOT NULL,
    priority task_priority NOT NULL DEFAULT 'medium',
    status checklist_status NOT NULL DEFAULT 'not_started',
    auto_generated BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_task_checklists_task_id ON task_checklists(task_id);
CREATE INDEX idx_task_checklists_type ON task_checklists(checklist_type);
CREATE INDEX idx_task_checklists_status ON task_checklists(status);

-- Individual checklist items
CREATE TABLE checklist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    checklist_id UUID NOT NULL REFERENCES task_checklists(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    priority task_priority NOT NULL DEFAULT 'medium',
    status checklist_item_status NOT NULL DEFAULT 'pending',
    validation_type validation_type NOT NULL,
    validation_criteria JSONB,
    validation_evidence TEXT,
    related_files JSONB DEFAULT '[]',
    related_templates JSONB DEFAULT '[]',
    assigned_agent VARCHAR(100),
    dependencies JSONB DEFAULT '[]',
    estimated_effort VARCHAR(50),
    completion_timestamp TIMESTAMPTZ,
    validated_by VARCHAR(100),
    validation_notes TEXT,
    auto_validation_config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_checklist_items_checklist_id ON checklist_items(checklist_id);
CREATE INDEX idx_checklist_items_status ON checklist_items(status);
CREATE INDEX idx_checklist_items_category ON checklist_items(category);
CREATE INDEX idx_checklist_items_validation_type ON checklist_items(validation_type);
CREATE INDEX idx_checklist_items_assigned_agent ON checklist_items(assigned_agent);
CREATE INDEX idx_checklist_items_title_search ON checklist_items USING gin(to_tsvector('english', title));

-- Checklist completion statistics
CREATE TABLE checklist_completion_stats (
    checklist_id UUID PRIMARY KEY REFERENCES task_checklists(id) ON DELETE CASCADE,
    total_items INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    blocked_items INTEGER DEFAULT 0,
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- ===============================================
-- TEMPLATE-CHECKLIST INTEGRATION
-- ===============================================

CREATE TABLE template_checklist_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    checklist_type checklist_type NOT NULL,
    generates_checklists JSONB DEFAULT '[]',
    required_validations JSONB DEFAULT '[]',
    quality_gates JSONB DEFAULT '{}',
    minimum_completion_percentage DECIMAL(5,2) DEFAULT 80.00,
    critical_items_required BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(template_id, checklist_type)
);

CREATE INDEX idx_template_checklist_mappings_template ON template_checklist_mappings(template_id);
CREATE INDEX idx_template_checklist_mappings_type ON template_checklist_mappings(checklist_type);

-- Quality gates configuration
CREATE TABLE quality_gates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    checklist_id UUID REFERENCES task_checklists(id) ON DELETE CASCADE,
    gate_type VARCHAR(50) NOT NULL,
    gate_config JSONB NOT NULL DEFAULT '{}',
    is_blocking BOOLEAN DEFAULT true,
    minimum_completion_percentage DECIMAL(5,2) DEFAULT 90.00,
    required_categories JSONB DEFAULT '[]',
    blocking_items JSONB DEFAULT '[]',
    status checklist_item_status DEFAULT 'pending',
    evaluated_at TIMESTAMPTZ,
    evaluated_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_quality_gates_task_id ON quality_gates(task_id);
CREATE INDEX idx_quality_gates_checklist_id ON quality_gates(checklist_id);
CREATE INDEX idx_quality_gates_status ON quality_gates(status);

-- ===============================================
-- CONTEXT INTEGRATION SCHEMA
-- ===============================================

CREATE TABLE enhanced_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    project_id VARCHAR(100) NOT NULL DEFAULT 'dhafnck_mcp',
    git_branch_name VARCHAR(100) NOT NULL DEFAULT 'main',
    user_id VARCHAR(100) NOT NULL DEFAULT 'default_id',
    template_context JSONB DEFAULT '{}',
    checklist_context JSONB DEFAULT '{}',
    document_context JSONB DEFAULT '{}',
    glob_context JSONB DEFAULT '{}',
    agent_context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(task_id, project_id, git_branch_name)
);

CREATE INDEX idx_enhanced_context_task_id ON enhanced_context(task_id);
CREATE INDEX idx_enhanced_context_project ON enhanced_context(project_id, git_branch_name);
CREATE INDEX idx_enhanced_context_user ON enhanced_context(user_id);

-- ===============================================
-- FILE PATTERN MONITORING
-- ===============================================

CREATE TABLE glob_pattern_monitoring (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    pattern TEXT NOT NULL,
    template_ids JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_glob_pattern_monitoring_task_id ON glob_pattern_monitoring(task_id);
CREATE INDEX idx_glob_pattern_monitoring_active ON glob_pattern_monitoring(is_active) WHERE is_active = true;

CREATE TABLE file_change_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    file_path TEXT NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    matched_patterns JSONB DEFAULT '[]',
    affected_templates JSONB DEFAULT '[]',
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_file_change_events_task_id ON file_change_events(task_id);
CREATE INDEX idx_file_change_events_processed ON file_change_events(processed) WHERE processed = false;
CREATE INDEX idx_file_change_events_created_at ON file_change_events(created_at);

-- ===============================================
-- PERFORMANCE OPTIMIZATION
-- ===============================================

CREATE TABLE template_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    variables_hash VARCHAR(64) NOT NULL,
    compiled_template TEXT,
    rendered_content TEXT,
    cache_created_at TIMESTAMPTZ DEFAULT NOW(),
    cache_expires_at TIMESTAMPTZ NOT NULL,
    cache_hits INTEGER DEFAULT 0
);

CREATE INDEX idx_template_cache_expires ON template_cache(cache_expires_at);
CREATE INDEX idx_template_cache_template_id ON template_cache(template_id);

CREATE TABLE validation_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    item_id UUID NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    validation_result JSONB NOT NULL,
    cache_created_at TIMESTAMPTZ DEFAULT NOW(),
    cache_expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_validation_cache_expires ON validation_cache(cache_expires_at);
CREATE INDEX idx_validation_cache_item_id ON validation_cache(item_id);

-- ===============================================
-- AUDIT AND TRACKING
-- ===============================================

CREATE TABLE template_checklist_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_entity ON template_checklist_audit(entity_type, entity_id);
CREATE INDEX idx_audit_created_at ON template_checklist_audit(created_at);
CREATE INDEX idx_audit_changed_by ON template_checklist_audit(changed_by);

-- ===============================================
-- FUNCTIONS AND TRIGGERS
-- ===============================================

-- Function to update checklist completion statistics
CREATE OR REPLACE FUNCTION update_checklist_completion_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO checklist_completion_stats (
        checklist_id, 
        total_items, 
        completed_items, 
        failed_items, 
        blocked_items, 
        completion_percentage,
        last_updated
    )
    SELECT 
        checklist_id,
        COUNT(*) as total_items,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_items,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_items,
        COUNT(CASE WHEN status = 'blocked' THEN 1 END) as blocked_items,
        CASE 
            WHEN COUNT(*) = 0 THEN 0
            ELSE ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0) / COUNT(*), 2)
        END as completion_percentage,
        NOW()
    FROM checklist_items
    WHERE checklist_id = COALESCE(NEW.checklist_id, OLD.checklist_id)
    GROUP BY checklist_id
    ON CONFLICT (checklist_id) 
    DO UPDATE SET
        total_items = EXCLUDED.total_items,
        completed_items = EXCLUDED.completed_items,
        failed_items = EXCLUDED.failed_items,
        blocked_items = EXCLUDED.blocked_items,
        completion_percentage = EXCLUDED.completion_percentage,
        last_updated = EXCLUDED.last_updated;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update checklist stats
CREATE TRIGGER update_checklist_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON checklist_items
    FOR EACH ROW
    EXECUTE FUNCTION update_checklist_completion_stats();

-- Function to create audit records
CREATE OR REPLACE FUNCTION create_audit_record()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO template_checklist_audit (
        entity_type,
        entity_id,
        action,
        old_values,
        new_values,
        changed_by
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN row_to_json(NEW) ELSE NULL END,
        current_setting('app.current_user', true)
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Audit triggers for key tables
CREATE TRIGGER templates_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON templates
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_record();

CREATE TRIGGER checklist_items_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON checklist_items
    FOR EACH ROW
    EXECUTE FUNCTION create_audit_record();

-- Trigger to update updated_at on templates
CREATE TRIGGER update_templates_timestamp
    BEFORE UPDATE ON templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update updated_at on task_checklists
CREATE TRIGGER update_task_checklists_timestamp
    BEFORE UPDATE ON task_checklists
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update updated_at on checklist_items
CREATE TRIGGER update_checklist_items_timestamp
    BEFORE UPDATE ON checklist_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update updated_at on enhanced_context
CREATE TRIGGER update_enhanced_context_timestamp
    BEFORE UPDATE ON enhanced_context
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===============================================
-- VIEWS FOR COMMON QUERIES
-- ===============================================

-- Template usage statistics view
CREATE VIEW template_usage_stats AS
SELECT 
    t.id,
    t.name,
    t.category,
    t.type,
    COUNT(tu.id) as usage_count,
    AVG(tu.generation_time_ms) as avg_generation_time,
    COUNT(CASE WHEN tu.cache_hit = true THEN 1 END) as cache_hits,
    MAX(tu.generated_at) as last_used
FROM templates t
LEFT JOIN template_usage tu ON t.id = tu.template_id
WHERE t.is_active = true
GROUP BY t.id, t.name, t.category, t.type;

-- Checklist progress summary view
CREATE VIEW checklist_progress_summary AS
SELECT 
    tc.id as checklist_id,
    tc.task_id,
    tc.checklist_type,
    tc.status as checklist_status,
    ccs.total_items,
    ccs.completed_items,
    ccs.failed_items,
    ccs.blocked_items,
    ccs.completion_percentage,
    COUNT(CASE WHEN ci.priority = 'urgent' THEN 1 END) as urgent_items,
    COUNT(CASE WHEN ci.priority = 'high' THEN 1 END) as high_priority_items
FROM task_checklists tc
LEFT JOIN checklist_completion_stats ccs ON tc.id = ccs.checklist_id
LEFT JOIN checklist_items ci ON tc.id = ci.checklist_id
GROUP BY tc.id, tc.task_id, tc.checklist_type, tc.status, 
         ccs.total_items, ccs.completed_items, ccs.failed_items, 
         ccs.blocked_items, ccs.completion_percentage;