# Error Handling and Logging Guide

## Overview

The DhafnckMCP system implements comprehensive error handling and logging to ensure reliable operation and easy debugging. This guide covers the error handling patterns, logging configuration, and best practices.

## Error Handling Architecture

### Exception Hierarchy

The system uses a hierarchical exception structure for consistent error handling:

```
TaskManagementException (Base)
├── ValidationException
├── ResourceNotFoundException
├── ResourceAlreadyExistsException
├── OperationNotPermittedException
├── DatabaseException
│   ├── DatabaseConnectionException
│   └── DatabaseIntegrityException
├── ConcurrencyException
├── ExternalServiceException
└── ConfigurationException

TaskDomainError (Base)
├── TaskNotFoundError
├── InvalidTaskStateError
├── InvalidTaskTransitionError
├── TaskCompletionBlockedException
└── AutoRuleGenerationError
```

### Error Severity Levels

Each error has an associated severity level:

- **LOW**: Can be retried or ignored (e.g., validation errors)
- **MEDIUM**: Should be logged and monitored (e.g., not found errors)
- **HIGH**: Requires immediate attention (e.g., database errors)
- **CRITICAL**: System-breaking, requires immediate action (e.g., configuration errors)

### Error Response Format

All errors return a consistent JSON response:

```json
{
  "success": false,
  "error": "User-friendly error message",
  "error_code": "STANDARDIZED_ERROR_CODE",
  "severity": "medium",
  "details": {
    "field": "affected_field",
    "resource_id": "resource_identifier"
  },
  "request_id": "unique-request-id",
  "recoverable": true
}
```

## Logging System

### Configuration

The logging system is configured through environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log directory
LOG_DIR=logs

# Log format (text or json)
LOG_FORMAT=json
```

### Logger Initialization

```python
from fastmcp.task_management.infrastructure.logging import TaskManagementLogger, init_logging

# Initialize logging system
init_logging()

# Get a logger for your module
logger = TaskManagementLogger.get_logger(__name__)
```

### Structured Logging

The system supports structured logging with contextual information:

```python
# Add context to logger
ctx_logger = TaskManagementLogger.add_context(
    logger,
    user_id="user123",
    task_id="task456",
    project_id="project789",
    operation="create_task"
)

# Log with context
ctx_logger.info("Task created successfully")
```

### Log Files

The system creates multiple log files:

1. **dhafnck_mcp.log** - Main application log with all levels
2. **dhafnck_mcp_errors.log** - Error-only log for quick issue identification

Both files support automatic rotation when they reach 10MB, keeping 5 backup copies.

## Error Handling Patterns

### Using the Error Handler Decorator

```python
from fastmcp.task_management.interface.utils.error_handler import handle_operation_error

@handle_operation_error("task creation")
async def create_task(self, request: CreateTaskRequest):
    # Your code here
    pass
```

### Using the Log Operation Decorator

```python
from fastmcp.task_management.infrastructure.logging import log_operation

@log_operation("create_task")
async def create_task(self, task_id: str, **kwargs):
    # Automatically logs start, completion, and errors
    pass
```

### Manual Error Handling

```python
try:
    result = await task_service.create_task(request)
except ValidationException as e:
    logger.warning(f"Validation failed: {e}")
    return {
        "success": False,
        "error": e.user_message,
        "error_code": e.error_code
    }
except TaskDomainError as e:
    logger.error(f"Domain error: {e}", exc_info=True)
    raise
```

## HTTP Error Middleware

The system includes global error handling middleware that:

1. Catches all exceptions
2. Logs errors with full context
3. Returns consistent error responses
4. Maps domain errors to appropriate HTTP status codes
5. Tracks request duration and adds request IDs

### Status Code Mapping

- **400 Bad Request**: Validation errors, low severity domain errors
- **404 Not Found**: Resource not found errors
- **409 Conflict**: Medium severity domain errors, state conflicts
- **422 Unprocessable Entity**: Input validation failures
- **500 Internal Server Error**: Unexpected errors, high severity issues
- **503 Service Unavailable**: Database errors, critical system issues

## Best Practices

### 1. Use Specific Exceptions

```python
# Good
raise TaskNotFoundException(task_id="task123")

