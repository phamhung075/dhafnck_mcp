"""Debug Service for Authentication"""

import logging

logger = logging.getLogger(__name__)


class DebugService:
    """Service for logging authentication debug information"""
    
    def __init__(self, context_service):
        self.context_service = context_service
    
    def log_authentication_details(self):
        """
        Log current authentication state for debugging purposes.
        """
        try:
            # Check custom context
            if self.context_service.user_context_available:
                context_user_id = self.context_service.get_current_user_id()
                logger.debug(f"Custom context user_id: {context_user_id}")
            
            # Check MCP context
            try:
                from mcp.server.auth.context import auth_context
                mcp_auth_context = auth_context.get()
                if mcp_auth_context:
                    logger.debug(f"MCP auth context type: {type(mcp_auth_context)}")
                    logger.debug(f"MCP auth context attributes: {dir(mcp_auth_context)}")
                    if hasattr(mcp_auth_context, 'user_id'):
                        logger.debug(f"MCP user_id: {mcp_auth_context.user_id}")
                    if hasattr(mcp_auth_context, 'client_id'):
                        logger.debug(f"MCP client_id: {mcp_auth_context.client_id}")
                else:
                    logger.debug("No MCP auth context available")
            except Exception as e:
                logger.debug(f"Error accessing MCP auth context: {e}")
            
            # Authentication is always required
            logger.debug("Authentication is always strictly enforced")
            
        except Exception as e:
            logger.error(f"Error logging authentication details: {e}")