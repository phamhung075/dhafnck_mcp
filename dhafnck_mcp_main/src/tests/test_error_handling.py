#!/usr/bin/env python3
"""Test script for error handling and logging system."""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastmcp.task_management.infrastructure.logging import TaskManagementLogger, init_logging, log_operation
from fastmcp.task_management.domain.exceptions.task_exceptions import (
    TaskNotFoundError,
    InvalidTaskStateError,
    ErrorSeverity
)
from fastmcp.task_management.domain.exceptions.base_exceptions import (
    ValidationException,
    ResourceNotFoundException,
    DatabaseException
)
from fastmcp.task_management.interface.utils.error_handler import UserFriendlyErrorHandler


# Initialize logging
init_logging()
logger = TaskManagementLogger.get_logger(__name__)


@log_operation("test_successful_operation")
async def test_successful_operation():
    """Test successful operation with logging."""
    logger.info("Performing successful operation")
    await asyncio.sleep(0.1)  # Simulate work
    return {"status": "success", "data": "test"}


@log_operation("test_validation_error")
async def test_validation_error():
    """Test validation error handling."""
    raise ValidationException(
        message="Invalid task priority",
        field="priority",
        value="invalid",
        user_message="Priority must be one of: high, medium, low"
    )


@log_operation("test_task_not_found")
async def test_task_not_found():
    """Test task not found error."""
    raise TaskNotFoundError("task-123")


@log_operation("test_database_error")
async def test_database_error():
    """Test database error handling."""
    raise DatabaseException(
        message="Connection timeout",
        operation="SELECT",
        table="tasks"
    )


async def test_error_handler():
    """Test the UserFriendlyErrorHandler."""
    print("\n=== Testing UserFriendlyErrorHandler ===\n")
    
    # Test various exceptions
    exceptions = [
        ValidationException("Invalid input", field="title", value=""),
        TaskNotFoundError("task-456"),
        DatabaseException("Connection failed"),
        ValueError("Invalid value"),
        KeyError("missing_field"),
        Exception("Unexpected error")
    ]
    
    for exc in exceptions:
        result = UserFriendlyErrorHandler.handle_error(
            exc,
            operation=f"test_{type(exc).__name__}",
            context={"test": True}
        )
        print(f"{type(exc).__name__}:")
        print(f"  Error: {result.get('error')}")
        print(f"  Code: {result.get('error_code')}")
        print(f"  Recovery: {result.get('recovery_instructions', [])[:1]}")
        print()


async def main():
    """Run all tests."""
    print("Testing Error Handling and Logging System")
    print("=" * 50)
    
    # Test successful operation
    print("\n1. Testing successful operation...")
    try:
        result = await test_successful_operation()
        print(f"   ✓ Success: {result}")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    
    # Test validation error
    print("\n2. Testing validation error...")
    try:
        await test_validation_error()
        print("   ✗ Should have raised ValidationException")
    except ValidationException as e:
        print(f"   ✓ Caught ValidationException: {e}")
        print(f"     - Error code: {e.error_code}")
        print(f"     - Severity: {e.severity.value}")
        print(f"     - Field: {e.context.get('field')}")
    
    # Test task not found
    print("\n3. Testing task not found error...")
    try:
        await test_task_not_found()
        print("   ✗ Should have raised TaskNotFoundError")
    except TaskNotFoundError as e:
        print(f"   ✓ Caught TaskNotFoundError: {e}")
        print(f"     - Task ID: {e.task_id}")
        print(f"     - Error code: {e.error_code}")
        print(f"     - Recoverable: {e.recoverable}")
    
    # Test database error
    print("\n4. Testing database error...")
    try:
        await test_database_error()
        print("   ✗ Should have raised DatabaseException")
    except DatabaseException as e:
        print(f"   ✓ Caught DatabaseException: {e}")
        print(f"     - Operation: {e.context.get('operation')}")
        print(f"     - Table: {e.context.get('table')}")
        print(f"     - Severity: {e.severity.value}")
    
    # Test error handler
    await test_error_handler()
    
    # Test logging context
    print("\n=== Testing Contextual Logging ===\n")
    ctx_logger = TaskManagementLogger.add_context(
        logger,
        user_id="test-user",
        task_id="test-task",
        project_id="test-project",
        operation="test_operation"
    )
    
    ctx_logger.info("This is a contextual log message")
    ctx_logger.warning("This is a warning with context")
    ctx_logger.error("This is an error with context", extra={"error_code": "TEST_ERROR"})
    
    print("\n✓ All tests completed. Check logs/ directory for detailed output.")
    print("\nLog files:")
    print("  - logs/dhafnck_mcp.log (all logs)")
    print("  - logs/dhafnck_mcp_errors.log (errors only)")


if __name__ == "__main__":
    asyncio.run(main())