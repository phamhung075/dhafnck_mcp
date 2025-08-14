"""Enhanced Context Auto-Detection Logic with Improved Error Handling and Fallbacks

This module provides improved auto-detection logic for git_branch_id from task_id
with better error handling, detailed error messages, and fallback options.

Root Cause Analysis:
- The original auto-detection fails when the task system is unavailable
- Error messages don't clearly indicate what went wrong during detection
- No fallback options when auto-detection fails
- Limited diagnostic information for troubleshooting

Improvements:
1. Enhanced error classification and messaging
2. Fallback options when task system is unavailable
3. Better diagnostic information in error responses
4. Graceful degradation with alternative workflows
"""

import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class AutoDetectionErrorType(Enum):
    """Classification of auto-detection errors"""
    TASK_SYSTEM_UNAVAILABLE = "task_system_unavailable"
    DATABASE_CONNECTION_FAILED = "database_connection_failed"
    TASK_NOT_FOUND = "task_not_found"
    TASK_NO_BRANCH = "task_no_branch"
    INVALID_TASK_ID_FORMAT = "invalid_task_id_format"
    UNKNOWN_ERROR = "unknown_error"


class ContextAutoDetectionEnhanced:
    """Enhanced context auto-detection with improved error handling"""
    
    @staticmethod
    def detect_git_branch_id_from_task(task_id: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Enhanced auto-detection of git_branch_id from task_id with detailed error reporting.
        
        Args:
            task_id: The task ID to look up
            
        Returns:
            Tuple of (git_branch_id, error_details) where:
            - git_branch_id is the detected branch ID or None if failed
            - error_details contains diagnostic information if detection failed
        """
        if not task_id:
            return None, {
                "error_type": AutoDetectionErrorType.INVALID_TASK_ID_FORMAT.value,
                "message": "Empty task_id provided",
                "diagnostic": "task_id parameter is required for auto-detection"
            }
        
        # Validate task_id format (basic UUID check)
        if not ContextAutoDetectionEnhanced._is_valid_uuid_format(task_id):
            return None, {
                "error_type": AutoDetectionErrorType.INVALID_TASK_ID_FORMAT.value,
                "message": f"Invalid task_id format: {task_id}",
                "diagnostic": "task_id should be a valid UUID format",
                "suggestion": "Verify the task_id format or provide git_branch_id directly"
            }
        
        try:
            # Import dependencies within try block to catch import errors
            from ...infrastructure.database.models import Task
            from ...infrastructure.database.database_config import get_session
            
            logger.info(f"Attempting auto-detection of git_branch_id for task: {task_id}")
            
            with get_session() as session:
                task = session.query(Task).filter_by(id=task_id).first()
                
                if not task:
                    logger.warning(f"Task {task_id} not found in database")
                    return None, {
                        "error_type": AutoDetectionErrorType.TASK_NOT_FOUND.value,
                        "message": f"Task '{task_id}' not found in database",
                        "diagnostic": "The task_id does not exist in the task management system",
                        "suggestion": "Verify the task_id is correct or create the task first",
                        "fallback_options": [
                            "Create the task using manage_task action='create'",
                            "Provide git_branch_id parameter directly",
                            "Use manage_context for direct context operations"
                        ]
                    }
                
                if not task.git_branch_id:
                    logger.warning(f"Task {task_id} exists but has no git_branch_id")
                    return None, {
                        "error_type": AutoDetectionErrorType.TASK_NO_BRANCH.value,
                        "message": f"Task '{task_id}' exists but has no associated git_branch_id",
                        "diagnostic": "The task is not properly linked to a git branch",
                        "suggestion": "Update the task with a valid git_branch_id or provide it directly",
                        "fallback_options": [
                            "Update task with git_branch_id using manage_task action='update'",
                            "Provide git_branch_id parameter directly",
                            "Check if the task was created properly with a branch"
                        ]
                    }
                
                logger.info(f"Successfully auto-detected git_branch_id '{task.git_branch_id}' for task '{task_id}'")
                return task.git_branch_id, None
                
        except ImportError as e:
            logger.error(f"Failed to import task management components: {e}")
            return None, {
                "error_type": AutoDetectionErrorType.TASK_SYSTEM_UNAVAILABLE.value,
                "message": "Task management system components are not available",
                "diagnostic": f"Import error: {str(e)}",
                "suggestion": "The task management system may not be properly initialized",
                "fallback_options": [
                    "Provide git_branch_id parameter directly",
                    "Use manage_context for direct context operations",
                    "Check if task management system is properly configured"
                ]
            }
        except Exception as e:
            # Check for specific database connection errors
            error_str = str(e).lower()
            if any(db_error in error_str for db_error in ['connection', 'database', 'session', 'sqlite']):
                logger.error(f"Database connection error during auto-detection: {e}")
                return None, {
                    "error_type": AutoDetectionErrorType.DATABASE_CONNECTION_FAILED.value,
                    "message": "Failed to connect to database for auto-detection",
                    "diagnostic": f"Database error: {str(e)}",
                    "suggestion": "Check database connection and configuration",
                    "fallback_options": [
                        "Provide git_branch_id parameter directly",
                        "Verify database is accessible and properly configured",
                        "Check if database service is running"
                    ]
                }
            else:
                logger.error(f"Unexpected error during auto-detection: {e}")
                return None, {
                    "error_type": AutoDetectionErrorType.UNKNOWN_ERROR.value,
                    "message": "Unexpected error during auto-detection",
                    "diagnostic": f"Error: {str(e)}",
                    "suggestion": "This is an unexpected error, please check logs for details",
                    "fallback_options": [
                        "Provide git_branch_id parameter directly",
                        "Use manage_context for direct context operations",
                        "Report this error for investigation"
                    ]
                }
    
    @staticmethod
    def _is_valid_uuid_format(uuid_string: str) -> bool:
        """Check if string looks like a valid UUID format"""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(uuid_string))
    
    @staticmethod
    def create_enhanced_error_response(action: str, error_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an enhanced error response with detailed diagnostic information.
        
        Args:
            action: The action that was attempted
            error_details: Detailed error information from detection
            
        Returns:
            Enhanced error response with troubleshooting guidance
        """
        base_message = f"git_branch_id is required for action '{action}' and could not be auto-detected from task_id"
        
        response = {
            "success": False,
            "error": base_message,
            "error_code": "AUTO_DETECTION_FAILED",
            "field": "git_branch_id",
            "auto_detection_details": error_details
        }
        
        # Add specific guidance based on error type
        error_type = error_details.get("error_type")
        
        if error_type == AutoDetectionErrorType.TASK_SYSTEM_UNAVAILABLE.value:
            response["hint"] = (
                "Task management system is unavailable. "
                "Provide git_branch_id parameter directly or use manage_context."
            )
            response["immediate_solutions"] = [
                "Provide git_branch_id parameter: git_branch_id='your-branch-uuid'",
                "Use manage_context instead of manage_context",
                "Check if task management system is properly initialized"
            ]
        elif error_type == AutoDetectionErrorType.TASK_NOT_FOUND.value:
            response["hint"] = (
                "Task does not exist in the system. "
                "Create the task first or provide git_branch_id directly."
            )
            response["immediate_solutions"] = [
                "Create task first: manage_task action='create' with git_branch_id",
                "Provide git_branch_id parameter directly",
                "Verify the task_id is correct"
            ]
        elif error_type == AutoDetectionErrorType.TASK_NO_BRANCH.value:
            response["hint"] = (
                "Task exists but is not linked to a git branch. "
                "Update the task or provide git_branch_id directly."
            )
            response["immediate_solutions"] = [
                "Update task: manage_task action='update' with git_branch_id",
                "Provide git_branch_id parameter directly",
                "Check task creation process to ensure branch linking"
            ]
        else:
            response["hint"] = (
                "Auto-detection failed. Provide git_branch_id parameter directly "
                "or check system configuration."
            )
            response["immediate_solutions"] = [
                "Provide git_branch_id parameter directly",
                "Use manage_context for advanced operations",
                "Check system logs for detailed error information"
            ]
        
        # Add fallback options if available
        if "fallback_options" in error_details:
            response["fallback_options"] = error_details["fallback_options"]
        
        return response


def apply_enhanced_auto_detection_fix():
    """
    Instructions for applying the enhanced auto-detection fix to the context controller.
    
    This function documents the changes needed in context_mcp_controller.py
    to implement the enhanced auto-detection logic.
    """
    return {
        "fix_description": "Enhanced Context Auto-Detection with Improved Error Handling",
        "files_to_modify": [
            "context_mcp_controller.py"
        ],
        "changes_needed": [
            {
                "location": "lines 430-456",
                "description": "Replace simple auto-detection with enhanced version",
                "new_logic": """
                # Enhanced auto-detection with detailed error handling
                git_branch_id_detected = None
                auto_detection_error = None
                
                if not git_branch_id and task_id:
                    git_branch_id_detected, auto_detection_error = ContextAutoDetectionEnhanced.detect_git_branch_id_from_task(task_id)
                    if git_branch_id_detected:
                        git_branch_id = git_branch_id_detected
                
                # Check if git_branch_id is required for this action
                actions_requiring_branch = ["create", "update", "get", "delete", "merge", "add_insight", "add_progress", "update_next_steps"]
                if action in actions_requiring_branch and not git_branch_id:
                    if auto_detection_error:
                        return ContextAutoDetectionEnhanced.create_enhanced_error_response(action, auto_detection_error)
                    else:
                        return {
                            "success": False,
                            "error": f"git_branch_id is required for action '{action}' but was not provided",
                            "error_code": "MISSING_FIELD",
                            "field": "git_branch_id",
                            "hint": "Provide git_branch_id parameter"
                        }
                """
            }
        ],
        "benefits": [
            "Detailed error classification and messaging",
            "Specific troubleshooting guidance for each error type",
            "Fallback options when auto-detection fails",
            "Better diagnostic information for debugging",
            "Graceful degradation when task system is unavailable"
        ],
        "testing_scenarios": [
            "Test with invalid task_id format",
            "Test with non-existent task_id",
            "Test with task that has no git_branch_id",
            "Test when task system is unavailable",
            "Test when database connection fails",
            "Test successful auto-detection"
        ]
    }