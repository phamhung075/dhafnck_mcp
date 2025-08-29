"""Rule Orchestration Controller - Modular Implementation

Generated from enhanced_rule_orchestrator.py refactoring
Date: 2025-01-27

This file contains the DDD-compliant controller for rule orchestration following established patterns.
"""

import logging
from typing import Dict, Any, Annotated, Optional, TYPE_CHECKING
from pydantic import Field  # type: ignore

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP

from ..cursor_rules_controller.manage_rule_description import MANAGE_RULE_DESCRIPTION, get_manage_rule_description
from ....application.facades.rule_orchestration_facade import IRuleOrchestrationFacade
from .factories.rule_orchestration_controller_factory import RuleOrchestrationControllerFactory

logger = logging.getLogger(__name__)


class RuleOrchestrationController:
    """
    DDD-compliant controller for rule orchestration operations.
    Delegates all business logic to the application facade.
    """
    
    def __init__(self, rule_orchestration_facade: IRuleOrchestrationFacade):
        """
        Initialize the controller with the application facade.
        
        Args:
            rule_orchestration_facade: The application facade for rule orchestration
        """
        self.facade = rule_orchestration_facade
        self._factory = RuleOrchestrationControllerFactory(rule_orchestration_facade)
        logger.info("RuleOrchestrationController initialized with modular architecture")
    
    def register_tools(self, mcp: "FastMCP"):
        """Register MCP tools with descriptions"""
        manage_rule_desc = get_manage_rule_description()

        @mcp.tool(description=manage_rule_desc["description"])
        def manage_rule(
            action: Annotated[str, Field(description=manage_rule_desc["parameters"].get("action", "Rule management action"))],
            target: Annotated[str, Field(description=manage_rule_desc["parameters"].get("target", "Target for the action"))] = "",
            content: Annotated[str, Field(description=manage_rule_desc["parameters"].get("content", "Content for the action"))] = "",
            user_id: Annotated[Optional[str], Field(description="User identifier for authentication and audit trails")] = None
        ) -> Dict[str, Any]:
            return self._factory.handle_manage_rule_request(action=action, target=target, content=content, user_id=user_id)
    
    def handle_manage_rule_request(self, action: str, target: str = "", content: str = "", user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle manage_rule MCP tool requests (legacy method)"""
        return self._factory.handle_manage_rule_request(action, target, content, user_id)
    
    def get_enhanced_rule_info(self) -> Dict[str, Any]:
        """Get enhanced information about the rule system (legacy method)"""
        return self._factory.get_enhanced_rule_info()
    
    def compose_nested_rules(self, rule_path: str) -> Dict[str, Any]:
        """Compose nested rules with inheritance (legacy method)"""
        return self._factory.compose_nested_rules(rule_path)
    
    def register_client(self, client_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a client for synchronization (legacy method)"""
        return self._factory.register_client(client_config)
    
    def sync_with_client(self, client_id: str, operation: str, client_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synchronize rules with a client (legacy method)"""
        return self._factory.sync_with_client(client_id, operation, client_rules)
    
    def _get_available_actions(self) -> list:
        """Get list of available actions (legacy method)"""
        return self._factory.get_rule_management_handler()._get_available_actions()
    
    def _enhance_response_with_workflow_guidance(self, response: Dict[str, Any], action: str, target: str = "") -> Dict[str, Any]:
        """Enhance response with workflow guidance (legacy method)"""
        return self._factory.get_rule_management_handler()._enhance_response_with_workflow_guidance(response, action, target)


def create_rule_orchestration_controller(facade: IRuleOrchestrationFacade) -> RuleOrchestrationController:
    """
    Factory function to create a rule orchestration controller.
    
    Args:
        facade: The application facade for rule orchestration
        
    Returns:
        Configured RuleOrchestrationController instance
    """
    return RuleOrchestrationController(facade)