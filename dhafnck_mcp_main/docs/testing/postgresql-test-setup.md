# PostgreSQL Test Database Setup

This document explains how to configure and use PostgreSQL for all tests in the DhafnckMCP project.

## Overview

The test suite is configured to use PostgreSQL for all tests to ensure consistency with the production environment. Tests use a separate PostgreSQL database to maintain isolation from development and production data.

## Quick Start

1. **Start the PostgreSQL test database:**
   ```bash
   ./scripts/start-test-db.sh
   ```

2. **Run tests:**
   ```bash
   uv run python -m pytest dhafnck_mcp_main/src/tests/ -v
   ```

3. **Stop the test database:**
   ```bash
   docker-compose -f docker-compose.test.yml down
   ```

## Configuration

### Environment Variables

The test configuration automatically sets up the following environment variables:

- `DATABASE_TYPE=postgresql` - Forces PostgreSQL usage
- `DATABASE_URL` - Fixed and configured test database URL
- `DISABLE_AUTH=true` - Disables authentication for tests
- `DHAFNCK_ENABLE_VISION=true` - Enables vision system for tests

### Test Database URL

The test suite will use one of the following in order of preference:

1. **TEST_DATABASE_URL** environment variable (if set)
2. **Local PostgreSQL** at `postgresql://postgres:test@localhost:5432/dhafnck_mcp_test`
3. **Fixed production URL** with test schema (if no local PostgreSQL)

### Docker Compose Configuration

The `docker-compose.test.yml` file sets up a PostgreSQL 15 Alpine container with:

- **Container name:** dhafnck_postgres_test
- **Port:** 5432
- **Database:** dhafnck_mcp_test
- **User:** postgres
- **Password:** test

## Test Isolation

Each test function gets a fresh database state through the following mechanisms:

1. **Schema Recreation:** Database schema is recreated for each test
2. **Transaction Rollback:** Tests run in transactions that are rolled back
3. **Test Data:** Basic test data (default project and branch) is created automatically

## Troubleshooting

### Connection Refused Error

If you see:
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

**Solution:** Start the PostgreSQL test database:
```bash
./scripts/start-test-db.sh
```

### DNS Resolution Error

If you see:
```
could not translate host name "db.dmuqoeppsoesqcijrwhw.supabase.co" to address: Name or service not known
```

**Solution:** Ensure TEST_DATABASE_URL is properly set or use local PostgreSQL.

### Malformed URL Error

If you see:
```
connection to server on socket "@@@db.dmuqoeppsoesqcijrwhw.supabase.co/.s.PGSQL.5432" failed
```

**Solution:** The test configuration automatically fixes malformed URLs. If this persists, check your DATABASE_URL environment variable.

## Advanced Configuration

### Using a Custom PostgreSQL Instance

Set the TEST_DATABASE_URL environment variable:
```bash
export TEST_DATABASE_URL="postgresql://user:password@host:port/database"
uv run python -m pytest dhafnck_mcp_main/src/tests/ -v
```

### Using Production Database with Test Schema

To use the production database with a test schema (not recommended):
```bash
unset TEST_DATABASE_URL
uv run python -m pytest dhafnck_mcp_main/src/tests/ -v
```

The test configuration will automatically:
1. Fix malformed URLs
2. Create a test schema
3. Isolate test data

## Best Practices

1. **Always use the test database** - Never run tests against production
2. **Start fresh** - Restart the test database if tests behave unexpectedly
3. **Check logs** - PostgreSQL logs are available via Docker:
   ```bash
   docker logs dhafnck_postgres_test
   ```
4. **Clean up** - Stop the test database when not in use to free resources

## CI/CD Integration

For CI/CD pipelines, use the Docker Compose service:

```yaml
# Example GitHub Actions
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: test
      POSTGRES_DB: dhafnck_mcp_test
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

## Related Documentation

- [Testing Guide](../testing.md)
- [Database Configuration](../configuration.md)
- [Docker Deployment](../docker-deployment.md)