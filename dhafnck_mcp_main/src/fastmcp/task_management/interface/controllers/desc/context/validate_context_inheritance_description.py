"""
Context Inheritance Validation Tool Description

This module contains the comprehensive documentation for the validate_context_inheritance MCP tool.
Separated from the controller logic for better maintainability and organization.
"""

VALIDATE_CONTEXT_INHERITANCE_DESCRIPTION = """
🔍 CONTEXT INHERITANCE VALIDATION SYSTEM - Debug and verify inheritance chains

⭐ WHAT IT DOES: Validates context inheritance chain and identifies any issues in the hierarchical context resolution process.
📋 WHEN TO USE: Debugging inheritance problems, verifying context resolution, and troubleshooting hierarchical context issues.
🎯 CRITICAL FOR: System diagnostics, inheritance troubleshooting, and context integrity verification.

🔧 VALIDATION CHECKS:
• Inheritance chain completeness
• Context resolution accuracy  
• Dependency hash validation
• Cache consistency verification
• Performance metrics analysis

📊 VALIDATION RESULTS:
• Chain validation status (valid/invalid)
• Missing or broken inheritance links
• Resolution path analysis
• Performance bottleneck identification
• Cache hit/miss ratios

🤖 AI USAGE RULES:

1. VALIDATION TRIGGERS:
   • Context resolution failing → Validate to identify inheritance issues
   • Performance degradation → Check for cache or resolution problems
   • Data inconsistencies → Verify inheritance chain integrity
   • Development debugging → Understand context flow and dependencies

2. PARAMETER REQUIREMENTS:
   • level: Required, must be 'project' or 'task' (global has no inheritance)
   • context_id: Required, must be valid UUID for existing context

3. LEVEL SELECTION RULES:
   • Use "task" when debugging task-specific context issues
   • Use "project" when debugging project-level inheritance problems
   • Start with "task" level as it includes full inheritance chain

4. VALIDATION INTERPRETATION:
   • valid=true: Inheritance chain is complete and functional
   • valid=false: Issues found - check validation_errors for details
   • warnings: Non-critical issues that may impact performance
   • errors: Critical issues requiring immediate attention

💡 PRACTICAL EXAMPLES:

1. Debug failing task context resolution:
   level="task", context_id="task-uuid-123"

2. Verify project inheritance after changes:
   level="project", context_id="project-uuid-456"

3. Performance investigation workflow:
   level="task", context_id="slow-task-uuid" → analyze resolution_timing

4. Cache consistency check:
   level="task", context_id="task-uuid" → examine cache_metrics

🔍 DIAGNOSTIC INTERPRETATION:

INHERITANCE CHAIN:
• Shows: Global → Project → Task resolution path
• Valid chain: Each level properly inherits from parent
• Broken chain: Missing parent contexts or circular dependencies

CACHE METRICS:
• hit_ratio > 80%: Good performance
• hit_ratio < 50%: Cache issues, consider cleanup
• miss_ratio high: Check for cache invalidation problems

RESOLUTION TIMING:
• < 10ms: Excellent performance
• 10-50ms: Acceptable performance
• > 50ms: Performance issue, investigate bottlenecks

VALIDATION ERRORS:
• "missing_parent": Parent context doesn't exist
• "circular_dependency": Context references create loop
• "cache_inconsistency": Cached data doesn't match source
• "resolution_failure": Cannot resolve inheritance chain

🛠️ TROUBLESHOOTING WORKFLOW:

FOR MISSING PARENT ERRORS:
1. Check if parent project/global context exists
2. Verify context creation order (parent before child)
3. Use manage_context to create missing parents

FOR PERFORMANCE ISSUES:
1. Check cache_metrics for high miss ratio
2. Use cleanup_cache action in manage_context
3. Analyze resolution_timing for bottlenecks

FOR CACHE INCONSISTENCY:
1. Force cache refresh with force_refresh=true
2. Clear problematic cache entries
3. Re-validate after cleanup

FOR CIRCULAR DEPENDENCIES:
1. Review context delegation history
2. Identify and break circular references
3. Restructure inheritance hierarchy if needed

🎯 VALIDATION RULES:
• level: Must be 'project' or 'task' (not 'global')
• context_id: Must be valid UUID format and exist in system
• Only validates contexts that should have inheritance
• Global context validation not supported (has no parents)

📊 RESPONSE FORMAT:
{
  "validation": {
    "valid": true/false,
    "errors": ["error_type: description"],
    "warnings": ["warning_type: description"],
    "inheritance_chain": ["global", "project", "task"],
    "resolution_path": [context_objects],
    "cache_metrics": {
      "hit_ratio": 0.85,
      "miss_ratio": 0.15,
      "entries": 42
    },
    "resolution_timing": {
      "total_ms": 15,
      "cache_lookup_ms": 2,
      "inheritance_resolution_ms": 13
    }
  },
  "resolution_metadata": {
    "resolved_at": "2024-01-01T00:00:00Z",
    "dependency_hash": "abc123",
    "cache_status": "hit"
  }
}

🔍 DIAGNOSTIC INFO:
• Full inheritance resolution path
• Cache performance metrics
• Dependencies hash verification
• Resolution timing analysis
• Error detection and suggestions

🛠️ TROUBLESHOOTING:
• Identifies missing parent contexts
• Detects circular dependencies
• Validates cache consistency
• Analyzes performance issues
• Provides repair suggestions

🛑 ERROR HANDLING:
• If required fields are missing, a clear error message is returned specifying which fields are needed.
• Invalid context levels or IDs return validation errors.
• Resolution failures provide detailed diagnostic information.
• Internal errors are logged and returned with a generic error message.
"""

VALIDATE_CONTEXT_INHERITANCE_PARAMETERS = {
    "level": "Context level to validate. Required. Valid: 'project', 'task' (global contexts don't have inheritance to validate)",
    "context_id": "Context identifier (UUID) to validate. Required. Must be valid task_id or project_id that exists in the system"
}