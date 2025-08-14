# How Context and Vision Work Together

## The Reality of the System

### What MCP Context System Is
- **A cloud notebook** where AI agents manually write and read notes
- **NOT automatic capture** - AI must remember to update it
- **Cloud-synced** - When AI writes, it syncs automatically
- **Multi-agent aware** - Other AIs can read the same notebook

### What Vision System Is
- **Server-side enrichment** that adds strategic context to responses
- **Workflow hints** that guide AI on what to do next
- **Progress tracking** through required parameters
- **NOT client-side tracking** - Works through MCP parameters only

## How They Work Together

### 1. Task Creation Flow
```
User creates task
    ↓
Vision System enriches response with:
    - Strategic alignment (why this matters)
    - Workflow hints (what to do)
    - Context template (what to track)
    ↓
AI reads enriched task
    ↓
AI manually updates context notebook with plans
```

### 2. During Work Flow
```
AI reads from context notebook (manual check)
    ↓
AI does work with built-in tools
    ↓
AI manually updates context notebook:
    - Files read/modified
    - Decisions made
    - Discoveries found
    ↓
Context syncs to cloud (automatic)
    ↓
Other AIs can see updates
```

### 3. Task Completion Flow
```
AI prepares to complete task
    ↓
Vision System REQUIRES completion_summary
    ↓
AI must provide detailed summary
    ↓
Summary becomes part of context
    ↓
Knowledge preserved for future
```

## The Manual Parts (AI Must Do)

### 1. Check Context Before Starting
```python
# AI should always start by checking context
context = manage_context(
    action="get",
    level="task",
    context_id=task_id,
    include_inherited=True
)

# See previous work and decisions
previous_work = context.get("data", {}).get("progress", [])
```

### 2. Update Context During Work
```python
# AI must manually track and update
manage_context(
    action="update",
    level="task",
    context_id=task_id,
    data={
        "files_modified": ["auth/jwt.py", "tests/test_jwt.py"],
        "decisions": ["Use Redis for token storage"],
        "discoveries": ["Found existing Redis config"],
        "progress": ["Implemented refresh token logic"]
    }
)
```

### 3. Complete with Summary (Vision Enforced)
```python
# Vision System makes this REQUIRED
manage_task(
    action="complete",
    task_id=task_id,
    completion_summary="""
    Implemented JWT refresh tokens:
    - Modified auth/jwt.py for generation
    - Added Redis storage integration
    - Created comprehensive tests
    - All tests passing
    """
)
```

## The Automatic Parts (System Does)

### 1. Vision Enrichment
When AI gets a task, the response automatically includes:
```json
{
    "task": {
        "id": "123",
        "title": "Implement refresh tokens",
        "vision_alignment": {
            "contributes_to": "Secure Authentication Epic",
            "business_value": "Improved user experience"
        },
        "workflow_guidance": {
            "next_action": "Read existing auth implementation",
            "suggested_approach": "Check for Redis availability first",
            "related_patterns": ["JWT implementation in auth/"]
        }
    }
}
```

### 2. Context Cloud Sync
- When AI writes to context → Syncs to cloud automatically
- When AI reads context → Gets latest from cloud automatically
- Network failures → Local journal ensures no data loss

### 3. Multi-Agent Notifications
- Agent A updates context → Agents B, C, D get notified
- Conflict resolution → Automatic merge or version
- Eventually consistent → All agents see same notebook

## Best Practices

### 1. Start Every Task
```python
# 1. Get task with vision enrichment
task = manage_task(action="get", task_id=task_id)

# 2. Check context notebook
context = manage_context(action="get", level="task", context_id=task_id)

# 3. Plan based on both
# - Vision tells you WHY and suggests HOW
# - Context tells you what was done before
```

### 2. Regular Updates
```python
# After each significant step
manage_context(
    action="add_progress",
    level="task",
    context_id=task_id,
    content="Completed authentication flow implementation"
)

# After discoveries
manage_context(
    action="add_insight",
    level="task",
    context_id=task_id,
    content="Redis TTL should be 24 hours for refresh tokens",
    category="technical"
)
```

### 3. Complete Thoroughly
```python
# Vision requires completion_summary
# Make it detailed for knowledge preservation
manage_task(
    action="complete",
    task_id=task_id,
    completion_summary=detailed_summary,
    testing_notes="All tests passing, 95% coverage"
)
```

## Why This Design?

### Constraints We Work With
1. **Cannot modify AI tools** - Claude Code/Cursor tools are fixed
2. **No persistent sessions** - Each AI call is independent
3. **No client tracking** - Can't see what AI does automatically
4. **Manual discipline needed** - AI must remember to update

### Benefits Despite Constraints
1. **Knowledge preserved** - Context captures decisions and work
2. **Multi-agent coordination** - All AIs see same notebook
3. **Strategic alignment** - Vision guides toward goals
4. **Workflow assistance** - Hints help AI know what to do
5. **Cloud reliability** - Automatic sync prevents data loss

## Summary

The Context System is a **manual cloud notebook** that AI must remember to use, while the Vision System provides **automatic enrichment** to guide the AI's work. Together they create a system where:

- AI gets strategic guidance (Vision)
- AI manually tracks work (Context)  
- Knowledge is preserved (Cloud sync)
- Multiple AIs can collaborate (Shared notebook)
- Progress toward goals is tracked (Vision alignment)

The key is **AI discipline** - remembering to check and update the notebook!