"""
Delegation Queue Management Tool Description

This module contains the comprehensive documentation for the manage_delegation_queue MCP tool.
Separated from the controller logic for better maintainability and organization.
"""

MANAGE_DELEGATION_QUEUE_DESCRIPTION = """
📋 DELEGATION QUEUE MANAGEMENT SYSTEM - Manual review and approval workflow

⭐ WHAT IT DOES: Manages delegation queue for manual review and approval of context delegations from lower to higher levels.
📋 WHEN TO USE: Delegation queue operations, manual approval workflows, and delegation oversight.
🎯 CRITICAL FOR: Delegation governance, manual review processes, and delegation audit trails.

| Action              | Required Parameters         | Optional Parameters                | Description                                      |
|---------------------|----------------------------|------------------------------------|--------------------------------------------------|
| list                | (none)                     | target_level, target_id            | Get pending delegations                          |
| approve             | delegation_id              |                                    | Approve a pending delegation                     |
| reject              | delegation_id              | rejection_reason                   | Reject a pending delegation                      |
| get_status          | (none)                     |                                    | Get queue status and statistics                  |

🔄 DELEGATION WORKFLOW:
1. Task/Project context requests delegation to higher level
2. Delegation is queued for manual review
3. Administrator reviews and approves/rejects
4. Approved delegations are applied to target context
5. Rejected delegations are logged with reason

📊 QUEUE STATISTICS:
• Total pending delegations
• Delegations by target level (project, global)
• Average approval time
• Rejection rate and common reasons

🤖 AI USAGE RULES:

1. ACTION SELECTION DECISION TREE:
   • Need to see what's pending → action="list"
   • Need to approve delegation → action="approve" + delegation_id
   • Need to reject delegation → action="reject" + delegation_id + rejection_reason
   • Need queue overview → action="get_status"

2. PARAMETER REQUIREMENTS:
   • action: Always required, must be 'list', 'approve', 'reject', or 'get_status'
   • delegation_id: Required for approve/reject actions only
   • rejection_reason: Optional for reject, but recommended for audit trail
   • target_level: Optional filter for list action ('project', 'global')
   • target_id: Optional filter for list action (specific project/context ID)

3. WORKFLOW PATTERNS:
   • Regular review: action="list" → review each → approve/reject
   • Bulk review: action="list" with filters → batch approve/reject
   • Status monitoring: action="get_status" for metrics

4. APPROVAL CRITERIA GUIDANCE:
   • Approve if delegation benefits organization-wide patterns
   • Approve if pattern is mature and reusable
   • Reject if delegation is task-specific or incomplete
   • Reject if security/compliance concerns exist

💡 PRACTICAL EXAMPLES:

1. List all pending delegations:
   action="list"

2. List delegations for specific project:
   action="list", target_level="project", target_id="proj-123"

3. Approve a delegation:
   action="approve", delegation_id="del-uuid-123"

4. Reject with reason:
   action="reject", delegation_id="del-uuid-456", rejection_reason="Pattern too specific for project scope"

5. Check queue status:
   action="get_status"

📈 DELEGATION REVIEW GUIDELINES:

APPROVE WHEN:
• Pattern solves common problem across multiple tasks/projects
• Implementation is mature and well-tested
• Documentation is clear and comprehensive
• Benefits outweigh maintenance overhead
• Security and compliance requirements met

REJECT WHEN:
• Pattern is task-specific or one-off solution
• Implementation is incomplete or experimental
• Documentation is insufficient
• Security concerns or compliance violations
• Would create organizational complexity

🎯 VALIDATION RULES:
• action: Must be one of ['list', 'approve', 'reject', 'get_status']
• delegation_id: Must be valid UUID format when provided
• target_level: Must be 'project' or 'global' when provided
• rejection_reason: Should be descriptive when provided

🔍 RESPONSE FORMATS:

LIST RESPONSE:
{
  "pending_delegations": [
    {
      "delegation_id": "uuid",
      "source_context": "task-123",
      "target_level": "project",
      "data": {...},
      "created_at": "2024-01-01T00:00:00Z",
      "reason": "Delegation reason"
    }
  ],
  "count": 1
}

APPROVE/REJECT RESPONSE:
{
  "success": true,
  "delegation_id": "uuid",
  "status": "approved" | "rejected",
  "reason": "optional rejection reason"
}

STATUS RESPONSE:
{
  "pending": 5,
  "approved": 15,
  "rejected": 3,
  "total": 23,
  "average_approval_time": "2.5 hours",
  "rejection_rate": "13%"
}

🔧 FEATURES:
• Filtering by target level and ID
• Detailed delegation metadata
• Audit trail for all actions
• Bulk operation support
• Automatic cleanup of old entries

🛑 ERROR HANDLING:
• If required fields are missing, a clear error message is returned specifying which fields are needed.
• Unknown actions return an error listing valid actions.
• Invalid delegation IDs return not found errors.
• Internal errors are logged and returned with a generic error message.
"""

MANAGE_DELEGATION_QUEUE_PARAMETERS = {
    "action": "Queue action to perform. Required. Valid: 'list', 'approve', 'reject', 'get_status'",
    "delegation_id": "Delegation identifier (UUID). Required for approve/reject actions. Get from list response.",
    "target_level": "Filter by target level for list action. Optional. Valid: 'project', 'global'",
    "target_id": "Filter by target ID for list action. Optional. Specific project or context identifier",
    "rejection_reason": "Reason for rejection. Optional but recommended for reject action. Used for audit trail and feedback"
}