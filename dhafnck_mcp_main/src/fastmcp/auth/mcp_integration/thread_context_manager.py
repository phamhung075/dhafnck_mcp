"""
Thread Context Manager for MCP Operations

This module provides utilities for properly propagating user context across thread boundaries
in MCP controllers. It solves the critical authentication issue where ContextVar values
do not propagate to new threads, causing all operations to fall back to default_id.
"""

import asyncio
import logging
import threading
from typing import Any, Callable, Optional, Dict
from contextvars import ContextVar, copy_context

from .user_context_middleware import (
    get_current_user_context, 
    get_current_user_id,
    current_user_context,
    MCPUserContext
)

logger = logging.getLogger(__name__)


class ThreadContextManager:
    """
    Thread Context Manager that ensures proper user context propagation
    across thread boundaries for MCP operations.
    
    This solves the critical authentication issue where JWT-authenticated
    users were being treated as 'default_id' in threaded async operations.
    """
    
    def __init__(self):
        """Initialize the thread context manager."""
        self._captured_context: Optional[MCPUserContext] = None
        self._captured_user_id: Optional[str] = None
        
    def capture_context(self) -> 'ThreadContextManager':
        """
        Capture the current user context before threading.
        
        Returns:
            Self for method chaining
        """
        try:
            self._captured_context = get_current_user_context()
            self._captured_user_id = get_current_user_id()
            
            if self._captured_context:
                logger.debug(f"ThreadContextManager: Captured user context for user {self._captured_context.user_id}")
            else:
                logger.debug("ThreadContextManager: No user context found to capture")
                
        except Exception as e:
            logger.warning(f"ThreadContextManager: Failed to capture user context: {e}")
            self._captured_context = None
            self._captured_user_id = None
            
        return self
    
    def restore_context(self) -> bool:
        """
        Restore the captured user context in the current thread.
        
        Returns:
            True if context was restored successfully, False otherwise
        """
        try:
            if self._captured_context:
                current_user_context.set(self._captured_context)
                logger.debug(f"ThreadContextManager: Restored user context for user {self._captured_context.user_id}")
                return True
            else:
                logger.debug("ThreadContextManager: No context to restore")
                return False
                
        except Exception as e:
            logger.warning(f"ThreadContextManager: Failed to restore user context: {e}")
            return False
    
    def run_async_with_context(self, async_func: Callable, *args, **kwargs) -> Any:
        """
        Run an async function in a new thread with proper context propagation.
        
        Args:
            async_func: The async function to execute
            *args: Positional arguments for the async function
            **kwargs: Keyword arguments for the async function
            
        Returns:
            The result of the async function
            
        Raises:
            Any exception raised by the async function
        """
        # Capture context before threading
        self.capture_context()
        
        result = None
        exception = None
        
        def run_in_new_loop():
            nonlocal result, exception
            try:
                # Restore context in the new thread
                context_restored = self.restore_context()
                
                if context_restored:
                    logger.debug("ThreadContextManager: Context successfully restored in new thread")
                else:
                    logger.warning("ThreadContextManager: Failed to restore context in new thread")
                
                # Create new event loop and run the async function
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(async_func(*args, **kwargs))
                    logger.debug("ThreadContextManager: Async function completed successfully")
                finally:
                    new_loop.close()
                    asyncio.set_event_loop(None)
                    
            except Exception as e:
                logger.error(f"ThreadContextManager: Exception in threaded async execution: {e}")
                exception = e
        
        # Run in new thread
        thread = threading.Thread(target=run_in_new_loop, name=f"MCPAsyncThread-{id(async_func)}")
        thread.start()
        thread.join()
        
        # Re-raise any exception that occurred
        if exception:
            raise exception
            
        return result
    
    def get_captured_user_id(self) -> Optional[str]:
        """
        Get the captured user ID.
        
        Returns:
            The captured user ID or None if no context was captured
        """
        return self._captured_user_id
    
    def has_captured_context(self) -> bool:
        """
        Check if context has been captured.
        
        Returns:
            True if context was captured, False otherwise
        """
        return self._captured_context is not None


class ContextPropagationMixin:
    """
    Mixin class that provides context propagation capabilities to MCP controllers.
    
    This can be mixed into any controller class to add the _run_async_with_context method
    with proper authentication context propagation.
    """
    
    def _run_async_with_context(self, async_func: Callable, *args, **kwargs) -> Any:
        """
        Helper method to run async functions with proper user context propagation across threads.
        
        This replaces the problematic threading implementations in MCP controllers and ensures
        that JWT-authenticated user context is properly maintained across thread boundaries.
        
        Args:
            async_func: The async function to execute
            *args: Positional arguments for the async function
            **kwargs: Keyword arguments for the async function
            
        Returns:
            The result of the async function
            
        Raises:
            Any exception raised by the async function
        """
        context_manager = ThreadContextManager()
        return context_manager.run_async_with_context(async_func, *args, **kwargs)


def create_thread_context_manager() -> ThreadContextManager:
    """
    Factory function to create a new ThreadContextManager instance.
    
    Returns:
        New ThreadContextManager instance
    """
    return ThreadContextManager()


def run_async_with_context(async_func: Callable, *args, **kwargs) -> Any:
    """
    Convenience function to run an async function with context propagation.
    
    Args:
        async_func: The async function to execute
        *args: Positional arguments for the async function
        **kwargs: Keyword arguments for the async function
        
    Returns:
        The result of the async function
        
    Raises:
        Any exception raised by the async function
    """
    context_manager = ThreadContextManager()
    return context_manager.run_async_with_context(async_func, *args, **kwargs)


def verify_context_propagation() -> Dict[str, Any]:
    """
    Utility function to verify that context propagation is working correctly.
    
    Returns:
        Dictionary with context verification results
    """
    try:
        current_context = get_current_user_context()
        current_user_id = get_current_user_id()
        
        return {
            "context_available": current_context is not None,
            "user_id": current_user_id,
            "user_context": {
                "user_id": current_context.user_id if current_context else None,
                "email": current_context.email if current_context else None,
                "roles": current_context.roles if current_context else None,
            } if current_context else None,
            "verification_successful": True
        }
    except Exception as e:
        return {
            "context_available": False,
            "user_id": None,
            "user_context": None,
            "verification_successful": False,
            "error": str(e)
        }