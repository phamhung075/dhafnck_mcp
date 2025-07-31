# Context Response Format Specification

## Overview

This document defines the standardized response format for all context operations in the DhafnckMCP system. All context management operations now return consistent, predictable response structures.

## Standardized Response Structure

All context operations return responses following this base structure:

```json
{
  "status": "success|partial_success|failure",
  "success": true|false,
  "operation": "manage_context.{action}",
  "operation_id": "uuid-string",
  "timestamp": "2025-01-19T10:30:00.000Z",
  "data": {
    // Operation-specific data (see below)
  },
  "metadata": {
    "context_operation": {
      "level": "global|project|branch|task",
      "context_id": "string",
      // Additional operation-specific fields
    },
    "operation_details": {
      "operation": "manage_context.{action}",
      "operation_id": "uuid-string",
      "timestamp": "2025-01-19T10:30:00.000Z"
    }
  },
  "confirmation": {
    "operation_completed": true|false,
    "data_persisted": true|false,
    "partial_failures": [],
    "operation_details": {
      "operation": "manage_context.{action}",
      "operation_id": "uuid-string",
      "timestamp": "2025-01-19T10:30:00.000Z"
    }
  }
}
```

## Operation-Specific Data Formats

### Single Context Operations (create, get, update, resolve)

**Actions**: `create`, `get`, `update`, `resolve`

**Data Structure**:
```json
{
  "data": {
    "context_data": {
      // The actual context object
      "id": "context-id",
      "level": "task",
      "data": {
        "title": "Context Title",
        "description": "Context Description",
        // ... other context fields
      },
      "created_at": "2025-01-19T10:30:00.000Z",
      "updated_at": "2025-01-19T10:30:00.000Z"
    }
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "context_id": "task-123",
      "inherited": false,    // For get operations
      "propagated": true,    // For update operations
      "created": true        // For create operations (indicates if new or existing)
    }
  }
}
```

**Examples**:

#### Create Context
```json
{
  "status": "success",
  "success": true,
  "operation": "manage_context.create",
  "operation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-19T10:30:00.000Z",
  "data": {
    "context_data": {
      "id": "task-123",
      "level": "task",
      "data": {
        "title": "Implement user authentication",
        "description": "Add JWT-based authentication system",
        "priority": "high",
        "status": "in_progress"
      },
      "created_at": "2025-01-19T10:30:00.000Z",
      "updated_at": "2025-01-19T10:30:00.000Z"
    }
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "context_id": "task-123",
      "created": true
    }
  }
}
```

#### Get Context
```json
{
  "status": "success",
  "success": true,
  "operation": "manage_context.get",
  "data": {
    "context_data": {
      "id": "task-123",
      "level": "task",
      "data": {
        "title": "Implement user authentication",
        "description": "Add JWT-based authentication system",
        "priority": "high",
        "status": "in_progress",
        "progress": 45
      }
    }
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "context_id": "task-123",
      "inherited": false
    }
  }
}
```

### List Operations

**Action**: `list`

**Data Structure**:
```json
{
  "data": {
    "contexts": [
      {
        "id": "context-1",
        "level": "task",
        "data": { /* context data */ }
      },
      {
        "id": "context-2", 
        "level": "task",
        "data": { /* context data */ }
      }
    ]
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "count": 2
    }
  }
}
```

**Example**:
```json
{
  "status": "success",
  "success": true,
  "operation": "manage_context.list",
  "data": {
    "contexts": [
      {
        "id": "task-123",
        "level": "task",
        "data": {
          "title": "Implement authentication",
          "status": "in_progress"
        }
      },
      {
        "id": "task-124",
        "level": "task", 
        "data": {
          "title": "Add user dashboard",
          "status": "todo"
        }
      }
    ]
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "count": 2
    }
  }
}
```

### Delegation Operations

**Action**: `delegate`

**Data Structure**:
```json
{
  "data": {
    "delegation_result": {
      "source_context_id": "task-123",
      "target_context_id": "project-456", 
      "delegated_data": { /* data that was delegated */ },
      "delegation_reason": "Reusable pattern for team"
    }
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "context_id": "task-123",
      "source_level": "task",
      "target_level": "project"
    }
  }
}
```

### Resolve Operations  

**Action**: `resolve`

