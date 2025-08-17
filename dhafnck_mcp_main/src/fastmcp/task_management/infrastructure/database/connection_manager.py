"""
Production-Ready Connection Manager with Connection Pool Reuse

This module provides a connection manager that properly reuses database connections
from the pool, significantly improving performance with cloud databases like Supabase.
"""

import logging
import threading
from typing import Optional, Dict
from contextlib import contextmanager
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from .database_config import get_db_config

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Thread-safe connection manager that reuses database connections.
    
    This manager ensures that connections are properly reused from the pool
    instead of creating new connections for each request, which is critical
    for cloud database performance.
    """
    
    _instance: Optional['ConnectionManager'] = None
    _lock = threading.Lock()
    _thread_local = threading.local()
    
    def __new__(cls):
        """Singleton pattern to ensure single connection manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize connection manager"""
        if not self._initialized:
            self._initialized = True
            self._db_config = get_db_config()
            # Create a scoped session factory for thread-safe session management
            self._scoped_session = scoped_session(self._db_config.SessionLocal)
            logger.info("ConnectionManager initialized with scoped session factory")
    
    @contextmanager
    def get_session(self):
        """
        Get a database session from the pool.
        
        This method returns a session from the connection pool and ensures
        it's properly returned to the pool after use, NOT closed.
        """
        session = self._scoped_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise
        finally:
            # IMPORTANT: Don't close the session, just remove it from the registry
            # This returns the connection to the pool instead of closing it
            self._scoped_session.remove()
    
    @contextmanager
    def get_transactional_session(self):
        """
        Get a session for explicit transaction management.
        
        Use this when you need to manage transactions manually.
        """
        session = self._scoped_session()
        try:
            yield session
            # Don't auto-commit here, let caller manage transaction
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction error: {e}")
            raise
        finally:
            self._scoped_session.remove()
    
    def get_raw_session(self) -> Session:
        """
        Get a raw session for advanced use cases.
        
        WARNING: Caller is responsible for proper cleanup!
        """
        return self._scoped_session()
    
    def remove_session(self):
        """Remove the current session from the registry"""
        self._scoped_session.remove()
    
    def get_connection_stats(self) -> Dict:
        """Get connection pool statistics"""
        engine = self._db_config.get_engine()
        pool = engine.pool
        
        stats = {
            "size": getattr(pool, 'size', lambda: 'N/A')(),
            "checked_in": getattr(pool, 'checkedin', lambda: 'N/A')(),
            "checked_out": getattr(pool, 'checked_out_connections', lambda: 'N/A')(),
            "overflow": getattr(pool, 'overflow', lambda: 'N/A')(),
            "total": getattr(pool, 'total', lambda: 'N/A')()
        }
        
        # Try to get more detailed stats if available
        try:
            if hasattr(pool, 'status'):
                stats['status'] = pool.status()
        except:
            pass
            
        return stats
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        self._scoped_session.remove()
        engine = self._db_config.get_engine()
        engine.dispose()
        logger.info("All database connections closed")


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


@contextmanager
def get_db_session():
    """
    Convenience function to get a database session.
    
    This is the primary interface for getting database sessions
    throughout the application.
    """
    manager = get_connection_manager()
    with manager.get_session() as session:
        yield session


def get_connection_stats() -> Dict:
    """Get current connection pool statistics"""
    manager = get_connection_manager()
    return manager.get_connection_stats()