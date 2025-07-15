"""Core configuration for dhafnck-db-server."""

import os
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseSettings, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PROJECT_NAME: str = "dhafnck Database Server"
    PROJECT_VERSION: str = "0.1.0"
    PROJECT_DESCRIPTION: str = "Database server for dhafnck_mcp project"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/dhafnck_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Supabase Configuration
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # JWT Configuration
    JWT_SECRET: str = "your-super-secret-jwt-signing-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    
    # Redis Configuration
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_CACHE_TTL: int = 300  # 5 minutes
    
    # CORS Configuration
    CORS_ORIGINS: List[AnyHttpUrl] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Performance Configuration
    QUERY_CACHE_TTL: int = 300
    CONNECTION_POOL_SIZE: int = 10
    CONNECTION_POOL_OVERFLOW: int = 20
    QUERY_TIMEOUT: int = 30
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 5
    HEALTH_CHECK_RETRIES: int = 3
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret length."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    class Config:
        """Pydantic configuration."""
        
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Database URL for SQLAlchemy
def get_database_url() -> str:
    """Get database URL for SQLAlchemy."""
    return settings.DATABASE_URL.replace("postgres://", "postgresql://")


# Redis URL
def get_redis_url() -> Optional[str]:
    """Get Redis URL with authentication."""
    if not settings.REDIS_URL:
        return None
    
    url = settings.REDIS_URL
    if settings.REDIS_PASSWORD:
        # Insert password into URL
        if "://" in url:
            protocol, rest = url.split("://", 1)
            url = f"{protocol}://:{settings.REDIS_PASSWORD}@{rest}"
    
    return url


# Logging configuration
def get_log_config() -> dict:
    """Get logging configuration."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "json": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
        },
        "handlers": {
            "default": {
                "formatter": "json" if settings.LOG_FORMAT == "json" else "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "json" if settings.LOG_FORMAT == "json" else "default",
                "class": "logging.FileHandler",
                "filename": settings.LOG_FILE,
            } if settings.LOG_FILE else None,
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["default"] + (["file"] if settings.LOG_FILE else []),
        },
    }