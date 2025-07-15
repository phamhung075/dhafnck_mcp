-- ===============================================
-- AGENT COORDINATION TABLES FIX
-- Updates the agent coordination tables to match
-- the repository's expected column names
-- ===============================================

-- Drop existing tables first
DROP TABLE IF EXISTS agent_communications;
DROP TABLE IF EXISTS conflict_resolutions;
DROP TABLE IF EXISTS work_handoffs;
DROP TABLE IF EXISTS work_assignments;
DROP TABLE IF EXISTS coordination_requests;

-- Recreate with correct column names
CREATE TABLE IF NOT EXISTS coordination_requests (
    request_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    requesting_agent_id TEXT NOT NULL,
    target_agent_id TEXT,
    coordination_type TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    request_data TEXT DEFAULT '{}',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS work_assignments (
    assignment_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    assigned_agent_id TEXT NOT NULL,
    assigning_agent_id TEXT DEFAULT 'system',
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deadline DATETIME,
    role TEXT,
    priority INTEGER DEFAULT 50,
    capabilities_required TEXT,
    context TEXT,
    metadata TEXT DEFAULT '{}',
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_handoffs (
    handoff_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT NOT NULL,
    from_agent_id TEXT NOT NULL,
    to_agent_id TEXT NOT NULL,
    initiated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accepted_at DATETIME,
    completed_at DATETIME,
    status TEXT NOT NULL DEFAULT 'PENDING',
    reason TEXT,
    handoff_data TEXT DEFAULT '{}',
    context TEXT,
    metadata TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conflict_resolutions (
    conflict_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    task_id TEXT,
    conflict_type TEXT NOT NULL,
    detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    resolution_strategy TEXT,
    involved_agents TEXT NOT NULL,
    conflict_details TEXT,
    resolution_details TEXT,
    resolved_by_agent_id TEXT,
    metadata TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_communications (
    message_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    from_agent_id TEXT NOT NULL,
    to_agent_ids TEXT NOT NULL DEFAULT '[]',
    task_id TEXT,
    communication_type TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'NORMAL',
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);