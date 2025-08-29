"""Main Authentication Service"""

import logging
from typing import Optional

from .....domain.constants import validate_user_id
from .....domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError
from .context_import_service import ContextImportService
from ..extractors import (
    RequestStateExtractor,
    ContextObjectExtractor,
    MCPContextExtractor
)

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Main authentication service for MCP controllers"""
    
    def __init__(self):
        self.context_service = ContextImportService()
        self.request_state_extractor = RequestStateExtractor()
        self.context_object_extractor = ContextObjectExtractor()
        self.mcp_context_extractor = MCPContextExtractor()
    
    def get_authenticated_user_id(
        self, 
        provided_user_id: Optional[str] = None, 
        operation_name: str = "Operation"
    ) -> str:
        """
        Get authenticated user ID from various sources with proper validation.
        
        This function tries to extract user_id from (in priority order):
        1. Provided user_id parameter
        2. RequestContextMiddleware context variables (NEW - set by DualAuthMiddleware)
        3. Legacy request state (old method)
        4. Custom user context middleware 
        5. MCP authentication context
        
        Args:
            provided_user_id: User ID provided explicitly (takes precedence)
            operation_name: Name of the operation for error messages
            
        Returns:
            Validated user ID string
            
        Raises:
            UserAuthenticationRequiredError: If no valid authentication is found
            DefaultUserProhibitedError: If prohibited user ID is used
            InvalidUserIdError: If user ID format is invalid
        """
        logger.info(f"🔍 get_authenticated_user_id called for operation: {operation_name}")
        logger.info(f"📝 Provided user_id: {provided_user_id}")
        logger.info(f"🔧 REQUEST_CONTEXT_AVAILABLE: {self.context_service.request_context_available}")
        logger.info(f"🔧 USER_CONTEXT_AVAILABLE: {self.context_service.user_context_available}")
        print(f"DEBUG: get_authenticated_user_id called for {operation_name} with provided_user_id={provided_user_id}")
        
        user_id = provided_user_id
        
        # If no user ID provided, try to extract from authentication context
        if user_id is None:
            logger.info("🔍 No user_id provided, trying authentication context sources...")
            
            # PRIORITY 1: Try RequestContextMiddleware context variables (NEW METHOD)
            if self.context_service.request_context_available:
                user_id = self._try_request_context_middleware()
            else:
                logger.warning("⚠️ RequestContextMiddleware context not available")
            
            # PRIORITY 2: Try legacy request state (set by DualAuthMiddleware)
            if user_id is None:
                logger.info("🔧 Trying legacy request state...")
                user_id = self.request_state_extractor.extract_user_id()
                if user_id:
                    logger.info(f"✅ Got user_id from legacy request state: {user_id}")
            
            # PRIORITY 3: Try custom user context middleware if no user_id yet
            if user_id is None and self.context_service.user_context_available:
                user_id = self._try_user_context_middleware()
            else:
                if user_id is None:
                    logger.warning("⚠️ User context middleware not available")
            
            # PRIORITY 4: Try MCP authentication context (gracefully handle missing module)
            if user_id is None:
                logger.info("🔧 Trying MCP authentication context...")
                user_id = self.mcp_context_extractor.extract_user_id()
            
            # If still no user ID, throw authentication error
            if user_id is None:
                logger.error(f"❌ No authentication found for {operation_name}")
                # Log all available context for debugging
                if self.context_service.request_context_available:
                    auth_context = self.context_service.get_authentication_context()
                    logger.error(f"❌ Full authentication context: {auth_context}")
                raise UserAuthenticationRequiredError(operation_name)
        else:
            logger.info(f"✅ Using provided user_id: {user_id}")
        
        # Validate the user ID (will throw if invalid)
        logger.info(f"🔍 Validating user_id: {user_id}")
        user_id = validate_user_id(user_id, operation_name)
        logger.info(f"✅ Final validated user_id: {user_id}")
        
        return user_id
    
    def _try_request_context_middleware(self) -> Optional[str]:
        """Try to get user ID from RequestContextMiddleware"""
        logger.info("🆕 Trying RequestContextMiddleware context variables...")
        try:
            context_user_obj = self.context_service.get_user_from_request_context()
            logger.info(f"🎯 RequestContextMiddleware returned: {context_user_obj} (type: {type(context_user_obj)})")
            
            # Extract user_id from the context object (handles BackwardCompatUserContext objects)
            extracted_user_id = self.context_object_extractor.extract_user_id(context_user_obj)
            logger.info(f"🔧 Extracted user_id: {extracted_user_id}")
            
            if extracted_user_id:
                logger.info(f"✅ Got user_id from RequestContextMiddleware: {extracted_user_id}")
                
                # Log additional context info for debugging
                if self.context_service.is_request_authenticated():
                    auth_method = self.context_service.get_current_auth_method()
                    logger.info(f"🔐 Authentication method: {auth_method}")
                
                return extracted_user_id
            else:
                logger.warning("⚠️ RequestContextMiddleware returned None or could not extract user_id - request not authenticated")
        except Exception as e:
            logger.error(f"❌ Error accessing RequestContextMiddleware context: {e}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
        return None
    
    def _try_user_context_middleware(self) -> Optional[str]:
        """Try to get user ID from custom user context middleware"""
        logger.info("🔧 Trying custom user context middleware...")
        try:
            context_user_obj = self.context_service.get_current_user_id()
            logger.info(f"🎯 Custom context middleware returned: {context_user_obj} (type: {type(context_user_obj)})")
            
            # Extract user_id from the context object (handles BackwardCompatUserContext objects)
            extracted_user_id = self.context_object_extractor.extract_user_id(context_user_obj)
            logger.info(f"🔧 Extracted user_id: {extracted_user_id}")
            
            if extracted_user_id:
                logger.info(f"✅ Got user_id from custom context middleware: {extracted_user_id}")
                return extracted_user_id
            else:
                logger.warning("⚠️ Custom context middleware returned None or could not extract user_id")
        except Exception as e:
            logger.error(f"❌ Error calling get_current_user_id(): {e}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
        return None