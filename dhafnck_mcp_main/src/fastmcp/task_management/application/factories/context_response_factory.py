"""Context Response Factory - Standardizes context data format across all task actions"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ContextResponseFactory:
    """Factory to create standardized context response format"""
    
    @staticmethod
    def create_unified_context(context_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Create a unified context format from various context data sources.
        
        Args:
            context_data: Raw context data from various sources
            
        Returns:
            Standardized context format or None if no valid context
        """
        if not context_data:
            return None
            
        try:
            # Handle different context data formats and extract the core template_context
            unified_context = None
            
            # Case 1: Direct template_context (from create action)
            if "template_context" in context_data:
                unified_context = context_data["template_context"]
            
            # Case 1b: Context has success and template_context (nested from create action)
            elif "success" in context_data and "template_context" in context_data:
                unified_context = context_data["template_context"]
                
            # Case 2: Nested context structure (from next action)
            elif "context" in context_data and isinstance(context_data["context"], dict):
                nested_context = context_data["context"]
                if "template_context" in nested_context:
                    unified_context = nested_context["template_context"]
                    
            # Case 3: Context data is already the template_context
            elif "metadata" in context_data and "task_id" in context_data.get("metadata", {}):
                unified_context = context_data
                
            # Case 4: Look for any nested structure with template_context
            else:
                for key, value in context_data.items():
                    if isinstance(value, dict) and "template_context" in value:
                        unified_context = value["template_context"]
                        break
                        
            if unified_context:
                # Ensure required structure exists
                return ContextResponseFactory._ensure_complete_structure(unified_context)
                
            logger.warning("No valid template_context found in context_data")
            return None
            
        except Exception as e:
            logger.error(f"Error creating unified context: {e}")
            return None
    
    @staticmethod
    def _ensure_complete_structure(context: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure the context has all required sections with default values"""
        
        # Default structure template
        default_structure = {
            "metadata": {},
            "objective": {
                "title": "",
                "description": "",
                "estimated_effort": "",
                "due_date": None
            },
            "requirements": {
                "checklist": [],
                "custom_requirements": [],
                "completion_criteria": []
            },
            "technical": {
                "technologies": [],
                "frameworks": [],
                "database": "",
                "key_files": [],
                "key_directories": [],
                "architecture_notes": "",
                "patterns_used": []
            },
            "dependencies": {
                "task_dependencies": [],
                "external_dependencies": [],
                "blocked_by": []
            },
            "progress": {
                "completed_actions": [],
                "current_session_summary": "",
                "next_steps": [],
                "completion_percentage": 0.0,
                "time_spent_minutes": 0
            },
            "subtasks": {
                "items": [],
                "total_count": 0,
                "completed_count": 0,
                "progress_percentage": 0.0
            },
            "notes": {
                "agent_insights": [],
                "challenges_encountered": [],
                "solutions_applied": [],
                "decisions_made": [],
                "general_notes": ""
            },
            "custom_sections": []
        }
        
        # Merge with existing context, preserving existing values
        for section, default_values in default_structure.items():
            if section not in context:
                context[section] = default_values
            elif isinstance(default_values, dict):
                # Ensure subsections exist
                for subsection, default_value in default_values.items():
                    if subsection not in context[section]:
                        context[section][subsection] = default_value
                        
        return context
    
    @staticmethod
    def apply_to_task_response(task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply unified context format to a task response.
        
        Args:
            task_data: Task response data with context_data field
            
        Returns:
            Task response with standardized context_data
        """
        if "context_data" in task_data:
            unified_context = ContextResponseFactory.create_unified_context(task_data["context_data"])
            task_data["context_data"] = unified_context
            task_data["context_available"] = unified_context is not None
            
        return task_data
    
    @staticmethod
    def apply_to_next_response(next_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply unified context format to a next task response.
        Simplifies the complex nested structure to a single context_data field.
        """
        if "task" in next_response:
            task_data = next_response["task"]
            
            # Extract context from context_info if it exists
            unified_context = None
            if "context_info" in task_data:
                context_info = task_data["context_info"] 
                unified_context = ContextResponseFactory.create_unified_context(context_info)
                
                # Apply unified context to the main task response
                task_data["context_data"] = unified_context
                task_data["context_available"] = unified_context is not None
                
                # Set context field to the context_id from metadata if available
                if unified_context and "metadata" in unified_context and "task_id" in unified_context["metadata"]:
                    task_data["context"] = unified_context["metadata"]["task_id"]
                elif "next_item" in task_data and "task" in task_data["next_item"] and "context_id" in task_data["next_item"]["task"]:
                    task_data["context"] = task_data["next_item"]["task"]["context_id"]
                
                # Remove redundant fields
                del task_data["context_info"]
            
            # Also apply to the nested task within next_item
            if "next_item" in task_data and "task" in task_data["next_item"]:
                nested_task = task_data["next_item"]["task"]
                if unified_context:
                    nested_task["context_data"] = unified_context
                    nested_task["context_available"] = True
                
        return next_response