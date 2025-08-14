# Database Setup Guide

This guide covers setting up the database for local development and production deployment. **DhafnckMCP uses a dual database architecture:**

- **Production**: Supabase cloud PostgreSQL (fully managed, global scale)
- **Local Development**: PostgreSQL Docker container (full feature parity with production)

> **🎯 Architecture:** This dual setup ensures development-production parity while leveraging Supabase's managed cloud services for production scale and global deployment.

> **🔧 Important:** The dual PostgreSQL architecture provides optimal performance, data integrity, and scalability for both local development and cloud production.

## Quick Start

### Production Setup: Supabase Cloud PostgreSQL
```bash
# Create a Supabase project at https://supabase.com
# Get your connection details from Settings > Database

export DATABASE_TYPE=supabase
export SUPABASE_URL=https://[project-ref].supabase.co
export SUPABASE_ANON_KEY=your-anon-key
export SUPABASE_DB_PASSWORD=your-database-password

# Run the application
python src/main.py
```

### Local Development: PostgreSQL Docker Container
```bash
# Start PostgreSQL and Redis containers
docker-compose up -d postgres redis

# Set environment variables for local development
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/dhafnck_mcp_dev

# Run the application
python src/main.py
```

### Option 3: SQLite (⚠️ DEPRECATED - Legacy Support Only)
```bash
# ⚠️ WARNING: SQLite is DEPRECATED and will be removed in future versions
# Limited concurrent access, inferior performance, and no production support
# STRONGLY RECOMMENDED: Use PostgreSQL instead

export DATABASE_TYPE=sqlite
# DATABASE_URL is auto-configured based on execution mode

# Run the application
python src/main.py
```

## Database Schema

The project supports both PostgreSQL and SQLite with automatic schema handling:

- **PostgreSQL Schema**: Native JSONB fields with optimal indexing and performance
- **SQLite Schema**: TEXT-based JSON fields with compatibility functions (legacy support)

All schema management is handled automatically by the ORM layer.

## JSON Field Compatibility

| Database | JSON Fields | Query Support |
|----------|-------------|---------------|
| SQLite | TEXT | `JSON_EXTRACT()`, `JSON_SET()`, `JSON_PATCH()` |
| PostgreSQL | JSONB | `->`, `->>`, `@>`, `jsonb_set()`, `||` |

The `DatabaseAdapter` class handles these differences automatically.

## Migration to PostgreSQL

When migrating from legacy SQLite to PostgreSQL (recommended):

```bash
# 1. Start local PostgreSQL
docker-compose -f docker-compose.dev.yml up -d

# 2. Run migration script
python scripts/migrate_to_postgresql.py \
  --sqlite-path ./dhafnck_mcp.db \
  --postgresql-url postgresql://dev_user:dev_password@localhost:5432/dhafnck_mcp_dev

# 3. Test with PostgreSQL locally
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/dhafnck_mcp_dev
python src/main.py

# 4. Deploy to Supabase
python scripts/migrate_to_postgresql.py \
  --sqlite-path ./dhafnck_mcp.db \
  --postgresql-url postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
```

## Environment Configuration

Copy and modify `.env.example`:

```bash
cp .env.example .env
```

### Local Development (PostgreSQL - Recommended)
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/dhafnck_mcp_dev
```

### Production (Supabase)
```env
DATABASE_TYPE=supabase
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres?sslmode=require
```

### Legacy Development (SQLite - ⚠️ DEPRECATED)
```env
# ⚠️ DEPRECATED: SQLite support will be removed in future versions
# Use PostgreSQL for better performance and concurrent access
DATABASE_TYPE=sqlite
# DATABASE_URL is auto-configured based on execution mode
```

## Docker Development Setup

The `docker-compose.dev.yml` provides:
- PostgreSQL 15 with automatic schema initialization
- Redis for caching
- Persistent volumes for data

```bash
# Start services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down

# Clean up (removes data)
docker-compose -f docker-compose.dev.yml down -v
```

## Database Features

### Hierarchical Context System
- **Global Context**: Organization-wide settings (singleton)
- **Project Context**: Project-specific settings (inherits from global)
- **Task Context**: Task-specific data (inherits from project)

### JSON Field Support
- **SQLite**: Uses TEXT fields with JSON functions
- **PostgreSQL**: Uses JSONB fields with native JSON operators

### Caching
- **Context Inheritance Cache**: Speeds up context resolution
- **Redis Support**: Optional Redis caching for improved performance

## Troubleshooting

### Common Issues

1. **"JSONB not supported in SQLite"**
   - Solution: Use the correct schema file for your database type

2. **Connection refused to PostgreSQL**
   - Solution: Ensure Docker containers are running: `docker-compose -f docker-compose.dev.yml up -d`

3. **Migration fails with foreign key errors**
   - Solution: Ensure tables are migrated in dependency order (handled by migration script)

### Database Verification

```bash
# Check SQLite tables
sqlite3 dhafnck_mcp.db ".tables"

# Check PostgreSQL tables
psql postgresql://dev_user:dev_password@localhost:5432/dhafnck_mcp_dev -c "\dt"
```

### Performance Tips

1. **Use PostgreSQL**: Superior JSON support, concurrent access, and performance
2. **Enable connection pooling**: Set `DB_POOL_SIZE=20` and `DB_MAX_OVERFLOW=40`
3. **Use Redis caching**: Set `REDIS_URL=redis://localhost:6379` in environment
4. **Monitor query performance**: Enable SQL logging with `DEBUG=true`
5. **Supabase for production**: Built-in connection pooling and global edge network

## Schema Updates

When updating the schema:

1. Modify the ORM models in `src/fastmcp/task_management/infrastructure/database/models.py`
2. Test with PostgreSQL locally using Docker
3. Update the `DatabaseAdapter` if new JSON operations are needed
4. Test migration scripts for SQLite compatibility (legacy support)
5. Deploy to Supabase with proper backup procedures