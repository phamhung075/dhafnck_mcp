# Database Setup Guide

This guide covers setting up the database for local development and production deployment.

## Quick Start

### Option 1: SQLite (Default for local development)
```bash
# Uses SQLite by default - no additional setup required
python src/main.py
```

### Option 2: PostgreSQL with Docker (Recommended for development)
```bash
# Start PostgreSQL and Redis
docker-compose -f docker-compose.dev.yml up -d

# Set environment variables
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/dhafnck_mcp_dev

# Run the application
python src/main.py
```

### Option 3: Supabase (Production)
```bash
# Create a Supabase project at https://supabase.com
# Get your connection string from Settings > Database

export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# Run the application
python src/main.py
```

## Database Schema

The project supports both SQLite and PostgreSQL:

- **SQLite Schema**: `database/schema/00_base_schema.sql` (uses TEXT for JSON fields)
- **PostgreSQL Schema**: `database/schema/postgresql/00_base_schema.sql` (uses JSONB for JSON fields)

## JSON Field Compatibility

| Database | JSON Fields | Query Support |
|----------|-------------|---------------|
| SQLite | TEXT | `JSON_EXTRACT()`, `JSON_SET()`, `JSON_PATCH()` |
| PostgreSQL | JSONB | `->`, `->>`, `@>`, `jsonb_set()`, `||` |

The `DatabaseAdapter` class handles these differences automatically.

## Migration from SQLite to PostgreSQL

When you're ready to deploy to production:

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

### Local Development (SQLite)
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./dhafnck_mcp.db
```

### Local Development (PostgreSQL)
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/dhafnck_mcp_dev
```

### Production (Supabase)
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
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

1. **Use PostgreSQL for production**: Better JSON support and performance
2. **Enable connection pooling**: Set `DATABASE_POOL_SIZE=10` in environment
3. **Use Redis caching**: Set `REDIS_URL=redis://localhost:6379` in environment
4. **Monitor query performance**: Enable SQL logging with `DEBUG=true`

## Schema Updates

When updating the schema:

1. Update both SQLite and PostgreSQL schema files
2. Test migrations with the migration script
3. Update the `DatabaseAdapter` if new JSON operations are needed
4. Test with both database types locally before deploying