"""
Database Configuration Module using SQLAlchemy ORM

This module provides database configuration for both SQLite and PostgreSQL,
making it easy to switch between databases based on environment configuration.
"""

import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class DatabaseConfig:
    """
    Database configuration manager that supports both SQLite and PostgreSQL.
    
    Uses DATABASE_TYPE and DATABASE_URL environment variables to determine
    which database to use.
    """
    
    def __init__(self):
        self.database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
        self.database_url = os.getenv("DATABASE_URL")
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        
        # Initialize database connection
        self._initialize_database()
    
    def _get_database_url(self) -> str:
        """Get the appropriate database URL based on configuration"""
        if self.database_type == "postgresql" and self.database_url:
            # Use PostgreSQL with provided URL
            logger.info("Using PostgreSQL database")
            return self.database_url
        else:
            # Default to SQLite
            # Check for MCP_DB_PATH for backward compatibility
            db_path = os.getenv("MCP_DB_PATH")
            if not db_path:
                # Use default SQLite path
                from .database_source_manager import DatabaseSourceManager
                manager = DatabaseSourceManager()
                db_path = manager.get_database_path()
            
            logger.info(f"Using SQLite database at: {db_path}")
            return f"sqlite:///{db_path}"
    
    def _create_engine(self, database_url: str) -> Engine:
        """Create SQLAlchemy engine with appropriate configuration"""
        if database_url.startswith("postgresql"):
            # PostgreSQL configuration
            engine = create_engine(
                database_url,
                pool_size=20,
                max_overflow=40,
                pool_pre_ping=True,  # Enable connection health checks
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=False,  # Set to True for SQL debugging
                future=True,  # Use SQLAlchemy 2.0 style
            )
        else:
            # SQLite configuration
            connect_args = {"check_same_thread": False}  # Allow multiple threads
            engine = create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=NullPool,  # SQLite doesn't benefit from connection pooling
                echo=False,  # Set to True for SQL debugging
                future=True,  # Use SQLAlchemy 2.0 style
            )
            
            # Configure SQLite for better performance
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")  # Enable foreign key constraints
                cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
                cursor.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
                cursor.close()
        
        return engine
    
    def _initialize_database(self):
        """Initialize database connection and create session factory"""
        try:
            database_url = self._get_database_url()
            self.engine = self._create_engine(database_url)
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False  # Don't expire objects after commit
            )
            
            # Test connection
            with self.engine.connect() as conn:
                if database_url.startswith("postgresql"):
                    result = conn.execute(text("SELECT version()"))
                    version = result.scalar()
                    logger.info(f"Connected to PostgreSQL: {version}")
                else:
                    result = conn.execute(text("SELECT sqlite_version()"))
                    version = result.scalar()
                    logger.info(f"Connected to SQLite: {version}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def create_tables(self):
        """Create all tables in the database"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_engine(self) -> Engine:
        """Get the SQLAlchemy engine"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        return self.engine
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the current database configuration"""
        return {
            "type": self.database_type,
            "url": self.database_url if self.database_type == "postgresql" else None,
            "engine": str(self.engine.url) if self.engine else None,
            "pool_size": self.engine.pool.size() if self.engine and hasattr(self.engine.pool, 'size') else None,
        }


# Global instance
_db_config: Optional[DatabaseConfig] = None


def get_db_config() -> DatabaseConfig:
    """Get or create the global database configuration"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_session() -> Session:
    """Get a new database session"""
    return get_db_config().get_session()


def close_db():
    """Close database connections"""
    global _db_config
    if _db_config:
        _db_config.close()
        _db_config = None