"""Standardized Response Formatter for MCP Controllers

This module provides a consistent response format across all MCP controllers
to address API response inconsistencies and operation success confirmation issues.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import uuid
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    """Response status types"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"


class StandardResponseFormatter:
    """Provides standardized response formatting for all MCP operations"""
    
    @staticmethod
    def create_response(
        status: ResponseStatus,
        operation: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        partial_failures: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        workflow_guidance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized response format
        
        Args:
            status: The operation status (success, partial_success, failure)
            operation: The operation that was performed
            data: The main data payload (e.g., task, context, etc.)
            error: Error message if any
            error_code: Standardized error code
            partial_failures: List of partial failures for partial_success status
            metadata: Additional metadata about the operation
            workflow_guidance: Workflow guidance data if applicable
            
        Returns:
            Standardized response dictionary
        """
        # Generate operation ID for tracking
        operation_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        response = {
            # Core response structure
            "status": status.value,
            "success": status == ResponseStatus.SUCCESS,  # Backward compatibility
            "operation": operation,
            "operation_id": operation_id,
            "timestamp": timestamp,
            
            # Confirmation details
            "confirmation": {
                "operation_completed": status != ResponseStatus.FAILURE,
                "data_persisted": status != ResponseStatus.FAILURE and data is not None,
                "partial_failures": partial_failures or [],
                "operation_details": {
                    "operation": operation,
                    "operation_id": operation_id,
                    "timestamp": timestamp
                }
            }
        }
        
        # Add data if present
        if data is not None:
            response["data"] = data
            
        # Add error information if present
        if error:
            response["error"] = {
                "message": error,
                "code": error_code or "UNKNOWN_ERROR",
                "operation": operation,
                "timestamp": timestamp
            }
            
        # Add metadata if present
        if metadata:
            response["metadata"] = metadata
            
        # Add workflow guidance if present
        if workflow_guidance:
            response["workflow_guidance"] = workflow_guidance
            
        # Log the operation
        logger.info(f"Operation {operation} completed with status {status.value} (ID: {operation_id})")
        
        return response
    
    @staticmethod
    def create_success_response(
        operation: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        workflow_guidance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a success response"""
        return StandardResponseFormatter.create_response(
            status=ResponseStatus.SUCCESS,
            operation=operation,
            data=data,
            metadata=metadata,
            workflow_guidance=workflow_guidance
        )
    
    @staticmethod
    def create_error_response(
        operation: str,
        error: str,
        error_code: str = "UNKNOWN_ERROR",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an error response"""
        return StandardResponseFormatter.create_response(
            status=ResponseStatus.FAILURE,
            operation=operation,
            error=error,
            error_code=error_code,
            metadata=metadata
        )
    
    @staticmethod
    def create_partial_success_response(
        operation: str,
        data: Dict[str, Any],
        partial_failures: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        workflow_guidance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a partial success response"""
        return StandardResponseFormatter.create_response(
            status=ResponseStatus.PARTIAL_SUCCESS,
            operation=operation,
            data=data,
            partial_failures=partial_failures,
            metadata=metadata,
            workflow_guidance=workflow_guidance
        )
    
    @staticmethod
    def create_validation_error_response(
        operation: str,
        field: str,
        expected: str,
        actual: Optional[str] = None,
        hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a validation error response with helpful details"""
        error_details = {
            "field": field,
            "expected": expected,
            "hint": hint or f"Please provide a valid {field}"
        }
        
        if actual:
            error_details["actual"] = actual
            
        return StandardResponseFormatter.create_response(
            status=ResponseStatus.FAILURE,
            operation=operation,
            error=f"Validation failed for field: {field}",
            error_code="VALIDATION_ERROR",
            metadata={"validation_details": error_details}
        )
    
    @staticmethod
    def verify_success(response: Dict[str, Any]) -> bool:
        """
        Verify if an operation was truly successful
        
        This addresses the issue of not trusting the success field alone
        
        Args:
            response: The response to verify
            
        Returns:
            True if the operation was successful, False otherwise
        """
        # Check multiple indicators as recommended in dhafnck_mcp.mdc
        return (
            response.get("status") == ResponseStatus.SUCCESS.value and
            response.get("success", False) and
            "error" not in response and
            response.get("confirmation", {}).get("operation_completed", False) and
            response.get("confirmation", {}).get("data_persisted", False) and
            len(response.get("confirmation", {}).get("partial_failures", [])) == 0
        )
    
    @staticmethod
    def extract_data(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Safely extract data from a standardized response
        
        Args:
            response: The response to extract data from
            
        Returns:
            The data payload or None if not present
        """
        if StandardResponseFormatter.verify_success(response):
            return response.get("data")
        return None
    
    @staticmethod
    def get_operation_id(response: Dict[str, Any]) -> Optional[str]:
        """Get the operation ID from a response for tracking"""
        return response.get("operation_id")
    
    @staticmethod
    def has_partial_failures(response: Dict[str, Any]) -> bool:
        """Check if a response has partial failures"""
        return (
            response.get("status") == ResponseStatus.PARTIAL_SUCCESS.value or
            len(response.get("confirmation", {}).get("partial_failures", [])) > 0
        )


class ErrorCodes:
    """Standardized error codes for consistent error handling"""
    
    # Validation errors
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Operation errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    OPERATION_FAILED = "OPERATION_FAILED"
    UNAUTHORIZED = "UNAUTHORIZED"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CONTEXT_ERROR = "CONTEXT_ERROR"
    
    # Business logic errors
    INVALID_STATE = "INVALID_STATE"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"