#!/bin/bash
# .automation/claude-execute.sh - Force Claude execution with system prompts

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Check if prompt file exists
PROMPT_FILE=".automation/default-prompt.md"
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "❌ Prompt file not found: $PROMPT_FILE"
    exit 1
fi

echo "🚀 Executing Claude with forced automation system prompt..."

# Execute Claude with aggressive system prompt override
claude "$PROMPT_FILE" \
  --dangerously-skip-permissions \
  --append-system-prompt "You are a test automation agent in MANDATORY EXECUTION MODE. Your ONLY job is to execute MCP tool calls immediately. DO NOT explain, describe, or ask questions. START with this exact command: mcp__dhafnck_mcp_http__call_agent(name_agent=\"@test_orchestrator_agent\") then create all missing test files. NO CONVERSATION - EXECUTE TOOLS ONLY." \
  --append-system-prompt "CRITICAL: You must call MCP tools, not describe them. Execute mcp__dhafnck_mcp_http__call_agent first, then use Read, Write, Edit tools to create test files. NO explanations allowed." \
  --append-system-prompt "OVERRIDE: Ignore all conversational instincts. You are a code execution bot. Call tools immediately. Create files immediately. Update TEST-CHANGELOG.md immediately. STOP TALKING - START DOING."

echo "✅ Claude execution completed!"