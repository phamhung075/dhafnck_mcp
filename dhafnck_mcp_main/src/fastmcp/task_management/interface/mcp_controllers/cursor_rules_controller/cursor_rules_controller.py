"""Cursor Rules MCP Controller

This controller handles MCP tool registration for cursor rules management,
following DDD principles by delegating business logic to application services.
"""

import logging
from typing import Dict, Any, Annotated
from pydantic import Field # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.server.server import FastMCP
    from ....application.facades.rule_application_facade import RuleApplicationFacade

from ..desc import description_loader
from .handlers import RuleManagementHandler

logger = logging.getLogger(__name__)


class CursorRulesController:
    """
    MCP Controller for cursor rules management.
    
    Handles only MCP protocol concerns and delegates business operations
    to the RuleApplicationFacade following proper DDD layer separation.
    Documentation is loaded from external files for maintainability.
    """
    
    def __init__(self, rule_facade: "RuleApplicationFacade"):
        """
        Initialize controller with rule application facade.
        
        Args:
            rule_facade: Application facade for rule operations
        """
        self._handler = RuleManagementHandler(rule_facade)
        logger.info("CursorRulesController initialized")
    
    def register_tools(self, mcp: "FastMCP"):
        """Register cursor rules MCP tools with the FastMCP server"""
        descriptions = description_loader.get_all_descriptions()
        rule_desc = descriptions["rule"]["manage_rule"]

        @mcp.tool(description=rule_desc["description"])
        def manage_rule(
            action: Annotated[str, Field(description=rule_desc["parameters"].get("action", "Rule management action to perform"))],
            target: Annotated[str, Field(description=rule_desc["parameters"].get("target", "Target for the action"))] = "",
            content: Annotated[str, Field(description=rule_desc["parameters"].get("content", "Content for the action"))] = ""
        ) -> Dict[str, Any]:
            return self._handler.handle_manage_rule(action, target, content)