# Avoid
raise Exception("Task not found")
```

### 2. Include Context

```python
raise ValidationException(
    message="Invalid priority value",
    field="priority",
    value=priority,
    context={"valid_values": ["high", "medium", "low"]}
)
```

### 3. Log at Appropriate Levels

```python
# Debug - Detailed diagnostic information
logger.debug(f"Checking cache for task {task_id}")

# Info - General informational messages
logger.info(f"Task {task_id} created successfully")

# Warning - Something unexpected but recoverable
logger.warning(f"Cache miss for task {task_id}, fetching from database")

# Error - Error events but application continues
logger.error(f"Failed to send notification for task {task_id}", exc_info=True)

# Critical - System might not recover
logger.critical(f"Database connection lost", exc_info=True)
```

### 4. Use Structured Logging

```python
# Good - Structured data
logger.info(
    "Task status updated",
    extra={
        "task_id": task_id,
        "old_status": old_status,
        "new_status": new_status,
        "updated_by": user_id
    }
)

# Avoid - Unstructured strings
logger.info(f"Task {task_id} status changed from {old_status} to {new_status}")
```

### 5. Handle Errors Gracefully

```python
async def get_task_with_fallback(task_id: str):
    try:
        # Try cache first
        return await cache_service.get_task(task_id)
    except CacheException as e:
        logger.warning(f"Cache error, falling back to database: {e}")
        # Fall back to database
        return await task_repository.get_task(task_id)
```

## Monitoring and Debugging

### Log Analysis

To analyze logs for specific patterns:

```bash
# Find all errors for a specific task
grep -i "task_id.*task123" logs/dhafnck_mcp.log | grep ERROR

# Get all database errors
grep "DATABASE_ERROR" logs/dhafnck_mcp_errors.log

# View logs in real-time
tail -f logs/dhafnck_mcp.log | jq '.'  # For JSON format
```

### Common Error Patterns

1. **Task Not Found**
   - Check if task ID is correct
   - Verify task hasn't been deleted
   - Ensure correct project/branch context

2. **Database Connection Errors**
   - Check database service is running
   - Verify connection string in environment
   - Check for connection pool exhaustion

3. **Validation Errors**
   - Review input data format
   - Check for required fields
   - Validate data types match schema

### Performance Monitoring

The logging system tracks operation duration:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Completed create_task in 0.145s",
  "operation": "create_task",
  "duration_ms": 145
}
```

## Error Recovery Strategies

### 1. Automatic Retry

For transient errors:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def create_task_with_retry(request):
    return await task_service.create_task(request)
```

### 2. Circuit Breaker

For external service calls:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_service():
    # Service call that might fail
    pass
```

### 3. Graceful Degradation

```python
async def get_task_details(task_id: str):
    task = await get_task(task_id)
    
    # Try to enrich with additional data
    try:
        task["analytics"] = await get_task_analytics(task_id)
    except ExternalServiceException:
        logger.warning(f"Analytics service unavailable for task {task_id}")
        task["analytics"] = None
    
    return task
```

## Testing Error Scenarios

### Unit Testing

```python
import pytest
from fastmcp.task_management.domain.exceptions import TaskNotFoundException

async def test_task_not_found():
    with pytest.raises(TaskNotFoundException) as exc_info:
        await task_service.get_task("non-existent-id")
    
    assert exc_info.value.task_id == "non-existent-id"
    assert exc_info.value.error_code == "TASK_NOT_FOUND"
```

### Integration Testing

```python
async def test_error_response_format(client):
    response = await client.get("/api/tasks/invalid-id")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error_code" in data
    assert "request_id" in data
```

## Troubleshooting

### Enable Debug Logging

For detailed troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export LOG_FORMAT=text  # Easier to read for debugging
```

### Common Issues

1. **"Logger not initialized"**
   - Ensure `init_logging()` is called at startup
   - Check import paths are correct

2. **"Permission denied" on log files**
   - Verify write permissions on log directory
   - Check user running the application

3. **"Log rotation not working"**
   - Ensure sufficient disk space
   - Check file permissions for creating new files

### Getting Help

When reporting issues, include:

1. Error message and stack trace
2. Request ID from error response
3. Relevant log entries (sanitized)
4. Steps to reproduce
5. Environment details (OS, Python version, etc.)