**Data Structure**:
```json
{
  "data": {
    "resolved_context": {
      "id": "task-123",
      "level": "task",
      "data": { /* context data with inheritance resolved */ },
      "inheritance_chain": [
        {"level": "global", "data": { /* inherited data */ }},
        {"level": "project", "data": { /* inherited data */ }},
        {"level": "branch", "data": { /* inherited data */ }},
        {"level": "task", "data": { /* local data */ }}
      ]
    }
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "context_id": "task-123"
    }
  }
}
```

### Delete Operations

**Action**: `delete`

**Data Structure**:
```json
{
  "data": {},
  "metadata": {
    "context_operation": {
      "level": "task",
      "context_id": "task-123"
    }
  }
}
```

## Error Response Format

All error responses follow this structure:

```json
{
  "status": "failure",
  "success": false,
  "operation": "manage_context.{action}",
  "operation_id": "uuid-string", 
  "timestamp": "2025-01-19T10:30:00.000Z",
  "error": {
    "message": "Context not found: task-123",
    "code": "NOT_FOUND",
    "operation": "manage_context.get",
    "timestamp": "2025-01-19T10:30:00.000Z"
  },
  "metadata": {
    "context_operation": {
      "level": "task",
      "context_id": "task-123"
    }
  },
  "confirmation": {
    "operation_completed": false,
    "data_persisted": false,
    "partial_failures": []
  }
}
```

## Key Benefits

### 1. **Predictable Field Names**
- Single context: Always `context_data`
- Multiple contexts: Always `contexts` (array)
- Delegation results: Always `delegation_result`
- Resolved contexts: Always `resolved_context`

### 2. **Consistent Metadata**
- All operations include `context_operation` metadata
- Operation details are standardized
- Context level and ID always available

### 3. **Operation Tracking**
- Every response includes unique `operation_id`
- Timestamps for audit trails
- Confirmation details for verification

### 4. **Backward Compatibility**
- Responses include legacy `success` field
- Error handling preserved
- Migration path for existing code

## Usage Examples

### JavaScript/TypeScript Usage

```typescript
interface ContextResponse {
  status: 'success' | 'partial_success' | 'failure';
  success: boolean;
  operation: string;
  operation_id: string;
  timestamp: string;
  data?: {
    context_data?: ContextData;
    contexts?: ContextData[];
    delegation_result?: DelegationResult;
    resolved_context?: ResolvedContext;
  };
  metadata?: {
    context_operation?: {
      level?: string;
      context_id?: string;
      inherited?: boolean;
      propagated?: boolean;
      created?: boolean;
      count?: number;
    };
  };
}

// Usage
const response: ContextResponse = await manageContext({
  action: 'get',
  level: 'task',
  context_id: 'task-123'
});

if (response.success && response.data?.context_data) {
  console.log('Context:', response.data.context_data);
}
```

### Python Usage

```python
from typing import Dict, Any, Optional, List

def handle_context_response(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract context data from standardized response."""
    if not response.get('success'):
        print(f"Error: {response.get('error', {}).get('message')}")
        return None
    
    data = response.get('data', {})
    
    # Handle different response types
    if 'context_data' in data:
        return data['context_data']
    elif 'contexts' in data:
        return data['contexts']
    elif 'resolved_context' in data:
        return data['resolved_context']
    
    return None

# Usage
response = manage_context(action='get', level='task', context_id='task-123')
context = handle_context_response(response)
```

## Migration Guide

### For Existing Code

1. **Update Response Handling**:
   ```python
   # Old way
   if response.get('success') and 'context' in response:
       context = response['context']
   
   # New way (backward compatible)
   if response.get('success'):
       context = response.get('data', {}).get('context_data')
   ```

2. **Use Helper Functions**:
   ```python
   from fastmcp.task_management.interface.utils.response_formatter import StandardResponseFormatter
   
   # Verify success reliably
   if StandardResponseFormatter.verify_success(response):
       data = StandardResponseFormatter.extract_data(response)
   ```

3. **Update Type Definitions**:
   - Use the provided TypeScript interfaces
   - Update error handling to check `error.code`
   - Use `operation_id` for request tracking

## API Version

- **Version**: 1.0.0
- **Effective Date**: 2025-01-19
- **Breaking Changes**: None (backward compatible)
- **Deprecation**: Legacy field names supported but deprecated

## Implementation Status

- ✅ StandardResponseFormatter updated with context formatting
- ✅ UnifiedContextMCPController updated to use new formatting
- ✅ Documentation complete
- 🔄 Tests needed for response format validation
- 🔄 Example code validation needed